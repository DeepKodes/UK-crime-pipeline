import csv

import config
from src.load import get_connection

EXPORTS = {
    "crime_by_area_month": "SELECT * FROM mart_crime_by_area_month",
    "crime_points": "SELECT * FROM mart_crime_points",
    "outcomes_by_category": "SELECT * FROM mart_outcomes_by_category",
    "monthly_totals": "SELECT * FROM mart_monthly_totals",
}


def _write_csv(cur, query, path):
    cur.execute(query)
    headers = [desc[0] for desc in cur.description]
    rows = cur.fetchall()
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(headers)
        writer.writerows(rows)
    return len(rows)


def export_all(conn=None):
    """Write every mart to exports/<name>.csv. Returns list of paths written."""
    own_conn = conn is None
    if own_conn:
        conn = get_connection()

    written = []
    try:
        with conn.cursor() as cur:
            for name, query in EXPORTS.items():
                path = config.EXPORT_DIR / f"{name}.csv"
                n = _write_csv(cur, query, path)
                print(f"  wrote {n:>6} rows -> {path.name}")
                written.append(path)
    finally:
        if own_conn:
            conn.close()
    return written


if __name__ == "__main__":
    export_all()
