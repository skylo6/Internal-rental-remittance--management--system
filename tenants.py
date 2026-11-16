
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime


from modules.tenants import (
    add_tenant,
    get_all_tenants,
    set_tenant_status,
    remove_tenant,
)



class TenantsPage:
    def __init__(self, parent):
        self.parent = parent
        self.property_lookup = {}

        self.build_ui()
        self.load_properties()
        self.load_tenants()

    def build_ui(self):
        self.parent.configure(bg="#F3F5F9")

        tk.Label(
            self.parent,
            text="Tenant Management",
            font=("Segoe UI", 22, "bold"),
            bg="#F3F5F9",
            fg="#142D4E",
        ).pack(anchor="w", padx=20, pady=(20, 5))

        tk.Label(
            self.parent,
            text="Register tenants and assign them to rental units.",
            font=("Segoe UI", 10),
            bg="#F3F5F9",
            fg="#64748B",
        ).pack(anchor="w", padx=20, pady=(0, 15))

        form = ttk.LabelFrame(
            self.parent,
            text="Register New Tenant",
            padding=12,
        )
        form.pack(fill="x", padx=20, pady=5)

        ttk.Label(form, text="Full Name").grid(
            row=0, column=0, sticky="w", padx=5, pady=4
        )
        self.name_entry = ttk.Entry(form, width=25)
        self.name_entry.grid(
            row=1, column=0, padx=5, pady=4, sticky="ew"
        )

        ttk.Label(form, text="Phone").grid(
            row=0, column=1, sticky="w", padx=5, pady=4
        )
        self.phone_entry = ttk.Entry(form, width=20)
        self.phone_entry.grid(
            row=1, column=1, padx=5, pady=4, sticky="ew"
        )

        ttk.Label(form, text="Email (optional)").grid(
            row=0, column=2, sticky="w", padx=5, pady=4
        )
        self.email_entry = ttk.Entry(form, width=25)
        self.email_entry.grid(
            row=1, column=2, padx=5, pady=4, sticky="ew"
        )

        ttk.Label(form, text="Property / Unit").grid(
            row=0, column=3, sticky="w", padx=5, pady=4
        )
        self.property_combo = ttk.Combobox(
            form, state="readonly", width=28
        )
        self.property_combo.grid(
            row=1, column=3, padx=5, pady=4, sticky="ew"
        )

        ttk.Label(
            form, text="Move-in Date (YYYY-MM-DD)"
        ).grid(row=2, column=0, sticky="w", padx=5, pady=4)

        self.date_entry = ttk.Entry(form, width=25)
        self.date_entry.grid(
            row=3, column=0, padx=5, pady=4, sticky="ew"
        )

        for column in range(4):
            form.columnconfigure(column, weight=1)

        ttk.Button(
            form,
            text="Register Tenant",
            command=self.add_tenant,
        ).grid(row=3, column=1, sticky="w", padx=5, pady=8)

        ttk.Button(
            form,
            text="Refresh",
            command=self.refresh,
        ).grid(row=3, column=2, sticky="w", padx=5, pady=8)

        ttk.Button(
            form,
            text="Deactivate Selected",
            command=self.deactivate_tenant,
        ).grid(row=3, column=3, sticky="w", padx=5, pady=8)

        
        ttk.Button(
            form,
            text="Remove Tenant",
            command=self.remove_selected_tenant,
        ).grid(row=4, column=3, sticky="w", padx=5, pady=8)


        table_frame = ttk.LabelFrame(
            self.parent,
            text="Registered Tenants",
            padding=10,
        )
        table_frame.pack(
            fill="both", expand=True, padx=20, pady=(12, 20)
        )

        columns = (
            "id", "name", "phone", "email",
            "property", "unit", "move_in", "status"
        )

        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            selectmode="browse",
        )

        headings = {
            "id": "ID",
            "name": "Tenant Name",
            "phone": "Phone",
            "email": "Email",
            "property": "Property",
            "unit": "Unit",
            "move_in": "Move-in Date",
            "status": "Status",
        }

        for column, heading in headings.items():
            self.tree.heading(column, text=heading)
            self.tree.column(column, width=120, minwidth=80)

        scrollbar = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.tree.yview,
        )
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def load_properties(self):
        from database import get_connection

        connection = get_connection()
        try:
            rows = connection.execute("""
                SELECT id, name, unit_number, status
                FROM properties
                ORDER BY name, unit_number
            """).fetchall()

            self.property_lookup = {}
            options = []

            for row in rows:
                label = (
                    f"{row['name']} - Unit {row['unit_number']} "
                    f"(ID {row['id']}) - {row['status']}"
                )
                options.append(label)
                self.property_lookup[label] = row["id"]

            self.property_combo["values"] = options

            if self.property_combo.get() not in self.property_lookup:
                self.property_combo.set("")

            if not options:
                self.property_combo.set("")
        finally:
            connection.close()

    def add_tenant(self):
        name = self.name_entry.get().strip()
        phone = self.phone_entry.get().strip()
        email = self.email_entry.get().strip()
        move_in = self.date_entry.get().strip()
        selected_property = self.property_combo.get()

        if not name or not phone or not selected_property:
            messagebox.showwarning(
                "Missing Information",
                "Enter the tenant's name and phone number, "
                "then select a property.",
            )
            return

        property_id = self.property_lookup.get(selected_property)

        if property_id is None:
            messagebox.showwarning(
                "No Property Selected",
                "Select a property before registering a tenant.",
            )
            return

        if move_in:
            try:
                datetime.strptime(move_in, "%Y-%m-%d")
            except ValueError:
                messagebox.showwarning(
                    "Invalid Date",
                    "Enter the move-in date as YYYY-MM-DD, "
                    "for example 2026-10-23.",
                )
                return
        else:
            move_in = None

        try:
            tenant_id = add_tenant(
                full_name=name,
                phone=phone,
                email=email or None,
                property_id=property_id,
                move_in_date=move_in,
            )

            messagebox.showinfo(
                "Success",
                f"Tenant registered successfully.\nTenant ID: {tenant_id}",
            )

            self.name_entry.delete(0, tk.END)
            self.phone_entry.delete(0, tk.END)
            self.email_entry.delete(0, tk.END)
            self.date_entry.delete(0, tk.END)

            self.refresh()

        except Exception as error:
            messagebox.showerror(
                "Registration Error",
                f"Could not register tenant.\n\n{error}",
            )

    def load_tenants(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        try:
            rows = get_all_tenants()

            for row in rows:
                self.tree.insert(
                    "",
                    tk.END,
                    values=(
                        row["id"],
                        row["full_name"],
                        row["phone"],
                        row["email"] or "-",
                        row["property_name"],
                        row["unit_number"],
                        row["move_in_date"] or "-",
                        row["status"],
                    ),
                )
        except Exception as error:
            messagebox.showerror(
                "Loading Error",
                f"Could not load tenants.\n\n{error}",
            )

    def deactivate_tenant(self):
        selected = self.tree.selection()

        if not selected:
            messagebox.showwarning(
                "No Tenant Selected",
                "Select a tenant from the table first.",
            )
            return

        values = self.tree.item(selected[0], "values")
        tenant_id = int(values[0])
        tenant_name = values[1]
        current_status = values[7]

        if current_status == "Inactive":
            messagebox.showinfo(
                "Already Inactive",
                "This tenant is already inactive.",
            )
            return

        confirm = messagebox.askyesno(
            "Confirm Deactivation",
            f"Deactivate tenant {tenant_name}?",
        )

        if not confirm:
            return

        try:
            set_tenant_status(tenant_id, "Inactive")
            messagebox.showinfo(
                "Success",
                "Tenant deactivated successfully.",
            )
            self.refresh()
        except Exception as error:
            messagebox.showerror(
                "Update Error",
                f"Could not deactivate tenant.\n\n{error}",
            )
     
    def remove_selected_tenant(self):
        selected = self.tree.selection()

        if not selected:
            messagebox.showwarning(
                "No Tenant Selected",
                "Select a tenant from the table first.",
            )
            return

        values = self.tree.item(selected[0], "values")
        tenant_id = int(values[0])
        tenant_name = values[1]

        confirm = messagebox.askyesno(
            "Confirm Removal",
            f"Permanently remove {tenant_name}?\n\n"
            "This cannot be undone.",
        )

        if not confirm:
            return

        try:
            remove_tenant(tenant_id)

            messagebox.showinfo(
                "Success",
                "Tenant removed successfully.",
            )
            self.refresh()

        except Exception as error:
            messagebox.showerror(
                "Removal Error",
                str(error),
            )
       

    def refresh(self):
        self.load_properties()
        self.load_tenants()
