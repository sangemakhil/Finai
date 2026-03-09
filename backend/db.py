import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).with_name("finance.db")

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_conn() as c, open(Path(__file__).with_name("schema.sql"), "r", encoding="utf-8") as f:
        c.executescript(f.read())

def fund_id_by_fuzzy(name: str):
    """Try exact → LIKE → startswith; return best match or None."""
    with get_conn() as c:
        # exact (case-insensitive)
        cur = c.execute("SELECT fund_id FROM funds WHERE LOWER(fund_name)=LOWER(?)", (name,))
        row = cur.fetchone()
        if row:
            return row["fund_id"]

        # LIKE anywhere
        cur = c.execute("SELECT fund_id, fund_name FROM funds WHERE LOWER(fund_name) LIKE LOWER(?)", (f"%{name}%",))
        rows = cur.fetchall()
        if rows:
            # naive pick: shortest name containing the token
            rows = sorted(rows, key=lambda r: len(r["fund_name"]))
            return rows[0]["fund_id"]

        # startswith fallback
        cur = c.execute("SELECT fund_id, fund_name FROM funds WHERE LOWER(fund_name) LIKE LOWER(?)", (f"{name.lower()}%",))
        rows = cur.fetchall()
        if rows:
            return rows[0]["fund_id"]

    return None

def seed_db():
    with get_conn() as c, open(Path(__file__).with_name("seed.sql"), "r", encoding="utf-8") as f:
        c.executescript(f.read())

def get_user_by_email(email: str):
    with get_conn() as c:
        cur = c.execute("SELECT * FROM users WHERE email = ?", (email,))
        return cur.fetchone()

def fund_id_by_name(name: str):
    with get_conn() as c:
        cur = c.execute("SELECT fund_id FROM funds WHERE LOWER(fund_name)=LOWER(?)", (name,))
        row = cur.fetchone()
        return row["fund_id"] if row else None

def sip_total_year(user_id: int, fund_id: int, year: int):
    with get_conn() as c:
        cur = c.execute(
            """
            SELECT COALESCE(SUM(amount),0) AS total, COUNT(*) AS n
            FROM sip_records
            WHERE user_id = ? AND fund_id = ? AND strftime('%Y', date) = ?
            """,
            (user_id, fund_id, str(year))
        )
        return dict(cur.fetchone())

def latest_nav(fund_id: int):
    with get_conn() as c:
        cur = c.execute(
            """
            SELECT date, nav_value
            FROM nav_history
            WHERE fund_id = ?
            ORDER BY date DESC
            LIMIT 1
            """,
            (fund_id,)
        )
        row = cur.fetchone()   # <- fetch exactly once
        return dict(row) if row else None

