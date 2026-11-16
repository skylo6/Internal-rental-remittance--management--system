
import tkinter as tk
from tkinter import ttk, messagebox

from modules.notifications import (
    get_notifications,
    get_unread_count,
    mark_notification_read,
    mark_all_notifications_read,
)


class NotificationsPage:
    def __init__(self, parent, user):
        self.parent = parent
        self.user = user
        self.user_id = user["id"]

        self.build_ui()
        self.refresh_notifications()

    def build_ui(self):
        self.parent.configure(bg="#F3F5F9")

        heading = tk.Frame(self.parent, bg="#F3F5F9")
        heading.pack(fill="x", pady=(0, 15))

        tk.Label(
            heading,
            text="Notification Centre",
            font=("Segoe UI", 22, "bold"),
            bg="#F3F5F9",
            fg="#142D4E"
        ).pack(anchor="w")

        tk.Label(
            heading,
            text="View updates and manage your unread notifications.",
            font=("Segoe UI", 10),
            bg="#F3F5F9",
            fg="#64748B"
        ).pack(anchor="w", pady=(4, 0))

        self.unread_label = tk.Label(
            heading,
            text="Unread notifications: 0",
            font=("Segoe UI", 11, "bold"),
            bg="#F3F5F9",
            fg="#D97706"
        )
        self.unread_label.pack(anchor="w", pady=(10, 0))

        toolbar = tk.Frame(self.parent, bg="#F3F5F9")
        toolbar.pack(fill="x", pady=(0, 10))

        ttk.Button(
            toolbar,
            text="Refresh",
            command=self.refresh_notifications
        ).pack(side="left", padx=(0, 8))

        ttk.Button(
            toolbar,
            text="Mark Selected as Read",
            command=self.mark_selected_read
        ).pack(side="left", padx=(0, 8))

        ttk.Button(
            toolbar,
            text="Mark All as Read",
            command=self.mark_all_read
        ).pack(side="left")

        table_frame = tk.Frame(self.parent, bg="white")
        table_frame.pack(fill="both", expand=True)

        columns = (
            "status",
            "category",
            "title",
            "message",
            "created_at"
        )

        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            selectmode="browse"
        )

        self.tree.heading("status", text="Status")
        self.tree.heading("category", text="Category")
        self.tree.heading("title", text="Title")
        self.tree.heading("message", text="Message")
        self.tree.heading("created_at", text="Date")

        self.tree.column("status", width=90, anchor="center")
        self.tree.column("category", width=140)
        self.tree.column("title", width=180)
        self.tree.column("message", width=350)
        self.tree.column("created_at", width=160)

        scrollbar = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(
            side="left",
            fill="both",
            expand=True,
            padx=(8, 0),
            pady=8
        )
        scrollbar.pack(side="right", fill="y", pady=8, padx=(0, 8))

        self.tree.tag_configure(
            "unread",
            font=("Segoe UI", 9, "bold")
        )

        self.tree.tag_configure(
            "read",
            font=("Segoe UI", 9)
        )

    def refresh_notifications(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        try:
            notifications = get_notifications(self.user_id)
            unread_count = get_unread_count(self.user_id)

            self.unread_label.config(
                text=f"Unread notifications: {unread_count}"
            )

            for notification in notifications:
                is_read = bool(notification["is_read"])

                self.tree.insert(
                    "",
                    "end",
                    iid=str(notification["id"]),
                    values=(
                        "Read" if is_read else "Unread",
                        notification["category"].replace("_", " ").title(),
                        notification["title"],
                        notification["message"],
                        notification["created_at"]
                    ),
                    tags=("read" if is_read else "unread",)
                )

        except Exception as error:
            messagebox.showerror(
                "Notification Error",
                f"Could not load notifications.\n\n{error}",
                parent=self.parent
            )

    def mark_selected_read(self):
        selected = self.tree.selection()

        if not selected:
            messagebox.showwarning(
                "No Selection",
                "Select a notification first.",
                parent=self.parent
            )
            return

        try:
            notification_id = int(selected[0])

            mark_notification_read(
                notification_id,
                self.user_id
            )

            self.refresh_notifications()

        except Exception as error:
            messagebox.showerror(
                "Update Error",
                f"Could not mark notification as read.\n\n{error}",
                parent=self.parent
            )

    def mark_all_read(self):
        try:
            mark_all_notifications_read(self.user_id)
            self.refresh_notifications()

        except Exception as error:
            messagebox.showerror(
                "Update Error",
                f"Could not mark notifications as read.\n\n{error}",
                parent=self.parent
            )
