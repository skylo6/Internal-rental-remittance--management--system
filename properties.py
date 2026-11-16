
import tkinter as tk
from tkinter import ttk, messagebox

from modules.properties import add_property, get_all_properties


class PropertiesPage:
    def __init__(self, parent):
        self.parent = parent
        self.build_ui()
        self.load_properties()

    def build_ui(self):
        self.parent.configure(bg="#F3F5F9")

        heading = tk.Frame(self.parent, bg="#F3F5F9")
        heading.pack(fill="x", padx=20, pady=(20, 10))

        tk.Label(
            heading,
            text="Property Management",
            font=("Arial", 20, "bold"),
            bg="#F3F5F9",
            fg="#172554"
        ).pack(anchor="w")

        tk.Label(
            heading,
            text="Add and manage rental properties.",
            font=("Arial", 10),
            bg="#F3F5F9",
            fg="#64748B"
        ).pack(anchor="w", pady=(4, 0))

        form = ttk.LabelFrame(
            self.parent,
            text="Add New Property",
            padding=15
        )
        form.pack(fill="x", padx=20, pady=10)

        ttk.Label(form, text="Property Name").grid(
            row=0, column=0, sticky="w", padx=5, pady=5
        )
        self.name_entry = ttk.Entry(form, width=30)
        self.name_entry.grid(
            row=1, column=0, padx=5, pady=5, sticky="ew"
        )

        ttk.Label(form, text="Location").grid(
            row=0, column=1, sticky="w", padx=5, pady=5
        )
        self.location_entry = ttk.Entry(form, width=30)
        self.location_entry.grid(
            row=1, column=1, padx=5, pady=5, sticky="ew"
        )

        ttk.Label(form, text="Unit Number").grid(
            row=0, column=2, sticky="w", padx=5, pady=5
        )
        self.unit_entry = ttk.Entry(form, width=20)
        self.unit_entry.grid(
            row=1, column=2, padx=5, pady=5, sticky="ew"
        )

        ttk.Label(form, text="Monthly Rent (KSh)").grid(
            row=0, column=3, sticky="w", padx=5, pady=5
        )
        self.rent_entry = ttk.Entry(form, width=18)
        self.rent_entry.grid(
            row=1, column=3, padx=5, pady=5, sticky="ew"
        )

        for column in range(4):
            form.columnconfigure(column, weight=1)

        ttk.Button(
            form,
            text="Add Property",
            command=self.add_property
        ).grid(row=2, column=0, sticky="w", padx=5, pady=12)

        table_frame = ttk.LabelFrame(
            self.parent,
            text="Registered Properties",
            padding=10
        )
        table_frame.pack(
            fill="both", expand=True, padx=20, pady=(5, 20)
        )

        columns = (
            "id", "name", "location", "unit", "rent", "status"
        )

        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings"
        )

        headings = {
            "id": "ID",
            "name": "Property",
            "location": "Location",
            "unit": "Unit",
            "rent": "Monthly Rent (KSh)",
            "status": "Status"
        }

        widths = {
            "id": 50,
            "name": 180,
            "location": 180,
            "unit": 100,
            "rent": 150,
            "status": 100
        }

        for column in columns:
            self.tree.heading(column, text=headings[column])
            self.tree.column(
                column,
                width=widths[column],
                anchor="w"
            )

        scrollbar = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        ttk.Button(
            self.parent,
            text="Refresh Properties",
            command=self.load_properties
        ).pack(anchor="e", padx=20, pady=(0, 15))

    def add_property(self):
        name = self.name_entry.get().strip()
        location = self.location_entry.get().strip()
        unit = self.unit_entry.get().strip()
        rent_text = self.rent_entry.get().strip()

        if not name or not location or not unit or not rent_text:
            messagebox.showwarning(
                "Missing Information",
                "Please fill in all property fields.",
                parent=self.parent
            )
            return

        try:
            add_property(name, location, unit, rent_text)

            messagebox.showinfo(
                "Success",
                "Property added successfully.",
                parent=self.parent
            )

            self.name_entry.delete(0, tk.END)
            self.location_entry.delete(0, tk.END)
            self.unit_entry.delete(0, tk.END)
            self.rent_entry.delete(0, tk.END)

            self.load_properties()

        except ValueError as error:
            messagebox.showerror(
                "Invalid Property Details",
                str(error),
                parent=self.parent
            )

        except Exception as error:
            messagebox.showerror(
                "Could Not Add Property",
                f"Could not save the property.\n\n{error}",
                parent=self.parent
            )

    def load_properties(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        try:
            rows = get_all_properties()

            for row in rows:
                self.tree.insert(
                    "",
                    tk.END,
                    values=(
                        row["id"],
                        row["name"],
                        row["location"],
                        row["unit_number"],
                        f"{row['monthly_rent']:,.2f}",
                        row["status"]
                    )
                )

        except Exception as error:
            messagebox.showerror(
                "Loading Error",
                f"Could not load properties.\n\n{error}",
                parent=self.parent
            )
