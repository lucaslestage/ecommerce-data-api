"""Public tests for the db/ layer: creators, videos, products, customers,
orders and users (Question 13).

Every function of db/ takes the cursor as its LAST parameter and returns
plain Python: a dictionary for one row, a list of dictionaries for several.

Every test runs against the small deterministic dataset of helpers.SEED:
    Creator  CRT_A (Alice), CRT_B (Bob, never sold anything), CRT_C (Cleo)
    Video    VID_1, VID_2 (CRT_A), VID_3 (CRT_B, no order), VID_4 (CRT_C)
    Product  PROD_1, PROD_2 (stock 5), PROD_3 (stock 0), PROD_4 (never sold)
    Customer CUST_1, CUST_2, CUST_3 (never ordered)
    Order    ORD_1 (90.0), ORD_2 (100.0), ORD_3 (refunded)
"""

import pytest

import db.creators
import db.customers
import db.orders
import db.products
import db.users
import db.videos

from helpers import call_or_todo, field, table_exists, todo_if


@pytest.fixture(autouse=True)
def _needs_the_schema(connection):
    """Every test below reads the seeded rows. As long as create_database()
    has not built the tables there is nothing to read, which is TODO (the
    work is not done yet), not a failure."""
    if not table_exists(connection, "Creator"):
        todo_if(True, "create_database")


# ---------------------------------------------------------------------------
# Creators
# ---------------------------------------------------------------------------
def test_get_creator(connection):
    creator = call_or_todo(db.creators.get_creator, "CRT_A", connection.cursor())
    todo_if(creator is None, "get_creator")
    assert creator, "CRT_A is in the database, get_creator() found nothing"
    assert field(creator, "name") == "Alice"
    assert field(creator, "followers") == 1000
    assert field(creator, "niche") == "Travel"


def test_get_creator_unknown_returns_an_empty_dict(connection):
    creator = call_or_todo(db.creators.get_creator, "CRT_NOPE", connection.cursor())
    todo_if(creator is None, "get_creator")
    assert creator == {}, (
        "an unknown creator must give an empty dictionary, not "
        f"{creator!r}. None is reserved for a query that failed.")


def test_get_creators(connection):
    creators = call_or_todo(db.creators.get_creators, connection.cursor())
    todo_if(creators is None, "get_creators")
    assert len(creators) == 3, f"expected the 3 seeded creators, got {creators}"
    assert {field(c, "creator_id") for c in creators} == {"CRT_A", "CRT_B", "CRT_C"}


def test_insert_creator(connection):
    done = call_or_todo(db.creators.insert_creator,
                        {"creator_id": "CRT_NEW", "name": "Dana",
                         "followers": 42, "niche": "Books"},
                        connection.cursor())
    todo_if(done is None, "insert_creator")
    assert done is True, f"insert_creator() returned {done!r} instead of True"
    row = connection.execute(
        "SELECT name, followers FROM Creator WHERE creator_id = 'CRT_NEW'").fetchone()
    assert row is not None, "insert_creator() returned True but wrote nothing"
    assert row["name"] == "Dana" and row["followers"] == 42


def test_insert_creator_refuses_a_duplicate(connection):
    done = call_or_todo(db.creators.insert_creator,
                        {"creator_id": "CRT_A", "name": "Clone",
                         "followers": 1, "niche": "Travel"},
                        connection.cursor())
    todo_if(done is None, "insert_creator")
    assert done is False, (
        "CRT_A already exists: the primary key forbids a second one, so "
        f"insert_creator() must return False, not {done!r}")


def test_update_creator_followers(connection):
    done = call_or_todo(db.creators.update_creator_followers, "CRT_A", 9999,
                        connection.cursor())
    todo_if(done is None, "update_creator_followers")
    assert done is True
    value = connection.execute(
        "SELECT followers FROM Creator WHERE creator_id = 'CRT_A'").fetchone()[0]
    assert value == 9999, f"the followers were not updated, still {value}"


def test_get_creator_videos(connection):
    videos = call_or_todo(db.creators.get_creator_videos, "CRT_A",
                          connection.cursor())
    todo_if(videos is None, "get_creator_videos")
    assert [field(v, "video_id") for v in videos] == ["VID_1", "VID_2"], (
        "CRT_A made VID_1 (1000 views) and VID_2 (200 views), the most "
        f"viewed first; got {[field(v, 'video_id') for v in videos]}")


def test_get_creators_without_sales(connection):
    creators = call_or_todo(db.creators.get_creators_without_sales,
                            connection.cursor())
    todo_if(creators is None, "get_creators_without_sales")
    ids = {field(c, "creator_id") for c in creators}
    assert ids == {"CRT_B"}, (
        "only CRT_B has no order coming from any of their videos; "
        f"got {sorted(ids)}")


# ---------------------------------------------------------------------------
# Videos
# ---------------------------------------------------------------------------
def test_get_video(connection):
    video = call_or_todo(db.videos.get_video, "VID_1", connection.cursor())
    todo_if(video is None, "get_video")
    assert video, "VID_1 is in the database, get_video() found nothing"
    assert field(video, "creator_id") == "CRT_A"
    assert field(video, "views") == 1000
    assert field(video, "likes") == 100


def test_get_video_unknown_returns_an_empty_dict(connection):
    video = call_or_todo(db.videos.get_video, "VID_NOPE", connection.cursor())
    todo_if(video is None, "get_video")
    assert video == {}, (
        f"an unknown video must give an empty dictionary, not {video!r}")


def test_get_videos(connection):
    videos = call_or_todo(db.videos.get_videos, connection.cursor())
    todo_if(videos is None, "get_videos")
    assert len(videos) == 4, f"expected the 4 seeded videos, got {len(videos)}"


def test_insert_video(connection):
    done = call_or_todo(db.videos.insert_video,
                        {"video_id": "VID_NEW", "creator_id": "CRT_A",
                         "views": 7, "likes": 3}, connection.cursor())
    todo_if(done is None, "insert_video")
    row = connection.execute(
        "SELECT creator_id, views, likes FROM Video "
        "WHERE video_id = 'VID_NEW'").fetchone()
    assert row is not None, "insert_video() wrote nothing"
    assert (row["creator_id"], row["views"], row["likes"]) == ("CRT_A", 7, 3)


def test_get_video_orders_count(connection):
    count = call_or_todo(db.videos.get_video_orders_count, "VID_1",
                         connection.cursor())
    todo_if(count is None, "get_video_orders_count")
    assert count == 2, (
        f"ORD_1 and ORD_3 both come from VID_1, so the count is 2, not {count}")


def test_get_video_orders_count_without_any_order(connection):
    cursor = connection.cursor()
    todo_if(call_or_todo(db.videos.get_video_orders_count, "VID_1", cursor)
            is None, "get_video_orders_count")
    count = call_or_todo(db.videos.get_video_orders_count, "VID_3", cursor)
    assert count == 0, f"VID_3 triggered no order, expected 0, got {count}"


def test_get_best_videos_puts_the_money_losing_video_last(connection):
    """Net revenue = what the video sold (refunds excluded) minus what was
    spent promoting it. VID_1 sold 90.0 and cost 500.0, so it is the worst."""
    videos = call_or_todo(db.videos.get_best_videos, 4, connection.cursor())
    todo_if(videos is None, "get_best_videos")
    assert len(videos) == 4, f"asked for 4 videos, got {len(videos)}"
    assert field(videos[-1], "video_id") == "VID_1", (
        "VID_1 sold 90.0 and cost 500.0 in promotion: its net revenue is the "
        f"lowest, so it comes last. Got {[field(v, 'video_id') for v in videos]}")


def test_get_best_videos_returns_only_n_videos(connection):
    videos = call_or_todo(db.videos.get_best_videos, 2, connection.cursor())
    todo_if(videos is None, "get_best_videos")
    assert len(videos) == 2, f"asked for 2 videos, got {len(videos)}"


# ---------------------------------------------------------------------------
# Products
# ---------------------------------------------------------------------------
def test_get_product(connection):
    product = call_or_todo(db.products.get_product, "PROD_1", connection.cursor())
    todo_if(product is None, "get_product")
    assert product, "PROD_1 is in the database, get_product() found nothing"
    assert field(product, "category") == "Kitchen"
    assert field(product, "price") == 40.0
    assert field(product, "stock") == 100


def test_get_product_unknown_returns_an_empty_dict(connection):
    product = call_or_todo(db.products.get_product, "PROD_NOPE",
                           connection.cursor())
    todo_if(product is None, "get_product")
    assert product == {}, (
        f"an unknown product must give an empty dictionary, not {product!r}")


def test_get_products(connection):
    products = call_or_todo(db.products.get_products, connection.cursor())
    todo_if(products is None, "get_products")
    assert len(products) == 4, f"expected the 4 seeded products, got {len(products)}"


def test_get_products_by_category(connection):
    products = call_or_todo(db.products.get_products_by_category, "Kitchen",
                            connection.cursor())
    todo_if(products is None, "get_products_by_category")
    assert [field(p, "product_id") for p in products] == ["PROD_1"], (
        "only PROD_1 is in the Kitchen category, got "
        f"{[field(p, 'product_id') for p in products]}")


def test_insert_product(connection):
    done = call_or_todo(db.products.insert_product,
                        {"product_id": "PROD_NEW", "category": "Books",
                         "price": 15.0, "cost": 5.0, "stock": 3},
                        connection.cursor())
    todo_if(done is None, "insert_product")
    row = connection.execute(
        "SELECT category, stock FROM Product "
        "WHERE product_id = 'PROD_NEW'").fetchone()
    assert row is not None, "insert_product() wrote nothing"
    assert (row["category"], row["stock"]) == ("Books", 3)


def test_update_product_stock(connection):
    call_or_todo(db.products.update_product_stock, "PROD_1", 7,
                 connection.cursor())
    value = connection.execute(
        "SELECT stock FROM Product WHERE product_id = 'PROD_1'").fetchone()[0]
    todo_if(value == 100, "update_product_stock")
    assert value == 7, f"the stock should be 7, found {value}"


def test_decrease_product_stock(connection):
    done = call_or_todo(db.products.decrease_product_stock, "PROD_1", 10,
                        connection.cursor())
    todo_if(done is None, "decrease_product_stock")
    assert done is True
    value = connection.execute(
        "SELECT stock FROM Product WHERE product_id = 'PROD_1'").fetchone()[0]
    assert value == 90, f"100 - 10 = 90, found {value}"


def test_decrease_product_stock_refuses_to_go_negative(connection):
    """PROD_3 has a stock of 0: taking one out of it must be refused, and
    must leave the stock alone."""
    done = call_or_todo(db.products.decrease_product_stock, "PROD_3", 1,
                        connection.cursor())
    todo_if(done is None, "decrease_product_stock")
    assert done is False, (
        "PROD_3 has no stock left, so the decrease must be refused and "
        f"return False, not {done!r}")
    value = connection.execute(
        "SELECT stock FROM Product WHERE product_id = 'PROD_3'").fetchone()[0]
    assert value == 0, f"the stock must stay at 0, found {value}"


def test_get_low_stock_products(connection):
    products = call_or_todo(db.products.get_low_stock_products, 10,
                            connection.cursor())
    todo_if(products is None, "get_low_stock_products")
    ids = [field(p, "product_id") for p in products]
    assert ids == ["PROD_3", "PROD_2"], (
        "below 10 there are PROD_3 (0) and PROD_2 (5), the emptiest first; "
        f"got {ids}")


def test_get_quantity_sold(connection):
    quantity = call_or_todo(db.products.get_quantity_sold, "PROD_1",
                            connection.cursor())
    todo_if(quantity is None, "get_quantity_sold")
    assert quantity == 3, (
        f"PROD_1 was ordered 2 times then 1 time, so 3 in all, not {quantity}")


def test_get_quantity_sold_of_a_product_nobody_ordered(connection):
    cursor = connection.cursor()
    # PROD_1 was sold: a None here means the function is not written yet.
    # Past that point, None is a wrong answer, not work left to do.
    todo_if(call_or_todo(db.products.get_quantity_sold, "PROD_1", cursor)
            is None, "get_quantity_sold")
    quantity = call_or_todo(db.products.get_quantity_sold, "PROD_4", cursor)
    assert quantity == 0, (
        "PROD_4 was never ordered: the answer is 0 and not None, which is "
        f"what SUM() gives on no row. Got {quantity}")


# ---------------------------------------------------------------------------
# Customers
# ---------------------------------------------------------------------------
def test_get_customer(connection):
    customer = call_or_todo(db.customers.get_customer, "CUST_1",
                            connection.cursor())
    todo_if(customer is None, "get_customer")
    assert customer, "CUST_1 is in the database, get_customer() found nothing"
    assert field(customer, "country") == "France"


def test_get_customer_unknown_returns_an_empty_dict(connection):
    customer = call_or_todo(db.customers.get_customer, "CUST_NOPE",
                            connection.cursor())
    todo_if(customer is None, "get_customer")
    assert customer == {}, (
        f"an unknown customer must give an empty dictionary, not {customer!r}")


def test_get_customers(connection):
    customers = call_or_todo(db.customers.get_customers, connection.cursor())
    todo_if(customers is None, "get_customers")
    assert len(customers) == 3, f"expected the 3 seeded customers, got {len(customers)}"


def test_insert_customer(connection):
    done = call_or_todo(db.customers.insert_customer,
                        {"customer_id": "CUST_NEW", "country": "Japan"},
                        connection.cursor())
    todo_if(done is None, "insert_customer")
    row = connection.execute(
        "SELECT country FROM Customer WHERE customer_id = 'CUST_NEW'").fetchone()
    assert row is not None, "insert_customer() wrote nothing"
    assert row["country"] == "Japan"


def test_update_customer_country(connection):
    call_or_todo(db.customers.update_customer_country, "CUST_1", "Brazil",
                 connection.cursor())
    value = connection.execute(
        "SELECT country FROM Customer WHERE customer_id = 'CUST_1'").fetchone()[0]
    todo_if(value == "France", "update_customer_country")
    assert value == "Brazil", f"the country should be Brazil, found {value}"


def test_get_products_bought_by_customer(connection):
    """CUST_1 bought PROD_1 and PROD_2 in ORD_1, and PROD_1 again in ORD_3:
    PROD_1 is returned once."""
    products = call_or_todo(db.customers.get_products_bought_by_customer,
                            "CUST_1", connection.cursor())
    todo_if(products is None, "get_products_bought_by_customer")
    ids = sorted(field(p, "product_id") for p in products)
    assert ids == ["PROD_1", "PROD_2"], (
        f"CUST_1 bought PROD_1 and PROD_2, each one once; got {ids}")


def test_get_total_spent_by_customer_ignores_refunds(connection):
    """CUST_1 placed ORD_1 (90.0) and ORD_3 (refunded): only 90.0 counts."""
    total = call_or_todo(db.customers.get_total_spent_by_customer, "CUST_1",
                         connection.cursor())
    todo_if(total is None, "get_total_spent_by_customer")
    assert total == 90.0, (
        "ORD_3 was refunded, so it must not be counted: the total is 90.0, "
        f"not {total}")


def test_get_total_spent_by_a_customer_who_never_ordered(connection):
    cursor = connection.cursor()
    todo_if(call_or_todo(db.customers.get_total_spent_by_customer, "CUST_1",
                         cursor) is None, "get_total_spent_by_customer")
    total = call_or_todo(db.customers.get_total_spent_by_customer, "CUST_3",
                         cursor)
    assert total == 0, f"CUST_3 never ordered, expected 0, got {total}"


# ---------------------------------------------------------------------------
# Orders
# ---------------------------------------------------------------------------
def test_get_order(connection):
    order = call_or_todo(db.orders.get_order, "ORD_1", connection.cursor())
    todo_if(order is None, "get_order")
    assert order, "ORD_1 is in the database, get_order() found nothing"
    assert field(order, "customer_id") == "CUST_1"
    assert field(order, "video_id") == "VID_1"
    assert field(order, "username") == "tester"


def test_get_order_unknown_returns_an_empty_dict(connection):
    order = call_or_todo(db.orders.get_order, "ORD_NOPE", connection.cursor())
    todo_if(order is None, "get_order")
    assert order == {}, (
        f"an unknown order must give an empty dictionary, not {order!r}")


def test_get_orders(connection):
    orders = call_or_todo(db.orders.get_orders, connection.cursor())
    todo_if(orders is None, "get_orders")
    assert len(orders) == 3, f"expected the 3 seeded orders, got {len(orders)}"


def test_get_orders_by_customer(connection):
    orders = call_or_todo(db.orders.get_orders_by_customer, "CUST_1",
                          connection.cursor())
    todo_if(orders is None, "get_orders_by_customer")
    assert {field(o, "order_id") for o in orders} == {"ORD_1", "ORD_3"}, (
        "CUST_1 placed ORD_1 and ORD_3, got "
        f"{[field(o, 'order_id') for o in orders]}")


def test_insert_order(connection):
    done = call_or_todo(db.orders.insert_order,
                        {"order_id": "ORD_NEW", "date": "2025-04-01",
                         "refunded": 0, "customer_id": "CUST_1",
                         "video_id": "VID_1", "username": "tester"},
                        connection.cursor())
    todo_if(done is None, "insert_order")
    row = connection.execute(
        'SELECT customer_id FROM "Order" WHERE order_id = ?',
        ("ORD_NEW",)).fetchone()
    assert row is not None, "insert_order() wrote nothing"
    assert row["customer_id"] == "CUST_1"


def test_insert_order_line(connection):
    done = call_or_todo(db.orders.insert_order_line,
                        {"order_id": "ORD_2", "product_id": "PROD_4",
                         "quantity": 3, "final_price": 25.0},
                        connection.cursor())
    todo_if(done is None, "insert_order_line")
    row = connection.execute(
        "SELECT quantity, final_price FROM Contains "
        "WHERE order_id = 'ORD_2' AND product_id = 'PROD_4'").fetchone()
    assert row is not None, "insert_order_line() wrote nothing"
    assert (row["quantity"], row["final_price"]) == (3, 25.0)


def test_get_order_lines(connection):
    lines = call_or_todo(db.orders.get_order_lines, "ORD_1", connection.cursor())
    todo_if(lines is None, "get_order_lines")
    assert len(lines) == 2, f"ORD_1 holds two lines, got {len(lines)}"
    assert {field(l, "product_id") for l in lines} == {"PROD_1", "PROD_2"}
    assert {field(l, "category") for l in lines} == {"Kitchen", "Beauty"}, (
        "each line must also carry the category of its product, which is "
        "read in the Product table")


def test_get_order_total(connection):
    total = call_or_todo(db.orders.get_order_total, "ORD_1", connection.cursor())
    todo_if(total is None, "get_order_total")
    assert total == 90.0, f"ORD_1 is 2 x 40.0 + 1 x 10.0 = 90.0, not {total}"


def test_get_order_total_of_an_unknown_order(connection):
    cursor = connection.cursor()
    todo_if(call_or_todo(db.orders.get_order_total, "ORD_1", cursor) is None,
            "get_order_total")
    total = call_or_todo(db.orders.get_order_total, "ORD_NOPE", cursor)
    assert total == 0, (
        "an order that does not exist is worth 0, not None: use COALESCE "
        f"around the SUM. Got {total}")


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------
def test_get_user(connection):
    user = call_or_todo(db.users.get_user, "tester", connection.cursor())
    todo_if(user is None, "get_user")
    assert user, "the user 'tester' is seeded, get_user() found nothing"
    assert field(user, "username") == "tester"


def test_get_users(connection):
    users = call_or_todo(db.users.get_users, connection.cursor())
    todo_if(users is None, "get_users")
    assert len(users) == 2, (
        f"two users are seeded (tester and other), got {len(users)}")


def test_get_orders_handled_by_user(connection):
    orders = call_or_todo(db.users.get_orders_handled_by_user, "tester",
                          connection.cursor())
    todo_if(orders is None, "get_orders_handled_by_user")
    assert {field(o, "order_id") for o in orders} == {"ORD_1", "ORD_3"}, (
        "'tester' prepared ORD_1 and ORD_3, got "
        f"{[field(o, 'order_id') for o in orders]}")


def test_update_password_changes_only_that_user(connection):
    before = connection.execute(
        "SELECT password FROM User WHERE username = 'other'").fetchone()[0]
    done = call_or_todo(db.users.update_password, "tester", "brand-new",
                        connection.cursor())
    todo_if(done is None, "update_password")
    after = connection.execute(
        "SELECT password FROM User WHERE username = 'other'").fetchone()[0]
    assert after == before, (
        "updating the password of 'tester' must leave 'other' alone: "
        "the UPDATE needs a WHERE clause")
