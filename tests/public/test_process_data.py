"""Public tests for data/process_data.py (Question 3).

The functions of the student read the raw file and write one file per entity
into data/. Each test runs them inside a temporary working directory holding
a tiny raw sample, then reads the files they wrote.

The sample holds 5 lines:
    ORD_1 (two products), ORD_2 (refunded), ORD_3 (the same line twice)
    CRT_A (Alice, twice, with two different niches), CRT_B (Bob)
"""

import csv
import os
import shutil

from helpers import FIXTURES_DIR, load_process_data, todo_if

RAW = "data/raw/tiktokshop.csv"


def setup_raw(tmp_path, monkeypatch):
    """Prepare a temporary working directory holding data/raw/<the sample>."""
    os.makedirs(tmp_path / "data" / "raw")
    shutil.copy(os.path.join(FIXTURES_DIR, "raw_sample", "tiktokshop.csv"),
                tmp_path / "data" / "raw" / "tiktokshop.csv")
    monkeypatch.chdir(tmp_path)


def run(module, name):
    """Call one process_*() function, whatever the student called it.

    Both the singular and the plural are accepted (process_video or
    process_videos), because only the generated files are part of the
    contract.
    """
    for candidate in (name, name + "s"):
        function = getattr(module, candidate, None)
        if function is not None:
            try:
                function(RAW)
            except NotImplementedError:
                todo_if(True, candidate)
            return
    todo_if(True, name)


def read(path):
    todo_if(not os.path.exists(path), f"{path} has not been written")
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def column(rows, name):
    assert name in rows[0], (
        f"expected a column {name!r}, found {list(rows[0])}. Use the names of "
        f"the ER diagram: the raw file does not use them.")
    return [row[name] for row in rows]


def test_process_creators(tmp_path, monkeypatch):
    """A creator is written once, even though it appears on many lines."""
    module = load_process_data()
    setup_raw(tmp_path, monkeypatch)
    run(module, "process_creator")

    creators = read("data/creator.csv")
    assert len(creators) == 2, (
        "the sample names two creators, Alice and Bob, so creator.csv holds "
        f"two lines, not {len(creators)}")
    assert sorted(column(creators, "creator_id")) == ["CRT_A", "CRT_B"]
    assert sorted(column(creators, "name")) == ["Alice", "Bob"]


def test_process_videos(tmp_path, monkeypatch):
    module = load_process_data()
    setup_raw(tmp_path, monkeypatch)
    run(module, "process_video")

    videos = read("data/video.csv")
    assert len(videos) == 3, (
        f"the sample holds three videos, got {len(videos)} lines")
    assert sorted(column(videos, "video_id")) == ["VID_1", "VID_2", "VID_3"]
    # views and likes describe the video, the creator_id links it to its author
    assert set(column(videos, "creator_id")) == {"CRT_A", "CRT_B"}
    assert "views" in videos[0], (
        f"expected a column 'views', found {list(videos[0])}")


def test_process_products(tmp_path, monkeypatch):
    module = load_process_data()
    setup_raw(tmp_path, monkeypatch)
    run(module, "process_product")

    products = read("data/product.csv")
    assert len(products) == 3, (
        f"the sample holds three products, got {len(products)} lines")
    for name in ("product_id", "category", "price", "cost", "stock"):
        column(products, name)


def test_process_customers(tmp_path, monkeypatch):
    module = load_process_data()
    setup_raw(tmp_path, monkeypatch)
    run(module, "process_customer")

    customers = read("data/customer.csv")
    assert len(customers) == 2, (
        f"the sample holds two customers, got {len(customers)} lines")
    assert sorted(column(customers, "country")) == ["France", "Mexico"]


def test_process_orders(tmp_path, monkeypatch):
    """One line per order, and the refund becomes a 0/1 column."""
    module = load_process_data()
    setup_raw(tmp_path, monkeypatch)
    run(module, "process_order")

    orders = read("data/order.csv")
    assert len(orders) == 3, (
        "the sample holds three orders (ORD_1 is written on two lines), so "
        f"order.csv holds three lines, not {len(orders)}")

    refunded = dict(zip(column(orders, "order_id"),
                        column(orders, "refunded")))
    assert str(refunded["ORD_2"]) in ("1", "True"), (
        "ORD_2 got 12.5 back, so it is refunded")
    assert str(refunded["ORD_1"]) in ("0", "False"), (
        "ORD_1 was never refunded")

    usernames = column(orders, "username")
    assert all(usernames), (
        "every order is prepared by one employee: the username column must "
        "name one of the users you created")


def test_process_contains(tmp_path, monkeypatch):
    """One line per product of an order, with the quantity fixed."""
    module = load_process_data()
    setup_raw(tmp_path, monkeypatch)
    run(module, "process_contain")

    lines = read("data/contains.csv")
    quantity = {(row["order_id"], row["product_id"]): row["quantity"]
                for row in lines}
    expected = {("ORD_1", "PROD_1"), ("ORD_1", "PROD_2"),
                ("ORD_2", "PROD_1"), ("ORD_3", "PROD_3")}
    missing = expected - set(quantity)
    assert not missing, (
        f"one line is expected per product of an order; missing "
        f"{sorted(missing)} in {sorted(quantity)}")
    assert int(float(quantity[("ORD_1", "PROD_1")])) == 1, (
        "a quantity of 0 in the raw file means one item: add 1 to every "
        "quantity")
    assert int(float(quantity[("ORD_3", "PROD_3")])) == 3, (
        "the raw quantity of ORD_3 is 2, so three items were sold")
    column(lines, "final_price")


def test_process_spends(tmp_path, monkeypatch):
    module = load_process_data()
    setup_raw(tmp_path, monkeypatch)
    run(module, "process_spend")

    spends = read("data/spend.csv")
    assert len(spends) == 3, (
        "the sample holds three campaigns (CAMP_1 pays for the two lines of "
        f"ORD_1), got {len(spends)} lines")
    assert sorted(column(spends, "campaign_id")) == ["CAMP_1", "CAMP_2",
                                                     "CAMP_3"]
    column(spends, "amount")


def test_process_users(tmp_path, monkeypatch):
    """The employees are not in the raw file: they must be created."""
    module = load_process_data()
    setup_raw(tmp_path, monkeypatch)
    run(module, "process_user")

    users = read("data/user.csv")
    assert len(users) >= 1, "user.csv must name at least one employee"
    for name in ("username", "password"):
        column(users, name)
