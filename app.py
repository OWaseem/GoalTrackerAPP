import json
import os

from flask import Flask, request, jsonify, send_from_directory
from datetime import date
from pywebpush import webpush, WebPushException
from apscheduler.schedulers.background import BackgroundScheduler
import atexit

from db import (
    init_db, add_goal, update_goal, list_goals, mark_done, mark_pending,
    delete_goal, get_goal, get_due_today, get_overdue,
    save_subscription, get_all_subscriptions, delete_subscription,
)

app = Flask(__name__, static_folder="static", static_url_path="")

VAPID_PRIVATE_KEY = os.environ.get("VAPID_PRIVATE_KEY")
VAPID_PUBLIC_KEY  = os.environ.get("VAPID_PUBLIC_KEY")
VAPID_CLAIMS      = {"sub": "mailto:noreply@goaltracker.app"}

init_db()


# ── Push notification job ─────────────────────────────────────────────────────

def _send_push(subscription, title, body):
    try:
        webpush(
            subscription_info=subscription,
            data=json.dumps({"title": title, "body": body}),
            vapid_private_key=VAPID_PRIVATE_KEY,
            vapid_claims=VAPID_CLAIMS,
        )
    except WebPushException as e:
        if e.response is not None and e.response.status_code == 410:
            delete_subscription(subscription["endpoint"])


def check_and_notify():
    if not VAPID_PRIVATE_KEY:
        return
    subscriptions = get_all_subscriptions()
    if not subscriptions:
        return
    for goal in get_overdue():
        for sub in subscriptions:
            _send_push(sub, "Overdue Goal",
                       f'"{goal.title}" was due {goal.due_date} and is still pending.')
    for goal in get_due_today():
        for sub in subscriptions:
            _send_push(sub, "Goal Due Today", f'"{goal.title}" is due today!')


# Start scheduler (skip in Flask reloader child process)
if not app.debug or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
    scheduler = BackgroundScheduler()
    scheduler.add_job(check_and_notify, "cron", hour=9, minute=0)
    scheduler.start()
    atexit.register(scheduler.shutdown)


# ── Static / PWA ──────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return send_from_directory("static", "index.html")


# ── Push API ──────────────────────────────────────────────────────────────────

@app.route("/api/vapid-public-key")
def vapid_public_key():
    return jsonify({"publicKey": VAPID_PUBLIC_KEY})


@app.route("/api/subscribe", methods=["POST"])
def subscribe():
    save_subscription(request.json)
    return "", 201


# ── Test endpoint ─────────────────────────────────────────────────────────────

@app.route("/api/test-notify", methods=["POST"])
def test_notify():
    subscriptions = get_all_subscriptions()
    if not subscriptions:
        return jsonify({"error": "No subscriptions found. Make sure you accepted notifications on your iPhone."}), 400
    for sub in subscriptions:
        _send_push(sub, "Goal Tracker Test", "Push notifications are working on your iPhone!")
    return jsonify({"sent": len(subscriptions)})


# ── Goals API ─────────────────────────────────────────────────────────────────

@app.route("/api/goals", methods=["GET"])
def get_goals():
    status   = request.args.get("status") or None
    category = request.args.get("category") or None
    goals     = list_goals(status=status, category=category)
    all_goals = list_goals()
    return jsonify({
        "goals": [_to_dict(g) for g in goals],
        "stats": {
            "pending":    sum(1 for g in all_goals if g.status == "pending"),
            "done":       sum(1 for g in all_goals if g.status == "done"),
            "categories": sorted({g.category for g in all_goals}),
        },
    })


@app.route("/api/goals", methods=["POST"])
def create_goal():
    data = request.json
    due_date = date.fromisoformat(data["due_date"]) if data.get("due_date") else None
    goal = add_goal(
        title=data["title"],
        description=data.get("description", ""),
        category=data.get("category", "general"),
        due_date=due_date,
    )
    return jsonify(_to_dict(goal)), 201


@app.route("/api/goals/<int:goal_id>", methods=["PUT"])
def edit_goal(goal_id):
    data = request.json
    due_date = date.fromisoformat(data["due_date"]) if data.get("due_date") else None
    goal = update_goal(
        goal_id,
        title=data["title"],
        description=data.get("description", ""),
        category=data.get("category", "general"),
        due_date=due_date,
    )
    if not goal:
        return jsonify({"error": "Not found"}), 404
    return jsonify(_to_dict(goal))


@app.route("/api/goals/<int:goal_id>", methods=["DELETE"])
def remove_goal(goal_id):
    if delete_goal(goal_id):
        return "", 204
    return jsonify({"error": "Not found"}), 404


@app.route("/api/goals/<int:goal_id>/done", methods=["PATCH"])
def done_goal(goal_id):
    mark_done(goal_id)
    return jsonify(_to_dict(get_goal(goal_id)))


@app.route("/api/goals/<int:goal_id>/pending", methods=["PATCH"])
def pending_goal(goal_id):
    mark_pending(goal_id)
    return jsonify(_to_dict(get_goal(goal_id)))


# ── Helper ────────────────────────────────────────────────────────────────────

def _to_dict(goal):
    return {
        "id":          goal.id,
        "title":       goal.title,
        "description": goal.description,
        "category":    goal.category,
        "due_date":    goal.due_date.isoformat() if goal.due_date else None,
        "status":      goal.status,
        "created_at":  goal.created_at,
    }


if __name__ == "__main__":
    app.run(debug=True)
