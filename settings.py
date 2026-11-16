
import tkinter as tk
from tkinter import ttk, messagebox

from database import get_connection
from auth import verify_password, hash_password


class SettingsPage:
    def __init__(self, parent, user=None):
        self.parent = parent
        self.user = user or {}

        self.username = self.user.get("username", "User")
        self.role = self.user.get("role", "manager")

        self.parent.configure(bg="#F3F5F9")

        self.create_settings_table()
        self.build_ui()
        self.load_preferences()

    def create_settings_table(self):
        """Create a table for saved notification preferences."""
        with get_connection() as connection:
            connection.execute("""
                CREATE TABLE IF NOT EXISTS notification_settings (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    rent_due INTEGER NOT NULL DEFAULT 1,
                    overdue_rent INTEGER NOT NULL DEFAULT 1,
                    payment_received INTEGER NOT NULL DEFAULT 1,
                    remittance_updates INTEGER NOT NULL DEFAULT 1,
                    expense_alerts INTEGER NOT NULL DEFAULT 0,
                    system_alerts INTEGER NOT NULL DEFAULT 1,
                    frequency TEXT NOT NULL DEFAULT 'daily'
                )
            """)

            connection.execute("""
                INSERT OR IGNORE INTO notification_settings (id)
                VALUES (1)
            """)

    def build_ui(self):
        heading = tk.Frame(self.parent, bg="#F3F5F9")
        heading.pack(fill="x", pady=(0, 15))

        tk.Label(
            heading,
            text="Settings",
            font=("Segoe UI", 22, "bold"),
            bg="#F3F5F9",
            fg="#142D4E"
        ).pack(anchor="w")

        tk.Label(
            heading,
            text="Manage your application preferences.",
            font=("Segoe UI", 10),
            bg="#F3F5F9",
            fg="#64748B"
        ).pack(anchor="w", pady=(4, 0))

        self.tabs = ttk.Notebook(self.parent)
        self.tabs.pack(fill="both", expand=True)

        self.general_tab = tk.Frame(self.tabs, bg="white")
        self.notifications_tab = tk.Frame(self.tabs, bg="white")
        self.appearance_tab = tk.Frame(self.tabs, bg="white")
        self.backup_tab = tk.Frame(self.tabs, bg="white")
        self.password_tab = tk.Frame(self.tabs, bg="white")

        self.tabs.add(self.general_tab, text="General")
        self.tabs.add(self.notifications_tab, text="Notifications")
        self.tabs.add(self.appearance_tab, text="Appearance")
        self.tabs.add(self.backup_tab, text="Data & Backup")
        self.tabs.add(self.password_tab, text="Change Password")

        self.build_general_tab()
        self.build_notifications_tab()
        self.build_appearance_tab()
        self.build_backup_tab()
        self.build_password_tab()

    def build_general_tab(self):
        frame = tk.Frame(
            self.general_tab,
            bg="white",
            padx=25,
            pady=25
        )
        frame.pack(fill="both", expand=True)

        tk.Label(
            frame,
            text="Account Information",
            font=("Segoe UI", 15, "bold"),
            bg="white",
            fg="#142D4E"
        ).pack(anchor="w", pady=(0, 15))

        tk.Label(
            frame,
            text=f"Application: Ole Segeri Rental Remittance System",
            font=("Segoe UI", 11),
            bg="white",
            fg="#334155",
            wraplength=600,
            justify="left"
        ).pack(anchor="w", pady=5)

        tk.Label(
            frame,
            text=f"Username: {self.username}",
            font=("Segoe UI", 11),
            bg="white",
            fg="#334155"
        ).pack(anchor="w", pady=5)

        tk.Label(
            frame,
            text=f"Role: {self.role.capitalize()}",
            font=("Segoe UI", 11),
            bg="white",
            fg="#334155"
        ).pack(anchor="w", pady=5)

        tk.Label(
            frame,
            text="Currency: Kenyan Shilling (KSh)",
            font=("Segoe UI", 11),
            bg="white",
            fg="#334155"
        ).pack(anchor="w", pady=5)

    def build_notifications_tab(self):
        frame = tk.Frame(
            self.notifications_tab,
            bg="white",
            padx=25,
            pady=20
        )
        frame.pack(fill="both", expand=True)

        tk.Label(
            frame,
            text="Notification Preferences",
            font=("Segoe UI", 15, "bold"),
            bg="white",
            fg="#142D4E"
        ).pack(anchor="w", pady=(0, 5))

        tk.Label(
            frame,
            text="Choose which alerts you want the system to generate.",
            font=("Segoe UI", 10),
            bg="white",
            fg="#64748B",
            wraplength=600
        ).pack(anchor="w", pady=(0, 15))

        self.preference_vars = {
            "rent_due": tk.BooleanVar(value=True),
            "overdue_rent": tk.BooleanVar(value=True),
            "payment_received": tk.BooleanVar(value=True),
            "remittance_updates": tk.BooleanVar(value=True),
            "expense_alerts": tk.BooleanVar(value=False),
            "system_alerts": tk.BooleanVar(value=True),
        }

        labels = [
            ("rent_due", "Rent due reminders"),
            ("overdue_rent", "Overdue rent alerts"),
            ("payment_received", "Payment received confirmations"),
            ("remittance_updates", "Remittance updates"),
            ("expense_alerts", "Expense notifications"),
            ("system_alerts", "System alerts"),
        ]

        for key, label in labels:
            ttk.Checkbutton(
                frame,
                text=label,
                variable=self.preference_vars[key]
            ).pack(anchor="w", pady=5)

        tk.Label(
            frame,
            text="Reminder Frequency",
            font=("Segoe UI", 11, "bold"),
            bg="white",
            fg="#142D4E"
        ).pack(anchor="w", pady=(15, 5))

        self.frequency_var = tk.StringVar(value="daily")

        for value, label in [
            ("immediate", "Immediately"),
            ("daily", "Daily summary"),
            ("weekly", "Weekly summary"),
        ]:
            ttk.Radiobutton(
                frame,
                text=label,
                value=value,
                variable=self.frequency_var
            ).pack(anchor="w", pady=3)

        ttk.Button(
            frame,
            text="Save Notification Settings",
            command=self.save_preferences
        ).pack(anchor="w", pady=(20, 5))

    def load_preferences(self):
        """Load saved notification settings from SQLite."""
        try:
            with get_connection() as connection:
                row = connection.execute("""
                    SELECT *
                    FROM notification_settings
                    WHERE id = 1
                """).fetchone()

            if row:
                for key, variable in self.preference_vars.items():
                    variable.set(bool(row[key]))

                self.frequency_var.set(row["frequency"])

        except Exception as error:
            messagebox.showerror(
                "Settings Error",
                f"Could not load notification preferences.\n\n{error}",
                parent=self.parent
            )

    def save_preferences(self):
        """Save notification settings to SQLite."""
        frequency = self.frequency_var.get()

        if frequency not in ("immediate", "daily", "weekly"):
            messagebox.showerror(
                "Invalid Frequency",
                "Please select a valid reminder frequency.",
                parent=self.parent
            )
            return

        values = {
            key: int(variable.get())
            for key, variable in self.preference_vars.items()
        }

        try:
            with get_connection() as connection:
                connection.execute("""
                    UPDATE notification_settings
                    SET rent_due = ?,
                        overdue_rent = ?,
                        payment_received = ?,
                        remittance_updates = ?,
                        expense_alerts = ?,
                        system_alerts = ?,
                        frequency = ?
                    WHERE id = 1
                """, (
                    values["rent_due"],
                    values["overdue_rent"],
                    values["payment_received"],
                    values["remittance_updates"],
                    values["expense_alerts"],
                    values["system_alerts"],
                    frequency
                ))

            messagebox.showinfo(
                "Settings Saved",
                "Your notification preferences have been saved.",
                parent=self.parent
            )

        except Exception as error:
            messagebox.showerror(
                "Save Error",
                f"Could not save notification settings.\n\n{error}",
                parent=self.parent
            )

    def build_appearance_tab(self):
        tk.Label(
            self.appearance_tab,
            text="Appearance preferences will be added in the next step.",
            font=("Segoe UI", 11),
            bg="white",
            fg="#334155",
            wraplength=500
        ).pack(anchor="w", padx=25, pady=25)

    def build_backup_tab(self):
        tk.Label(
            self.backup_tab,
            text=(
                "Database backup and report export will be implemented "
                "after the notification settings are tested."
            ),
            font=("Segoe UI", 11),
            bg="white",
            fg="#334155",
            wraplength=500,
            justify="left"
        ).pack(anchor="w", padx=25, pady=25)

        
    def build_password_tab(self):
        """Display the form for changing the logged-in user's password."""
        frame = tk.Frame(
            self.password_tab,
            bg="white",
            padx=25,
            pady=25
        )
        frame.pack(fill="both", expand=True)

        tk.Label(
            frame,
            text="Change Password",
            font=("Segoe UI", 15, "bold"),
            bg="white",
            fg="#142D4E"
        ).pack(anchor="w", pady=(0, 8))

        tk.Label(
            frame,
            text="Enter your current password, then choose a new password.",
            font=("Segoe UI", 10),
            bg="white",
            fg="#64748B"
        ).pack(anchor="w", pady=(0, 20))

        self.current_password_var = tk.StringVar()
        self.new_password_var = tk.StringVar()
        self.confirm_password_var = tk.StringVar()

        fields = [
            ("Current password", self.current_password_var),
            ("New password", self.new_password_var),
            ("Confirm new password", self.confirm_password_var),
        ]

        for label_text, variable in fields:
            tk.Label(
                frame,
                text=label_text,
                font=("Segoe UI", 10, "bold"),
                bg="white",
                fg="#334155"
            ).pack(anchor="w", pady=(8, 4))

            ttk.Entry(
                frame,
                textvariable=variable,
                show="*",
                width=38
            ).pack(anchor="w", ipady=5)

        ttk.Button(
            frame,
            text="Update Password",
            command=self.change_password
        ).pack(anchor="w", pady=(22, 5))

    def change_password(self):
        """Verify the current password and securely update it."""
        current_password = self.current_password_var.get()
        new_password = self.new_password_var.get()
        confirm_password = self.confirm_password_var.get()

        if not current_password or not new_password or not confirm_password:
            messagebox.showerror(
                "Missing Information",
                "Please fill in all password fields.",
                parent=self.parent
            )
            return

        if len(new_password) < 8:
            messagebox.showerror(
                "Weak Password",
                "Your new password must contain at least 8 characters.",
                parent=self.parent
            )
            return

        if new_password != confirm_password:
            messagebox.showerror(
                "Password Mismatch",
                "The new password and confirmation do not match.",
                parent=self.parent
            )
            return

        try:
            with get_connection() as connection:
                user = connection.execute(
                    """
                    SELECT password_hash
                    FROM users
                    WHERE id = ? AND is_active = 1
                    """,
                    (self.user.get("id"),)
                ).fetchone()

                if user is None:
                    messagebox.showerror(
                        "Account Error",
                        "Your active account could not be found.",
                        parent=self.parent
                    )
                    return

                if not verify_password(
                    current_password,
                    user["password_hash"]
                ):
                    messagebox.showerror(
                        "Incorrect Password",
                        "Your current password is incorrect.",
                        parent=self.parent
                    )
                    return

                new_hash = hash_password(new_password)

                connection.execute(
                    """
                    UPDATE users
                    SET password_hash = ?
                    WHERE id = ? AND is_active = 1
                    """,
                    (new_hash, self.user["id"])
                )

            self.current_password_var.set("")
            self.new_password_var.set("")
            self.confirm_password_var.set("")

            messagebox.showinfo(
                "Password Updated",
                "Your password has been changed successfully.",
                parent=self.parent
            )

        except Exception as error:
            messagebox.showerror(
                "Password Error",
                f"Could not update your password.\n\n{error}",
                parent=self.parent
            )

