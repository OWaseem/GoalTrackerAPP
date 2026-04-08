import sys
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from db import init_db, add_goal, update_goal, list_goals, mark_done, mark_pending, delete_goal, get_goal


# ── Colours & fonts ───────────────────────────────────────────────────────────
BG          = "#1e1e2e"
SURFACE     = "#2a2a3d"
ACCENT      = "#7c6af7"
ACCENT_DARK = "#5a4fd6"
TEXT        = "#cdd6f4"
SUBTEXT     = "#a6adc8"
RED         = "#f38ba8"
YELLOW      = "#f9e2af"
GREEN       = "#a6e3a1"
FONT        = ("SF Pro Display", 13)
FONT_BOLD   = ("SF Pro Display", 13, "bold")
FONT_TITLE  = ("SF Pro Display", 20, "bold")
FONT_SMALL  = ("SF Pro Display", 11)
FONT_TINY   = ("SF Pro Display", 10)


# ── Goal Dialog (Add & Edit) ──────────────────────────────────────────────────
class GoalDialog(tk.Toplevel):
    def __init__(self, parent, goal=None):
        super().__init__(parent)
        self._editing = goal is not None
        self.title("Edit Goal" if self._editing else "Add Goal")
        self.resizable(False, False)
        self.configure(bg=BG)
        self.result = None
        self._goal = goal

        self._build()
        self.grab_set()
        self.transient(parent)

        self.update_idletasks()
        px, py = parent.winfo_x(), parent.winfo_y()
        pw, ph = parent.winfo_width(), parent.winfo_height()
        w, h = self.winfo_width(), self.winfo_height()
        self.geometry(f"+{px + (pw - w) // 2}+{py + (ph - h) // 2}")

    def _field(self, frame, label, row, placeholder=""):
        tk.Label(frame, text=label, bg=BG, fg=SUBTEXT, font=FONT_SMALL).grid(
            row=row, column=0, sticky="w", pady=(8, 2)
        )
        var = tk.StringVar(value=placeholder)
        entry = tk.Entry(
            frame, textvariable=var, font=FONT,
            bg=SURFACE, fg=TEXT, insertbackground=TEXT,
            relief="flat", width=36,
        )
        entry.grid(row=row + 1, column=0, sticky="ew", ipady=6, padx=2)
        return var, entry

    def _build(self):
        frame = tk.Frame(self, bg=BG, padx=28, pady=24)
        frame.pack(fill="both", expand=True)

        heading = "Edit Goal" if self._editing else "New Goal"
        tk.Label(frame, text=heading, bg=BG, fg=TEXT, font=FONT_TITLE).grid(
            row=0, column=0, sticky="w", pady=(0, 12)
        )

        g = self._goal
        self.title_var, title_entry = self._field(frame, "Title *", 1, g.title if g else "")
        self.desc_var,  _           = self._field(frame, "Description", 3, g.description if g else "")
        self.cat_var,   _           = self._field(frame, "Category", 5, g.category if g else "general")

        if g and g.due_date:
            default_due = g.due_date.strftime("%m-%d-%Y")
        else:
            default_due = date.today().strftime("%m-%d-%Y")
        self.due_var, _ = self._field(frame, "Due Date  (MM-DD-YYYY)", 7, default_due)

        title_entry.focus_set()

        btn_frame = tk.Frame(frame, bg=BG)
        btn_frame.grid(row=9, column=0, sticky="e", pady=(20, 0))

        tk.Button(
            btn_frame, text="Cancel", command=self.destroy,
            bg=SURFACE, fg=SUBTEXT, font=FONT, relief="flat",
            padx=16, pady=8, cursor="hand2",
            activebackground=SURFACE, activeforeground=TEXT,
        ).pack(side="left", padx=(0, 8))

        btn_label = "Save Changes" if self._editing else "Add Goal"
        tk.Button(
            btn_frame, text=btn_label, command=self._submit,
            bg=ACCENT, fg="white", font=FONT_BOLD, relief="flat",
            padx=16, pady=8, cursor="hand2",
            activebackground=ACCENT_DARK, activeforeground="white",
        ).pack(side="left")

        self.bind("<Return>", lambda _: self._submit())
        self.bind("<Escape>", lambda _: self.destroy())

    def _submit(self):
        title = self.title_var.get().strip()
        if not title:
            messagebox.showwarning("Missing Title", "Please enter a goal title.", parent=self)
            return

        due_date = None
        due_str = self.due_var.get().strip()
        if due_str:
            try:
                due_date = datetime.strptime(due_str, "%m-%d-%Y").date()
            except ValueError:
                messagebox.showerror("Invalid Date", "Use MM-DD-YYYY format.", parent=self)
                return

        self.result = {
            "title":       title,
            "description": self.desc_var.get().strip(),
            "category":    self.cat_var.get().strip() or "general",
            "due_date":    due_date,
        }
        self.destroy()


# ── Main App ──────────────────────────────────────────────────────────────────
class GoalTrackerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Goal Tracker")
        self.geometry("860x620")
        self.minsize(700, 480)
        self.configure(bg=BG)

        init_db()
        self._build()
        self._refresh()

    def _build(self):
        # Header
        header = tk.Frame(self, bg=BG, padx=24, pady=16)
        header.pack(fill="x")

        tk.Label(header, text="Goal Tracker", bg=BG, fg=TEXT, font=FONT_TITLE).pack(side="left")
        self.stats_label = tk.Label(header, text="", bg=BG, fg=SUBTEXT, font=FONT_SMALL)
        self.stats_label.pack(side="left", padx=20)

        tk.Button(
            header, text="+ Add Goal", command=self._open_add_dialog,
            bg=ACCENT, fg="white", font=FONT_BOLD, relief="flat",
            padx=14, pady=7, cursor="hand2",
            activebackground=ACCENT_DARK, activeforeground="white",
        ).pack(side="right")

        # Filter bar
        filter_bar = tk.Frame(self, bg=SURFACE, padx=24, pady=10)
        filter_bar.pack(fill="x")

        tk.Label(filter_bar, text="Status:", bg=SURFACE, fg=SUBTEXT, font=FONT_SMALL).pack(side="left")
        self.status_var = tk.StringVar(value="All")
        status_menu = ttk.Combobox(
            filter_bar, textvariable=self.status_var,
            values=["All", "pending", "done"],
            state="readonly", width=10, font=FONT_SMALL,
        )
        status_menu.pack(side="left", padx=(4, 20))
        status_menu.bind("<<ComboboxSelected>>", lambda _: self._refresh())

        tk.Label(filter_bar, text="Category:", bg=SURFACE, fg=SUBTEXT, font=FONT_SMALL).pack(side="left")
        self.cat_var = tk.StringVar(value="All")
        self.cat_menu = ttk.Combobox(
            filter_bar, textvariable=self.cat_var,
            state="readonly", width=14, font=FONT_SMALL,
        )
        self.cat_menu.pack(side="left", padx=(4, 0))
        self.cat_menu.bind("<<ComboboxSelected>>", lambda _: self._refresh())

        # Scrollable card area
        container = tk.Frame(self, bg=BG)
        container.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(container, bg=BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.cards_frame = tk.Frame(self.canvas, bg=BG)
        self._canvas_win = self.canvas.create_window((0, 0), window=self.cards_frame, anchor="nw")

        self.cards_frame.bind("<Configure>", lambda e: self.canvas.configure(
            scrollregion=self.canvas.bbox("all")
        ))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfig(
            self._canvas_win, width=e.width
        ))
        self.canvas.bind_all("<MouseWheel>", lambda e: self.canvas.yview_scroll(
            int(-1 * (e.delta / 120)), "units"
        ))

    # ── Data ──────────────────────────────────────────────────────────────────
    def _refresh(self):
        status   = self.status_var.get() if self.status_var.get() != "All" else None
        category = self.cat_var.get()    if self.cat_var.get()    != "All" else None

        goals     = list_goals(status=status, category=category)
        all_goals = list_goals()

        cats = sorted({g.category for g in all_goals})
        self.cat_menu["values"] = ["All"] + cats

        pending = sum(1 for g in all_goals if g.status == "pending")
        done    = sum(1 for g in all_goals if g.status == "done")
        self.stats_label.config(text=f"{pending} pending  ·  {done} done")

        for w in self.cards_frame.winfo_children():
            w.destroy()

        if not goals:
            tk.Label(
                self.cards_frame,
                text="No goals yet — click + Add Goal to get started.",
                bg=BG, fg=SUBTEXT, font=FONT,
            ).pack(pady=40)
            return

        today = date.today()
        for i, g in enumerate(goals):
            self._build_card(g, i + 1, today)

    # ── Card ──────────────────────────────────────────────────────────────────
    def _build_card(self, g, num, today):
        if g.status == "done":
            due_color   = GREEN
            due_text    = g.due_date.strftime("%m-%d-%Y") if g.due_date else ""
            toggle_text = "Pending"
            toggle_bg   = YELLOW
            toggle_fg   = BG
            toggle_cmd  = lambda gid=g.id: self._mark_pending(gid)
        elif g.due_date and g.due_date < today:
            due_color   = RED
            due_text    = g.due_date.strftime("%m-%d-%Y") + "  ·  overdue"
            toggle_text = "Done"
            toggle_bg   = GREEN
            toggle_fg   = BG
            toggle_cmd  = lambda gid=g.id: self._mark_done(gid)
        elif g.due_date and g.due_date == today:
            due_color   = YELLOW
            due_text    = "Due today"
            toggle_text = "Done"
            toggle_bg   = GREEN
            toggle_fg   = BG
            toggle_cmd  = lambda gid=g.id: self._mark_done(gid)
        else:
            due_color   = SUBTEXT
            due_text    = g.due_date.strftime("%m-%d-%Y") if g.due_date else ""
            toggle_text = "Done"
            toggle_bg   = GREEN
            toggle_fg   = BG
            toggle_cmd  = lambda gid=g.id: self._mark_done(gid)

        card = tk.Frame(self.cards_frame, bg=SURFACE, padx=20, pady=14)
        card.pack(fill="x", padx=20, pady=(8, 0))

        # Top row: number + title/description + category badge
        top = tk.Frame(card, bg=SURFACE)
        top.pack(fill="x")

        tk.Label(top, text=str(num), bg=SURFACE, fg=SUBTEXT,
                 font=FONT_SMALL, width=2).pack(side="left", padx=(0, 10), anchor="n")

        body = tk.Frame(top, bg=SURFACE)
        body.pack(side="left", fill="x", expand=True)

        tk.Label(body, text=g.title, bg=SURFACE, fg=TEXT,
                 font=FONT_BOLD, anchor="w").pack(fill="x")
        if g.description:
            tk.Label(body, text=g.description, bg=SURFACE, fg=SUBTEXT,
                     font=FONT_SMALL, anchor="w", wraplength=520, justify="left").pack(fill="x", pady=(2, 0))

        tk.Label(top, text=g.category, bg=ACCENT, fg="white",
                 font=FONT_TINY, padx=8, pady=3).pack(side="right", anchor="n")

        # Bottom row: due date + action buttons
        bottom = tk.Frame(card, bg=SURFACE)
        bottom.pack(fill="x", pady=(10, 0))

        if due_text:
            tk.Label(bottom, text=due_text, bg=SURFACE, fg=due_color,
                     font=FONT_SMALL).pack(side="left")

        btn_frame = tk.Frame(bottom, bg=SURFACE)
        btn_frame.pack(side="right")

        tk.Button(
            btn_frame, text=toggle_text, command=toggle_cmd,
            bg=toggle_bg, fg=toggle_fg, font=FONT_SMALL, relief="flat",
            padx=10, pady=4, cursor="hand2",
        ).pack(side="left", padx=(0, 6))

        tk.Button(
            btn_frame, text="Edit", command=lambda gid=g.id: self._edit(gid),
            bg=ACCENT, fg="white", font=FONT_SMALL, relief="flat",
            padx=10, pady=4, cursor="hand2",
            activebackground=ACCENT_DARK, activeforeground="white",
        ).pack(side="left", padx=(0, 6))

        tk.Button(
            btn_frame, text="Remove", command=lambda gid=g.id: self._delete(gid),
            bg=RED, fg=BG, font=FONT_SMALL, relief="flat",
            padx=10, pady=4, cursor="hand2",
        ).pack(side="left")

    # ── Actions ───────────────────────────────────────────────────────────────
    def _open_add_dialog(self):
        dlg = GoalDialog(self)
        self.wait_window(dlg)
        if dlg.result:
            add_goal(**dlg.result)
            self._refresh()

    def _edit(self, goal_id):
        goal = get_goal(goal_id)
        if not goal:
            return
        dlg = GoalDialog(self, goal=goal)
        self.wait_window(dlg)
        if dlg.result:
            update_goal(goal_id, **dlg.result)
            self._refresh()

    def _mark_done(self, goal_id):
        mark_done(goal_id)
        self._refresh()

    def _mark_pending(self, goal_id):
        mark_pending(goal_id)
        self._refresh()

    def _delete(self, goal_id):
        goal = get_goal(goal_id)
        if goal and messagebox.askyesno("Remove Goal", f'Remove "{goal.title}"?'):
            delete_goal(goal_id)
            self._refresh()


if __name__ == "__main__":
    app = GoalTrackerApp()
    app.mainloop()
