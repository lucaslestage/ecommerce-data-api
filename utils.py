import bcrypt
import jwt
import datetime
from functools import wraps
from flask import request, jsonify
from db.users import get_user
import db

import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
CONFIG_FILE = "./config/config"

def load_config():
    """Loads the application configuration from the configuration file
    into a dictionary.

    The configuration file is a text file where each line is of the form
    key,value

    Returns
    -------
    A dictionary.
        The application configuration.
    """
    config = {}

    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        for line in f:
            key, value = line.strip().split(",", 1)
            config[key] = value

    return config

def hash_password(plain_password):
    """Hash a password

    Parameters
    ----------
    plain_password
        plain password to hash

    Returns
    -------
    hashed_password
        A password hash
    """
    return bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt())


def check_password(plain_password, hashed_password):
    """Check the plain password against its hashed value

    Parameters
    ----------
    plain_password
        the plain password to check
    hashed_password
        a password hash to check if it is the hash of the plain password

    Returns
    -------
    bool
        True if hashed_password is the hash of plain_password, False otherwise
    """
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password)


def check_user(username, plain_password):
    """Authenticate a user based on its username and a plain password.

    Parameters
    ----------
    username
        the user's username
    plain_password
        the plain password to check

    Returns
    -------
    bool
        True if the password is associated to the user, False otherwise
    """
    conn = db.get_db_connection()

    if conn is None:
        return False
    
    cursor = conn.cursor()

    user = get_user(username, cursor)

    if user == {} or user is None:
        return False

    print("plain:", plain_password, type(plain_password))
    print("stored:", user["password"], type(user["password"]))

    return check_password(plain_password, user["password"])


def generate_token(username):
    """Generate a token with a username and an expiration date of 1 hour.

    Parameters
    ----------
    username
        the user's username

    Returns
    -------
    token
        the generated token based on the username and an expiration date of 1 hour
    """
    token_info = {
        "username": username,
        "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1)
    }

    token = jwt.encode(token_info, SECRET_KEY, algorithm="HS256")

    return token

def check_token(token):
    """Check the validity of a token.

    Parameters
    ----------
    token
        the token to check

    Returns
    -------
    payload
        The payload associated with the token if the token is correctly decoded.
        An error if the token is expired or invalid
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"]) 
        return payload
    except jwt.ExpiredSignatureError:
        raise jwt.ExpiredSignatureError
    except jwt.InvalidTokenError:
        raise jwt.InvalidTokenError


def token_required(f):
    """A decorator to specify which routes need a token validation."""

    @wraps(f)
    def decorated(*args, **kwargs):
        """Define the behaviour of a route when a token validation is required."""
        token = None

        # The header is expected to look like "Authorization: Bearer <token>".
        # Anything else (no header, an empty one, "Bearer" with nothing after
        # it, or another scheme) leaves the token unset and is answered with a
        # 401: a malformed request is the client's mistake, not a server
        # failure, so it must not be allowed to raise.
        parts = request.headers.get("Authorization", "").split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            token = parts[1]

        if not token:
            return jsonify({"message": "Missing token"}), 401

        try:
            payload = check_token(token)
            if not "username" in payload or not "exp" in payload:
                return jsonify({"error": "Invalid token"}), 401

        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401
        return f(*args, **kwargs)

    return decorated
