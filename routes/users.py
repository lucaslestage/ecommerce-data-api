from flask import Blueprint, request, jsonify

from db import get_db_connection, close_db_connection

import utils
import requests
import db.users

users_bp = Blueprint("users", __name__)

@users_bp.route("/", methods=["GET"])
@utils.token_required
def get_all_users():
    """Fetch all users from the database.

    Returns
    -------
    status_code
        200 by default if no error occurred
        500 if an error occurred while fetching the users
    data
        users as a json if no error occurs (can be empty if no users)
        an error message if an error occurred while fetching the users.
    """
    conn = get_db_connection()

    if conn is None:
        return "Error", 500

    cursor = conn.cursor()

    all_users = db.users.get_users(cursor)
    close_db_connection(cursor, conn)

    if all_users is None:
        return "Error: while fetching users", 500
    return jsonify({"users": [user["username"] for user in all_users]}), 200


@users_bp.route("/<user_username>", methods=["GET"])
@utils.token_required
def get_user(user_username):
    """Fetch a single user from the database based on its username.

    200 with the user, 404 if no user has this username, 500 on error.
    The password never leaves the server, even hashed.
    """
    conn = get_db_connection()

    if conn is None:
        return "Error", 500

    cursor = conn.cursor()

    user = db.users.get_user(user_username, cursor)

    if user is None:
        close_db_connection(cursor, conn)
        return "Error", 500

    if len(user) == 0:
        close_db_connection(cursor, conn)
        return "No user has this username", 404 

    user.pop("password")

    return jsonify(user), 200

@users_bp.route("/<user_username>", methods=["PATCH"])
@utils.token_required
def patch_password(user_username):
    """Patch the password of a user.
    The password must be passed in the data of the PATCH request.

    200 if the password is changed, 400 if no password is given in the
    request, 500 on error.
    """
    conn = get_db_connection()

    if conn is None:
        return "Error", 500

    cursor = conn.cursor()

    data = request.get_json()

    if data is None or "password" not in data:
        close_db_connection(cursor, conn)
        return "No password given", 400

    password = data["password"]

    success = db.users.update_password(
        user_username,
        password,
        cursor
    )

    close_db_connection(cursor, conn)

    if not success:
        return "Error", 500

    return jsonify({"message": "Password updated"}), 200

@users_bp.route("/", methods=["POST"])
def add_user():
    """Add a user to the database.
    The username and password must be passed in the data of the POST request.

    Registration is open (no token required): a user needs to create an
    account before being able to obtain a token.
    """
    conn = get_db_connection()

    if conn is None:
        return "Error", 500

    cursor = conn.cursor()

    data = request.get_json()

    if data is None or "password" not in data or "username" not in data:
        close_db_connection(cursor, conn)
        return "No password given or Username given", 400

    success = db.users.insert_user({
        "username": data["username"], 
        "password": data["password"]
    }, 
    cursor)

    close_db_connection(cursor, conn)

    if not success:
        return "Error", 500

    return jsonify({"message": "Password updated"}), 200


@users_bp.route("/orders/<user_username>", methods=["GET"])
def get_user_orders(user_username):
    """Fetch all the orders one employee prepared.

    200 with {"orders": [...]}, 404 if no user has this username,
    500 on error.
    """
    # TODO
    return jsonify({"message": "TODO"})
