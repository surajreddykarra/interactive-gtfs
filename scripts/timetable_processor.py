"""
Timetable Processor - Generates timetable data from GTFS.
"""
import pandas as pd
from typing import Dict, List, Any, Set
from collections import defaultdict
import logging

from gtfs_extractor import GTFSFeed
from utils import normalize_time, prefix_id, time_to_minutes
from config import FEEDS

logger = logging.getLogger("transit_preprocessor")


class TimetableProcessor:
    """Processes timetable/schedule data from GTFS feeds."""
    
    def __init__(self):
        self.timetable: Dict[str, Dict[str, Dict[str, List[str]]]] = {}
        # timetable[stop_id][route_id] = {"weekday": [...], "weekend": [...]}
    
    def process_feed(self, feed: GTFSFeed) -> Dict[str, Dict[str, Dict[str, List[str]]]]:
        """
        Process timetable data from a single GTFS feed.
        
        Args:
            feed: GTFSFeed object containing the data
            
        Returns:
            Timetable dictionary for this feed
        """
        if feed.stop_times is None or feed.trips is None:
            logger.warning(f"No timetable data for {feed.agency_code}")
            return {}
        
        logger.info(f"Processing timetable for {feed.agency_code}...")
        
        # Determine service days
        weekday_services, weekend_services = self._get_service_days(feed)
        
        # Build trip -> route mapping
        trip_to_route: Dict[str, str] = {}
        trip_to_service: Dict[str, str] = {}
        
        for _, row in feed.trips.iterrows():
            trip_id = str(row.get("trip_id", "")).strip()
            route_id = str(row.get("route_id", "")).strip()
            service_id = str(row.get("service_id", "")).strip()
            
            if trip_id:
                trip_to_route[trip_id] = route_id
                trip_to_service[trip_id] = service_id
        
        # Process stop times
        feed_timetable: Dict[str, Dict[str, Dict[str, Set[str]]]] = defaultdict(
            lambda: defaultdict(lambda: {"weekday": set(), "weekend": set()})
        )
        
        for _, row in feed.stop_times.iterrows():
            stop_id = str(row.get("stop_id", "")).strip()
            trip_id = str(row.get("trip_id", "")).strip()
            arrival_time = str(row.get("arrival_time", "")).strip()
            
            if not (stop_id and trip_id and arrival_time):
                continue
            
            route_id = trip_to_route.get(trip_id)
            service_id = trip_to_service.get(trip_id)
            
            if not route_id:
                continue
            
            normalized_time = normalize_time(arrival_time)
            if not normalized_time:
                continue
            
            # Prefix IDs
            prefixed_stop = prefix_id(feed.agency_code, stop_id)
            prefixed_route = prefix_id(feed.agency_code, route_id)
            
            # Determine day type
            if service_id in weekday_services:
                feed_timetable[prefixed_stop][prefixed_route]["weekday"].add(normalized_time)
            if service_id in weekend_services:
                feed_timetable[prefixed_stop][prefixed_route]["weekend"].add(normalized_time)
            
            # If we couldn't determine service days, add to both
            if service_id not in weekday_services and service_id not in weekend_services:
                feed_timetable[prefixed_stop][prefixed_route]["weekday"].add(normalized_time)
                feed_timetable[prefixed_stop][prefixed_route]["weekend"].add(normalized_time)
        
        # Convert sets to sorted lists and merge into main timetable
        for stop_id, routes in feed_timetable.items():
            if stop_id not in self.timetable:
                self.timetable[stop_id] = {}
            
            for route_id, day_times in routes.items():
                self.timetable[stop_id][route_id] = {
                    "weekday": sorted(day_times["weekday"], key=lambda t: time_to_minutes(t)),
                    "weekend": sorted(day_times["weekend"], key=lambda t: time_to_minutes(t))
                }
        
        logger.info(f"  Processed timetable for {len(feed_timetable)} stops")
        return dict(feed_timetable)
    
    def _get_service_days(self, feed: GTFSFeed) -> tuple:
        """
        Determine which service_ids run on weekdays vs weekends.
        
        Returns:
            Tuple of (weekday_service_ids, weekend_service_ids)
        """
        weekday_services: Set[str] = set()
        weekend_services: Set[str] = set()
        
        if feed.calendar is not None and len(feed.calendar) > 0:
            for _, row in feed.calendar.iterrows():
                service_id = str(row.get("service_id", "")).strip()
                if not service_id:
                    continue
                
                # Check weekday columns
                weekday_cols = ["monday", "tuesday", "wednesday", "thursday", "friday"]
                is_weekday = any(
                    str(row.get(col, "0")).strip() == "1" 
                    for col in weekday_cols
                )
                
                # Check weekend columns
                weekend_cols = ["saturday", "sunday"]
                is_weekend = any(
                    str(row.get(col, "0")).strip() == "1" 
                    for col in weekend_cols
                )
                
                if is_weekday:
                    weekday_services.add(service_id)
                if is_weekend:
                    weekend_services.add(service_id)
        
        # Handle calendar_dates.txt exceptions
        if feed.calendar_dates is not None and len(feed.calendar_dates) > 0:
            # This is a simplified handling - just add all services
            for _, row in feed.calendar_dates.iterrows():
                service_id = str(row.get("service_id", "")).strip()
                if service_id:
                    # Add to both by default if we can't determine
                    weekday_services.add(service_id)
                    weekend_services.add(service_id)
        
        # If no calendar info, return all trip service_ids
        if not weekday_services and not weekend_services:
            if feed.trips is not None:
                all_services = set(feed.trips["service_id"].unique())
                weekday_services = all_services
                weekend_services = all_services
                logger.warning(f"  No calendar data, assuming all services run daily")
        
        return weekday_services, weekend_services
    
    def process_all_feeds(self, feeds: Dict[str, GTFSFeed]) -> Dict[str, Dict[str, Dict[str, List[str]]]]:
        """
        Process timetable data from all feeds.
        
        Args:
            feeds: Dictionary of GTFSFeed objects
            
        Returns:
            Combined timetable dictionary
        """
        self.timetable = {}
        
        for agency_code, feed in feeds.items():
            self.process_feed(feed)
        
        logger.info(f"Total timetable entries: {len(self.timetable)} stops")
        return self.timetable
    
    def get_timetable(self) -> Dict[str, Dict[str, Dict[str, List[str]]]]:
        """Get the complete timetable dictionary."""
        return self.timetable
    
    def get_compact_timetable(self) -> Dict[str, Dict[str, List[str]]]:
        """
        Get a compact version of the timetable without day type separation.
        Useful for simpler visualizations.
        """
        compact = {}
        
        for stop_id, routes in self.timetable.items():
            compact[stop_id] = {}
            for route_id, day_times in routes.items():
                # Merge weekday and weekend, remove duplicates
                all_times = set(day_times.get("weekday", []))
                all_times.update(day_times.get("weekend", []))
                compact[stop_id][route_id] = sorted(all_times, key=lambda t: time_to_minutes(t))
        
        return compact
