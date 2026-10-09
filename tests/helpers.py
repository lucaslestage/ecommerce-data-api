"""Helpers and the deterministic seed dataset shared by the test suite.

Three outcomes are distinguished by the tests:
    - SUCCESS : the test passed;
    - FAILED  : the code ran but produced a wrong result;
    - TODO    : the function/route is not implemented yet (skeleton sentinel),
                reported as a pytest "skip" whose reason starts with "TODO".
Use `todo_if(...)` and `call_or_todo(...)` to mark the TODO case.
"""

import os
import sqlite3
import importlib.util

import pytest

# A secret long enough to avoid PyJWT's InsecureKeyLengthWarning.
TEST_SECRET = "test-secret-key-that-is-long-enough-123456"

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")

# ---------------------------------------------------------------------------
# Small deterministic dataset
# ---------------------------------------------------------------------------
SEED = {
    # Three creators. CRT_B is the one whose videos never sold anything.
    "Creator": (["creator_id", "name", "followers", "niche"],
                [("CRT_A", "Alice", 1000, "Travel"),
                 ("CRT_B", "Bob", 500, "Cooking"),
                 ("CRT_C", "Cleo", 2000, "Gaming")]),

    # VID_3 belongs to CRT_B and triggers no order.
    "Video": (["video_id", "creator_id", "views", "likes"],
              [("VID_1", "CRT_A", 1000, 100),
               ("VID_2", "CRT_A", 200, 10),
               ("VID_3", "CRT_B", 50, 1),
               ("VID_4", "CRT_C", 5000, 900)]),

    # PROD_2 and PROD_3 are low on stock; PROD_4 is never ordered.
    "Product": (["product_id", "category", "price", "cost", "stock"],
                [("PROD_1", "Kitchen", 40.0, 20.0, 100),
                 ("PROD_2", "Beauty", 10.0, 4.0, 5),
                 ("PROD_3", "Tech", 100.0, 60.0, 0),
                 ("PROD_4", "Toys", 25.0, 20.0, 50)]),

    # CUST_3 never ordered anything.
    "Customer": (["customer_id", "country"],
                 [("CUST_1", "France"),
                  ("CUST_2", "Mexico"),
                  ("CUST_3", "Spain")]),

    # ORD_3 is refunded: the money totals must ignore it.
    "Order": (["order_id", "date", "refunded", "customer_id", "video_id", "username"],
              [("ORD_1", "2025-01-10", 0, "CUST_1", "VID_1", "tester"),
               ("ORD_2", "2025-02-11", 0, "CUST_2", "VID_4", "other"),
               ("ORD_3", "2025-03-12", 1, "CUST_1", "VID_1", "tester")]),

    # ORD_1 is worth 2 x 40.0 + 1 x 10.0 = 90.0, ORD_2 is worth 100.0.
    "Contains": (["order_id", "product_id", "quantity", "final_price"],
                 [("ORD_1", "PROD_1", 2, 40.0),
                  ("ORD_1", "PROD_2", 1, 10.0),
                  ("ORD_2", "PROD_3", 1, 100.0),
                  ("ORD_3", "PROD_1", 1, 40.0)]),

    "Spend": (["campaign_id", "video_id", "amount"],
              [("CAMP_1", "VID_1", 500.0),
               ("CAMP_2", "VID_4", 100.0)]),
}

# The order the tables must be filled in: a row never points at a row that
# does not exist yet.
LOADING_ORDER = ["Creator", "Video", "Product", "Customer", "Order",
                 "Contains", "Spend"]

SEED_USER = ("tester", "secret")    # password hashed at seed time
OTHER_USER = ("other", "secret2")   # a second account, to prove isolation


# ---------------------------------------------------------------------------
# TODO / implementation helpers
# ---------------------------------------------------------------------------
def todo_if(condition, what="not implemented"):
    """Skip the test (reported as TODO) when `condition` is true."""
    if condition:
        pytest.skip(f"TODO: {what}")


def call_or_todo(func, *args, **kwargs):
    """Call `func`; if it raises NotImplementedError, mark the test as TODO."""
    try:
        return func(*args, **kwargs)
    except NotImplementedError:
        pytest.skip("TODO: NotImplementedError")


def is_todo_response(response):
    """True if a route still returns the skeleton {"message": "TODO"}."""
    try:
        return response.get_json() == {"message": "TODO"}
    except Exception:
        return False


def route_registered(client, path, method="GET"):
    """True if `path` is served by a registered route (the blueprint exists)."""
    from werkzeug.exceptions import NotFound, MethodNotAllowed
    adapter = client.application.url_map.bind("localhost")
    try:
        adapter.match(path, method=method)
        return True
    except MethodNotAllowed:
        return True  # path exists, just for another method
    except NotFound:
        return False


def todo_route(client, response, path, method="GET"):
    """Mark the test as TODO when the route is not registered yet or still
    returns the skeleton {"message": "TODO"} sentinel."""
    if not route_registered(client, path, method) or is_todo_response(response):
        pytest.skip(f"TODO: {method} {path}")


def todo_if_unauthorized(response):
    """Mark the test as TODO when the route answered 401.

    The routes are written long before the API is secured: Questions 14 to 19
    are done with no token at all, and the @token_required decorator is only
    added at Question 24. A test of those questions therefore always sends an
    Authorization header --- harmless while the route is open, needed once it
    is protected --- but a 401 means the token machinery is not ready yet
    (Questions 22-23), which is not what the test is about.
    """
    if response.status_code == 401:
        pytest.skip("TODO: a valid token (Questions 22-23)")


def is_hash_of(plain, stored):
    """True if `stored` is a bcrypt hash of `plain`.

    What Question 21 wrote is verified with bcrypt directly, NOT with the
    student's check_password(): a Question 21 test must not fail because of a
    Question 20 bug. The subject asks for bcrypt by name, so pinning it here
    is part of the contract.
    """
    import bcrypt

    raw = stored if isinstance(stored, bytes) else str(stored).encode()
    try:
        return bcrypt.checkpw(plain.encode(), raw)
    except (ValueError, TypeError):
        return False   # not a bcrypt hash at all


def payload_or_todo(token):
    """The payload the student's check_token() reads back from `token`.

    The skeleton returns an empty payload, so anything without a username
    means the function is not written yet (TODO rather than FAILED).
    """
    import utils

    try:
        payload = utils.check_token(token)
    except Exception:
        pytest.skip("TODO: check_token")
    if not payload or "username" not in payload:
        pytest.skip("TODO: check_token")
    return payload


def token_refused(token):
    """True if check_token() refuses `token`.

    Refusing may be raising (what token_required expects) or returning nothing
    usable: both are accepted, only letting a bad token through is an error.
    """
    import utils

    try:
        payload = utils.check_token(token)
    except Exception:
        return True
    return not payload or "username" not in payload


def auth_ready():
    """True once password hashing and token generation are implemented."""
    import utils
    try:
        return utils.hash_password("x") is not None and bool(utils.generate_token("x"))
    except Exception:
        return False


def field(row, column):
    """The value of `column` in `row`.

    The field names are part of the contract: the subject asks for the names
    of the ER diagram, so an alias or a renamed column is an error, not a
    detail. The message says which name was expected.
    """
    try:
        keys = list(row.keys())
    except AttributeError:
        raise AssertionError(
            f"expected a row holding a column {column!r}, got {row!r}. "
            f"These functions return the rows of a query, and the tests read "
            f"them by column name.")
    assert column in keys, (
        f"expected a column {column!r}, found {keys}. Use the field names of "
        f"the ER diagram: renaming a column (or giving it an alias) breaks "
        f"everything that reads it.")
    return row[column]


def names(rows):
    """The `name` column of each row."""
    return [field(row, "name") for row in rows]


def table_exists(connection, name):
    cur = connection.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", [name]
    )
    return cur.fetchone() is not None


def connect(path):
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def load_process_data():
    """Import data/process_data.py as a module (independently of packaging)."""
    path = os.path.join("data", "process_data.py")
    spec = importlib.util.spec_from_file_location("process_data", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check_it_ran(done, printed):
    """Used by the tests of populate_database(): a function that is not
    written yet is silent (-> TODO), one that ran and failed reports the error
    it caught (-> FAILED, with that error)."""
    todo_if(not done and not printed.strip(), "populate_database")
    assert done, ("populate_database() returned "
                  f"{done!r} instead of True. It printed:\n{printed.strip()}")
