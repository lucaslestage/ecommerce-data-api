import utils
import sqlite3

def insert_user(user: dict, cursor) -> bool:
    """Inserts a user into to the database.

    Parameters
    ----------
    user: a dictionary
        User personal data: user["username"] and user["password"].
    cursor:
        The object used to query the database.

    Returns
    -------
    bool
        True if no error occurs, False otherwise.
    """
    try:
        query_insert_user = "INSERT INTO User (username, password) VALUES (?, ?)"
        cursor.execute(query_insert_user, (user["username"],utils.hash_password(user["password"])))
        cursor.connection.commit()          # <-- à ajouter, sinon l'insertion est perdue
    except sqlite3.IntegrityError as error:
        print(f"An integrity error occurred while inserting the user: {error}")
        return False
    except sqlite3.Error as error:
        print(f"A database error occurred while inserting the user: {error}")
        return False
    return True


def get_user(username: str, cursor) -> dict | None:
    """Get a user from the database based on its username.

    Parameters
    ----------
    username: string
        User's username.
    cursor:
        The object used to query the database.

    Returns
    -------
    dict
        The user username and password.
        An EMPTY dictionary if no user has this username.
        None if the query to the database failed.

    The three cases are distinct on purpose: "no such user" is a successful
    query returning nothing (the route answers 404), while a failed query is
    an error (the route answers 500).
    """
    try:
        query_get_user = "SELECT * FROM User WHERE username = ?"
        cursor.execute(query_get_user, (username,))

        user = cursor.fetchone()
        if user is None:
            # No user has this username: a successful query returning nothing,
            # NOT a failure. The route answers 404, not 500.
            return {}
    except sqlite3.Error as error:
        print(f"A database error occurred while fetching the user: {error}")
        return None

    return dict(user)


def get_users(cursor) -> list[dict] | None:
    """Get all users from the database.

    Parameters
    ----------
    cursor:
        The object used to query the database.

    Returns
    -------
    list
        The list of all the users if no error occurs, None otherwise.
    """
    try:
        query_get_users = "SELECT username FROM User"
        cursor.execute(query_get_users, tuple())

    except sqlite3.Error as error:
        print(f"A database error occurred while fetching the users: {error}")
        return None

    # The db layer returns plain Python: convert each row to a dictionary here,
    # so that sqlite3 never leaks outside db/ and the routes can jsonify the
    # result directly.
    return [dict(row) for row in cursor.fetchall()]

def update_password(username: str, password, cursor) -> bool:
    """Update the password of a user.

    Parameters
    ----------
    username: string
        User's username.
    password: bytes
        New password
    cursor:
        The object used to query the database.

    Returns
    -------
    bool
        True if no error occurs, False otherwise.
    """

    try:
        user = get_user(username, cursor)

        if user == {} or user is None:
            print("No user has this username")
            return False

        query_update_password = """
            UPDATE User
            SET password = ?
            WHERE username = ?
        """

        cursor.execute(
            query_update_password,
            (utils.hash_password(password), username)
        )

        cursor.connection.commit()
    except sqlite3.Error as error:
        print(f"A database error occurred while updating the password: {error}")
        return False
    return True

def get_orders_handled_by_user(username: str, cursor) -> list[dict] | None:
    """Get all the orders one employee prepared.

    Parameters
    ----------
    username: string
        User's username.
    cursor:
        The object used to query the database.

    Returns
    -------
    list
        The list of the orders (possibly empty), or None if the query to the
        database failed.
    """
    try:
        query_get_orders = """
            SELECT *
            FROM "Order"
            WHERE username = ?
        """

        cursor.execute(query_get_orders, (username,))
        orders = cursor.fetchall()

    except sqlite3.Error as error:
        print(f"A database error occurred while fetching the orders: {error}")
        return None

    return [dict(order) for order in orders]