import sqlite3
from pathlib import Path

import pandas as pd

DB_PATH = Path(__file__).parent / "fintrack.db"


def get_connection():
    return sqlite3.connect(DB_PATH)


def create_table():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner TEXT NOT NULL,
                date TEXT NOT NULL,
                description TEXT NOT NULL,
                category TEXT NOT NULL,
                transaction_type TEXT NOT NULL,
                amount REAL NOT NULL CHECK(amount > 0),
                account TEXT DEFAULT ''
            )
        """)


def add_transaction(
    owner,
    date,
    description,
    category,
    transaction_type,
    amount,
    account=""
):
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO transactions (
                owner,
                date,
                description,
                category,
                transaction_type,
                amount,
                account
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            owner,
            str(date),
            description.strip(),
            category,
            transaction_type,
            float(amount),
            account.strip()
        ))


def get_transactions(owner=None):
    with get_connection() as conn:
        if owner and owner != "All":
            df = pd.read_sql_query(
                """
                SELECT * FROM transactions
                WHERE owner = ?
                ORDER BY date DESC, id DESC
                """,
                conn,
                params=(owner,)
            )
        else:
            df = pd.read_sql_query(
                """
                SELECT * FROM transactions
                ORDER BY date DESC, id DESC
                """,
                conn
            )

    return df


def delete_transaction(transaction_id):
    with get_connection() as conn:
        conn.execute(
            "DELETE FROM transactions WHERE id = ?",
            (int(transaction_id),)
        )


def transaction_exists(
    owner,
    date,
    description,
    amount,
    account=""
):
    with get_connection() as conn:
        result = conn.execute("""
            SELECT 1
            FROM transactions
            WHERE owner = ?
              AND date = ?
              AND description = ?
              AND amount = ?
              AND account = ?
            LIMIT 1
        """, (
            owner,
            str(date),
            description.strip(),
            float(amount),
            account.strip()
        )).fetchone()

    return result is not None