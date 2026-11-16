import tkinter as tk
from tkinter import messagebox
from auth import login


class LoginWindow:
    def __init__(self, root, on_login_success):
        self.root = root
        self.on_login_success = on_login_success

        self.root.title("Internal Rental Remittance System")
        self.root.state("zoomed")
        self.root.configure(bg="#F3F5F9")

        self.create_widgets()

    def create_widgets(self):
        container = tk.Frame(
            self.root,
            bg="white",
            padx=40,
            pady=35
        )
        container.place(
            relx=0.5,
            rely=0.5,
            anchor="center",
            width=480,
            height=420
        )

        tk.Label(
            container,
            text="RENTAL REMITTANCE",
            font=("Segoe UI", 21, "bold"),
            bg="white",
            fg="#142D4E"
        ).pack(pady=(10, 8))

        tk.Label(
            container,
            text="Sign in to your account",
            font=("Segoe UI", 11),
            bg="white",
            fg="#666666"
        ).pack(pady=(0, 25))

        tk.Label(
            container,
            text="Username",
            font=("Segoe UI", 10, "bold"),
            bg="white"
        ).pack(anchor="w")

        self.username_entry = tk.Entry(
            container,
            font=("Segoe UI", 12),
            relief="solid",
            bd=1
        )
        self.username_entry.pack(fill="x", ipady=8, pady=(5, 15))

        tk.Label(
            container,
            text="Password",
            font=("Segoe UI", 10, "bold"),
            bg="white"
        ).pack(anchor="w")

        self.password_entry = tk.Entry(
            container,
            font=("Segoe UI", 12),
            show="*",
            relief="solid",
            bd=1
        )
        self.password_entry.pack(fill="x", ipady=8, pady=(5, 10))

        self.show_password = tk.BooleanVar(value=False)

        tk.Checkbutton(
            container,
            text="Show password",
            variable=self.show_password,
            command=self.toggle_password,
            bg="white",
            activebackground="white"
        ).pack(anchor="w")

        tk.Button(
            container,
            text="LOGIN",
            command=self.handle_login,
            font=("Segoe UI", 11, "bold"),
            bg="#142D4E",
            fg="white",
            activebackground="#24466D",
            activeforeground="white",
            relief="flat",
            cursor="hand2"
        ).pack(fill="x", ipady=10, pady=(20, 5))

        self.username_entry.focus_set()
        self.root.bind("<Return>", lambda event: self.handle_login())

    def toggle_password(self):
        self.password_entry.config(
            show="" if self.show_password.get() else "*"
        )

    def handle_login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get()

        if not username or not password:
            messagebox.showwarning(
                "Missing details",
                "Please enter your username and password."
            )
            return

        user = login(username, password)

        if user:
            self.root.unbind("<Return>")
            self.on_login_success(user)
        else:
            messagebox.showerror(
                "Login failed",
                "Incorrect username or password."
            )
            self.password_entry.delete(0, tk.END)
            self.password_entry.focus_set()
