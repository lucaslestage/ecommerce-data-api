"""Public tests for the routes (Questions 14, 17, 18 and 19).

A route that is not registered yet, or that still answers the skeleton
{"message": "TODO"}, is reported as TODO rather than as a failure: these
tests are meant to be run from the first session, long before the routes
exist.
"""

import pytest

from helpers import (connect, field, table_exists, todo_if,
                     todo_if_unauthorized, todo_route)


@pytest.fixture(autouse=True)
def _needs_the_schema(db_path):
    """A route reads the database: until create_database() builds the tables
    it can only answer 500, which is TODO rather than a wrong answer."""
    conn = connect(db_path)
    missing = not table_exists(conn, "Creator")
    conn.close()
    if missing:
        todo_if(True, "create_database")


def body_of(response, key):
    """The list a route answers, whether it is wrapped in a key or not."""
    body = response.get_json()
    if isinstance(body, dict):
        return body.get(key, body)
    return body


# ---------------------------------------------------------------------------
# Question 17 - the blueprints
# ---------------------------------------------------------------------------
def test_the_users_blueprint_is_registered(client):
    """app.py must register each blueprint, otherwise none of its routes
    exists, however well the functions themselves are written."""
    r = client.get("/users/")
    assert r.status_code != 404, (
        "GET /users/ answers 404: the blueprint is not registered. In "
        'create_app(), add\n'
        '      app.register_blueprint(users_bp, url_prefix="/users")')


# ---------------------------------------------------------------------------
# Question 17 - the routes about the users
# ---------------------------------------------------------------------------
def test_get_all_users(client, auth_header):
    r = client.get("/users/", headers=auth_header)
    todo_route(client, r, "/users/")
    todo_if_unauthorized(r)
    assert r.status_code == 200
    users = body_of(r, "users")
    assert len(users) == 2, f"two users are seeded, the route returned {users}"


def test_get_one_user(client, auth_header):
    r = client.get("/users/tester", headers=auth_header)
    todo_route(client, r, "/users/tester")
    todo_if_unauthorized(r)
    assert r.status_code == 200, (
        f"GET /users/tester answered {r.status_code}; 'tester' exists")
    body = r.get_json()
    user = body.get("user", body) if isinstance(body, dict) else body
    assert field(user, "username") == "tester"


def test_get_an_unknown_user_is_404(client, auth_header):
    """A user who does not exist is not an error of the server: the query
    succeeded and found nothing, which is a 404."""
    r = client.get("/users/ghost", headers=auth_header)
    todo_route(client, r, "/users/ghost")
    todo_if_unauthorized(r)
    assert r.status_code == 404, (
        f"GET /users/ghost answered {r.status_code}; nobody is called "
        "'ghost', so the answer is 404, not 500")


def test_add_user(client):
    """Registration is open: it is how an account is created in the first
    place, so it needs no token."""
    r = client.post("/users/", json={"username": "newcomer",
                                     "password": "secret"})
    todo_route(client, r, "/users/", method="POST")
    assert r.status_code in (200, 201), (
        f"POST /users/ answered {r.status_code} for a valid new account")
    check = client.post("/login", json={"username": "newcomer",
                                        "password": "secret"})
    if check.status_code != 404:       # /login may not be written yet
        assert check.status_code in (200, 401), (
            "the account was created, so /login must answer 200 (or 401 "
            f"while hashing is not done), not {check.status_code}")


def test_add_user_without_a_password(client):
    r = client.post("/users/", json={"username": "halfway"})
    todo_route(client, r, "/users/", method="POST")
    assert r.status_code == 400, (
        "a registration with no password is an invalid request: 400, "
        f"got {r.status_code}")


# ---------------------------------------------------------------------------
# Question 18 - the debug routes
# ---------------------------------------------------------------------------
def test_data_creators(client):
    r = client.get("/data/creators")
    todo_route(client, r, "/data/creators")
    todo_if_unauthorized(r)
    assert r.status_code == 200
    assert len(body_of(r, "creators")) == 3, "three creators are seeded"


def test_data_products(client):
    r = client.get("/data/products")
    todo_route(client, r, "/data/products")
    todo_if_unauthorized(r)
    assert r.status_code == 200
    assert len(body_of(r, "products")) == 4, "four products are seeded"


def test_data_orders(client):
    r = client.get("/data/orders")
    todo_route(client, r, "/data/orders")
    todo_if_unauthorized(r)
    assert r.status_code == 200
    assert len(body_of(r, "orders")) == 3, "three orders are seeded"


# ---------------------------------------------------------------------------
# Question 19 - the remaining routes
# ---------------------------------------------------------------------------
def test_get_creator_route(client):
    r = client.get("/creators/CRT_A")
    todo_route(client, r, "/creators/CRT_A")
    todo_if_unauthorized(r)
    assert r.status_code == 200
    body = r.get_json()
    creator = body.get("creator", body) if isinstance(body, dict) else body
    assert field(creator, "name") == "Alice"


def test_get_an_unknown_creator_is_404(client):
    r = client.get("/creators/CRT_NOPE")
    todo_route(client, r, "/creators/CRT_NOPE")
    todo_if_unauthorized(r)
    assert r.status_code == 404, (
        "no creator has this id, so the answer is 404, not "
        f"{r.status_code}")


def test_get_creator_videos_route(client):
    r = client.get("/creators/CRT_A/videos")
    todo_route(client, r, "/creators/CRT_A/videos")
    todo_if_unauthorized(r)
    assert r.status_code == 200
    videos = body_of(r, "videos")
    assert [field(v, "video_id") for v in videos] == ["VID_1", "VID_2"], (
        "the videos of CRT_A, the most viewed first")


def test_get_video_route(client):
    """A video is read through its creator: the route lives in the creators
    blueprint, so its address starts with /creators."""
    r = client.get("/creators/videos/VID_1")
    todo_route(client, r, "/creators/videos/VID_1")
    todo_if_unauthorized(r)
    assert r.status_code == 200
    body = r.get_json()
    video = body.get("video", body) if isinstance(body, dict) else body
    assert field(video, "creator_id") == "CRT_A"


def test_get_product_route(client):
    r = client.get("/products/PROD_1")
    todo_route(client, r, "/products/PROD_1")
    todo_if_unauthorized(r)
    assert r.status_code == 200
    body = r.get_json()
    product = body.get("product", body) if isinstance(body, dict) else body
    assert field(product, "category") == "Kitchen"


def test_get_an_unknown_product_is_404(client):
    r = client.get("/products/PROD_NOPE")
    todo_route(client, r, "/products/PROD_NOPE")
    todo_if_unauthorized(r)
    assert r.status_code == 404, (
        f"no product has this id, so the answer is 404, not {r.status_code}")


def test_get_low_stock_products_route(client):
    r = client.get("/products/low_stock/10")
    todo_route(client, r, "/products/low_stock/10")
    todo_if_unauthorized(r)
    assert r.status_code == 200
    products = body_of(r, "products")
    assert [field(p, "product_id") for p in products] == ["PROD_3", "PROD_2"], (
        "below 10 there are PROD_3 (0) and PROD_2 (5), the emptiest first")


def test_get_quantity_sold_route(client):
    r = client.get("/products/sold/PROD_1")
    todo_route(client, r, "/products/sold/PROD_1")
    todo_if_unauthorized(r)
    assert r.status_code == 200
    body = r.get_json()
    assert body.get("quantity") == 3, (
        f'expected {{"quantity": 3}}, got {body}')


def test_get_order_carries_its_lines_and_its_total(client):
    r = client.get("/orders/ORD_1")
    todo_route(client, r, "/orders/ORD_1")
    todo_if_unauthorized(r)
    assert r.status_code == 200
    body = r.get_json()
    order = body.get("order", body) if isinstance(body, dict) else body
    assert len(order.get("lines", [])) == 2, (
        f"ORD_1 holds two lines, got {order}")
    assert order.get("total") == 90.0, (
        f"ORD_1 is worth 2 x 40.0 + 1 x 10.0 = 90.0, got {order.get('total')}")


def test_get_an_unknown_order_is_404(client):
    r = client.get("/orders/ORD_NOPE")
    todo_route(client, r, "/orders/ORD_NOPE")
    todo_if_unauthorized(r)
    assert r.status_code == 404, (
        f"no order has this id, so the answer is 404, not {r.status_code}")


def test_get_customer_route(client):
    r = client.get("/orders/customers/CUST_1")
    todo_route(client, r, "/orders/customers/CUST_1")
    todo_if_unauthorized(r)
    assert r.status_code == 200
    body = r.get_json()
    customer = body.get("customer", body) if isinstance(body, dict) else body
    assert field(customer, "country") == "France"
    assert customer.get("total_spent") == 90.0, (
        "the refunded order does not count: CUST_1 spent 90.0, got "
        f"{customer.get('total_spent')}")
