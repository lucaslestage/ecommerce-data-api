"""Public tests for init_database() (Question 7).

init_database() is the function create_db.py calls: it must build the schema
AND load the data, in an order the foreign keys allow. These tests run it in a
temporary directory, against entity files we control, so they never depend on
the CSV files the student generated.
"""

import contextlib
import io

import pytest

import db
import utils
from helpers import connect, table_exists, todo_if

ENTITY_FILES = {
    "user": "username,password\nuser01,password01\n",
    "creator": ("creator_id,name,followers,niche\n"
                "CRT_A,Alice,1000,Travel\n"),
    "video": "video_id,creator_id,views,likes\nVID_1,CRT_A,1000,100\n",
    "product": ("product_id,category,price,cost,stock\n"
                "PROD_1,Kitchen,40.0,20.0,100\n"),
    "customer": "customer_id,country\nCUST_1,France\n",
    "order": ("order_id,date,refunded,customer_id,video_id,username\n"
              "ORD_1,2025-01-10,0,CUST_1,VID_1,user01\n"),
    "contains": ("order_id,product_id,quantity,final_price\n"
                 "ORD_1,PROD_1,2,40.0\n"),
    "spend": "campaign_id,video_id,amount\nCAMP_1,VID_1,500.0\n",
}

TABLES = ["User", "Creator", "Video", "Product", "Customer", "Order",
          "Contains", "Spend"]


@pytest.fixture
def initialised(tmp_path, monkeypatch):
    """Run the student's init_database() in a temporary working directory.

    init_database() reads its file names relative to the current directory, so
    we give it a data/ directory holding the entity files above.
    """
    (tmp_path / "data").mkdir()
    for name, content in ENTITY_FILES.items():
        (tmp_path / "data" / f"{name}.csv").write_text(content)

    database = tmp_path / "data" / "test.db"
    monkeypatch.setattr(
        utils, "load_config",
        lambda: {"db": str(database), "SECRET_KEY": "x" * 42},
    )
    monkeypatch.chdir(tmp_path)

    printed = io.StringIO()
    with contextlib.redirect_stdout(printed):
        try:
            db.init_database()
        except Exception as error:                      # noqa: BLE001
            pytest.fail(f"init_database() raised {error!r}. It printed:\n"
                        f"{printed.getvalue().strip()}")

    todo_if(not database.exists(), "init_database")
    conn = connect(str(database))
    yield conn, printed.getvalue()
    conn.close()


def test_init_database_creates_the_schema(initialised):
    conn, printed = initialised
    missing = [name for name in TABLES if not table_exists(conn, name)]
    todo_if(len(missing) >= len(TABLES) - 1, "create_database")
    assert not missing, (
        f"init_database() ran but these tables do not exist: {sorted(missing)}")


def test_init_database_loads_every_file(initialised):
    """Creating the tables is not enough: init_database() must populate them."""
    conn, printed = initialised
    present = [name for name in TABLES if table_exists(conn, name)]
    todo_if(len(present) <= 1, "create_database")

    counts = {name: conn.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0]
              for name in present}
    todo_if(all(count == 0 for count in counts.values()),
            "the call to populate_database() in init_database()")
    empty = [name for name, count in counts.items() if count == 0]
    assert not empty, (
        f"these tables were created but not loaded: {sorted(empty)}. "
        f"init_database() must pass every entity file to populate_database(). "
        f"It printed:\n{printed.strip()}")


def test_init_database_loads_in_a_valid_order(initialised):
    """A referenced row must be there before the row pointing at it.

    Loading Video before Creator either fails outright or leaves foreign keys
    pointing at nothing; both show up here.
    """
    conn, printed = initialised
    checks = [
        ("Video", "creator_id", "Creator", "creator_id"),
        ("Order", "customer_id", "Customer", "customer_id"),
        ("Order", "video_id", "Video", "video_id"),
        ("Order", "username", "User", "username"),
        ("Contains", "order_id", "Order", "order_id"),
        ("Contains", "product_id", "Product", "product_id"),
        ("Spend", "video_id", "Video", "video_id"),
    ]
    usable = [c for c in checks
              if table_exists(conn, c[0]) and table_exists(conn, c[2])]
    todo_if(not usable, "create_database")
    todo_if(all(conn.execute(f'SELECT COUNT(*) FROM "{c[0]}"').fetchone()[0] == 0
                for c in usable), "the call to populate_database()")

    problems = []
    for table, column, target, key in usable:
        dangling = conn.execute(
            f'SELECT COUNT(*) FROM "{table}" WHERE {column} IS NOT NULL '
            f'AND {column} NOT IN (SELECT {key} FROM "{target}")'
        ).fetchone()[0]
        if dangling:
            problems.append(
                f"{dangling} row(s) of {table} point at a {target} that is "
                f"not there: load {target} before {table}.")
    assert not problems, "\n".join(problems)
