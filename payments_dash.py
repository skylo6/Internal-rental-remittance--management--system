
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date

from database import get_connection
from modules.payments import (
    record_payment,
    get_all_payments,
    get_total_collected,
)


class PaymentDashboard:
    def __init__(self, parent):
        self.parent = parent
        self.tenant_lookup = {}

        self.build_ui()
        self.load_tenants()
        self.load_payments()
        self.load_total()

    def build_ui(self):
        self.parent.configure(bg="#F3F5F9")

        tk.Label(
            self.parent,
            text="Rent Payments",
            font=("Segoe UI", 22, "bold"),
            bg="#F3F5F9",
            fg="#142D4E",
        ).pack(anchor="w", padx=20, pady=(20, 5))

        tk.Label(
            self.parent,
            text="Record rent received and review payment history.",
            font=("Segoe UI", 10),
            bg="#F3F5F9",
            fg="#64748B",
        ).pack(anchor="w", padx=20, pady=(0, 15))

        self.total_label = tk.Label(
            self.parent,
            text="Total Collected: KSh 0.00",
            font=("Segoe UI", 12, "bold"),
            bg="#F3F5F9",
            fg="#142D4E",
        )
        self.total_label.pack(
            anchor="w", padx=20, pady=(0, 10)
        )

        form = ttk.LabelFrame(
            self.parent,
            text="Record Rent Payment",
            padding=12,
        )
        form.pack(fill="x", padx=20, pady=5)

        ttk.Label(form, text="Tenant").grid(
            row=0, column=0, sticky="w", padx=5, pady=4
        )
        self.tenant_combo = ttk.Combobox(
            form, state="readonly", width=30
        )
        self.tenant_combo.grid(
            row=1, column=0, padx=5, pady=4, sticky="ew"
        )

        ttk.Label(form, text="Amount (KSh)").grid(
            row=0, column=1, sticky="w", padx=5, pady=4
        )
        self.amount_entry = ttk.Entry(form)
        self.amount_entry.grid(
            row=1, column=1, padx=5, pady=4, sticky="ew"
        )

        ttk.Label(
            form, text="Payment Date (YYYY-MM-DD)"
        ).grid(row=0, column=2, sticky="w", padx=5, pady=4)

        self.date_entry = ttk.Entry(form)
        self.date_entry.insert(0, date.today().isoformat())
        self.date_entry.grid(
            row=1, column=2, padx=5, pady=4, sticky="ew"
        )

        ttk.Label(
            form, text="Rent Month (YYYY-MM)"
        ).grid(row=0, column=3, sticky="w", padx=5, pady=4)

        self.month_entry = ttk.Entry(form)
        self.month_entry.insert(
            0, date.today().strftime("%Y-%m")
        )
        self.month_entry.grid(
            row=1, column=3, padx=5, pady=4, sticky="ew"
        )

        ttk.Label(form, text="Payment Method").grid(
            row=2, column=0, sticky="w", padx=5, pady=4
        )
        self.method_combo = ttk.Combobox(
            form,
            values=("M-Pesa", "Cash", "Bank Transfer", "Other"),
            state="readonly",
        )
        self.method_combo.current(0)
        self.method_combo.grid(
            row=3, column=0, padx=5, pady=4, sticky="ew"
        )

        ttk.Label(
            form, text="Reference (optional)"
        ).grid(row=2, column=1, sticky="w", padx=5, pady=4)

        self.reference_entry = ttk.Entry(form)
        self.reference_entry.grid(
            row=3, column=1, padx=5, pady=4, sticky="ew"
        )

        for column in range(4):
            form.columnconfigure(column, weight=1)

        ttk.Button(
            form,
            text="Save Payment",
            command=self.save_payment,
        ).grid(row=3, column=2, padx=5, pady=8, sticky="w")

        ttk.Button(
            form,
            text="Refresh",
            command=self.refresh,
        ).grid(row=3, column=3, padx=5, pady=8, sticky="w")

        table_frame = ttk.LabelFrame(
            self.parent,
            text="Payment History",
            padding=10,
        )
        table_frame.pack(
            fill="both", expand=True, padx=20, pady=(12, 20)
        )

        columns = (
            "id", "tenant", "property", "amount",
            "date", "month", "method", "reference",
        )

        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
        )

        headings = {
            "id": "ID",
            "tenant": "Tenant",
            "property": "Property / Unit",
            "amount": "Amount (KSh)",
            "date": "Payment Date",
            "month": "Rent Month",
            "method": "Method",
            "reference": "Reference",
        }

        for column, heading in headings.items():
            self.tree.heading(column, text=heading)
            self.tree.column(column, width=125, minwidth=80)

        scrollbar = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.tree.yview,
        )
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def load_tenants(self):
        connection = get_connection()

        try:
            rows = connection.execute("""
                SELECT
                    t.id,
                    t.full_name,
                    t.property_id,
                    p.name AS property_name,
                    p.unit_number
                FROM tenants t
                JOIN properties p ON p.id = t.property_id
                WHERE t.status = 'Active'
                ORDER BY t.full_name
            """).fetchall()

            self.tenant_lookup = {}
            options = []

            for row in rows:
                label = (
                    f"{row['full_name']} - "
                    f"{row['property_name']} / "
                    f"Unit {row['unit_number']} "
                    f"(ID {row['id']})"
                )
                options.append(label)
                self.tenant_lookup[label] = dict(row)

            self.tenant_combo["values"] = options

            if options:
                current = self.tenant_combo.get()
                if current in self.tenant_lookup:
                    self.tenant_combo.set(current)
                else:
                    self.tenant_combo.current(0)
            else:
                self.tenant_combo.set("")

        except Exception as error:
            messagebox.showerror(
                "Tenant Loading Error",
                f"Could not load tenants.\n\n{error}",
            )
        finally:
            connection.close()

    def save_payment(self):
        tenant = self.tenant_lookup.get(
            self.tenant_combo.get()
        )

        amount_text = self.amount_entry.get().strip()
        payment_date = self.date_entry.get().strip()
        rent_month = self.month_entry.get().strip()
        method = self.method_combo.get().strip()
        reference = self.reference_entry.get().strip() or None

        if tenant is None:
            messagebox.showwarning(
                "No Tenant",
                "Register an active tenant before recording rent.",
            )
            return

        try:
            amount = float(amount_text)

            if amount <= 0:
                raise ValueError(
                    "Payment amount must be greater than zero."
                )

            if not method:
                raise ValueError("Select a payment method.")

            payment_id = record_payment(
                tenant_id=tenant["id"],
                amount=amount,
                payment_date=payment_date,
                rent_month=rent_month,
                method=method,
                reference=reference,
            )

            messagebox.showinfo(
                "Success",
                f"Rent payment recorded successfully.\n"
                f"Payment ID: {payment_id}",
            )

            self.amount_entry.delete(0, tk.END)
            self.reference_entry.delete(0, tk.END)

            self.refresh()

        except ValueError as error:
            messagebox.showerror(
                "Invalid Payment",
                str(error),
            )

        except Exception as error:
            messagebox.showerror(
                "Payment Error",
                f"Could not record payment.\n\n{error}",
            )

    def load_payments(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        try:
            rows = get_all_payments()

            for row in rows:
                self.tree.insert(
                    "",
                    tk.END,
                    values=(
                        row["id"],
                        row["tenant_name"],
                        f"{row['property_name']} / "
                        f"{row['unit_number']}",
                        f"{row['amount']:,.2f}",
                        row["payment_date"],
                        row["rent_month"],
                        row["method"],
                        row["reference"] or "-",
                    ),
                )

        except Exception as error:
            messagebox.showerror(
                "Payment History Error",
                f"Could not load payments.\n\n{error}",
            )

    def load_total(self):
        try:
            total = get_total_collected()

            self.total_label.config(
                text=f"Total Collected: KSh {total:,.2f}"
            )

        except Exception as error:
            messagebox.showerror(
                "Total Error",
                f"Could not load payment total.\n\n{error}",
            )

    def refresh(self):
        self.load_tenants()
        self.load_payments()
        self.load_total()
