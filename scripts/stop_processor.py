"""
Stop Processor - Processes GTFS stops data into the required output format.
"""
import pandas as pd
from typing import Dict, List, Any, Optional, Set
from collections import defaultdict
import logging

from gtfs_extractor import GTFSFeed
from utils import (
    normalize_time, 
    clean_stop_name, 
    round_coordinate, 
    prefix_id,
    validate_hyderabad_coordinate,
    time_to_minutes,
    estimate_frequency
)
from config import COORDINATE_PRECISION

logger = logging.getLogger("transit_preprocessor")


class StopProcessor:
    """Processes stop data from GTFS feeds."""
    
    def __init__(self):
        self.all_stops: List[Dict[str, Any]] = []
        self.stop_to_routes: Dict[str, List[str]] = defaultdict(list)
        self.stop_route_times: Dict[str, Dict[str, List[str]]] = defaultdict(lambda: defaultdict(list))
    
    def process_feed(self, feed: GTFSFeed) -> List[Dict[str, Any]]:
        """
        Process stops from a single GTFS feed.
        
        Args:
            feed: GTFSFeed object containing the data
            
        Returns:
            List of processed stop dictionaries
        """
        if feed.stops is None:
            logger.warning(f"No stops data for {feed.agency_code}")
            return []
        
        logger.info(f"Processing stops for {feed.agency_code}...")
        
        # Get route info for each stop
        stop_routes = self._get_stop_routes(feed)
        stop_times_data = self._get_stop_times_per_route(feed)
        
        processed_stops = []
        skipped = 0
        
        for _, row in feed.stops.iterrows():
            stop_id = str(row.get("stop_id", "")).strip()
            if not stop_id:
                skipped += 1
                continue
            
            # Get coordinates
            try:
                lat = float(row.get("stop_lat", 0))
                lon = float(row.get("stop_lon", 0))
            except (ValueError, TypeError):
                skipped += 1
                continue
            
            # Validate coordinates
            if not validate_hyderabad_coordinate(lat, lon):
                # Be lenient - just warn but still include
                pass
            
            # Get routes serving this stop
            routes = stop_routes.get(stop_id, [])
            
            # Skip stops with no routes for Metro (HMRL)
            # These are typically exit markers, not actual stations
            if not routes and feed.agency_code == "HMRL":
                skipped += 1
                continue
            
            # Prefix the stop_id for uniqueness
            prefixed_stop_id = prefix_id(feed.agency_code, stop_id)
            
            # Get time data
            times_by_route = stop_times_data.get(stop_id, {})
            first_time, last_time = self._get_first_last_times(times_by_route)
            
            # Build prefixed route list
            prefixed_routes = [prefix_id(feed.agency_code, r) for r in routes]
            
            # Store stop-to-routes mapping
            self.stop_to_routes[prefixed_stop_id] = prefixed_routes
            
            # Store times per route
            for route_id, times in times_by_route.items():
                prefixed_route = prefix_id(feed.agency_code, route_id)
                self.stop_route_times[prefixed_stop_id][prefixed_route] = times
            
            stop_data = {
                "stop_id": prefixed_stop_id,
                "original_id": stop_id,
                "name": clean_stop_name(row.get("stop_name", "")),
                "lat": round_coordinate(lat),
                "lon": round_coordinate(lon),
                "agency": feed.agency_code,
                "transit_type": feed.transit_type,
                "routes": prefixed_routes,
                "first_time": first_time,
                "last_time": last_time,
                "route_count": len(routes),
            }
            
            # Add optional fields if available
            if "stop_code" in row and row["stop_code"]:
                stop_data["stop_code"] = str(row["stop_code"])
            
            if "platform_code" in row and row["platform_code"]:
                stop_data["platform_code"] = str(row["platform_code"])
            
            if "stop_desc" in row and row["stop_desc"]:
                stop_data["description"] = str(row["stop_desc"])
            
            processed_stops.append(stop_data)
        
        logger.info(f"  Processed {len(processed_stops)} stops, skipped {skipped}")
        self.all_stops.extend(processed_stops)
        
        return processed_stops
    
    def _get_stop_routes(self, feed: GTFSFeed) -> Dict[str, List[str]]:
        """
        Get the list of routes serving each stop.
        
        This joins stop_times -> trips -> routes to find all routes
        that have trips stopping at each stop.
        """
        if feed.stop_times is None or feed.trips is None:
            return {}
        
        stop_routes: Dict[str, Set[str]] = defaultdict(set)
        
        # Create trip_id -> route_id mapping
        trip_to_route = dict(zip(feed.trips["trip_id"], feed.trips["route_id"]))
        
        # For each stop in stop_times, find the route
        for _, row in feed.stop_times.iterrows():
            stop_id = str(row.get("stop_id", "")).strip()
            trip_id = str(row.get("trip_id", "")).strip()
            
            if stop_id and trip_id:
                route_id = trip_to_route.get(trip_id)
                if route_id:
                    stop_routes[stop_id].add(route_id)
        
        # Convert sets to sorted lists
        return {stop: sorted(routes) for stop, routes in stop_routes.items()}
    
    def _get_stop_times_per_route(self, feed: GTFSFeed) -> Dict[str, Dict[str, List[str]]]:
        """
        Get arrival times for each stop grouped by route.
        
        Returns:
            Dict[stop_id, Dict[route_id, List[arrival_times]]]
        """
        if feed.stop_times is None or feed.trips is None:
            return {}
        
        result: Dict[str, Dict[str, List[str]]] = defaultdict(lambda: defaultdict(list))
        
        # Create trip_id -> route_id mapping
        trip_to_route = dict(zip(feed.trips["trip_id"], feed.trips["route_id"]))
        
        for _, row in feed.stop_times.iterrows():
            stop_id = str(row.get("stop_id", "")).strip()
            trip_id = str(row.get("trip_id", "")).strip()
            arrival_time = str(row.get("arrival_time", "")).strip()
            
            if stop_id and trip_id and arrival_time:
                route_id = trip_to_route.get(trip_id)
                if route_id:
                    normalized_time = normalize_time(arrival_time)
                    if normalized_time:
                        result[stop_id][route_id].append(normalized_time)
        
        # Sort and deduplicate times
        for stop_id in result:
            for route_id in result[stop_id]:
                times = result[stop_id][route_id]
                result[stop_id][route_id] = sorted(set(times))
        
        return result
    
    def _get_first_last_times(self, times_by_route: Dict[str, List[str]]) -> tuple:
        """
        Get the earliest and latest times across all routes for a stop.
        """
        all_times = []
        for times in times_by_route.values():
            all_times.extend(times)
        
        if not all_times:
            return ("", "")
        
        # Sort by time value
        sorted_times = sorted(all_times, key=lambda t: time_to_minutes(t))
        return (sorted_times[0], sorted_times[-1])
    
    def process_all_feeds(self, feeds: Dict[str, GTFSFeed]) -> List[Dict[str, Any]]:
        """
        Process stops from all feeds.
        
        Args:
            feeds: Dictionary of GTFSFeed objects
            
        Returns:
            Combined list of all processed stops
        """
        self.all_stops = []
        self.stop_to_routes = defaultdict(list)
        self.stop_route_times = defaultdict(lambda: defaultdict(list))
        
        for agency_code, feed in feeds.items():
            self.process_feed(feed)
        
        logger.info(f"Total stops processed: {len(self.all_stops)}")
        return self.all_stops
    
    def get_stop_to_routes_map(self) -> Dict[str, List[str]]:
        """Get the stop-to-routes lookup dictionary."""
        return dict(self.stop_to_routes)
    
    def get_stop_route_times(self) -> Dict[str, Dict[str, List[str]]]:
        """Get the stop-route times dictionary for timetable generation."""
        # Convert defaultdict to regular dict
        return {stop: dict(routes) for stop, routes in self.stop_route_times.items()}
