# UK Crime ETL Pipeline (Metropolitan Police)

**A scheduled data pipeline that ingests live UK street-level crime data from a real API, warehouses it in PostgreSQL, and publishes a Tableau dashboard.**

Every month this pipeline pulls Metropolitan Police (London) crime data from the
[data.police.uk](https://data.police.uk/) API, walking the force's real
neighbourhood boundaries, cleans and de-duplicates it, loads it into a
PostgreSQL warehouse, and writes summarised CSV extracts that drive a Tableau
Public dashboard. A single recent month is ~90,000 crimes.

> **Data note:** Street-level locations are *anonymised approximations* snapped
> to nearby points and not exact crime locations. Data also lags one to two
> months, so the pipeline reads the API's "last updated" endpoint rather than
> assuming the current month exists.

---

## Architecture

```
data.police.uk API
      │                  extract.py: list the force's neighbourhoods, fetch
      │                  each real boundary polygon, query crime within it (POST)
      ▼
   data/raw/*.json     — raw landing zone (git-ignored)
      │                  transform.py: flatten, cast types, tag nearest borough, de-duplicate
      ▼
   PostgreSQL          — fact_crime table (idempotent upsert) + mart views
      │                  export_tableau.py
      ▼
   exports/*.csv       — public-safe summaries (committed)
      │
      ▼
   Tableau Public dashboard
```

Rather than tiling an arbitrary bounding box (which clips dense areas and covers
empty ground), the extract step discovers the force's real neighbourhood
boundaries from the API and queries crime within each one, it's accurate,
complete coverage of the whole force area. Crimes appearing in more than one
neighbourhood are removed in the transform step, and the load step upserts on a
stable crime id, so re-running a month is idempotent (it updates outcomes
rather than creating duplicates). Neighbourhood boundaries are cached to
`data/boundaries/`, so only the first run pays the boundary-fetch cost.

---

## Repository layout

```
uk-crime-pipeline/
├── config.py                 # force, borough centroids, DB config
├── src/
│   ├── extract.py            # API ingest: neighbourhoods, boundaries, crime
│   ├── transform.py          # flatten, borough tagging, de-duplication
│   ├── load.py               # schema and idempotent upsert into PostgreSQL
│   ├── export_tableau.py     # write CSV extracts from the mart views
│   └── pipeline.py           # orchestrates extract, transform, load, export
├── sql/
│   └── schema.sql            # fact table and Tableau mart views
├── exports/                  # committed CSV extracts for Tableau
├── tests/
│   └── test_transform.py     # unit tests (pytest)
├── scripts/
│   └── make_mock_data.py     # API-shaped mock data for offline testing
├── .github/workflows/
│   └── pipeline.yml          # scheduled monthly refresh (CI, with Postgres)
├── requirements.txt
└── .env.example              # DB credentials template (copy to .env)
```

---

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env          # then edit .env with your PostgreSQL details
createdb gm_crime             # the pipeline creates its tables on first run
```

---

## Running

```bash
python -m src.pipeline                 # latest available month (recommended)
python -m src.pipeline --month 2026-06 # a specific month
python -m src.pipeline --month 2026-06 --skip-extract   # reuse downloaded raw JSON
```

Run the tests:
```bash
pytest -q
```

The first live run fetches ~680 neighbourhood boundaries and takes several minutes, later months reuse the cached boundaries and run faster.

---

## The warehouse

`fact_crime` holds one row per unique crime. Four views feed the dashboard:

| View | Purpose |
|---|---|
| `mart_monthly_totals` | total crimes per month (trend line) |
| `mart_crime_by_area_month` | crimes by borough, category and month |
| `mart_crime_points` | point-level lat/lng for the map |
| `mart_outcomes_by_category` | how crimes resolve, by category |

`export_tableau.py` writes each to `exports/*.csv`.

---

## Tableau dashboard

The `exports/` CSVs feed a Tableau Public workbook with a crime-density map,
a monthly trend line, a category breakdown, and an outcome breakdown
showing how few crimes reach a charge. Filters for month, borough and category
drive all views.

**Live dashboard:** (https://public.tableau.com/shared/KFZDQ5QYK?:display_count=n&:origin=viz_share_link)

---

## Scheduling

`.github/workflows/pipeline.yml` runs the pipeline monthly on GitHub Actions
against an ephemeral PostgreSQL service container, then commits the refreshed
`exports/` CSVs. For a persistent warehouse, point the workflow's `PG*` env
vars at a managed PostgreSQL instance via repository secrets. Locally, a `cron`
entry calling `python -m src.pipeline` does the same job.

---

## License

MIT. Crime data © Crown copyright, provided under the Open Government Licence via data.police.uk.
