import tkinter as tk

from database import initialize_database
from ui.login import LoginWindow
from ui.admin_dash import AdminDashboard
from ui.managers_dash import ManagersDashboard


def main():
    initialize_database()

    root = tk.Tk()
    root.title("Ole Segeri - Rental Remittance System")
    root.state("zoomed")
    root.configure(bg="#F3F5F9")

    def clear_screen():
        root.unbind("<Return>")

        for widget in root.winfo_children():
            widget.destroy()

            root.update_idletasks()

    def open_dashboard(user):
        clear_screen()

        role = user["role"].strip().lower()

        if role == "admin":
            AdminDashboard(root, user, show_login)

        elif role == "manager":
            ManagersDashboard(root, user, show_login)

        else:
            tk.Label(
                root,
                text=f"Unsupported user role: {role}",
                font=("Segoe UI", 16),
                bg="#F3F5F9",
                fg="#142D4E"
            ).pack(pady=50)

    def show_login():
        clear_screen()
        root.title("Ole Segere - Rental Remittance System ")
        root.configure(bg="#F3F5F9")
        root.state("zoomed")

        
        LoginWindow(root, open_dashboard)

    show_login()
    root.mainloop()


if __name__ == "__main__":
    main()