
from auth import create_user, login


def test_account(username, password, role):
    print(f"\n--- Testing {role.upper()} Account ---")

    success, message = create_user(username, password, role)
    print(message)

    user = login(username, password)

    if user is not None:
        print("Login successful:", True)
        print("Username:", user["username"])
        print("User role:", user["role"])
        print(
            "Role verification:",
            "PASS" if user["role"].lower() == role else "FAIL"
        )
    else:
        print("Login successful:", False)
        print("Check the credentials or account status.")


if __name__ == "__main__":
    test_account("admin", "AdminTest123!", "admin")
    test_account("manager", "ManagerTest123!", "manager")
