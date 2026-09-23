import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import transform  


def _raw(category="burglary", pid="abc123", lat="51.497", lng="-0.137", outcome="Under investigation"):
    return {
        "category": category,
        "location": {
            "latitude": lat,
            "longitude": lng,
            "street": {"id": 12345, "name": "On or near High St"},
        },
        "outcome_status": None if outcome is None else {"category": outcome, "date": "2026-07"},
        "persistent_id": pid,
        "id": 999,
        "month": "2026-07",
    }


def test_flatten_casts_floats_and_flattens():
    row = transform.flatten_record(_raw())
    assert row["latitude"] == 51.497
    assert row["longitude"] == -0.137
    assert row["street_name"] == "On or near High St"
    assert row["category"] == "burglary"
    assert row["outcome_category"] == "Under investigation"


def test_borough_assignment_picks_nearest():
    # A point on Westminster's centroid should map to Westminster.
    assert transform.assign_borough(51.497, -0.137) == "Westminster"
    # A point on Croydon's centroid should map to Croydon.
    assert transform.assign_borough(51.371, -0.099) == "Croydon"


def test_null_outcome_handled():
    row = transform.flatten_record(_raw(outcome=None))
    assert row["outcome_category"] is None
    assert row["outcome_date"] is None


def test_empty_persistent_id_gets_surrogate_uid():
    row = transform.flatten_record(_raw(pid=""))
    assert row["crime_uid"]  # non-empty
    assert row["persistent_id"] is None


def test_dedupe_collapses_duplicates():
    records = [_raw(pid="same"), _raw(pid="same"), _raw(pid="other")]
    rows = transform.transform(records)
    assert len(rows) == 2


def test_missing_coordinates_do_not_crash():
    rec = _raw()
    rec["location"]["latitude"] = None
    rec["location"]["longitude"] = None
    row = transform.flatten_record(rec)
    assert row["latitude"] is None
    assert row["borough"] is None
