import json
import time

import requests

import config


def _get(url, params=None):
    """GET with polite delay and simple retry. Returns parsed JSON or None."""
    headers = {"User-Agent": config.USER_AGENT}
    for attempt in range(1, config.MAX_RETRIES + 1):
        time.sleep(config.REQUEST_DELAY)
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=config.REQUEST_TIMEOUT)
        except requests.RequestException as exc:
            if attempt == config.MAX_RETRIES:
                raise
            print(f"    network error ({exc}); retry {attempt}/{config.MAX_RETRIES}")
            continue
        if resp.status_code == 200:
            return resp.json()
        if resp.status_code == 429:
            wait = 2 ** attempt
            print(f"    rate limited; backing off {wait}s")
            time.sleep(wait)
            continue
        if attempt == config.MAX_RETRIES:
            resp.raise_for_status()
    return None


def get_neighbourhoods():
    """Return the list of {id, name} neighbourhoods for the configured force."""
    data = _get(f"{config.API_BASE}/{config.FORCE}/neighbourhoods")
    return data or []


def get_boundary(nbhd_id):
    """
    Return a neighbourhood's boundary as a list of (lat, lng) string pairs.
    Cached to data/boundaries/<id>.json to avoid re-fetching every run.
    """
    cache = config.BOUNDARY_DIR / f"{nbhd_id}.json"
    if cache.exists():
        with open(cache, "r", encoding="utf-8") as fh:
            return json.load(fh)

    data = _get(f"{config.API_BASE}/{config.FORCE}/{nbhd_id}/boundary")
    points = [(p["latitude"], p["longitude"]) for p in (data or [])]
    with open(cache, "w", encoding="utf-8") as fh:
        json.dump(points, fh)
    return points


def _poly_from_boundary(points):
    """
    Build the API 'poly' string from boundary points, downsampling very large
    polygons to keep requests light.
    """
    if len(points) > config.MAX_POLY_POINTS:
        step = len(points) // config.MAX_POLY_POINTS
        points = points[::step]
    return ":".join(f"{lat},{lng}" for lat, lng in points)


def get_latest_month():
    """Ask the API for the most recent month of data available (YYYY-MM)."""
    data = _get(f"{config.API_BASE}/crime-last-updated")
    if data and data.get("date"):
        return data["date"][:7]
    raise RuntimeError("Could not determine latest available month from API")


def _fetch_crimes_in_poly(poly, date):
    """
    POST the crimes-street query for a polygon + month. POST is used (rather
    than GET) so large boundary polygons don't hit the API's URL-length limit.
    Returns a list of raw crime dicts.
    """
    url = f"{config.API_BASE}/crimes-street/all-crime"
    headers = {"User-Agent": config.USER_AGENT}
    for attempt in range(1, config.MAX_RETRIES + 1):
        time.sleep(config.REQUEST_DELAY)
        try:
            resp = requests.post(
                url, data={"poly": poly, "date": date},
                headers=headers, timeout=config.REQUEST_TIMEOUT,
            )
        except requests.RequestException as exc:
            if attempt == config.MAX_RETRIES:
                raise
            print(f"    network error ({exc}); retry {attempt}/{config.MAX_RETRIES}")
            continue
        if resp.status_code == 200:
            return resp.json() or []
        if resp.status_code == 503:
            print("    neighbourhood too dense (>10k crimes); skipping")
            return []
        if resp.status_code == 429:
            wait = 2 ** attempt
            print(f"    rate limited; backing off {wait}s")
            time.sleep(wait)
            continue
        if attempt == config.MAX_RETRIES:
            resp.raise_for_status()
    return []


def extract_month(date):
    """
    Pull every crime in the force area for `date` (YYYY-MM), save the combined
    raw JSON to data/raw/<date>.json, and return the path.
    """
    neighbourhoods = get_neighbourhoods()
    print(f"Extracting {date} across {len(neighbourhoods)} London (Met) neighbourhoods...")

    all_crimes = []
    for i, nbhd in enumerate(neighbourhoods, 1):
        nbhd_id = nbhd.get("id")
        boundary = get_boundary(nbhd_id)
        if not boundary:
            print(f"  {i}/{len(neighbourhoods)} {nbhd_id}: no boundary; skipping")
            continue
        poly = _poly_from_boundary(boundary)
        crimes = _fetch_crimes_in_poly(poly, date)
        all_crimes.extend(crimes)
        if i % 20 == 0 or i == len(neighbourhoods):
            print(f"  {i}/{len(neighbourhoods)} neighbourhoods done "
                  f"(running total {len(all_crimes)} crimes)")

    out_path = config.RAW_DIR / f"{date}.json"
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(all_crimes, fh)
    print(f"Saved {len(all_crimes)} raw records to {out_path}")
    return out_path


if __name__ == "__main__":
    import sys

    month = sys.argv[1] if len(sys.argv) > 1 else get_latest_month()
    extract_month(month)
