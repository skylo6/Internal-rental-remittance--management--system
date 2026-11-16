
import sqlite3
from pathlib import Path

DATABASE_PATH = Path(__file__).resolve().parent / "rental_system.db"


def get_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database():
    connection = get_connection()

    try:
        connection.execute("BEGIN")

        # Users table
        table = connection.execute("""
            SELECT name FROM sqlite_master
            WHERE type = 'table' AND name = 'users'
        """).fetchone()

        if table is None:
            connection.execute("""
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL
                        CHECK (role IN ('admin', 'manager')),
                    is_active INTEGER NOT NULL DEFAULT 1
                        CHECK (is_active IN (0, 1)),
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)
        else:
            columns = {
                row["name"]
                for row in connection.execute(
                    "PRAGMA table_info(users)"
                ).fetchall()
            }

            required = {
                "id", "username", "password_hash",
                "role", "is_active", "created_at"
            }

            if not required.issubset(columns):
                raise RuntimeError(
                    "Unexpected users table structure."
                )

            schema = connection.execute("""
                SELECT sql FROM sqlite_master
                WHERE type = 'table' AND name = 'users'
            """).fetchone()["sql"]

            if "'manager'" not in schema:
                connection.execute("""
                    CREATE TABLE users_new (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT NOT NULL UNIQUE,
                        password_hash TEXT NOT NULL,
                        role TEXT NOT NULL
                            CHECK (role IN ('admin', 'manager')),
                        is_active INTEGER NOT NULL DEFAULT 1
                            CHECK (is_active IN (0, 1)),
                        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                connection.execute("""
                    INSERT INTO users_new
                    (id, username, password_hash, role,
                     is_active, created_at)
                    SELECT id, username, password_hash,
                           CASE WHEN role = 'owner'
                                THEN 'manager' ELSE role END,
                           is_active, created_at
                    FROM users
                """)

                connection.execute("DROP TABLE users")
                connection.execute(
                    "ALTER TABLE users_new RENAME TO users"
                )
            else:
                connection.execute("""
                    UPDATE users SET role = 'manager'
                    WHERE role = 'owner'
                """)

        # Properties
        connection.execute("""
            CREATE TABLE IF NOT EXISTS properties (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                location TEXT NOT NULL,
                unit_number TEXT NOT NULL,
                monthly_rent REAL NOT NULL CHECK (monthly_rent >= 0),
                status TEXT NOT NULL DEFAULT 'Vacant'
                    CHECK (status IN ('Occupied', 'Vacant')),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (name, unit_number)
            )
        """)

        # Tenants
        connection.execute("""
            CREATE TABLE IF NOT EXISTS tenants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                phone TEXT NOT NULL,
                email TEXT,
                property_id INTEGER NOT NULL,
                move_in_date TEXT,
                status TEXT NOT NULL DEFAULT 'Active'
                    CHECK (status IN ('Active', 'Inactive')),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (property_id)
                    REFERENCES properties(id)
            )
        """)

        # Rent payments
        connection.execute("""
            CREATE TABLE IF NOT EXISTS rent_payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id INTEGER NOT NULL,
                property_id INTEGER NOT NULL,
                amount REAL NOT NULL CHECK (amount > 0),
                payment_date TEXT NOT NULL,
                rent_month TEXT NOT NULL,
                method TEXT NOT NULL DEFAULT 'M-Pesa',
                reference TEXT UNIQUE,
                recorded_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (tenant_id) REFERENCES tenants(id),
                FOREIGN KEY (property_id) REFERENCES properties(id)
            )
        """)

        # Property expenses
        connection.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                property_id INTEGER NOT NULL,
                description TEXT NOT NULL,
                amount REAL NOT NULL CHECK (amount > 0),
                expense_date TEXT NOT NULL,
                category TEXT NOT NULL DEFAULT 'Other',
                recorded_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (property_id) REFERENCES properties(id)
            )
        """)

        # Remittances
        connection.execute("""
            CREATE TABLE IF NOT EXISTS remittances (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                property_id INTEGER NOT NULL,
                period TEXT NOT NULL,
                gross_rent REAL NOT NULL DEFAULT 0,
                expenses REAL NOT NULL DEFAULT 0,
                amount_due REAL NOT NULL DEFAULT 0,
                amount_paid REAL NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'Pending'
                    CHECK (status IN ('Pending', 'Partial', 'Paid')),
                payment_date TEXT,
                reference TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (property_id, period),
                FOREIGN KEY (property_id) REFERENCES properties(id)
            )
        """)

        connection.commit()
        print("Database initialized successfully.")
        print("Supported roles: admin, manager")
        print(
            "Tables ready: users, properties, tenants, "
            "rent_payments, expenses, remittances"
        )

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


if __name__ == "__main__":
    initialize_database()
