import getpass

PASSWORD = "finance123"   # change this to your own


def authenticate_user():

    attempts = 3

    for _ in range(attempts):

        entered = getpass.getpass("Enter password: ")

        if entered == PASSWORD:
            print("Access granted.\n")
            return True

        else:
            print("Incorrect password.\n")

    print("Too many failed attempts. Exiting.")
    return False