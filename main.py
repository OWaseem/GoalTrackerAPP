import sys
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from db import init_db, add_goal, update_goal, list_goals, mark_done, mark_pending, delete_goal, get_goal


# ── Colours & fonts ──────────────────────────────────────────────────────────
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

        # Centre over parent
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
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 12)
        )

        # Pre-fill values when editing
        g = self._goal
        self.title_var, title_entry = self._field(frame, "Title *", 1, g.title if g else "")
        self.desc_var,  _           = self._field(frame, "Description", 3, g.description if g else "")
        self.cat_var,   _           = self._field(frame, "Category", 5, g.category if g else "general")

        # Due date: pre-fill existing or default to today, formatted MM-DD-YYYY
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
        self.geometry("820x540")
        self.minsize(700, 440)
        self.configure(bg=BG)

        init_db()
        self._build()
        self._refresh()

    # ── Layout ────────────────────────────────────────────────────────────────
    def _build(self):
        # Header
        header = tk.Frame(self, bg=BG, padx=24, pady=18)
        header.pack(fill="x")

        tk.Label(header, text="Goal Tracker", bg=BG, fg=TEXT, font=FONT_TITLE).pack(side="left")

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

        # Table
        # Action buttons — packed before table so expand=True doesn't hide them
        btn_bar = tk.Frame(self, bg=BG, padx=24, pady=12)
        btn_bar.pack(fill="x", side="bottom")

        tk.Button(
            btn_bar, text="Mark Done", command=self._mark_done,
            bg=GREEN, fg=BG, font=FONT_BOLD, relief="flat",
            padx=14, pady=7, cursor="hand2",
            activebackground="#7ecf7a", activeforeground=BG,
        ).pack(side="left", padx=(0, 10))

        tk.Button(
            btn_bar, text="Mark Pending", command=self._mark_pending,
            bg=YELLOW, fg=BG, font=FONT_BOLD, relief="flat",
            padx=14, pady=7, cursor="hand2",
            activebackground="#e8cc80", activeforeground=BG,
        ).pack(side="left", padx=(0, 10))

        tk.Button(
            btn_bar, text="Edit", command=self._edit,
            bg=ACCENT, fg="white", font=FONT_BOLD, relief="flat",
            padx=14, pady=7, cursor="hand2",
            activebackground=ACCENT_DARK, activeforeground="white",
        ).pack(side="left", padx=(0, 10))

        tk.Button(
            btn_bar, text="Remove Goal", command=self._delete,
            bg=RED, fg=BG, font=FONT_BOLD, relief="flat",
            padx=14, pady=7, cursor="hand2",
            activebackground="#e06080", activeforeground=BG,
        ).pack(side="left")

        self.status_label = tk.Label(btn_bar, text="", bg=BG, fg=SUBTEXT, font=FONT_SMALL)
        self.status_label.pack(side="right")

        table_frame = tk.Frame(self, bg=BG, padx=24, pady=12)
        table_frame.pack(fill="both", expand=True)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview",
            background=SURFACE, fieldbackground=SURFACE,
            foreground=TEXT, font=FONT, rowheight=36,
        )
        style.configure("Treeview.Heading",
            background=BG, foreground=SUBTEXT,
            font=FONT_SMALL, relief="flat",
        )
        style.map("Treeview", background=[("selected", ACCENT)])

        cols = ("ID", "Title", "Category", "Due Date", "Status")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings", selectmode="browse")

        self.tree.heading("ID",       text="ID")
        self.tree.heading("Title",    text="Title")
        self.tree.heading("Category", text="Category")
        self.tree.heading("Due Date", text="Due Date")
        self.tree.heading("Status",   text="Status")

        self.tree.column("ID",       width=44,  anchor="center")
        self.tree.column("Title",    width=280, anchor="w")
        self.tree.column("Category", width=110, anchor="center")
        self.tree.column("Due Date", width=160, anchor="center")
        self.tree.column("Status",   width=90,  anchor="center")

        # Row colour tags
        self.tree.tag_configure("overdue",  foreground=RED)
        self.tree.tag_configure("today",    foreground=YELLOW)
        self.tree.tag_configure("done",     foreground=GREEN)
        self.tree.tag_configure("pending",  foreground=TEXT)

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")


    # ── Data ──────────────────────────────────────────────────────────────────
    def _refresh(self):
        status   = self.status_var.get() if self.status_var.get() != "All" else None
        category = self.cat_var.get()    if self.cat_var.get()    != "All" else None

        goals = list_goals(status=status, category=category)

        # Update category dropdown with current unique categories
        all_goals = list_goals()
        cats = sorted({g.category for g in all_goals})
        self.cat_menu["values"] = ["All"] + cats

        # Clear and repopulate table
        for row in self.tree.get_children():
            self.tree.delete(row)

        today = date.today()
        for i, g in enumerate(goals, start=1):
            due_str = g.due_date.strftime("%m-%d-%Y") if g.due_date else "—"

            if g.status == "done":
                tag = "done"
            elif g.due_date and g.due_date < today:
                due_str += "  (overdue)"
                tag = "overdue"
            elif g.due_date and g.due_date == today:
                due_str += "  (today)"
                tag = "today"
            else:
                tag = "pending"

            self.tree.insert("", "end", iid=str(g.id), values=(
                i, g.title, g.category, due_str, g.status
            ), tags=(tag,))

        pending = sum(1 for g in all_goals if g.status == "pending")
        done    = sum(1 for g in all_goals if g.status == "done")
        self.status_label.config(text=f"{pending} pending  ·  {done} done")

    # ── Actions ───────────────────────────────────────────────────────────────
    def _selected_id(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("No Selection", "Please select a goal first.")
            return None
        return int(sel[0])

    def _open_add_dialog(self):
        dlg = GoalDialog(self)
        self.wait_window(dlg)
        if dlg.result:
            add_goal(**dlg.result)
            self._refresh()

    def _edit(self):
        goal_id = self._selected_id()
        if goal_id is None:
            return
        goal = get_goal(goal_id)
        if goal is None:
            return
        dlg = GoalDialog(self, goal=goal)
        self.wait_window(dlg)
        if dlg.result:
            update_goal(goal_id, **dlg.result)
            self._refresh()

    def _mark_done(self):
        goal_id = self._selected_id()
        if goal_id is None:
            return
        goal = get_goal(goal_id)
        if goal and goal.status == "done":
            messagebox.showinfo("Already Done", f'"{goal.title}" is already marked as done.')
            return
        mark_done(goal_id)
        self._refresh()

    def _mark_pending(self):
        goal_id = self._selected_id()
        if goal_id is None:
            return
        goal = get_goal(goal_id)
        if goal and goal.status == "pending":
            messagebox.showinfo("Already Pending", f'"{goal.title}" is already pending.')
            return
        mark_pending(goal_id)
        self._refresh()

    def _delete(self):
        goal_id = self._selected_id()
        if goal_id is None:
            return
        goal = get_goal(goal_id)
        if goal and messagebox.askyesno("Remove Goal", f'Remove "{goal.title}"?'):
            delete_goal(goal_id)
            self._refresh()


if __name__ == "__main__":
    app = GoalTrackerApp()
    app.mainloop()
