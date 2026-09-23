import psycopg2
from psycopg2.extras import execute_values

import config

COLUMNS = [
    "crime_uid", "persistent_id", "category", "month",
    "latitude", "longitude", "street_id", "street_name",
    "borough", "outcome_category", "outcome_date",
]

UPSERT_SQL = f"""
INSERT INTO fact_crime ({", ".join(COLUMNS)})
VALUES %s
ON CONFLICT (crime_uid) DO UPDATE SET
    outcome_category = EXCLUDED.outcome_category,
    outcome_date     = EXCLUDED.outcome_date,
    ingested_at      = now();
"""


def get_connection():
    """Open a psycopg2 connection using the env-driven DB_CONFIG."""
    return psycopg2.connect(**config.DB_CONFIG)


def init_schema(conn):
    """Create tables and views from sql/schema.sql."""
    with open(config.SQL_DIR / "schema.sql", "r", encoding="utf-8") as fh:
        ddl = fh.read()
    with conn.cursor() as cur:
        cur.execute(ddl)
    conn.commit()


def load_rows(conn, rows):
    """Upsert a list of row dicts into fact_crime. Returns the count loaded."""
    if not rows:
        print("No rows to load.")
        return 0
    values = [[row.get(col) for col in COLUMNS] for row in rows]
    with conn.cursor() as cur:
        execute_values(cur, UPSERT_SQL, values, page_size=1000)
    conn.commit()
    print(f"Upserted {len(values)} rows into fact_crime")
    return len(values)


if __name__ == "__main__":
    # Quick connectivity check: create the schema and report the row count.
    conn = get_connection()
    init_schema(conn)
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM fact_crime;")
        print("fact_crime rows:", cur.fetchone()[0])
    conn.close()
