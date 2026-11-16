
import tkinter as tk
from tkinter import ttk, messagebox

from modules.properties import get_all_properties
from modules.tenants import get_all_tenants
from modules.payments import get_all_payments
from modules.expenses import get_all_expenses
from modules.remittances import get_all_remittances


class ManagersDashboard:
    def __init__(self, root, user, on_logout):
        self.root = root
        self.user = user
        self.on_logout = on_logout

        self.root.title("Ole Segere - Rental Remittance System")
        self.root.geometry("1100x700")
        self.root.minsize(900, 600)
        self.root.configure(bg="#F3F5F9")

        self.build_ui()
        self.refresh_dashboard()

    def build_ui(self):
        header = tk.Frame(self.root, bg="#142D4E", height=85)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(
            header,
            text="OLE SEGERI",
            bg="#142D4E",
            fg="white",
            font=("Arial", 20, "bold")
        ).pack(side="left", padx=25, pady=20)

        tk.Label(
            header,
            text=f"Manager: {self.user.get('username', 'Manager')}",
            bg="#142D4E",
            fg="white",
            font=("Arial", 11)
        ).pack(side="right", padx=25)

        content = tk.Frame(self.root, bg="#F3F5F9")
        content.pack(fill="both", expand=True, padx=25, pady=25)

        tk.Label(
            content,
            text="Manager Dashboard",
            bg="#F3F5F9",
            fg="#142D4E",
            font=("Arial", 22, "bold")
        ).pack(anchor="w")

        tk.Label(
            content,
            text="Overview of rental operations",
            bg="#F3F5F9",
            fg="#64748B",
            font=("Arial", 11)
        ).pack(anchor="w", pady=(5, 20))

        self.stats_frame = tk.Frame(content, bg="#F3F5F9")
        self.stats_frame.pack(fill="x", pady=10)

        self.stat_labels = {}

        cards = [
            ("properties", "Properties"),
            ("tenants", "Tenants"),
            ("payments", "Rent Payments"),
            ("expenses", "Expenses"),
            ("remittances", "Remittances"),
        ]

        for key, title in cards:
            card = tk.Frame(
                self.stats_frame,
                bg="white",
                highlightbackground="#DCE3EC",
                highlightthickness=1
            )
            card.pack(side="left", fill="both", expand=True, padx=5)

            tk.Label(
                card,
                text=title,
                bg="white",
                fg="#64748B",
                font=("Arial", 10)
            ).pack(anchor="w", padx=12, pady=(15, 8))

            value_label = tk.Label(
                card,
                text="0",
                bg="white",
                fg="#142D4E",
                font=("Arial", 23, "bold")
            )
            value_label.pack(anchor="w", padx=12, pady=(0, 15))
            self.stat_labels[key] = value_label

        buttons_frame = tk.LabelFrame(
            content,
            text="Rental Management",
            bg="#F3F5F9",
            fg="#142D4E",
            font=("Arial", 12, "bold"),
            padx=15,
            pady=15
        )
        buttons_frame.pack(fill="x", pady=25)

        pages = [
            ("Properties", "properties"),
            ("Tenants", "tenants"),
            ("Rent Payments", "payments"),
            ("Expenses", "expenses"),
            ("Remittances", "remittances"),
        ]

        for title, module_name in pages:
            ttk.Button(
                buttons_frame,
                text=title,
                command=lambda name=module_name: self.open_page(name)
            ).pack(side="left", padx=6, pady=8)

        footer = tk.Frame(content, bg="#F3F5F9")
        footer.pack(fill="x", side="bottom", pady=10)

        ttk.Button(
            footer,
            text="Refresh Dashboard",
            command=self.refresh_dashboard
        ).pack(side="left")

        ttk.Button(
            footer,
            text="Logout",
            command=self.logout
        ).pack(side="right")

    def refresh_dashboard(self):
        try:
            properties = get_all_properties()
            tenants = get_all_tenants()
            payments = get_all_payments()
            expenses = get_all_expenses()
            remittances = get_all_remittances()

            self.stat_labels["properties"].config(
                text=str(len(properties))
            )
            self.stat_labels["tenants"].config(
                text=str(len(tenants))
            )
            self.stat_labels["payments"].config(
                text=str(len(payments))
            )
            self.stat_labels["expenses"].config(
                text=str(len(expenses))
            )
            self.stat_labels["remittances"].config(
                text=str(len(remittances))
            )

        except Exception as error:
            messagebox.showerror(
                "Dashboard Error",
                f"Could not load dashboard data:\n{error}"
            )

    def open_page(self, page_name):
        try:
            if page_name == "properties":
                from ui.properties import PropertiesPage
                page_class = PropertiesPage

            elif page_name == "tenants":
                from ui.tenants import TenantsPage
                page_class = TenantsPage

            elif page_name == "payments":
                from ui.payments_dash import PaymentsPage
                page_class = PaymentsPage

            elif page_name == "expenses":
                from ui.expenses import ExpensesPage
                page_class = ExpensesPage

            elif page_name == "remittances":
                from ui.remittances import RemittancesPage
                page_class = RemittancesPage

            window = tk.Toplevel(self.root)
            page_class(window)

        except Exception as error:
            messagebox.showerror(
                "Page Error",
                f"Could not open {page_name}:\n{error}"
            )

    def logout(self):
        if messagebox.askyesno(
            "Logout",
            "Are you sure you want to log out?"
        ):
            return
        if self.on_logout:
            self.on_logout()

            from main import LoginWindow
            root = tk.Tk()
            LoginWindow(root)
            root.mainloop()
