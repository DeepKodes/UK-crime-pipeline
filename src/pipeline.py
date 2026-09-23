import argparse

import config
from src import extract, transform, load, export_tableau


def run(month=None, skip_extract=False):
    # EXTRACT
    if month is None:
        month = extract.get_latest_month()
        print(f"Latest available month: {month}")

    raw_path = config.RAW_DIR / f"{month}.json"
    if skip_extract:
        if not raw_path.exists():
            raise FileNotFoundError(
                f"{raw_path} not found — cannot --skip-extract for {month}"
            )
        print(f"Skipping extract; using {raw_path}")
    else:
        raw_path = extract.extract_month(month)

    # TRANSFORM 
    rows = transform.transform_file(raw_path)

    # LOAD 
    conn = load.get_connection()
    try:
        load.init_schema(conn)
        load.load_rows(conn, rows)

        # EXPORT
        print("Exporting Tableau CSVs...")
        export_tableau.export_all(conn)
    finally:
        conn.close()

    print(f"\nPipeline complete for {month}.")


def main():
    parser = argparse.ArgumentParser(description="GM crime ETL pipeline")
    parser.add_argument("--month", help="Month to process, YYYY-MM (default: latest)")
    parser.add_argument(
        "--skip-extract",
        action="store_true",
        help="Reuse existing raw JSON instead of calling the API",
    )
    args = parser.parse_args()
    run(month=args.month, skip_extract=args.skip_extract)


if __name__ == "__main__":
    main()
