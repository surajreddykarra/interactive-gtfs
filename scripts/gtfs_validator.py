"""
GTFS Validator - Validates GTFS data against the spec.
"""
import pandas as pd
from typing import Dict, List, Tuple, Optional
import logging

from config import GTFS_REQUIRED_COLUMNS, HYDERABAD_BBOX
from gtfs_extractor import GTFSFeed

logger = logging.getLogger("transit_preprocessor")


class ValidationError(Exception):
    """Raised when GTFS validation fails."""
    pass


class ValidationWarning:
    """Container for validation warnings."""
    def __init__(self, file: str, message: str, severity: str = "warning"):
        self.file = file
        self.message = message
        self.severity = severity
    
    def __repr__(self):
        return f"[{self.severity.upper()}] {self.file}: {self.message}"


class GTFSValidator:
    """Validates GTFS feeds against the specification."""
    
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[ValidationWarning] = []
    
    def validate_feed(self, feed: GTFSFeed) -> Tuple[bool, List[str], List[ValidationWarning]]:
        """
        Validate a GTFS feed.
        
        Args:
            feed: GTFSFeed object to validate
            
        Returns:
            Tuple of (is_valid, errors, warnings)
        """
        self.errors = []
        self.warnings = []
        
        logger.info(f"Validating {feed.agency_code}...")
        
        # Required files check
        self._validate_required_files(feed)
        
        # Column validation for each file
        self._validate_columns(feed)
        
        # Data-specific validation
        if feed.stops is not None:
            self._validate_stops(feed)
        
        if feed.routes is not None:
            self._validate_routes(feed)
        
        if feed.stop_times is not None:
            self._validate_stop_times(feed)
        
        if feed.trips is not None:
            self._validate_trips(feed)
        
        # Service calendar validation
        self._validate_calendar(feed)
        
        # Log results
        is_valid = len(self.errors) == 0
        
        if is_valid:
            logger.info(f"  ✓ Validation passed with {len(self.warnings)} warnings")
        else:
            logger.error(f"  ✗ Validation failed with {len(self.errors)} errors")
        
        for warning in self.warnings[:5]:  # Show first 5 warnings
            logger.warning(f"    {warning}")
        
        if len(self.warnings) > 5:
            logger.warning(f"    ... and {len(self.warnings) - 5} more warnings")
        
        return is_valid, self.errors, self.warnings
    
    def _validate_required_files(self, feed: GTFSFeed):
        """Check that all required GTFS files are present."""
        required = ["agency.txt", "stops.txt", "routes.txt", "trips.txt", "stop_times.txt"]
        
        for filename in required:
            if filename not in feed.available_files:
                # Check if we have the corresponding DataFrame
                attr_name = filename.replace(".txt", "")
                if getattr(feed, attr_name, None) is None:
                    self.errors.append(f"Missing required file: {filename}")
    
    def _validate_columns(self, feed: GTFSFeed):
        """Validate that required columns exist in each file."""
        file_to_df = {
            "agency.txt": feed.agency,
            "stops.txt": feed.stops,
            "routes.txt": feed.routes,
            "trips.txt": feed.trips,
            "stop_times.txt": feed.stop_times,
            "calendar.txt": feed.calendar,
        }
        
        for filename, df in file_to_df.items():
            if df is None:
                continue
            
            if filename not in GTFS_REQUIRED_COLUMNS:
                continue
            
            required_cols = GTFS_REQUIRED_COLUMNS[filename]
            missing = [col for col in required_cols if col not in df.columns]
            
            if missing:
                # Special case: routes.txt requires short_name OR long_name
                if filename == "routes.txt" and "route_short_name" in missing:
                    if "route_long_name" in df.columns:
                        missing.remove("route_short_name")
                
                if missing:
                    self.warnings.append(ValidationWarning(
                        filename,
                        f"Missing columns: {', '.join(missing)}",
                        "warning"
                    ))
    
    def _validate_stops(self, feed: GTFSFeed):
        """Validate stops data."""
        stops = feed.stops
        
        # Check for required columns
        if "stop_lat" not in stops.columns or "stop_lon" not in stops.columns:
            self.errors.append("stops.txt missing stop_lat or stop_lon columns")
            return
        
        # Convert coordinates to numeric
        stops["stop_lat"] = pd.to_numeric(stops["stop_lat"], errors="coerce")
        stops["stop_lon"] = pd.to_numeric(stops["stop_lon"], errors="coerce")
        
        # Check for invalid coordinates
        invalid_coords = stops[
            (stops["stop_lat"].isna()) | 
            (stops["stop_lon"].isna()) |
            (stops["stop_lat"] < -90) | (stops["stop_lat"] > 90) |
            (stops["stop_lon"] < -180) | (stops["stop_lon"] > 180)
        ]
        
        if len(invalid_coords) > 0:
            self.warnings.append(ValidationWarning(
                "stops.txt",
                f"{len(invalid_coords)} stops have invalid coordinates",
                "warning"
            ))
        
        # Check if stops are within Hyderabad bounding box
        outside_hyd = stops[
            (stops["stop_lat"] < HYDERABAD_BBOX["min_lat"]) |
            (stops["stop_lat"] > HYDERABAD_BBOX["max_lat"]) |
            (stops["stop_lon"] < HYDERABAD_BBOX["min_lon"]) |
            (stops["stop_lon"] > HYDERABAD_BBOX["max_lon"])
        ]
        
        if len(outside_hyd) > 0:
            self.warnings.append(ValidationWarning(
                "stops.txt",
                f"{len(outside_hyd)} stops are outside Hyderabad bounding box",
                "info"
            ))
        
        # Check for duplicate stop_ids
        duplicates = stops[stops.duplicated(subset=["stop_id"], keep=False)]
        if len(duplicates) > 0:
            self.warnings.append(ValidationWarning(
                "stops.txt",
                f"{len(duplicates)} duplicate stop_ids found",
                "warning"
            ))
        
        # Check for empty stop names
        if "stop_name" in stops.columns:
            empty_names = stops[stops["stop_name"].str.strip() == ""]
            if len(empty_names) > 0:
                self.warnings.append(ValidationWarning(
                    "stops.txt",
                    f"{len(empty_names)} stops have empty names",
                    "warning"
                ))
    
    def _validate_routes(self, feed: GTFSFeed):
        """Validate routes data."""
        routes = feed.routes
        
        # Check for duplicate route_ids
        if "route_id" in routes.columns:
            duplicates = routes[routes.duplicated(subset=["route_id"], keep=False)]
            if len(duplicates) > 0:
                self.warnings.append(ValidationWarning(
                    "routes.txt",
                    f"{len(duplicates)} duplicate route_ids found",
                    "warning"
                ))
        
        # Check route_type values
        if "route_type" in routes.columns:
            routes["route_type"] = pd.to_numeric(routes["route_type"], errors="coerce")
            invalid_types = routes[~routes["route_type"].isin([0, 1, 2, 3, 4, 5, 6, 7, 11, 12])]
            if len(invalid_types) > 0:
                self.warnings.append(ValidationWarning(
                    "routes.txt",
                    f"{len(invalid_types)} routes have non-standard route_type values",
                    "info"
                ))
    
    def _validate_stop_times(self, feed: GTFSFeed):
        """Validate stop_times data."""
        stop_times = feed.stop_times
        
        # Check for empty times
        if "arrival_time" in stop_times.columns:
            empty_arrivals = stop_times[stop_times["arrival_time"].str.strip() == ""]
            if len(empty_arrivals) > 0:
                self.warnings.append(ValidationWarning(
                    "stop_times.txt",
                    f"{len(empty_arrivals)} records have empty arrival_time",
                    "warning"
                ))
        
        # Check stop_sequence is numeric
        if "stop_sequence" in stop_times.columns:
            stop_times["stop_sequence"] = pd.to_numeric(
                stop_times["stop_sequence"], errors="coerce"
            )
            invalid_seq = stop_times[stop_times["stop_sequence"].isna()]
            if len(invalid_seq) > 0:
                self.warnings.append(ValidationWarning(
                    "stop_times.txt",
                    f"{len(invalid_seq)} records have invalid stop_sequence",
                    "warning"
                ))
        
        # Check for orphan trips (trips not in trips.txt)
        if feed.trips is not None and "trip_id" in stop_times.columns:
            trip_ids_in_trips = set(feed.trips["trip_id"].unique())
            trip_ids_in_times = set(stop_times["trip_id"].unique())
            orphan_trips = trip_ids_in_times - trip_ids_in_trips
            if orphan_trips:
                self.warnings.append(ValidationWarning(
                    "stop_times.txt",
                    f"{len(orphan_trips)} trips in stop_times not found in trips.txt",
                    "warning"
                ))
    
    def _validate_trips(self, feed: GTFSFeed):
        """Validate trips data."""
        trips = feed.trips
        
        # Check for orphan routes (routes not in routes.txt)
        if feed.routes is not None and "route_id" in trips.columns:
            route_ids_in_routes = set(feed.routes["route_id"].unique())
            route_ids_in_trips = set(trips["route_id"].unique())
            orphan_routes = route_ids_in_trips - route_ids_in_routes
            if orphan_routes:
                self.warnings.append(ValidationWarning(
                    "trips.txt",
                    f"{len(orphan_routes)} routes in trips not found in routes.txt",
                    "warning"
                ))
    
    def _validate_calendar(self, feed: GTFSFeed):
        """Validate calendar data (calendar.txt and/or calendar_dates.txt)."""
        has_calendar = feed.calendar is not None and len(feed.calendar) > 0
        has_calendar_dates = feed.calendar_dates is not None and len(feed.calendar_dates) > 0
        
        if not has_calendar and not has_calendar_dates:
            self.warnings.append(ValidationWarning(
                "calendar",
                "Neither calendar.txt nor calendar_dates.txt found - service days unknown",
                "warning"
            ))
            return
        
        # Get service_ids from trips
        if feed.trips is not None and "service_id" in feed.trips.columns:
            trip_service_ids = set(feed.trips["service_id"].unique())
            
            # Check if all service_ids have calendar entries
            calendar_service_ids = set()
            if has_calendar:
                calendar_service_ids.update(feed.calendar["service_id"].unique())
            if has_calendar_dates:
                calendar_service_ids.update(feed.calendar_dates["service_id"].unique())
            
            missing_services = trip_service_ids - calendar_service_ids
            if missing_services:
                self.warnings.append(ValidationWarning(
                    "calendar",
                    f"{len(missing_services)} service_ids in trips have no calendar entry",
                    "warning"
                ))


def validate_all_feeds(feeds: Dict[str, GTFSFeed]) -> Dict[str, Tuple[bool, List[str], List[ValidationWarning]]]:
    """
    Validate all GTFS feeds.
    
    Args:
        feeds: Dictionary of GTFSFeed objects
        
    Returns:
        Dictionary mapping agency codes to validation results
    """
    validator = GTFSValidator()
    results = {}
    
    for agency_code, feed in feeds.items():
        results[agency_code] = validator.validate_feed(feed)
    
    return results
