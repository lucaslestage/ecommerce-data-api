"""Public tests for db.create_database().

Every other test of the suite builds its database with your
create_database(), so when the schema is wrong they all break at once without
telling you why. These tests look at the schema itself and name precisely what
is missing.
"""

import contextlib
import os

import pytest

from db import create_database

from helpers import connect, todo_if

# The tables of the model, and the columns each of them must hold.
EXPECTED = {
    "User": ["username", "password"],
    "Creator": ["creator_id", "name", "followers", "niche"],
    "Video": ["video_id", "creator_id", "views", "likes"],
    "Product": ["product_id", "category", "price", "cost", "stock"],
    "Customer": ["customer_id", "country"],
    "Order": ["order_id", "date", "refunded", "customer_id", "video_id",
              "username"],
    "Contains": ["order_id", "product_id", "quantity", "final_price"],
    "Spend": ["campaign_id", "video_id", "amount"],
}

# The primary key of each table, as PRAGMA table_info reports it.
EXPECTED_KEYS = {
    "User": ["username"],
    "Creator": ["creator_id"],
    "Video": ["video_id"],
    "Product": ["product_id"],
    "Customer": ["customer_id"],
    "Order": ["order_id"],
    "Contains": ["order_id", "product_id"],
    "Spend": ["campaign_id"],
}

# Every foreign key: (column, the table it must point at, lowercased).
EXPECTED_FOREIGN_KEYS = {
    "Video": [("creator_id", "creator")],
    "Order": [("customer_id", "customer"), ("video_id", "video"),
              ("username", "user")],
    "Contains": [("order_id", "order"), ("product_id", "product")],
    "Spend": [("video_id", "video")],
}

HINTS = {
    "Order": ('ORDER is a reserved SQL keyword: this table can only be '
              'created if its name is quoted, CREATE TABLE "Order"(...)'),
}


@pytest.fixture
def schema(tmp_path):
    """A database built by the student's create_database(), and nothing else."""
    conn = connect(str(tmp_path / "schema.db"))
    with contextlib.redirect_stdout(open(os.devnull, "w")):
        create_database(conn.cursor(), conn)
    conn.commit()
    yield conn
    conn.close()


def table_names(conn):
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
    return [row["name"] for row in rows]


def find_table(conn, wanted):
    """Table names are case insensitive in SQLite, so compare them lowered."""
    for name in table_names(conn):
        if name.lower() == wanted.lower():
            return name
    return None


def table_info(conn, table):
    return conn.execute(f'PRAGMA table_info("{table}")').fetchall()


def missing_tables(conn):
    return [wanted for wanted in EXPECTED if find_table(conn, wanted) is None]


def skip_when_not_started(conn):
    """Only the User table is given in the skeleton: as long as none of the
    others exists, create_database() has simply not been done yet."""
    todo_if(len(missing_tables(conn)) >= len(EXPECTED) - 1, "create_database")


def test_every_table_is_created(schema):
    skip_when_not_started(schema)

    missing = missing_tables(schema)
    hints = "".join(f"\n  - {name}: {HINTS[name]}"
                    for name in missing if name in HINTS)
    assert not missing, (
        f"missing table(s): {missing}"
        f"\ntables found: {sorted(table_names(schema))}{hints}")


def test_every_table_has_its_columns(schema):
    skip_when_not_started(schema)

    problems = []
    for table, expected_columns in EXPECTED.items():
        name = find_table(schema, table)
        if name is None:
            continue  # already reported by the test above
        columns = [row["name"] for row in table_info(schema, name)]
        missing = [c for c in expected_columns if c not in columns]
        if missing:
            problems.append(f"  {name}: missing {missing}, found {columns}")

    assert not problems, (
        "some tables do not hold the columns of the model:\n"
        + "\n".join(problems)
        + "\nUse the names of the ER diagram; a foreign key is named after the"
          " table it points at, followed by _id.")


def test_primary_keys_are_declared(schema):
    skip_when_not_started(schema)

    problems = []
    for table, expected_key in EXPECTED_KEYS.items():
        name = find_table(schema, table)
        if name is None:
            continue
        # In PRAGMA table_info, `pk` is 0 for a normal column, and the rank of
        # the column inside the primary key otherwise (1, 2, ...).
        key = [row["name"] for row in sorted(table_info(schema, name),
                                             key=lambda row: row["pk"])
               if row["pk"]]
        if sorted(key) != sorted(expected_key):
            problems.append(f"  {name}: primary key is {key or 'not declared'}"
                            f", expected {expected_key}")

    assert not problems, (
        "wrong primary key(s):\n" + "\n".join(problems)
        + "\nThe table that records which products an order contains is"
          " identified by the pair of the two keys it links,"
          " e.g. PRIMARY KEY (order_id, product_id).")


def test_the_foreign_keys_are_declared(schema):
    """A foreign key column is not enough on its own: it must be declared,
    so that the schema itself records where it points."""
    skip_when_not_started(schema)

    problems = []
    for table, expected in EXPECTED_FOREIGN_KEYS.items():
        name = find_table(schema, table)
        if name is None:
            continue
        declared = {row["from"]: row["table"].lower()
                    for row in schema.execute(
                        f'PRAGMA foreign_key_list("{name}")')}
        for column, target in expected:
            if declared.get(column) != target:
                problems.append(
                    f"  {name}.{column} -> {declared.get(column) or 'nothing'}"
                    f", expected -> {target}")

    assert not problems, (
        "wrong or missing foreign key(s):\n" + "\n".join(problems)
        + "\nDeclare them with REFERENCES, e.g. "
          "creator_id TEXT REFERENCES Creator(creator_id).")


def test_the_money_rules_are_enforced(schema):
    """Two rules of the model are the database's job, not the code's:
    the brand never sells at a loss, and the stock never goes negative."""
    skip_when_not_started(schema)

    name = find_table(schema, "Product")
    if name is None:
        pytest.skip("TODO: the Product table does not exist yet")

    problems = []
    for description, row in (
            ("sell at a loss (price below cost)",
             ("PROD_X", "Test", 5.0, 10.0, 1)),
            ("a negative stock",
             ("PROD_Y", "Test", 10.0, 5.0, -1))):
        try:
            schema.execute(
                f'INSERT INTO "{name}" '
                "(product_id, category, price, cost, stock) "
                "VALUES (?, ?, ?, ?, ?)", row)
            problems.append(f"  the database accepted {description}")
        except Exception:
            pass          # refused, which is what we want
        finally:
            schema.execute(f'DELETE FROM "{name}" WHERE product_id = ?',
                           (row[0],))

    assert not problems, (
        "the database must refuse these rows:\n" + "\n".join(problems)
        + "\nAdd the rules to the CREATE TABLE, e.g. CHECK (price >= cost).")
