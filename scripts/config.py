"""
Configuration constants for the Hyderabad Transit Preprocessor.
"""
from pathlib import Path
import logging

# ==============================================================================
# PATHS
# ==============================================================================

# Base directory (scripts folder)
BASE_DIR = Path(__file__).parent.parent

# Input data directory containing GTFS zip files
DATA_DIR = BASE_DIR / "data"

# Output directory for preprocessed JSON/GeoJSON files
OUTPUT_DIR = BASE_DIR / "app" / "public" / "data"

# Temporary extraction directory
TEMP_DIR = BASE_DIR / "scripts" / ".temp"

# ==============================================================================
# GTFS FEED CONFIGURATION
# ==============================================================================

# Feed configurations with agency codes and expected files
FEEDS = {
    "HMRL": {
        "name": "Hyderabad Metro Rail Limited",
        "pattern": "gtfs_hmrl",  # Partial match for zip filename
        "transit_type": "metro",
        "route_type": 1,  # GTFS route_type for metro/subway
        "color_default": "#FF0000",  # Default color if not in routes.txt
        "has_shapes": True,  # HMRL has shapes.txt
    },
    "MMTS": {
        "name": "Multi-Modal Transport System (Suburban Rail)",
        "pattern": "MMTS",
        "transit_type": "rail",
        "route_type": 2,  # GTFS route_type for rail
        "color_default": "#2196F3",
        "has_shapes": False,  # MMTS may not have shapes.txt
    },
    "TGSRTC": {
        "name": "Telangana State Road Transport Corporation",
        "pattern": "TGSRTC",
        "transit_type": "bus",
        "route_type": 3,  # GTFS route_type for bus
        "color_default": "#4CAF50",
        "has_shapes": False,  # TGSRTC may not have shapes.txt
    },
}

# ==============================================================================
# GTFS SPEC - Required columns per file
# ==============================================================================

GTFS_REQUIRED_COLUMNS = {
    "agency.txt": ["agency_id", "agency_name", "agency_timezone"],
    "stops.txt": ["stop_id", "stop_name", "stop_lat", "stop_lon"],
    "routes.txt": ["route_id", "route_type"],  # route_short_name OR route_long_name
    "trips.txt": ["route_id", "service_id", "trip_id"],
    "stop_times.txt": ["trip_id", "arrival_time", "departure_time", "stop_id", "stop_sequence"],
    "calendar.txt": ["service_id", "monday", "tuesday", "wednesday", "thursday", 
                     "friday", "saturday", "sunday", "start_date", "end_date"],
}

GTFS_OPTIONAL_FILES = [
    "calendar_dates.txt",
    "shapes.txt",
    "fare_attributes.txt",
    "fare_rules.txt",
    "transfers.txt",
    "frequencies.txt",
    "feed_info.txt",
]

# ==============================================================================
# OUTPUT CONFIGURATION
# ==============================================================================

# Coordinate precision (5 decimals ≈ 1.1m accuracy)
COORDINATE_PRECISION = 5

# Timezone for time normalization
LOCAL_TIMEZONE = "Asia/Kolkata"

# Output file names
OUTPUT_FILES = {
    "stops": "stops.geojson",
    "routes": "routes.geojson",
    "stop_to_routes": "stop_to_routes.json",
    "route_to_stops": "route_to_stops.json",
    "timetable": "timetable.json",
    "metadata": "metadata.json",
}

# ==============================================================================
# MAP DISPLAY CONFIGURATION
# ==============================================================================

# Hyderabad bounding box (for validation)
HYDERABAD_BBOX = {
    "min_lat": 17.0,
    "max_lat": 17.8,
    "min_lon": 78.0,
    "max_lon": 79.0,
}

# Map center
HYDERABAD_CENTER = [17.385, 78.4867]

# Route type to display name mapping (GTFS spec)
ROUTE_TYPE_NAMES = {
    0: "tram",
    1: "metro",
    2: "rail",
    3: "bus",
    4: "ferry",
    5: "cable_car",
    6: "gondola",
    7: "funicular",
    11: "trolleybus",
    12: "monorail",
}

# ==============================================================================
# LOGGING CONFIGURATION
# ==============================================================================

LOG_LEVEL = logging.INFO
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging():
    """Configure logging for the preprocessor."""
    logging.basicConfig(
        level=LOG_LEVEL,
        format=LOG_FORMAT,
        datefmt=LOG_DATE_FORMAT,
    )
    return logging.getLogger("transit_preprocessor")
