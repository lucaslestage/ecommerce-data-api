"""Pytest fixtures for the TikTok Shop test suite.

Everything runs against a small deterministic database (see helpers.SEED)
loaded into a temporary SQLite file, so the assertions never depend on the
real scraped data.
"""

import os
import sqlite3
import contextlib

import pytest

import db
import utils
from db import create_database
from app import create_app

from helpers import (
    SEED, SEED_USER, OTHER_USER, TEST_SECRET, table_exists, connect,
)


# Hashing a password with bcrypt costs ~0.2 s at its default cost, and the
# seeded database is rebuilt for every single test: hashing here once, at the
# cheapest cost, turns minutes of waiting into seconds. It changes nothing for
# the code under test, since bcrypt reads the cost from the hash itself.
_HASHES = {}


def cheap_hash(password):
    import bcrypt

    if password not in _HASHES:
        _HASHES[password] = bcrypt.hashpw(password.encode(),
                                          bcrypt.gensalt(rounds=4))
    return _HASHES[password]


@pytest.fixture
def db_path(tmp_path, monkeypatch):
    """Create a temporary database, build the schema with the student's
    create_database(), seed the deterministic data, and make the whole
    application use it (by patching the configuration loader)."""
    path = str(tmp_path / "test.db")
    conn = connect(path)

    # Build the schema using the code under test (quietly).
    with contextlib.redirect_stdout(open(os.devnull, "w")):
        create_database(conn.cursor(), conn)

    # Two known users with a valid bcrypt hash of their password.
    if table_exists(conn, "User"):
        for username, password in (SEED_USER, OTHER_USER):
            try:
                conn.execute(
                    "INSERT INTO User (username, password) VALUES (?, ?)",
                    (username, cheap_hash(password)),
                )
            except sqlite3.Error:
                pass

    # Seed each table that actually exists (tolerant to missing tables).
    for table, (columns, rows) in SEED.items():
        if not table_exists(conn, table):
            continue
        placeholders = ", ".join(["?"] * len(columns))
        # The quotes make reserved table names such as "Order" usable.
        query = (f'INSERT INTO "{table}" ({", ".join(columns)}) '
                 f"VALUES ({placeholders})")
        try:
            conn.executemany(query, rows)
        except sqlite3.Error:
            pass

    conn.commit()
    conn.close()

    # get_db_connection() and the token helpers read the config at call time,
    # so patching load_config redirects the whole app to the temp database.
    monkeypatch.setattr(
        utils, "load_config",
        lambda: {"db": path, "SECRET_KEY": TEST_SECRET},
    )
    return path


@pytest.fixture
def connection(db_path):
    """A direct connection to the seeded test database (for white-box tests)."""
    conn = connect(db_path)
    yield conn
    conn.close()


@pytest.fixture
def client(db_path):
    """A Flask test client wired to the seeded test database."""
    return create_app().test_client()


@pytest.fixture
def token(db_path):
    """A valid bearer token for the seeded user (empty string if tokens are
    not implemented yet)."""
    try:
        return utils.generate_token(SEED_USER[0]) or ""
    except Exception:
        return ""


@pytest.fixture
def auth_header(token):
    return {"Authorization": f"Bearer {token}"}
