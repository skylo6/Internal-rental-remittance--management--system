
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import csv
from database import get_connection


class ReportsPage:
    def __init__(self, parent):
        self.parent = parent
        self.build_ui()
        self.load_summary()

    def build_ui(self):
        self.parent.configure(bg="#F3F5F9")

        tk.Label(
            self.parent,
            text="Reports & Analytics",
            font=("Segoe UI", 22, "bold"),
            bg="#F3F5F9",
            fg="#142D4E"
        ).pack(anchor="w", padx=20, pady=(20, 5))

        tk.Label(
            self.parent,
            text="Review rental activity and export reports to CSV.",
            font=("Segoe UI", 10),
            bg="#F3F5F9",
            fg="#64748B"
        ).pack(anchor="w", padx=20, pady=(0, 15))

        cards = ttk.Frame(self.parent)
        cards.pack(fill="x", padx=20, pady=5)

        self.properties_label = self.make_card(
            cards, "Properties", "0"
        )
        self.tenants_label = self.make_card(
            cards, "Active Tenants", "0"
        )
        self.rent_label = self.make_card(
            cards, "Rent Collected (KSh)", "0.00"
        )
        self.expenses_label = self.make_card(
            cards, "Expenses (KSh)", "0.00"
        )

        actions = ttk.Frame(self.parent)
        actions.pack(fill="x", padx=20, pady=12)

        ttk.Button(
            actions,
            text="Refresh Reports",
            command=self.load_summary
        ).pack(side="left", padx=(0, 8))

        ttk.Button(
            actions,
            text="Export Rent Payments",
            command=self.export_payments
        ).pack(side="left", padx=8)

        ttk.Button(
            actions,
            text="Export Remittances",
            command=self.export_remittances
        ).pack(side="left", padx=8)

        table_frame = ttk.LabelFrame(
            self.parent,
            text="Recent Rent Payments",
            padding=10
        )
        table_frame.pack(
            fill="both", expand=True, padx=20, pady=(0, 20)
        )

        columns = (
            "id", "tenant", "property", "amount",
            "date", "month", "method", "reference"
        )

        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings"
        )

        headings = {
            "id": "ID",
            "tenant": "Tenant",
            "property": "Property / Unit",
            "amount": "Amount (KSh)",
            "date": "Payment Date",
            "month": "Rent Month",
            "method": "Method",
            "reference": "Reference"
        }

        for column, heading in headings.items():
            self.tree.heading(column, text=heading)
            self.tree.column(column, width=125, minwidth=80)

        scrollbar = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def make_card(self, parent, title, value):
        card = ttk.LabelFrame(parent, text=title, padding=15)
        card.pack(side="left", fill="both", expand=True, padx=5)

        label = tk.Label(
            card,
            text=value,
            font=("Segoe UI", 16, "bold"),
            bg="#F3F5F9",
            fg="#142D4E"
        )
        label.pack(pady=5)

        return label

    def load_summary(self):
        connection = get_connection()
        try:
            properties = connection.execute("""
                SELECT COUNT(*) AS total
                FROM properties
            """).fetchone()["total"]

            tenants = connection.execute("""
                SELECT COUNT(*) AS total
                FROM tenants
                WHERE status = 'Active'
            """).fetchone()["total"]

            rent = connection.execute("""
                SELECT COALESCE(SUM(amount), 0) AS total
                FROM rent_payments
            """).fetchone()["total"]

            expenses = connection.execute("""
                SELECT COALESCE(SUM(amount), 0) AS total
                FROM expenses
            """).fetchone()["total"]

            self.properties_label.config(text=str(properties))
            self.tenants_label.config(text=str(tenants))
            self.rent_label.config(text=f"{rent:,.2f}")
            self.expenses_label.config(text=f"{expenses:,.2f}")

            for item in self.tree.get_children():
                self.tree.delete(item)

            rows = connection.execute("""
                SELECT
                    rp.id,
                    t.full_name,
                    p.name AS property_name,
                    p.unit_number,
                    rp.amount,
                    rp.payment_date,
                    rp.rent_month,
                    rp.method,
                    rp.reference
                FROM rent_payments rp
                JOIN tenants t ON t.id = rp.tenant_id
                JOIN properties p ON p.id = rp.property_id
                ORDER BY rp.payment_date DESC, rp.id DESC
                LIMIT 100
            """).fetchall()

            for row in rows:
                self.tree.insert("", tk.END, values=(
                    row["id"],
                    row["full_name"],
                    f"{row['property_name']} / {row['unit_number']}",
                    f"{row['amount']:,.2f}",
                    row["payment_date"],
                    row["rent_month"],
                    row["method"],
                    row["reference"] or "-"
                ))
        except Exception as error:
            messagebox.showerror(
                "Reports Error",
                f"Could not load reports.\n\n{error}"
            )
        finally:
            connection.close()

    def export_payments(self):
        filename = filedialog.asksaveasfilename(
            title="Export Rent Payments",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")]
        )

        if not filename:
            return

        connection = get_connection()
        try:
            rows = connection.execute("""
                SELECT
                    rp.id,
                    t.full_name AS tenant,
                    p.name AS property,
                    p.unit_number,
                    rp.amount,
                    rp.payment_date,
                    rp.rent_month,
                    rp.method,
                    rp.reference
                FROM rent_payments rp
                JOIN tenants t ON t.id = rp.tenant_id
                JOIN properties p ON p.id = rp.property_id
                ORDER BY rp.payment_date DESC, rp.id DESC
            """).fetchall()

            with open(
                filename, "w", newline="", encoding="utf-8-sig"
            ) as file:
                writer = csv.writer(file)
                writer.writerow([
                    "Payment ID", "Tenant", "Property",
                    "Unit Number", "Amount (KSh)", "Payment Date",
                    "Rent Month", "Method", "Reference"
                ])

                for row in rows:
                    writer.writerow(tuple(row))

            messagebox.showinfo(
                "Export Complete",
                f"Rent payments exported to:\n{filename}"
            )
        except Exception as error:
            messagebox.showerror(
                "Export Error",
                f"Could not export payments.\n\n{error}"
            )
        finally:
            connection.close()

    def export_remittances(self):
        filename = filedialog.asksaveasfilename(
            title="Export Remittances",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")]
        )

        if not filename:
            return

        connection = get_connection()
        try:
            rows = connection.execute("""
                SELECT
                    r.id,
                    p.name AS property,
                    r.period,
                    r.gross_rent,
                    r.expenses,
                    r.amount_due,
                    r.amount_paid,
                    r.status,
                    r.payment_date,
                    r.reference
                FROM remittances r
                JOIN properties p ON p.id = r.property_id
                ORDER BY r.period DESC, r.id DESC
            """).fetchall()

            with open(
                filename, "w", newline="", encoding="utf-8-sig"
            ) as file:
                writer = csv.writer(file)
                writer.writerow([
                    "Remittance ID", "Property", "Period",
                    "Gross Rent (KSh)", "Expenses (KSh)",
                    "Amount Due (KSh)", "Amount Paid (KSh)",
                    "Status", "Payment Date", "Reference"
                ])

                for row in rows:
                    writer.writerow(tuple(row))

            messagebox.showinfo(
                "Export Complete",
                f"Remittances exported to:\n{filename}"
            )
        except Exception as error:
            messagebox.showerror(
                "Export Error",
                f"Could not export remittances.\n\n{error}"
            )
        finally:
            connection.close()
