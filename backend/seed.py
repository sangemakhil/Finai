import random
from datetime import datetime, timedelta
from pathlib import Path

SEED_FILE = Path(__file__).with_name("seed.sql")

# -------------------------
# Helper functions
# -------------------------

def random_nav(base, vol=5):
    """Generate small daily NAV fluctuation around base."""
    return round(base + random.uniform(-vol, vol), 2)

def generate_daily_navs(fund_id, base_nav, days=180):
    out = []
    today = datetime.today()
    for i in range(days):
        date = today - timedelta(days=i)
        nav = random_nav(base_nav)
        out.append((fund_id, date.strftime("%Y-%m-%d"), nav))
    return out


def generate_sip_year(user_id, fund_id, year, amount, start_nav):
    """Generate monthly SIP entries with realistic nav & units."""
    rows = []
    nav = start_nav
    for month in range(1, 13):
        date = f"{year}-{month:02d}-05"
        nav += random.uniform(-3, 3)
        nav_val = round(nav, 2)
        units = round(amount / nav_val, 4)
        rows.append((user_id, fund_id, date, amount, nav_val, units))
    return rows


# -------------------------
# Seed Data Construction
# -------------------------

def generate_seed_sql():
    sql = []

    # USERS
    sql.append("""
INSERT OR IGNORE INTO users (id, email, password_hash) VALUES
  (1, 'demo@example.com', 'demo');
""")

    # FUNDS
    funds = [
        (1, "HDFC Equity Growth", "Equity", "High", 0.012),
        (2, "ICICI Balanced Advantage", "Hybrid", "Moderate", 0.009),
        (3, "SBI Bluechip Fund", "Equity", "Moderate", 0.011)
    ]

    sql.append("INSERT OR IGNORE INTO funds (fund_id, fund_name, fund_type, risk_level, expense_ratio) VALUES\n" +
               ",\n".join(f"  ({f[0]}, '{f[1]}', '{f[2]}', '{f[3]}', {f[4]})" for f in funds) +
               ";\n")

    # SIP RECORDS
    sql.append("DELETE FROM sip_records;")

    sip_rows = []
    # HDFC Equity Growth
    sip_rows += generate_sip_year(1, 1, 2023, 500, 450)
    sip_rows += generate_sip_year(1, 1, 2024, 600, 485)
    sip_rows += generate_sip_year(1, 1, 2025, 650, 520)[:10]   # YTD

    # ICICI BAF
    sip_rows += generate_sip_year(1, 2, 2023, 300, 210)
    sip_rows += generate_sip_year(1, 2, 2024, 350, 225)
    sip_rows += generate_sip_year(1, 2, 2025, 400, 240)[:10]

    # SBI Bluechip
    sip_rows += generate_sip_year(1, 3, 2023, 400, 320)
    sip_rows += generate_sip_year(1, 3, 2024, 450, 340)
    sip_rows += generate_sip_year(1, 3, 2025, 500, 360)[:10]

    sql.append("INSERT INTO sip_records (user_id, fund_id, date, amount, nav_at_purchase, units_purchased) VALUES\n" +
               ",\n".join(
                   f"  ({r[0]}, {r[1]}, '{r[2]}', {r[3]}, {r[4]}, {r[5]})"
                   for r in sip_rows
               ) +
               ";\n")

    # NAV HISTORY
    sql.append("DELETE FROM nav_history;")

    nav_rows = []
    nav_rows += generate_daily_navs(1, 550, 180)  # HDFC
    nav_rows += generate_daily_navs(2, 245, 180)  # ICICI
    nav_rows += generate_daily_navs(3, 365, 180)  # SBI Bluechip

    sql.append("INSERT INTO nav_history (fund_id, date, nav_value) VALUES\n" +
               ",\n".join(
                   f"  ({r[0]}, '{r[1]}', {r[2]})"
                   for r in nav_rows
               ) +
               ";\n")

    return "\n".join(sql)


# -------------------------
# Write to seed.sql
# -------------------------

def write_seed_file():
    sql_text = generate_seed_sql()
    SEED_FILE.write_text(sql_text, encoding="utf-8")
    print(f"✅ Generated seed.sql with realistic data → {SEED_FILE}")


if __name__ == "__main__":
    write_seed_file()
