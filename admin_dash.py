
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date

from database import get_connection
from auth import create_user

from ui.properties import PropertiesPage
from ui.properties import PropertiesPage
from ui.tenants import TenantsPage
from ui.payments_dash import PaymentDashboard
from ui.expenses import ExpensesPage
from ui.remittances import RemittancesPage
from ui.reports import ReportsPage


class AdminDashboard:
    def __init__(self, root, user, on_logout):
        self.root = root
        self.user = user
        self.on_logout = on_logout

        self.role = user["role"].strip().lower()
        self.username = user["username"]

        self.root.title("Ole Segere - Rental Remittance System")
        self.root.geometry("1100x700")
        self.root.minsize(900, 600)
        self.root.configure(bg="#F3F5F9")

        self.build_dashboard()

    def build_dashboard(self):
        # Clear the previous screen if rebuilding.
        for widget in self.root.winfo_children():
            widget.destroy()

        # Header
        header = tk.Frame(self.root, bg="#142D4E", height=70)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(
            header,
            text="OLE SEGERE | RENTAL REMITTANCE",
            font=("Segoe UI", 16, "bold"),
            bg="#142D4E",
            fg="white"
        ).pack(side="left", padx=25)

        tk.Button(
            header,
            text="Logout",
            font=("Segoe UI", 10, "bold"),
            bg="#E74C3C",
            fg="white",
            activebackground="#C0392B",
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            padx=15,
            pady=7,
            command=self.logout
        ).pack(side="right", padx=20)

        tk.Label(
            header,
            text=f"{self.role.capitalize()}: {self.username}",
            font=("Segoe UI", 10),
            bg="#142D4E",
            fg="white"
        ).pack(side="right", padx=10)

        # Sidebar
        sidebar = tk.Frame(self.root, bg="white", width=210)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        tk.Label(
            sidebar,
            text="MAIN MENU",
            font=("Segoe UI", 10, "bold"),
            bg="white",
            fg="#64748B"
        ).pack(anchor="w", padx=20, pady=(25, 15))

        menu_items = ["Dashboard", "Properties"]

        if self.role == "admin":
            menu_items.append("Managers")

        menu_items.extend([
            "Tenants",
            "Rent Payments",
            "Expenses",
            "Remittances",
            "Reports",
            "Settings"
        ])

        for item in menu_items:
            button = tk.Button(
                sidebar,
                text=item,
                font=("Segoe UI", 10),
                bg="white",
                fg="#142D4E",
                activebackground="#E8EEF6",
                relief="flat",
                anchor="w",
                padx=20,
                pady=10,
                cursor="hand2",
                command=lambda name=item: self.open_section(name)
            )
            button.pack(fill="x", padx=8, pady=2)

            button.bind(
                "<Enter>",
                lambda event, btn=button: btn.config(bg="#E8EEF6")
            )
            button.bind(
                "<Leave>",
                lambda event, btn=button: btn.config(bg="white")
            )

        # All pages will appear inside this frame.
        self.content = tk.Frame(self.root, bg="#F3F5F9")
        self.content.pack(
            side="left",
            fill="both",
            expand=True,
            padx=20,
            pady=20
        )

        self.open_section("Dashboard")

    def clear_content(self):
        for widget in self.content.winfo_children():
            widget.destroy()

    def open_section(self, section):
        if section == "Managers" and self.role != "admin":
            messagebox.showwarning(
                "Access Denied",
                "Only the admin can manage manager accounts."
            )
            return

        self.clear_content()

        pages = {
            "Properties": PropertiesPage,
            "Tenants": TenantsPage,
            "Rent Payments": PaymentDashboard,
            "Expenses": ExpensesPage,
            "Remittances": RemittancesPage,
            "Reports": ReportsPage
        }

        if section == "Dashboard":
            self.show_home()
        elif section in pages:
            try:
                pages[section](self.content)
            except Exception as error:
                messagebox.showerror(
                    "Page Error",
                    f"Could not open {section}.\n\n{error}"
                )
        elif section == "Managers":
            self.show_managers()
        elif section == "Settings":
            self.show_settings()

    def show_home(self):
        today = date.today()
        current_month = today.strftime("%Y-%m")

        tk.Label(
            self.content,
            text=f"{self.role.capitalize()} Dashboard",
            font=("Segoe UI", 22, "bold"),
            bg="#F3F5F9",
            fg="#142D4E"
        ).pack(anchor="w")

        tk.Label(
            self.content,
            text=f"Rental operations overview | {current_month}",
            font=("Segoe UI", 11),
            bg="#F3F5F9",
            fg="#64748B"
        ).pack(anchor="w", pady=(5, 15))

        connection = get_connection()
        try:
            properties = connection.execute("""
                SELECT COUNT(*) AS total FROM properties
            """).fetchone()["total"]

            tenants = connection.execute("""
                SELECT COUNT(*) AS total
                FROM tenants
                WHERE status = 'Active'
            """).fetchone()["total"]

            rent = connection.execute("""
                SELECT COALESCE(SUM(amount), 0) AS total
                FROM rent_payments
                WHERE rent_month = ?
            """, (current_month,)).fetchone()["total"]

            expected = connection.execute("""
                SELECT COALESCE(SUM(p.monthly_rent), 0) AS total
                FROM tenants t
                JOIN properties p ON p.id = t.property_id
                WHERE t.status = 'Active'
            """).fetchone()["total"]

            expenses = connection.execute("""
                SELECT COALESCE(SUM(amount), 0) AS total
                FROM expenses
                WHERE substr(expense_date, 1, 7) = ?
            """, (current_month,)).fetchone()["total"]

            remittance_due = connection.execute("""
                SELECT COALESCE(
                    SUM(MAX(amount_due - amount_paid, 0)), 0
                ) AS total
                FROM remittances
                WHERE period = ?
            """, (current_month,)).fetchone()["total"]

            recent = connection.execute("""
                SELECT
                    rp.payment_date,
                    t.full_name,
                    p.name AS property_name,
                    rp.amount,
                    rp.method
                FROM rent_payments rp
                JOIN tenants t ON t.id = rp.tenant_id
                JOIN properties p ON p.id = rp.property_id
                ORDER BY rp.payment_date DESC, rp.id DESC
                LIMIT 10
            """).fetchall()

        finally:
            connection.close()

        outstanding = max(float(expected) - float(rent), 0)

        cards = [
            ("Properties", str(properties)),
            ("Active Tenants", str(tenants)),
            ("Rent Collected", f"KSh {rent:,.2f}"),
            ("Outstanding Rent*", f"KSh {outstanding:,.2f}"),
            ("Monthly Expenses", f"KSh {expenses:,.2f}"),
            ("Remittance Due", f"KSh {remittance_due:,.2f}")
        ]

        cards_frame = tk.Frame(self.content, bg="#F3F5F9")
        cards_frame.pack(fill="x")

        for index, (title, value) in enumerate(cards):
            card = tk.Frame(
                cards_frame,
                bg="white",
                padx=12,
                pady=15,
                highlightbackground="#E2E8F0",
                highlightthickness=1
            )
            card.grid(
                row=index // 3,
                column=index % 3,
                padx=5,
                pady=5,
                sticky="nsew"
            )

            tk.Label(
                card,
                text=title,
                font=("Segoe UI", 9),
                bg="white",
                fg="#64748B"
            ).pack(anchor="w")

            tk.Label(
                card,
                text=value,
                font=("Segoe UI", 13, "bold"),
                bg="white",
                fg="#142D4E",
                wraplength=180
            ).pack(anchor="w", pady=(10, 0))

        for column in range(3):
            cards_frame.columnconfigure(column, weight=1)

        tk.Label(
            self.content,
            text="Recent Rent Payments",
            font=("Segoe UI", 13, "bold"),
            bg="#F3F5F9",
            fg="#142D4E"
        ).pack(anchor="w", pady=(15, 8))

        table_frame = ttk.Frame(self.content)
        table_frame.pack(fill="both", expand=True)

        columns = ("date", "tenant", "property", "amount", "method")
        table = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings"
        )

        headings = {
            "date": "Payment Date",
            "tenant": "Tenant",
            "property": "Property",
            "amount": "Amount (KSh)",
            "method": "Method"
        }

        for column, heading in headings.items():
            table.heading(column, text=heading)
            table.column(column, width=130, minwidth=80)

        scrollbar = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=table.yview
        )
        table.configure(yscrollcommand=scrollbar.set)

        table.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        for row in recent:
            table.insert("", "end", values=(
                row["payment_date"],
                row["full_name"],
                row["property_name"],
                f"{row['amount']:,.2f}",
                row["method"]
            ))

        if not recent:
            table.insert(
                "", "end",
                values=("-", "No payments recorded", "-", "0.00", "-")
            )

        tk.Label(
            self.content,
            text="*Outstanding rent is an estimate based on active tenants' "
                 "monthly rent minus payments recorded for this month.",
            font=("Segoe UI", 8),
            bg="#F3F5F9",
            fg="#64748B",
            wraplength=750,
            justify="left"
        ).pack(anchor="w", pady=(5, 0))

    def show_managers(self):
        tk.Label(
            self.content,
            text="Manager Accounts",
            font=("Segoe UI", 22, "bold"),
            bg="#F3F5F9",
            fg="#142D4E"
        ).pack(anchor="w", pady=(0, 15))

        form = ttk.LabelFrame(
            self.content,
            text="Create Manager Account",
            padding=12
        )
        form.pack(fill="x", pady=(0, 15))

        ttk.Label(form, text="Username").grid(
            row=0, column=0, sticky="w", padx=5, pady=4
        )
        self.manager_username = ttk.Entry(form)
        self.manager_username.grid(
            row=1, column=0, sticky="ew", padx=5, pady=4
        )

        ttk.Label(form, text="Password (minimum 8 characters)").grid(
            row=0, column=1, sticky="w", padx=5, pady=4
        )
        self.manager_password = ttk.Entry(form, show="*")
        self.manager_password.grid(
            row=1, column=1, sticky="ew", padx=5, pady=4
        )

        ttk.Button(
            form,
            text="Create Manager",
            command=self.create_manager
        ).grid(row=1, column=2, padx=8, pady=4)

        form.columnconfigure(0, weight=1)
        form.columnconfigure(1, weight=1)

        ttk.Label(
            self.content,
            text="Existing Manager Accounts",
            font=("Segoe UI", 12, "bold")
        ).pack(anchor="w", pady=(5, 8))

        self.manager_tree = ttk.Treeview(
            self.content,
            columns=("id", "username", "status", "created"),
            show="headings"
        )

        for column, heading, width in [
            ("id", "ID", 60),
            ("username", "Username", 180),
            ("status", "Status", 120),
            ("created", "Created At", 220)
        ]:
            self.manager_tree.heading(column, text=heading)
            self.manager_tree.column(column, width=width)

        self.manager_tree.pack(fill="both", expand=True)
        self.load_managers()

    def load_managers(self):
        for item in self.manager_tree.get_children():
            self.manager_tree.delete(item)

        connection = get_connection()
        try:
            rows = connection.execute("""
                SELECT id, username, is_active, created_at
                FROM users
                WHERE role = 'manager'
                ORDER BY id DESC
            """).fetchall()

            for row in rows:
                self.manager_tree.insert("", "end", values=(
                    row["id"],
                    row["username"],
                    "Active" if row["is_active"] else "Inactive",
                    row["created_at"] or "-"
                ))
        finally:
            connection.close()

    def create_manager(self):
        username = self.manager_username.get().strip()
        password = self.manager_password.get()

        if not username or not password:
            messagebox.showwarning(
                "Missing Details",
                "Enter both a username and password."
            )
            return

        try:
            success, message = create_user(
                username, password, "manager"
            )
        except Exception as error:
            messagebox.showerror(
                "Error",
                f"Could not create manager account.\n\n{error}"
            )
            return

        if success:
            messagebox.showinfo("Success", message)
            self.manager_username.delete(0, tk.END)
            self.manager_password.delete(0, tk.END)
            self.load_managers()
        else:
            messagebox.showerror("Could Not Create Account", message)

    def show_settings(self):
        tk.Label(
            self.content,
            text="Settings",
            font=("Segoe UI", 22, "bold"),
            bg="#F3F5F9",
            fg="#142D4E"
        ).pack(anchor="w", pady=(0, 15))

        tk.Label(
            self.content,
            text=(
                "Ole Segeri Rental Remittance System\n\n"
                f"Logged-in username: {self.username}\n"
                f"Role: {self.role.capitalize()}\n\n"
                "User access is managed through the admin's "
                "Managers section."
            ),
            font=("Segoe UI", 12),
            bg="#F3F5F9",
            fg="#334155",
            justify="left"
        ).pack(anchor="w")

    def logout(self):
        if not messagebox.askyesno(
            "Logout",
            "Are you sure you want to log out?"
        ):
            return

        if self.on_logout:
         self.on_logout()

        for widget in self.root.winfo_children():
            widget.destroy()

        from ui.login import LoginWindow
        LoginWindow(self.root)
