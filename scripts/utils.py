"""
Utility functions for the Hyderabad Transit Preprocessor.
"""
import re
from typing import List, Tuple, Optional
from config import COORDINATE_PRECISION


def normalize_time(gtfs_time: str) -> str:
    """
    Normalize GTFS time to HH:MM format.
    
    GTFS allows times > 24:00:00 for trips that span midnight.
    This function wraps those times to standard 24-hour format.
    
    Args:
        gtfs_time: Time string in H:MM:SS or HH:MM:SS format
        
    Returns:
        Normalized time string in HH:MM format
        
    Examples:
        >>> normalize_time("25:30:00")
        "01:30"
        >>> normalize_time("9:05:00")
        "09:05"
    """
    if not gtfs_time or gtfs_time.strip() == "":
        return ""
    
    # Handle different time formats
    parts = gtfs_time.strip().split(":")
    if len(parts) < 2:
        return ""
    
    try:
        hours = int(parts[0])
        minutes = int(parts[1])
        
        # Wrap hours > 24
        hours = hours % 24
        
        return f"{hours:02d}:{minutes:02d}"
    except (ValueError, IndexError):
        return ""


def time_to_minutes(time_str: str) -> int:
    """
    Convert HH:MM time string to minutes since midnight.
    
    Args:
        time_str: Time in HH:MM format
        
    Returns:
        Minutes since midnight (0-1439)
    """
    if not time_str:
        return 0
    
    try:
        h, m = map(int, time_str.split(":"))
        return h * 60 + m
    except (ValueError, AttributeError):
        return 0


def minutes_to_time(minutes: int) -> str:
    """
    Convert minutes since midnight to HH:MM format.
    
    Args:
        minutes: Minutes since midnight
        
    Returns:
        Time string in HH:MM format
    """
    h = (minutes // 60) % 24
    m = minutes % 60
    return f"{h:02d}:{m:02d}"


def round_coordinate(coord: float, precision: int = COORDINATE_PRECISION) -> float:
    """
    Round a coordinate to specified decimal places.
    
    Args:
        coord: Latitude or longitude value
        precision: Number of decimal places
        
    Returns:
        Rounded coordinate
    """
    return round(float(coord), precision)


def round_coordinates(coords: List[Tuple[float, float]], 
                      precision: int = COORDINATE_PRECISION) -> List[List[float]]:
    """
    Round a list of coordinate pairs to specified precision.
    
    Args:
        coords: List of (lon, lat) tuples
        precision: Number of decimal places
        
    Returns:
        List of [lon, lat] lists with rounded values
    """
    return [[round(c[0], precision), round(c[1], precision)] for c in coords]


def validate_coordinate(lat: float, lon: float) -> bool:
    """
    Validate that coordinates are within valid ranges.
    
    Args:
        lat: Latitude value
        lon: Longitude value
        
    Returns:
        True if coordinates are valid
    """
    try:
        lat = float(lat)
        lon = float(lon)
        return -90 <= lat <= 90 and -180 <= lon <= 180
    except (ValueError, TypeError):
        return False


def validate_hyderabad_coordinate(lat: float, lon: float) -> bool:
    """
    Validate that coordinates are within Hyderabad bounding box.
    
    Args:
        lat: Latitude value
        lon: Longitude value
        
    Returns:
        True if coordinates are within Hyderabad area
    """
    try:
        lat = float(lat)
        lon = float(lon)
        # Rough bounding box for Hyderabad region
        return 16.5 <= lat <= 18.0 and 77.5 <= lon <= 79.5
    except (ValueError, TypeError):
        return False


def clean_stop_name(name: str) -> str:
    """
    Clean and normalize a stop name.
    
    Args:
        name: Raw stop name from GTFS
        
    Returns:
        Cleaned stop name
    """
    if not name:
        return "Unknown Stop"
    
    # Strip whitespace
    name = name.strip()
    
    # Remove extra whitespace
    name = re.sub(r'\s+', ' ', name)
    
    # Title case if all uppercase
    if name.isupper():
        name = name.title()
    
    return name


def clean_route_name(short_name: Optional[str], long_name: Optional[str]) -> str:
    """
    Get the best route name from short_name and long_name.
    
    Args:
        short_name: Route short name (e.g., "10", "RED")
        long_name: Route long name (e.g., "Downtown - Airport")
        
    Returns:
        Best available route name
    """
    short = (short_name or "").strip()
    long = (long_name or "").strip()
    
    if short and long:
        return f"{short} - {long}" if len(short) < 10 else long
    elif short:
        return short
    elif long:
        return long
    else:
        return "Unknown Route"


def parse_color(color: Optional[str], default: str = "#888888") -> str:
    """
    Parse and validate a color string.
    
    Args:
        color: Color string (with or without #)
        default: Default color if invalid
        
    Returns:
        Valid hex color string with #
    """
    if not color:
        return default
    
    color = color.strip()
    
    # Add # if missing
    if not color.startswith("#"):
        color = f"#{color}"
    
    # Validate hex color
    if re.match(r'^#[0-9A-Fa-f]{6}$', color):
        return color.upper()
    
    return default


def prefix_id(agency_code: str, original_id: str) -> str:
    """
    Prefix an ID with agency code to ensure uniqueness across feeds.
    
    Args:
        agency_code: Agency identifier (e.g., "HMRL", "MMTS")
        original_id: Original ID from GTFS
        
    Returns:
        Prefixed ID
    """
    return f"{agency_code}_{original_id}"


def simplify_coordinates(coords: List[Tuple[float, float]], 
                         tolerance: float = 0.0001) -> List[Tuple[float, float]]:
    """
    Simplify a coordinate sequence by removing points too close together.
    
    This is a simple distance-based simplification, not Douglas-Peucker.
    
    Args:
        coords: List of (lon, lat) tuples
        tolerance: Minimum distance between consecutive points (in degrees)
        
    Returns:
        Simplified coordinate list
    """
    if len(coords) <= 2:
        return coords
    
    simplified = [coords[0]]
    
    for coord in coords[1:-1]:
        last = simplified[-1]
        dist = ((coord[0] - last[0])**2 + (coord[1] - last[1])**2)**0.5
        if dist >= tolerance:
            simplified.append(coord)
    
    # Always include last point
    simplified.append(coords[-1])
    
    return simplified


def estimate_frequency(times: List[str]) -> dict:
    """
    Estimate service frequency from a list of arrival times.
    
    Args:
        times: List of HH:MM time strings
        
    Returns:
        Dictionary with frequency statistics
    """
    if not times or len(times) < 2:
        return {"avg_headway": None, "trips_per_hour": 0}
    
    # Convert to minutes
    minutes = sorted([time_to_minutes(t) for t in times if t])
    
    if len(minutes) < 2:
        return {"avg_headway": None, "trips_per_hour": 0}
    
    # Calculate headways
    headways = [minutes[i+1] - minutes[i] for i in range(len(minutes)-1)]
    headways = [h for h in headways if 0 < h < 120]  # Filter outliers
    
    if not headways:
        return {"avg_headway": None, "trips_per_hour": len(minutes)}
    
    avg_headway = sum(headways) / len(headways)
    trips_per_hour = round(60 / avg_headway, 1) if avg_headway > 0 else 0
    
    return {
        "avg_headway": round(avg_headway, 1),
        "trips_per_hour": trips_per_hour
    }
