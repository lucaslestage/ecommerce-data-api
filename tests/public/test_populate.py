"""Public tests for populate_database() (Question 6).

These tests build a small set of CSV files, load them with the student's
populate_database(), and check what actually landed in the database: every
table filled, the values loaded as they are, and the foreign keys still
matching afterwards.
"""

import contextlib
import io

import pytest

from db import create_database, populate_database
from helpers import check_it_ran, connect, table_exists

# A miniature, self-consistent dataset. Referenced tables come first: a Video
# points at a Creator, an Order at a Customer, a Video and a User, a line of
# an order at both the order and the product.
CSV_FILES = {
    "User": "username,password\nuser01,password01\n",
    "Creator": ("creator_id,name,followers,niche\n"
                "CRT_A,Alice,1000,Travel\n"
                "CRT_B,Bob,500,Cooking\n"),
    "Video": ("video_id,creator_id,views,likes\n"
              "VID_1,CRT_A,1000,100\n"
              "VID_2,CRT_B,50,1\n"),
    "Product": ("product_id,category,price,cost,stock\n"
                "PROD_1,Kitchen,40.0,20.0,100\n"
                "PROD_2,Beauty,10.0,4.0,5\n"),
    "Customer": "customer_id,country\nCUST_1,France\n",
    "Order": ("order_id,date,refunded,customer_id,video_id,username\n"
              "ORD_1,2025-01-10,0,CUST_1,VID_1,user01\n"
              "ORD_2,2025-01-11,0,CUST_1,VID_2,user01\n"),
    "Contains": ("order_id,product_id,quantity,final_price\n"
                 "ORD_1,PROD_1,2,40.0\n"
                 "ORD_1,PROD_2,1,10.0\n"),
    "Spend": "campaign_id,video_id,amount\nCAMP_1,VID_1,500.0\n",
}


@pytest.fixture
def empty_schema(tmp_path):
    """A database holding the student's schema and NO data.

    The seeded fixture cannot be reused here: populating a table that already
    holds the seed rows collides on the primary keys, which would fail the
    test for a reason that has nothing to do with populate_database().
    """
    conn = connect(str(tmp_path / "empty.db"))
    with contextlib.redirect_stdout(io.StringIO()):
        create_database(conn.cursor(), conn)
    conn.commit()
    return conn


@pytest.fixture
def populated(tmp_path, empty_schema):
    """Run the student's populate_database() on the CSV files above.

    Returns (connection, whether it reported success, what it printed).
    """
    conn = empty_schema
    files = {}
    for table, content in CSV_FILES.items():
        path = tmp_path / f"{table.lower()}.csv"
        path.write_text(content)
        # Only feed the tables the student actually created.
        if table_exists(conn, table):
            files[table] = str(path)

    if not files:
        pytest.skip("TODO: create_database")

    printed = io.StringIO()
    with contextlib.redirect_stdout(printed):
        done = populate_database(conn.cursor(), conn, files)
    yield conn, done, printed.getvalue()
    conn.close()


def test_populate_returns_true(populated):
    _, done, printed = populated
    check_it_ran(done, printed)


def test_every_table_is_filled(populated):
    conn, done, printed = populated
    check_it_ran(done, printed)
    empty = []
    for table in CSV_FILES:
        if not table_exists(conn, table):
            continue
        count = conn.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
        if count == 0:
            empty.append(table)
    assert not empty, (
        "populate_database() reported success but these tables are still "
        f"empty: {sorted(empty)}.")


def test_the_values_are_loaded_as_they_are(populated):
    conn, done, printed = populated
    check_it_ran(done, printed)

    creator = conn.execute(
        "SELECT * FROM Creator WHERE creator_id = 'CRT_A'").fetchone()
    assert creator is not None, "the creator CRT_A has not been loaded"
    assert creator["name"] == "Alice"
    assert creator["followers"] == 1000, (
        "the number of followers must be loaded as it is, "
        f"got {creator['followers']!r}")


def test_the_reserved_name_order_is_quoted(populated):
    """ORDER is a SQL keyword: the INSERT only works on a quoted name."""
    conn, done, printed = populated
    check_it_ran(done, printed)
    if not table_exists(conn, "Order"):
        pytest.skip("TODO: the Order table does not exist yet")
    count = conn.execute('SELECT COUNT(*) FROM "Order"').fetchone()[0]
    assert count == 2, (
        'the "Order" table is still empty: its name must be quoted in the '
        'INSERT, INSERT INTO "Order" (...)')


def test_the_foreign_keys_still_match(populated):
    """Every foreign key loaded must designate a row that exists."""
    conn, done, printed = populated
    check_it_ran(done, printed)
    checks = [
        ("Video", "creator_id", "Creator", "creator_id"),
        ("Order", "customer_id", "Customer", "customer_id"),
        ("Order", "video_id", "Video", "video_id"),
        ("Order", "username", "User", "username"),
        ("Contains", "order_id", "Order", "order_id"),
        ("Contains", "product_id", "Product", "product_id"),
        ("Spend", "video_id", "Video", "video_id"),
    ]
    problems = []
    for table, column, target, key in checks:
        if not (table_exists(conn, table) and table_exists(conn, target)):
            continue
        dangling = conn.execute(
            f'SELECT COUNT(*) FROM "{table}" WHERE {column} IS NOT NULL '
            f'AND {column} NOT IN (SELECT {key} FROM "{target}")'
        ).fetchone()[0]
        if dangling:
            problems.append(f"{dangling} row(s) of {table} have a {column} "
                            f"that matches no {target}.{key}")
    assert not problems, "\n".join(problems)
