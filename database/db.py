import sqlite3
from datetime import date, timedelta

from flask import g

DATABASE = "expense_tracker.db"


def get_db():
    """Return a SQLite connection for the current app context, reused
    across calls within the same request via Flask's `g`."""
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(e=None):
    """Close the connection stored on `g`, if any."""
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """Create all tables if they don't already exist."""
    db = get_db()
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            name          TEXT NOT NULL,
            email         TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at    TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS expenses (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            category    TEXT NOT NULL,
            amount      REAL NOT NULL,
            description TEXT,
            date        TEXT NOT NULL,
            created_at  TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users (id)
        );
        """
    )
    db.commit()


def seed_db():
    """Insert one demo user and sample expenses, for local dev only.
    Safe to call multiple times — skips if the demo user already exists."""
    from werkzeug.security import generate_password_hash

    db = get_db()

    existing = db.execute(
        "SELECT id FROM users WHERE email = ?", ("demo@spendly.dev",)
    ).fetchone()
    if existing is not None:
        return

    cursor = db.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        ("Demo User", "demo@spendly.dev", generate_password_hash("password123")),
    )
    user_id = cursor.lastrowid

    today = date.today()
    sample_expenses = [
        ("Food", 450.00, "Groceries at the supermarket", today - timedelta(days=1)),
        ("Travel", 1200.00, "Cab to the airport", today - timedelta(days=3)),
        ("Bills", 2500.00, "Electricity bill", today - timedelta(days=5)),
        ("Food", 300.50, "Dinner with friends", today - timedelta(days=6)),
        ("Bills", 800.00, "Internet bill", today - timedelta(days=10)),
        ("Travel", 150.00, "Metro card recharge", today - timedelta(days=12)),
        ("Shopping", 1999.00, "New headphones", today - timedelta(days=15)),
    ]
    db.executemany(
        """
        INSERT INTO expenses (user_id, category, amount, description, date)
        VALUES (?, ?, ?, ?, ?)
        """,
        [
            (user_id, cat, amt, desc, d.isoformat())
            for cat, amt, desc, d in sample_expenses
        ],
    )
    db.commit()


if __name__ == "__main__":
    # Manual dev entrypoint: `python3 database/db.py` creates and seeds
    # expense_tracker.db without needing app.py route wiring (which
    # doesn't exist yet — register/login POST handlers are a later step).
    from flask import Flask

    app = Flask(__name__)
    with app.app_context():
        init_db()
        seed_db()
    print(f"Initialized and seeded {DATABASE}")
