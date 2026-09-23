import hashlib
import json

import config


def assign_borough(lat, lng):
    """Return the name of the nearest GM borough centroid to (lat, lng)."""
    if lat is None or lng is None:
        return None
    best_name, best_dist = None, float("inf")
    for name, (blat, blng) in config.BOROUGH_CENTROIDS.items():
        dist = (lat - blat) ** 2 + (lng - blng) ** 2   # squared euclidean is fine here
        if dist < best_dist:
            best_name, best_dist = name, dist
    return best_name


def _to_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def make_uid(month, category, lat, lng, street_id, persistent_id):
    """
    Stable unique id for a crime.

    Uses the API's persistent_id where present. Some categories (notably
    anti-social behaviour) ship an empty persistent_id, so for those we hash
    the other identifying fields. This means two anti-social crimes snapped to
    the exact same anonymised point in the same month collapse into one.
    """
    if persistent_id and persistent_id.strip():
        return persistent_id.strip()
    key = f"{month}|{category}|{lat}|{lng}|{street_id}"
    return hashlib.md5(key.encode("utf-8")).hexdigest()


def flatten_record(rec):
    """Flatten one raw API crime dict into a flat row dict."""
    location = rec.get("location") or {}
    street = location.get("street") or {}
    outcome = rec.get("outcome_status") or {}

    lat = _to_float(location.get("latitude"))
    lng = _to_float(location.get("longitude"))
    street_id = street.get("id")
    category = rec.get("category")
    month = rec.get("month")
    persistent_id = rec.get("persistent_id") or ""

    return {
        "crime_uid": make_uid(month, category, lat, lng, street_id, persistent_id),
        "persistent_id": persistent_id or None,
        "category": category,
        "month": month,
        "latitude": lat,
        "longitude": lng,
        "street_id": street_id,
        "street_name": street.get("name"),
        "borough": assign_borough(lat, lng),
        "outcome_category": outcome.get("category"),
        "outcome_date": outcome.get("date"),
    }


def transform(raw_records):
    """Flatten and de-duplicate a list of raw API records."""
    seen = {}
    for rec in raw_records:
        row = flatten_record(rec)
        # last write wins — keeps the most complete outcome if duplicated
        seen[row["crime_uid"]] = row
    return list(seen.values())


def transform_file(path):
    """Load raw JSON from disk and return clean, de-duplicated rows."""
    with open(path, "r", encoding="utf-8") as fh:
        raw = json.load(fh)
    rows = transform(raw)
    print(f"Transformed {len(raw)} raw -> {len(rows)} unique rows")
    return rows


if __name__ == "__main__":
    import sys

    transform_file(sys.argv[1])
