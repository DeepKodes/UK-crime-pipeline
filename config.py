import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()  # read a local .env file if present

# Paths
ROOT = Path(__file__).resolve().parent
RAW_DIR = ROOT / "data" / "raw"                 # git-ignored landing zone for API JSON
BOUNDARY_DIR = ROOT / "data" / "boundaries"     # cached neighbourhood boundaries
EXPORT_DIR = ROOT / "exports"                   # committed public-safe CSVs for Tableau
SQL_DIR = ROOT / "sql"

RAW_DIR.mkdir(parents=True, exist_ok=True)
BOUNDARY_DIR.mkdir(parents=True, exist_ok=True)
EXPORT_DIR.mkdir(parents=True, exist_ok=True)


API_BASE = "https://data.police.uk/api"
FORCE = "metropolitan"           # the police force to ingest (London)
USER_AGENT = "uk-crime-pipeline/1.0 (portfolio project)"
REQUEST_DELAY = 0.2              # seconds between API calls
REQUEST_TIMEOUT = 60             # seconds
MAX_RETRIES = 3                  # network retries per request
MAX_POLY_POINTS = 150            # downsample huge boundary polygons to this many points

# Approximate borough centroids (lat, lng). Each crime is tagged with its nearest borough. This is an approximation, see the README note on locations. Inner + a few outer London boroughs, which covers the Met's busiest areas.

BOROUGH_CENTROIDS = {
    "Westminster": (51.497, -0.137),
    "Camden": (51.545, -0.150),
    "Islington": (51.546, -0.103),
    "Hackney": (51.545, -0.055),
    "Tower Hamlets": (51.515, -0.030),
    "Southwark": (51.474, -0.081),
    "Lambeth": (51.457, -0.117),
    "Wandsworth": (51.457, -0.191),
    "Kensington and Chelsea": (51.499, -0.194),
    "Hammersmith and Fulham": (51.492, -0.223),
    "Greenwich": (51.486, 0.006),
    "Lewisham": (51.446, -0.020),
    "Newham": (51.525, 0.035),
    "Haringey": (51.591, -0.111),
    "Brent": (51.564, -0.275),
    "Ealing": (51.513, -0.305),
    "Croydon": (51.371, -0.099),
    "Barnet": (51.625, -0.200),
}

# Bounding box (south, west, north, east), which is only used by the mock-data generator to produce realistic points. Roughly Greater London here.
GM_BBOX = {"south": 51.28, "west": -0.51, "north": 51.69, "east": 0.33}

# Database

DB_CONFIG = {
    "host": os.getenv("PGHOST", "localhost"),
    "port": os.getenv("PGPORT", "5432"),
    "dbname": os.getenv("PGDATABASE", "gm_crime"),
    "user": os.getenv("PGUSER", "postgres"),
    "password": os.getenv("PGPASSWORD", ""),
}
