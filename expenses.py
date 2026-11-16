
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date

from database import get_connection
from modules.expenses import (
    add_expense,
    get_all_expenses,
    get_total_expenses,
)


class ExpensesPage:
    def __init__(self, parent):
        self.parent = parent
        self.property_lookup = {}

        self.build_ui()
        self.load_properties()
        self.load_expenses()
        self.load_total()

    def build_ui(self):
        self.parent.configure(bg="#F3F5F9")

        tk.Label(
            self.parent,
            text="Property Expenses",
            font=("Segoe UI", 22, "bold"),
            bg="#F3F5F9",
            fg="#142D4E"
        ).pack(anchor="w", padx=20, pady=(20, 5))

        tk.Label(
            self.parent,
            text="Record and review expenses for each property.",
            font=("Segoe UI", 10),
            bg="#F3F5F9",
            fg="#64748B"
        ).pack(anchor="w", padx=20, pady=(0, 10))

        self.total_label = tk.Label(
            self.parent,
            text="Total Expenses: KSh 0.00",
            font=("Segoe UI", 12, "bold"),
            bg="#F3F5F9",
            fg="#142D4E"
        )
        self.total_label.pack(anchor="w", padx=20, pady=(0, 10))

        form = ttk.LabelFrame(
            self.parent,
            text="Record New Expense",
            padding=12
        )
        form.pack(fill="x", padx=20, pady=5)

        ttk.Label(form, text="Property").grid(
            row=0, column=0, sticky="w", padx=5, pady=4
        )
        self.property_combo = ttk.Combobox(
            form, state="readonly", width=28
        )
        self.property_combo.grid(
            row=1, column=0, sticky="ew", padx=5, pady=4
        )

        ttk.Label(form, text="Description").grid(
            row=0, column=1, sticky="w", padx=5, pady=4
        )
        self.description_entry = ttk.Entry(form, width=28)
        self.description_entry.grid(
            row=1, column=1, sticky="ew", padx=5, pady=4
        )

        ttk.Label(form, text="Amount (KSh)").grid(
            row=0, column=2, sticky="w", padx=5, pady=4
        )
        self.amount_entry = ttk.Entry(form)
        self.amount_entry.grid(
            row=1, column=2, sticky="ew", padx=5, pady=4
        )

        ttk.Label(
            form, text="Expense Date (YYYY-MM-DD)"
        ).grid(row=2, column=0, sticky="w", padx=5, pady=4)

        self.date_entry = ttk.Entry(form)
        self.date_entry.insert(0, date.today().isoformat())
        self.date_entry.grid(
            row=3, column=0, sticky="ew", padx=5, pady=4
        )

        ttk.Label(form, text="Category").grid(
            row=2, column=1, sticky="w", padx=5, pady=4
        )
        self.category_combo = ttk.Combobox(
            form,
            values=(
                "Repairs",
                "Maintenance",
                "Water",
                "Electricity",
                "Cleaning",
                "Security",
                "Other"
            ),
            state="readonly"
        )
        self.category_combo.current(0)
        self.category_combo.grid(
            row=3, column=1, sticky="ew", padx=5, pady=4
        )

        buttons = ttk.Frame(form)
        buttons.grid(
            row=3, column=2, sticky="w", padx=5, pady=8
        )

        ttk.Button(
            buttons,
            text="Save Expense",
            command=self.save_expense
        ).pack(side="left", padx=(0, 5))

        ttk.Button(
            buttons,
            text="Refresh",
            command=self.refresh
        ).pack(side="left", padx=5)

        for column in range(3):
            form.columnconfigure(column, weight=1)

        table_frame = ttk.LabelFrame(
            self.parent,
            text="Expense History",
            padding=10
        )
        table_frame.pack(
            fill="both", expand=True, padx=20, pady=(12, 20)
        )

        columns = (
            "id",
            "property",
            "description",
            "amount",
            "date",
            "category"
        )

        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings"
        )

        headings = {
            "id": "ID",
            "property": "Property / Unit",
            "description": "Description",
            "amount": "Amount (KSh)",
            "date": "Expense Date",
            "category": "Category"
        }

        for column, heading in headings.items():
            self.tree.heading(column, text=heading)
            self.tree.column(column, width=150, minwidth=80)

        scrollbar = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def load_properties(self):
        connection = get_connection()

        try:
            rows = connection.execute("""
                SELECT id, name, unit_number
                FROM properties
                ORDER BY name, unit_number
            """).fetchall()

            self.property_lookup = {}
            options = []

            for row in rows:
                label = (
                    f"{row['name']} - Unit {row['unit_number']} "
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

    def save_expense(self):
        property_label = self.property_combo.get()
        property_id = self.property_lookup.get(property_label)

        description = self.description_entry.get().strip()
        amount_text = self.amount_entry.get().strip()
        expense_date = self.date_entry.get().strip()
        category = self.category_combo.get()

        if property_id is None:
            messagebox.showwarning(
                "No Property",
                "Please register a property before recording expenses."
            )
            return

        if not description:
            messagebox.showwarning(
                "Missing Description",
                "Enter a description for the expense."
            )
            return

        try:
            amount = float(amount_text)
            if amount <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror(
                "Invalid Amount",
                "Enter an amount greater than zero."
            )
            return

        try:
            date.fromisoformat(expense_date)
        except ValueError:
            messagebox.showerror(
                "Invalid Date",
                "Enter a valid date in YYYY-MM-DD format."
            )
            return

        if not category:
            messagebox.showwarning(
                "Missing Category",
                "Select an expense category."
            )
            return

        try:
            add_expense(
                property_id=property_id,
                description=description,
                amount=amount,
                expense_date=expense_date,
                category=category
            )

            messagebox.showinfo(
                "Success",
                "Expense recorded successfully."
            )

            self.description_entry.delete(0, tk.END)
            self.amount_entry.delete(0, tk.END)
            self.date_entry.delete(0, tk.END)
            self.date_entry.insert(0, date.today().isoformat())

            self.load_expenses()
            self.load_total()

        except Exception as error:
            messagebox.showerror(
                "Expense Error",
                f"Could not record the expense.\n\n{error}"
            )

    def load_expenses(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        try:
            rows = get_all_expenses()

            for row in rows:
                self.tree.insert("", tk.END, values=(
                    row["id"],
                    row["property_name"],
                    row["description"],
                    f"{row['amount']:,.2f}",
                    row["expense_date"],
                    row["category"]
                ))

        except Exception as error:
            messagebox.showerror(
                "Loading Error",
                f"Could not load expenses.\n\n{error}"
            )

    def load_total(self):
        try:
            total = get_total_expenses()
            self.total_label.config(
                text=f"Total Expenses: KSh {total:,.2f}"
            )
        except Exception as error:
            messagebox.showerror(
                "Total Error",
                f"Could not calculate total expenses.\n\n{error}"
            )

    def refresh(self):
        self.load_properties()
        self.load_expenses()
        self.load_total()
