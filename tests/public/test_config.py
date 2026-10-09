"""Public tests for load_config() (Question 4).

The configuration file is a text file whose lines are of the form `key,value`.
Everything else in the application reads the database path and the JWT secret
through this function, so a bug here makes every later question look broken.
"""

import utils

from helpers import todo_if


def write_config(tmp_path, monkeypatch, content):
    """Point utils.CONFIG_FILE at a configuration file we control."""
    path = tmp_path / "config"
    path.write_text(content)
    monkeypatch.setattr(utils, "CONFIG_FILE", str(path))
    return path


def load(tmp_path, monkeypatch, content):
    write_config(tmp_path, monkeypatch, content)
    config = utils.load_config()
    # The skeleton returns an empty dictionary: not written yet.
    todo_if(not config, "load_config")
    return config


def test_load_config_returns_a_dictionary(tmp_path, monkeypatch):
    config = load(tmp_path, monkeypatch, "db,./data/test.db\n")
    assert isinstance(config, dict)


def test_load_config_reads_the_database_path(tmp_path, monkeypatch):
    config = load(tmp_path, monkeypatch, "db,./data/tiktok.db\n")
    assert config.get("db") == "./data/tiktok.db"


def test_load_config_reads_the_secret_key(tmp_path, monkeypatch):
    config = load(tmp_path, monkeypatch,
                  "db,./data/tiktok.db\nSECRET_KEY,a-very-secret-key\n")
    assert config.get("SECRET_KEY") == "a-very-secret-key"


def test_load_config_reads_every_line(tmp_path, monkeypatch):
    config = load(tmp_path, monkeypatch,
                  "db,./data/tiktok.db\n"
                  "SECRET_KEY,a-very-secret-key\n"
                  "other,something\n")
    assert set(config) >= {"db", "SECRET_KEY", "other"}, (
        f"expected the three keys of the file, got {sorted(config)}. "
        f"Every line of the configuration file must end up in the dictionary.")


def test_load_config_splits_the_key_from_the_value(tmp_path, monkeypatch):
    config = load(tmp_path, monkeypatch, "db,./data/tiktok.db\n")
    assert "db,./data/tiktok.db" not in config, (
        "the whole line was used as a key: split it on the comma into a key "
        "and a value.")
    assert config.get("db") == "./data/tiktok.db", (
        f"expected the value after the comma, got {config.get('db')!r}. "
        f"Watch out for the trailing newline.")
