"""Public tests for registration, authentication and protected routes.

The security questions (20 to 24) are tested here as their own questions: a
password that is not hashed, a token that never expires or a token whose
signature is not checked are failures, not details.

Each question is judged against a reference implementation rather than against
the student's other answers: Question 21 verifies the stored hash with bcrypt
directly, not with the student's check_password(), so a Question 20 bug cannot
also fail Question 21.
"""

import datetime

import pytest

import utils
from helpers import (
    todo_if, is_todo_response, auth_ready as _auth_ready,
    is_hash_of, payload_or_todo, token_refused, connect,
    SEED_USER, OTHER_USER, TEST_SECRET,
)


# ---- Registration (open route) ----------------------------------------
def test_register_open(client):
    r = client.post("/users/", json={"username": "newbie", "password": "pw"})
    todo_if(is_todo_response(r), "POST /users/ (register)")
    assert r.status_code == 200


# ---- Login -------------------------------------------------------------
def test_login_success(client):
    todo_if(not _auth_ready(), "hashing/token not implemented")
    r = client.post("/login", json={"username": "tester", "password": "secret"})
    todo_if(is_todo_response(r), "POST /login")
    assert r.status_code == 200
    assert "token" in r.get_json()


def test_login_wrong_password(client):
    todo_if(not _auth_ready(), "hashing/token not implemented")
    r = client.post("/login", json={"username": "tester", "password": "WRONG"})
    todo_if(is_todo_response(r), "POST /login")
    assert r.status_code == 401


# ---- Token protection --------------------------------------------------
def test_users_list_requires_token(client):
    todo_if(not _auth_ready(), "token protection not implemented")
    r = client.get("/users/")  # no Authorization header
    assert r.status_code == 401


def test_get_user_with_token(client, token, auth_header):
    todo_if(not token, "tokens not implemented")
    r = client.get("/users/tester", headers=auth_header)
    todo_if(is_todo_response(r), "GET /users/<username>")
    assert r.status_code == 200
    assert r.get_json()["username"] == "tester"


def test_patch_password_with_token(client, token, auth_header):
    """PATCH /users/<username> changes the password of that account."""
    todo_if(not token, "tokens not implemented")
    r = client.patch("/users/tester", json={"password": "a-new-secret"},
                     headers=auth_header)
    todo_if(is_todo_response(r), "PATCH /users/<username>")
    assert r.status_code == 200, (
        f"PATCH /users/tester answered {r.status_code} for a valid change")

    again = client.post("/login", json={"username": "tester",
                                        "password": "a-new-secret"})
    if again.status_code != 404:        # /login may not be written yet
        assert again.status_code == 200, (
            "the password was changed, so logging in with the new one must "
            f"succeed; got {again.status_code}")


def test_patch_password_without_a_password(client, token, auth_header):
    todo_if(not token, "tokens not implemented")
    r = client.patch("/users/tester", json={}, headers=auth_header)
    todo_if(is_todo_response(r), "PATCH /users/<username>")
    assert r.status_code == 400, (
        "a PATCH with no password in the body is an invalid request: 400, "
        f"got {r.status_code}")


# ---- Question 20: hashing ----------------------------------------------
def test_hash_password_does_not_keep_the_plain_text(db_path):
    hashed = utils.hash_password("secret")
    todo_if(hashed is None, "hash_password")
    raw = hashed if isinstance(hashed, bytes) else str(hashed).encode()
    assert raw != b"secret", (
        "hash_password() returned the password itself. The point of hashing "
        "is that the database never holds the plain text.")
    assert is_hash_of("secret", hashed), (
        "hash_password() did not return a bcrypt hash of the password. "
        "Use bcrypt.hashpw() with bcrypt.gensalt().")


def test_check_password_tells_the_right_one_from_the_wrong_one(db_path):
    hashed = utils.hash_password("secret")
    todo_if(hashed is None, "hash_password")
    # Prove check_password works on the good password before trusting its "no".
    todo_if(not utils.check_password("secret", hashed), "check_password")
    assert not utils.check_password("WRONG", hashed), (
        "check_password() accepted a wrong password.")


def test_check_user_against_the_database(client, db_path):
    todo_if(not _auth_ready(), "hashing not implemented")
    conn = connect(db_path)
    cursor = conn.cursor()
    try:
        ok = utils.check_user(SEED_USER[0], SEED_USER[1])
    except TypeError:
        ok = utils.check_user(SEED_USER[0], SEED_USER[1], cursor)
    finally:
        conn.close()
    todo_if(not ok, "check_user")
    assert ok is not False


def test_check_user_refuses_a_wrong_password(client, db_path):
    todo_if(not _auth_ready(), "hashing not implemented")
    conn = connect(db_path)
    cursor = conn.cursor()
    try:
        try:
            good = utils.check_user(SEED_USER[0], SEED_USER[1])
            bad = utils.check_user(SEED_USER[0], "NOT-THE-PASSWORD")
        except TypeError:
            good = utils.check_user(SEED_USER[0], SEED_USER[1], cursor)
            bad = utils.check_user(SEED_USER[0], "NOT-THE-PASSWORD", cursor)
    finally:
        conn.close()
    todo_if(not good, "check_user")
    assert not bad, ("check_user() accepted a wrong password: it must compare "
                     "the password, not only look the username up.")


# ---- Question 21: insert_user stores the hash --------------------------
def test_insert_user_stores_a_hash(client, db_path):
    todo_if(not _auth_ready(), "hashing not implemented")
    r = client.post("/users/", json={"username": "hashme", "password": "pw123"})
    todo_if(is_todo_response(r), "POST /users/ (register)")
    assert r.status_code == 200

    conn = connect(db_path)
    row = conn.execute("SELECT password FROM User WHERE username = ?",
                       ["hashme"]).fetchone()
    conn.close()
    assert row is not None, "the user was not inserted"

    stored = row["password"]
    raw = stored if isinstance(stored, bytes) else str(stored).encode()
    assert raw != b"pw123", (
        "the password is stored in plain text. insert_user() must store "
        "hash_password(user['password']).")
    assert is_hash_of("pw123", stored), (
        "what is stored is not a bcrypt hash of the password. "
        "(Careful not to hash the username by mistake.)")


# ---- Question 22: tokens ------------------------------------------------
def test_generate_token_returns_a_token(db_path):
    token = utils.generate_token("tester")
    todo_if(not token, "generate_token")
    assert isinstance(token, (str, bytes))
    assert token not in ("tester", b"tester"), (
        "generate_token() returned the username: it must return a signed JWT.")


def test_check_token_reads_the_username_back(db_path):
    token = utils.generate_token("tester")
    todo_if(not token, "generate_token")
    payload = payload_or_todo(token)
    assert payload["username"] == "tester", (
        f"the token carries {payload.get('username')!r} instead of 'tester'. "
        f"The payload must hold the username.")


def test_the_token_expires(db_path):
    """The subject asks for a token that expires after one hour."""
    token = utils.generate_token("tester")
    todo_if(not token, "generate_token")
    payload = payload_or_todo(token)
    assert "exp" in payload, (
        "the token has no expiry date. The payload must carry an 'exp' one "
        "hour in the future, otherwise a stolen token is valid forever.")

    now = datetime.datetime.now(datetime.timezone.utc).timestamp()
    delta = payload["exp"] - now
    assert 0 < delta <= 3600 + 120, (
        f"the token expires in {delta / 60:.0f} minutes; the subject asks for "
        f"one hour.")


def test_check_token_refuses_a_tampered_token(db_path):
    """A token whose payload was edited must not be accepted.

    check_token() is first exercised on a GOOD token: the skeleton returns an
    empty payload, so a test that only asked "is this bad token refused?"
    would pass on code nobody has written.
    """
    import jwt

    good = utils.generate_token("tester")
    todo_if(not good, "generate_token")
    payload_or_todo(good)   # the baseline: check_token works on a real token

    forged = jwt.encode({"username": "attacker",
                         "exp": datetime.datetime.now(datetime.timezone.utc)
                         + datetime.timedelta(hours=1)},
                        "not-the-right-secret-but-long-enough-1234567", algorithm="HS256")
    assert token_refused(forged), (
        "a token signed with another secret was accepted. check_token() must "
        "verify the signature with the SECRET_KEY of the configuration.")


# ---- Question 23: POST /login ------------------------------------------
def test_login_returns_a_usable_token(client, db_path):
    """/login must hand out a real token, not a made-up string.

    The baseline is established FIRST: check_token() is shown to read back a
    token that generate_token() produced. Only then is the token from /login
    asserted to be readable --- otherwise a /login answering
    {"token": "a-token"} would merely report TODO, because the unreadable
    string looks exactly like a check_token() nobody has written yet.
    """
    todo_if(not _auth_ready(), "hashing/token not implemented")
    reference = utils.generate_token("tester")
    todo_if(not reference, "generate_token")
    payload_or_todo(reference)          # baseline: the token machinery works

    r = client.post("/login", json={"username": "tester", "password": "secret"})
    todo_if(is_todo_response(r), "POST /login")
    assert r.status_code == 200
    token = r.get_json().get("token")
    assert token, "POST /login answered 200 without a token"

    try:
        payload = utils.check_token(token)
    except Exception as error:                          # noqa: BLE001
        pytest.fail(f"the token handed out by /login is rejected by "
                    f"check_token() ({error!r}): it is not a real token.")
    assert payload and "username" in payload, (
        f"the token handed out by /login carries nothing readable "
        f"({payload!r}): /login must return generate_token(username), not a "
        f"made-up string.")
    assert payload["username"] == "tester", (
        f"/login handed out a token for {payload.get('username')!r}. It must "
        f"be a real token for the user who logged in, not somebody else's.")


def test_login_missing_password(client):
    todo_if(not _auth_ready(), "hashing/token not implemented")
    r = client.post("/login", json={"username": "tester"})
    todo_if(is_todo_response(r), "POST /login")
    assert r.status_code == 400, (
        f"a request with no password answered {r.status_code}; a missing "
        f"field in the body is a 400.")
