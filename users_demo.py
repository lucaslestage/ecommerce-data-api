import db.users
from db import get_db_connection, close_db_connection


def print_users():
    """Print the users in the database in the console."""
    conn = get_db_connection()
    cursor = conn.cursor()

    users = db.users.get_users(cursor)
    if users != None :
        print("Users in database:", [dict(user) for user in users])

    close_db_connection(cursor, conn)


def insert_hubert(cursor):
    """Inserts a user into the database.

    Parameters
    ----------
    cursor:
        The object used to query the database.

    Returns
    -------
    bool
        True if the user could be inserted, False otherwise.
    """

    # Personal data of user Hubert
    hubert = {"username": "hubert", "password": "117"}

    print("Inserting user Hubert...")
    if db.users.insert_user(hubert, cursor):
        print("Hubert added successfully !")
        return True
    else:
        print("Impossible to add Hubert ...")
        return False


########## TEST FUNCTIONS ##########

def test_insert_user():
    print("## TEST: insert a user")
    # Open a connection to the database.
    conn = get_db_connection()

    # Get the cursor for the connection. This object is used to execute queries
    # in the database.
    cursor = conn.cursor()

    # Insert user Hubert
    insert_hubert(cursor)
    # Close connection
    close_db_connection(cursor, conn)


def test_update_password_existing_user():
    print("\n## TEST: update a user that is in the database")
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Update user hubert
        update_ok = db.users.update_password("hubert", "12", cursor)

        # Print results from update
        print("Update successful:", update_ok)
        print("Number of modified rows in the database:", cursor.rowcount)
    except NotImplementedError as error:
        print("update_password() not implemented")
    close_db_connection(cursor, conn)


def test_update_password_non_existing_user():
    print("\n## TEST: update a user that does not exist in the database")
    conn = get_db_connection()
    cursor = conn.cursor()

    # Update user bond
    try:
        update_ok = db.users.update_password("bond", "12", cursor)
        # Print results from update
        print("Update successful:", update_ok)
        print("Number of modified rows in the database:", cursor.rowcount)
    except NotImplementedError as error:
        print("update_password() not implemented")

    close_db_connection(cursor, conn)


if __name__ == "__main__":

    test_insert_user()
    print_users()

    test_update_password_existing_user()
    test_update_password_non_existing_user()
    print_users()
