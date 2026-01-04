"""
Route Processor - Processes GTFS route data and generates route geometries.
"""
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict
import logging

from gtfs_extractor import GTFSFeed
from utils import (
    clean_route_name,
    parse_color,
    prefix_id,
    round_coordinates,
    simplify_coordinates
)
from config import ROUTE_TYPE_NAMES, COORDINATE_PRECISION

logger = logging.getLogger("transit_preprocessor")


class RouteProcessor:
    """Processes route data from GTFS feeds."""
    
    def __init__(self):
        self.all_routes: List[Dict[str, Any]] = []
        self.route_to_stops: Dict[str, List[Dict[str, Any]]] = {}
    
    def process_feed(self, feed: GTFSFeed) -> List[Dict[str, Any]]:
        """
        Process routes from a single GTFS feed.
        
        Args:
            feed: GTFSFeed object containing the data
            
        Returns:
            List of processed route dictionaries with geometry
        """
        if feed.routes is None:
            logger.warning(f"No routes data for {feed.agency_code}")
            return []
        
        logger.info(f"Processing routes for {feed.agency_code}...")
        
        # Build shape geometries if available
        shapes = self._build_shapes(feed) if feed.shapes is not None else {}
        
        # Get stop sequences for each route
        route_stops = self._get_route_stop_sequences(feed)
        
        # Pre-compute route to shape mapping (finds first valid shape for each route)
        route_to_shape = self._get_route_to_shape_mapping(feed, shapes)
        
        # Pre-compute stop coordinates lookup
        stop_coords = self._build_stop_coords(feed)
        
        processed_routes = []
        
        for _, row in feed.routes.iterrows():
            route_id = str(row.get("route_id", "")).strip()
            if not route_id:
                continue
            
            # Get route name
            short_name = str(row.get("route_short_name", "")) if pd.notna(row.get("route_short_name")) else ""
            long_name = str(row.get("route_long_name", "")) if pd.notna(row.get("route_long_name")) else ""
            route_name = clean_route_name(short_name, long_name)
            
            # Get route type
            try:
                route_type = int(row.get("route_type", feed.route_type))
            except (ValueError, TypeError):
                route_type = feed.route_type
            
            route_type_name = ROUTE_TYPE_NAMES.get(route_type, feed.transit_type)
            
            # Get route color
            color = parse_color(
                row.get("route_color") if pd.notna(row.get("route_color")) else None,
                feed.color_default
            )
            text_color = parse_color(
                row.get("route_text_color") if pd.notna(row.get("route_text_color")) else None,
                "#FFFFFF"
            )
            
            # Get stops for this route
            stops_data = route_stops.get(route_id, [])
            
            # Get geometry (using pre-computed lookups)
            geometry = self._get_route_geometry(
                route_id, 
                shapes, 
                route_to_shape, 
                stops_data,
                stop_coords
            )
            
            # Prefix IDs
            prefixed_route_id = prefix_id(feed.agency_code, route_id)
            prefixed_stops = [
                {
                    "stop_id": prefix_id(feed.agency_code, s["stop_id"]),
                    "name": s["name"],
                    "seq": s["seq"]
                }
                for s in stops_data
            ]
            
            # Store route-to-stops mapping
            self.route_to_stops[prefixed_route_id] = prefixed_stops
            
            route_data = {
                "route_id": prefixed_route_id,
                "original_id": route_id,
                "name": route_name,
                "short_name": short_name,
                "long_name": long_name,
                "type": route_type,
                "type_name": route_type_name,
                "agency": feed.agency_code,
                "color": color,
                "text_color": text_color,
                "stops": [s["stop_id"] for s in prefixed_stops],
                "stop_count": len(stops_data),
                "geometry": geometry,
            }
            
            # Add optional description
            if pd.notna(row.get("route_desc")):
                route_data["description"] = str(row["route_desc"])
            
            processed_routes.append(route_data)
        
        logger.info(f"  Processed {len(processed_routes)} routes")
        self.all_routes.extend(processed_routes)
        
        return processed_routes
    
    def _build_shapes(self, feed: GTFSFeed) -> Dict[str, List[Tuple[float, float]]]:
        """
        Build shape geometries from shapes.txt.
        
        Returns:
            Dict mapping shape_id to list of (lon, lat) coordinates
        """
        if feed.shapes is None or len(feed.shapes) == 0:
            return {}
        
        logger.info("  Building shapes from shapes.txt...")
        
        shapes: Dict[str, List[Tuple[float, float, int]]] = defaultdict(list)
        
        for _, row in feed.shapes.iterrows():
            shape_id = str(row.get("shape_id", "")).strip()
            if not shape_id:
                continue
            
            try:
                lat = float(row["shape_pt_lat"])
                lon = float(row["shape_pt_lon"])
                seq = int(row.get("shape_pt_sequence", 0))
                shapes[shape_id].append((lon, lat, seq))
            except (ValueError, TypeError, KeyError):
                continue
        
        # Sort by sequence and extract coordinates
        result = {}
        for shape_id, points in shapes.items():
            sorted_points = sorted(points, key=lambda p: p[2])
            result[shape_id] = [(p[0], p[1]) for p in sorted_points]
        
        logger.info(f"  Built {len(result)} shapes")
        return result
    
    def _get_trip_shapes(self, feed: GTFSFeed) -> Dict[str, str]:
        """
        Get mapping from trip_id to shape_id.
        """
        if feed.trips is None:
            return {}
        
        if "shape_id" not in feed.trips.columns:
            return {}
        
        result = {}
        for _, row in feed.trips.iterrows():
            trip_id = str(row.get("trip_id", "")).strip()
            shape_id = str(row.get("shape_id", "")).strip()
            if trip_id and shape_id:
                result[trip_id] = shape_id
        
        return result
    
    def _get_route_to_shape_mapping(self, feed: GTFSFeed, shapes: Dict[str, List[Tuple[float, float]]]) -> Dict[str, str]:
        """
        Pre-compute mapping from route_id to shape_id.
        Finds the first valid shape for each route.
        """
        if feed.trips is None or not shapes:
            return {}
        
        if "shape_id" not in feed.trips.columns:
            return {}
        
        result = {}
        trips_df = feed.trips[["route_id", "shape_id"]].copy()
        trips_df["route_id"] = trips_df["route_id"].astype(str)
        trips_df["shape_id"] = trips_df["shape_id"].astype(str)
        
        # Group by route and get first shape
        for route_id, group in trips_df.groupby("route_id"):
            for shape_id in group["shape_id"]:
                if shape_id and shape_id in shapes:
                    result[route_id] = shape_id
                    break
        
        return result
    
    def _build_stop_coords(self, feed: GTFSFeed) -> Dict[str, Tuple[float, float]]:
        """
        Pre-compute stop coordinates lookup.
        """
        if feed.stops is None:
            return {}
        
        stop_coords = {}
        for _, row in feed.stops.iterrows():
            stop_id = str(row["stop_id"]).strip()
            try:
                lat = float(row["stop_lat"])
                lon = float(row["stop_lon"])
                stop_coords[stop_id] = (lon, lat)
            except (ValueError, TypeError):
                continue
        
        return stop_coords

    def _get_route_stop_sequences(self, feed: GTFSFeed) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get the ordered stop sequence for each route.
        
        Uses stop_times to find the trip with the most stops for each route,
        which typically represents the full route. This is important for metro
        lines where some trips may only cover part of the line.
        """
        if feed.stop_times is None or feed.trips is None or feed.stops is None:
            return {}
        
        # Create lookup maps
        stop_names = dict(zip(feed.stops["stop_id"].astype(str), feed.stops["stop_name"]))
        
        # Build route -> trips mapping efficiently
        trips_df = feed.trips[["route_id", "trip_id"]].copy()
        trips_df["route_id"] = trips_df["route_id"].astype(str)
        trips_df["trip_id"] = trips_df["trip_id"].astype(str)
        
        # Prepare stop_times for efficient lookup
        st_df = feed.stop_times[["trip_id", "stop_id", "stop_sequence"]].copy()
        st_df["trip_id"] = st_df["trip_id"].astype(str)
        st_df["stop_id"] = st_df["stop_id"].astype(str)
        st_df["stop_sequence"] = pd.to_numeric(st_df["stop_sequence"], errors="coerce")
        
        # Count stops per trip to find the trip with the most stops
        trip_stop_counts = st_df.groupby("trip_id").size().reset_index(name="stop_count")
        
        # Join with trips to get route_id
        trips_with_counts = trips_df.merge(trip_stop_counts, on="trip_id")
        
        # Get the trip with the most stops for each route
        idx = trips_with_counts.groupby("route_id")["stop_count"].idxmax()
        best_trips = trips_with_counts.loc[idx]
        route_to_trip = dict(zip(best_trips["route_id"], best_trips["trip_id"]))
        
        # Group stop_times by trip_id for fast lookup
        trip_stops_grouped = st_df.groupby("trip_id")
        
        result: Dict[str, List[Dict[str, Any]]] = {}
        
        for route_id, rep_trip in route_to_trip.items():
            try:
                trip_stops = trip_stops_grouped.get_group(rep_trip)
            except KeyError:
                continue
            
            if len(trip_stops) == 0:
                continue
            
            # Sort by sequence
            trip_stops = trip_stops.sort_values("stop_sequence")
            
            # Build stop list
            stops = []
            for seq, (_, row) in enumerate(trip_stops.iterrows(), 1):
                stop_id = str(row["stop_id"])
                stops.append({
                    "stop_id": stop_id,
                    "name": stop_names.get(stop_id, stop_id),
                    "seq": seq
                })
            
            result[route_id] = stops
        
        return result
    
    def _get_route_geometry(
        self,
        route_id: str,
        shapes: Dict[str, List[Tuple[float, float]]],
        route_to_shape: Dict[str, str],
        stops_data: List[Dict[str, Any]],
        stop_coords: Dict[str, Tuple[float, float]]
    ) -> Optional[Dict[str, Any]]:
        """
        Get the GeoJSON LineString geometry for a route.
        
        First tries to use shapes.txt, then falls back to stop coordinates.
        """
        coordinates = None
        
        # Try to get shape from pre-computed route_to_shape mapping
        if shapes and route_id in route_to_shape:
            shape_id = route_to_shape[route_id]
            if shape_id in shapes:
                coordinates = shapes[shape_id]
        
        # Fallback: generate from stop coordinates
        if coordinates is None:
            coordinates = self._generate_shape_from_stops(stops_data, stop_coords)
        
        if not coordinates or len(coordinates) < 2:
            return None
        
        # Simplify and round coordinates
        if len(coordinates) > 100:
            coordinates = simplify_coordinates(coordinates, tolerance=0.0002)
        
        rounded = round_coordinates(coordinates, COORDINATE_PRECISION)
        
        return {
            "type": "LineString",
            "coordinates": rounded
        }
    
    def _generate_shape_from_stops(
        self, 
        stops_data: List[Dict[str, Any]], 
        stop_coords: Dict[str, Tuple[float, float]]
    ) -> List[Tuple[float, float]]:
        """
        Generate a route shape from stop coordinates when shapes.txt is unavailable.
        """
        if not stops_data:
            return []
        
        # Build coordinate list in stop sequence order
        coordinates = []
        for stop in stops_data:
            stop_id = stop["stop_id"]
            if stop_id in stop_coords:
                coordinates.append(stop_coords[stop_id])
        
        return coordinates
    
    def process_all_feeds(self, feeds: Dict[str, GTFSFeed]) -> List[Dict[str, Any]]:
        """
        Process routes from all feeds.
        
        Args:
            feeds: Dictionary of GTFSFeed objects
            
        Returns:
            Combined list of all processed routes
        """
        self.all_routes = []
        self.route_to_stops = {}
        
        for agency_code, feed in feeds.items():
            self.process_feed(feed)
        
        logger.info(f"Total routes processed: {len(self.all_routes)}")
        return self.all_routes
    
    def get_route_to_stops_map(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get the route-to-stops lookup dictionary."""
        return self.route_to_stops
