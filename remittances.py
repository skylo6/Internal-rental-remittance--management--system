
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date

from database import get_connection
from modules.remittances import (
    create_remittance,
    get_all_remittances,
    record_remittance_payment,
)


class RemittancesPage:
    def __init__(self, parent):
        self.parent = parent
        self.property_lookup = {}

        self.build_ui()
        self.load_properties()
        self.load_remittances()

    def build_ui(self):
        self.parent.configure(bg="#F3F5F9")

        tk.Label(
            self.parent,
            text="Rent Remittances",
            font=("Segoe UI", 22, "bold"),
            bg="#F3F5F9",
            fg="#142D4E"
        ).pack(anchor="w", padx=20, pady=(20, 5))

        tk.Label(
            self.parent,
            text="Calculate rent collected, expenses, and the amount payable.",
            font=("Segoe UI", 10),
            bg="#F3F5F9",
            fg="#64748B"
        ).pack(anchor="w", padx=20, pady=(0, 15))

        form = ttk.LabelFrame(
            self.parent,
            text="Calculate Monthly Remittance",
            padding=12
        )
        form.pack(fill="x", padx=20, pady=5)

        ttk.Label(form, text="Property").grid(
            row=0, column=0, sticky="w", padx=5, pady=4
        )
        self.property_combo = ttk.Combobox(
            form, state="readonly", width=30
        )
        self.property_combo.grid(
            row=1, column=0, sticky="ew", padx=5, pady=4
        )

        ttk.Label(form, text="Period (YYYY-MM)").grid(
            row=0, column=1, sticky="w", padx=5, pady=4
        )
        self.period_entry = ttk.Entry(form)
        self.period_entry.insert(0, date.today().strftime("%Y-%m"))
        self.period_entry.grid(
            row=1, column=1, sticky="ew", padx=5, pady=4
        )

        ttk.Button(
            form,
            text="Calculate & Save",
            command=self.calculate_remittance
        ).grid(row=1, column=2, padx=8, pady=4)

        ttk.Button(
            form,
            text="Refresh",
            command=self.refresh
        ).grid(row=1, column=3, padx=8, pady=4)

        for column in range(4):
            form.columnconfigure(column, weight=1)

        payment_form = ttk.LabelFrame(
            self.parent,
            text="Record Remittance Payment",
            padding=10
        )
        payment_form.pack(fill="x", padx=20, pady=(10, 5))

        ttk.Label(payment_form, text="Amount (KSh)").grid(
            row=0, column=0, sticky="w", padx=5, pady=4
        )
        self.payment_amount_entry = ttk.Entry(payment_form)
        self.payment_amount_entry.grid(
            row=1, column=0, sticky="ew", padx=5, pady=4
        )

        ttk.Label(payment_form, text="Payment Date").grid(
            row=0, column=1, sticky="w", padx=5, pady=4
        )
        self.payment_date_entry = ttk.Entry(payment_form)
        self.payment_date_entry.insert(0, date.today().isoformat())
        self.payment_date_entry.grid(
            row=1, column=1, sticky="ew", padx=5, pady=4
        )

        ttk.Label(payment_form, text="Reference (optional)").grid(
            row=0, column=2, sticky="w", padx=5, pady=4
        )
        self.reference_entry = ttk.Entry(payment_form)
        self.reference_entry.grid(
            row=1, column=2, sticky="ew", padx=5, pady=4
        )

        ttk.Button(
            payment_form,
            text="Record Payment for Selected Remittance",
            command=self.record_payment
        ).grid(row=1, column=3, padx=8, pady=4)

        for column in range(4):
            payment_form.columnconfigure(column, weight=1)

        self.summary_label = tk.Label(
            self.parent,
            text="Select a property and period to calculate a remittance.",
            font=("Segoe UI", 11, "bold"),
            bg="#F3F5F9",
            fg="#142D4E",
            anchor="w",
            justify="left"
        )
        self.summary_label.pack(fill="x", padx=25, pady=10)

        table_frame = ttk.LabelFrame(
            self.parent,
            text="Remittance History",
            padding=10
        )
        table_frame.pack(
            fill="both", expand=True, padx=20, pady=(0, 20)
        )

        columns = (
            "id", "property", "period", "gross",
            "expenses", "due", "paid", "balance", "status"
        )

        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            selectmode="browse"
        )

        headings = {
            "id": "ID",
            "property": "Property",
            "period": "Period",
            "gross": "Gross Rent (KSh)",
            "expenses": "Expenses (KSh)",
            "due": "Amount Due (KSh)",
            "paid": "Amount Paid (KSh)",
            "balance": "Balance (KSh)",
            "status": "Status"
        }

        for column, heading in headings.items():
            self.tree.heading(column, text=heading)
            self.tree.column(column, width=125, minwidth=85)

        scrollbar = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.tree.bind(
            "<<TreeviewSelect>>",
            self.show_selected_remittance
        )

    def load_properties(self):
        connection = get_connection()

        try:
            rows = connection.execute("""
                SELECT id, name, location
                FROM properties
                ORDER BY name
            """).fetchall()

            self.property_lookup = {}
            options = []

            for row in rows:
                label = (
                    f"{row['name']} - {row['location']} "
                    f"(ID {row['id']})"
                )
                options.append(label)
                self.property_lookup[label] = row["id"]

            self.property_combo["values"] = options

            if options and self.property_combo.get() not in options:
                self.property_combo.current(0)

            if not options:
                self.property_combo.set("")

        finally:
            connection.close()

    def calculate_remittance(self):
        property_label = self.property_combo.get()
        property_id = self.property_lookup.get(property_label)
        period = self.period_entry.get().strip()

        if property_id is None:
            messagebox.showwarning(
                "No Property",
                "Please add a property before calculating remittances."
            )
            return

        try:
            if (
                len(period) != 7
                or period[4] != "-"
                or not period[:4].isdigit()
                or not period[5:].isdigit()
                or not 1 <= int(period[5:]) <= 12
            ):
                raise ValueError

            # Validate that the year and month form a valid date.
            date.fromisoformat(period + "-01")

        except ValueError:
            messagebox.showerror(
                "Invalid Period",
                "Enter a valid period in YYYY-MM format, for example 2026-10."
            )
            return

        try:
            remittance_id = create_remittance(property_id, period)

            rows = get_all_remittances()
            remittance = next(
                (row for row in rows if row["id"] == remittance_id),
                None
            )

            if remittance:
                self.show_summary(remittance)

            self.load_remittances()

            messagebox.showinfo(
                "Remittance Calculated",
                "The monthly remittance has been calculated and saved."
            )

        except Exception as error:
            messagebox.showerror(
                "Remittance Error",
                f"Could not calculate remittance.\n\n{error}"
            )

    def record_payment(self):
        selected = self.tree.selection()

        if not selected:
            messagebox.showwarning(
                "Select Remittance",
                "Select a remittance record from the table first."
            )
            return

        remittance_id = int(
            self.tree.item(selected[0], "values")[0]
        )

        amount_text = self.payment_amount_entry.get().strip()
        payment_date = self.payment_date_entry.get().strip()
        reference = self.reference_entry.get().strip() or None

        try:
            amount = float(amount_text)
            if amount <= 0:
                raise ValueError("Amount must be greater than zero.")
        except ValueError:
            messagebox.showerror(
                "Invalid Amount",
                "Enter a valid payment amount greater than zero."
            )
            return

        try:
            date.fromisoformat(payment_date)
        except ValueError:
            messagebox.showerror(
                "Invalid Date",
                "Enter a valid payment date in YYYY-MM-DD format."
            )
            return

        try:
            record_remittance_payment(
                remittance_id=remittance_id,
                amount=amount,
                payment_date=payment_date,
                reference=reference
            )

            self.payment_amount_entry.delete(0, tk.END)
            self.reference_entry.delete(0, tk.END)

            self.load_remittances()

            messagebox.showinfo(
                "Payment Recorded",
                "Remittance payment recorded successfully."
            )

        except Exception as error:
            messagebox.showerror(
                "Payment Error",
                f"Could not record payment.\n\n{error}"
            )

    def load_remittances(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        try:
            rows = get_all_remittances()

            for row in rows:
                self.tree.insert("", tk.END, values=(
                    row["id"],
                    row["property_name"],
                    row["period"],
                    f"{row['gross_rent']:,.2f}",
                    f"{row['expenses']:,.2f}",
                    f"{row['amount_due']:,.2f}",
                    f"{row['amount_paid']:,.2f}",
                    f"{row['balance']:,.2f}",
                    row["status"]
                ))

        except Exception as error:
            messagebox.showerror(
                "Loading Error",
                f"Could not load remittance history.\n\n{error}"
            )

    def show_selected_remittance(self, event=None):
        selected = self.tree.selection()

        if not selected:
            return

        values = self.tree.item(selected[0], "values")

        self.summary_label.config(
            text=(
                f"Remittance ID: {values[0]}  |  "
                f"Property: {values[1]}  |  Period: {values[2]}\n"
                f"Gross Rent: KSh {values[3]}  |  "
                f"Expenses: KSh {values[4]}  |  "
                f"Amount Due: KSh {values[5]}\n"
                f"Paid: KSh {values[6]}  |  "
                f"Balance: KSh {values[7]}  |  "
                f"Status: {values[8]}"
            )
        )

    def show_summary(self, remittance):
        self.summary_label.config(
            text=(
                f"Period: {remittance['period']}  |  "
                f"Gross Rent: KSh {remittance['gross_rent']:,.2f}  |  "
                f"Expenses: KSh {remittance['expenses']:,.2f}\n"
                f"Amount Due: KSh {remittance['amount_due']:,.2f}  |  "
                f"Already Paid: KSh {remittance['amount_paid']:,.2f}  |  "
                f"Status: {remittance['status']}"
            )
        )

    def refresh(self):
        self.load_properties()
        self.load_remittances()
