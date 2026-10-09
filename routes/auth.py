from flask import Blueprint, request, jsonify
from utils import check_user, check_token, generate_token

auth_bp = Blueprint("login", __name__)


@auth_bp.route("/login", methods=["POST"])
def login():
    """Login a user and provide a token for future requests to the API

    Returns
    -------
    data
        a token to authenticate future request to the API.
        an error message "No username or password provided" if the
            username or password is not provided
        a message "Invalid credentials" if the username is unknown OR the
            password is wrong
        an error message "Error: while authenticating user" if an error
            occurred while authenticating the user.
    status_code
        200 if the token is correctly provided
        400 if the username or password is not provided
        401 if the credentials are wrong
        500 if an error occurred while authenticating the user

    Answer an unknown username and a wrong password in exactly the same way
    (401, same message). Answering differently would tell an attacker which
    usernames exist.
    """
    data = request.get_json()

    if not data or ("username" not in data) or ("password" not in data) :
        return jsonify({"error": "No username or password provided"}), 400

    username = data["username"]
    password = data["password"]

    try:
        if not check_user(username, password):
            return jsonify({"message": "Invalid credentials"}), 401
    except Exception :
        print("An error occurred while authenticating the user")
        return jsonify({"error": "Error: while authenticating user"}), 500

    token = generate_token(username)
    return jsonify({"token": token}), 200
