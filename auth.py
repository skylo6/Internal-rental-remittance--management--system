
import hashlib
import hmac
import secrets

from database import get_connection


def hash_password(password):
    """Hash a password securely using PBKDF2."""
    salt = secrets.token_bytes(16)

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        600_000
    )

    return salt.hex() + ":" + password_hash.hex()


def verify_password(password, stored_hash):
    """Verify a password against its stored hash."""
    try:
        salt_hex, hash_hex = stored_hash.split(":")
        salt = bytes.fromhex(salt_hex)

        expected_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            600_000
        )

        return hmac.compare_digest(
            expected_hash.hex(),
            hash_hex
        )

    except (ValueError, TypeError, AttributeError):
        return False


def create_user(username, password, role):
    """Create an Admin or Manager account."""
    username = username.strip()
    role = role.strip().lower()

    if not username or not password:
        return False, "Username and password are required."

    if role not in ("admin", "manager"):
        return False, "Role must be admin or manager."

    if len(password) < 8:
        return False, "Password must contain at least 8 characters."

    password_hash = hash_password(password)

    try:
        with get_connection() as connection:
            connection.execute(
                """
                INSERT INTO users (username, password_hash, role)
                VALUES (?, ?, ?)
                """,
                (username, password_hash, role)
            )

        return True, "User created successfully."

    except Exception as error:
        if "UNIQUE constraint failed" in str(error):
            return False, "That username already exists."
        raise


def login(username, password):
    """Authenticate an active user."""
    with get_connection() as connection:
        user = connection.execute(
            """
            SELECT id, username, password_hash, role
            FROM users
            WHERE username = ? AND is_active = 1
            """,
            (username.strip(),)
        ).fetchone()

    if user is None:
        return None

    if verify_password(password, user["password_hash"]):
        return {
            "id": user["id"],
            "username": user["username"],
            "role": user["role"]
        }

    return None
