"""
Output Generator - Generates the final JSON/GeoJSON output files.
"""
import json
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime
import logging

from config import OUTPUT_DIR, OUTPUT_FILES, HYDERABAD_CENTER, FEEDS

logger = logging.getLogger("transit_preprocessor")


class OutputGenerator:
    """Generates JSON/GeoJSON output files from processed data."""
    
    def __init__(self, output_dir: Path = OUTPUT_DIR):
        self.output_dir = Path(output_dir)
        
    def ensure_output_dir(self):
        """Create output directory if it doesn't exist."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Output directory: {self.output_dir}")
    
    def generate_stops_geojson(self, stops: List[Dict[str, Any]]) -> Path:
        """
        Generate stops.geojson file.
        
        Args:
            stops: List of processed stop dictionaries
            
        Returns:
            Path to the generated file
        """
        features = []
        
        for stop in stops:
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [stop["lon"], stop["lat"]]
                },
                "properties": {
                    "stop_id": stop["stop_id"],
                    "name": stop["name"],
                    "agency": stop["agency"],
                    "transit_type": stop["transit_type"],
                    "routes": stop["routes"],
                    "route_count": stop["route_count"],
                    "first_time": stop.get("first_time", ""),
                    "last_time": stop.get("last_time", ""),
                }
            }
            
            # Add optional fields
            if "stop_code" in stop:
                feature["properties"]["stop_code"] = stop["stop_code"]
            if "platform_code" in stop:
                feature["properties"]["platform_code"] = stop["platform_code"]
            if "description" in stop:
                feature["properties"]["description"] = stop["description"]
            
            features.append(feature)
        
        geojson = {
            "type": "FeatureCollection",
            "features": features
        }
        
        output_path = self.output_dir / OUTPUT_FILES["stops"]
        self._write_json(output_path, geojson)
        logger.info(f"  Generated {output_path.name} with {len(features)} stops")
        
        return output_path
    
    def generate_routes_geojson(self, routes: List[Dict[str, Any]]) -> Path:
        """
        Generate routes.geojson file.
        
        Args:
            routes: List of processed route dictionaries
            
        Returns:
            Path to the generated file
        """
        features = []
        
        for route in routes:
            if route.get("geometry") is None:
                continue
            
            feature = {
                "type": "Feature",
                "geometry": route["geometry"],
                "properties": {
                    "route_id": route["route_id"],
                    "name": route["name"],
                    "short_name": route.get("short_name", ""),
                    "long_name": route.get("long_name", ""),
                    "type": route["type"],
                    "type_name": route["type_name"],
                    "agency": route["agency"],
                    "color": route["color"],
                    "text_color": route["text_color"],
                    "stops": route["stops"],
                    "stop_count": route["stop_count"],
                }
            }
            
            if "description" in route:
                feature["properties"]["description"] = route["description"]
            
            features.append(feature)
        
        geojson = {
            "type": "FeatureCollection",
            "features": features
        }
        
        output_path = self.output_dir / OUTPUT_FILES["routes"]
        self._write_json(output_path, geojson)
        logger.info(f"  Generated {output_path.name} with {len(features)} routes")
        
        return output_path
    
    def generate_stop_to_routes(self, stop_to_routes: Dict[str, List[str]]) -> Path:
        """
        Generate stop_to_routes.json lookup file.
        
        Args:
            stop_to_routes: Dictionary mapping stop_id to list of route_ids
            
        Returns:
            Path to the generated file
        """
        output_path = self.output_dir / OUTPUT_FILES["stop_to_routes"]
        self._write_json(output_path, stop_to_routes)
        logger.info(f"  Generated {output_path.name} with {len(stop_to_routes)} entries")
        
        return output_path
    
    def generate_route_to_stops(self, route_to_stops: Dict[str, List[Dict[str, Any]]]) -> Path:
        """
        Generate route_to_stops.json lookup file.
        
        Args:
            route_to_stops: Dictionary mapping route_id to list of stop info dicts
            
        Returns:
            Path to the generated file
        """
        output_path = self.output_dir / OUTPUT_FILES["route_to_stops"]
        self._write_json(output_path, route_to_stops)
        logger.info(f"  Generated {output_path.name} with {len(route_to_stops)} entries")
        
        return output_path
    
    def generate_timetable(self, timetable: Dict[str, Dict[str, Any]]) -> Path:
        """
        Generate timetable.json file.
        
        Args:
            timetable: Timetable dictionary
            
        Returns:
            Path to the generated file
        """
        output_path = self.output_dir / OUTPUT_FILES["timetable"]
        self._write_json(output_path, timetable)
        
        # Count entries
        stop_count = len(timetable)
        route_entries = sum(len(routes) for routes in timetable.values())
        logger.info(f"  Generated {output_path.name} with {stop_count} stops, {route_entries} route entries")
        
        return output_path
    
    def generate_metadata(
        self, 
        stops: List[Dict[str, Any]], 
        routes: List[Dict[str, Any]],
        feeds_info: Dict[str, Any]
    ) -> Path:
        """
        Generate metadata.json file with statistics and info.
        
        Args:
            stops: List of processed stops
            routes: List of processed routes
            feeds_info: Dictionary with feed-specific info
            
        Returns:
            Path to the generated file
        """
        # Calculate statistics per agency
        agency_stats = {}
        for agency_code in FEEDS.keys():
            agency_stops = [s for s in stops if s["agency"] == agency_code]
            agency_routes = [r for r in routes if r["agency"] == agency_code]
            
            agency_stats[agency_code] = {
                "name": FEEDS[agency_code]["name"],
                "transit_type": FEEDS[agency_code]["transit_type"],
                "stop_count": len(agency_stops),
                "route_count": len(agency_routes),
                "color_default": FEEDS[agency_code]["color_default"],
            }
            
            # Add feed-specific info if available
            if agency_code in feeds_info:
                agency_stats[agency_code].update(feeds_info[agency_code])
        
        # Group by transit type
        transit_type_stats = {}
        for transit_type in ["metro", "rail", "bus"]:
            type_stops = [s for s in stops if s["transit_type"] == transit_type]
            type_routes = [r for r in routes if r["type_name"] == transit_type]
            transit_type_stats[transit_type] = {
                "stop_count": len(type_stops),
                "route_count": len(type_routes),
            }
        
        metadata = {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "version": "1.0.0",
            "city": "Hyderabad",
            "center": HYDERABAD_CENTER,
            "default_zoom": 12,
            "totals": {
                "stops": len(stops),
                "routes": len(routes),
            },
            "agencies": agency_stats,
            "transit_types": transit_type_stats,
            "route_type_names": {
                "0": "tram",
                "1": "metro",
                "2": "rail",
                "3": "bus",
            },
            "files": OUTPUT_FILES,
        }
        
        output_path = self.output_dir / OUTPUT_FILES["metadata"]
        self._write_json(output_path, metadata)
        logger.info(f"  Generated {output_path.name}")
        
        return output_path
    
    def _write_json(self, path: Path, data: Any):
        """Write data to a JSON file with minimal formatting."""
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, separators=(',', ':'))
    
    def generate_all(
        self,
        stops: List[Dict[str, Any]],
        routes: List[Dict[str, Any]],
        stop_to_routes: Dict[str, List[str]],
        route_to_stops: Dict[str, List[Dict[str, Any]]],
        timetable: Dict[str, Dict[str, Any]],
        feeds_info: Dict[str, Any] = None
    ) -> Dict[str, Path]:
        """
        Generate all output files.
        
        Args:
            stops: List of processed stops
            routes: List of processed routes
            stop_to_routes: Stop to routes lookup
            route_to_stops: Route to stops lookup
            timetable: Timetable data
            feeds_info: Optional feed-specific metadata
            
        Returns:
            Dictionary mapping output names to file paths
        """
        logger.info("Generating output files...")
        self.ensure_output_dir()
        
        outputs = {
            "stops": self.generate_stops_geojson(stops),
            "routes": self.generate_routes_geojson(routes),
            "stop_to_routes": self.generate_stop_to_routes(stop_to_routes),
            "route_to_stops": self.generate_route_to_stops(route_to_stops),
            "timetable": self.generate_timetable(timetable),
            "metadata": self.generate_metadata(stops, routes, feeds_info or {}),
        }
        
        # Calculate total size
        total_size = sum(p.stat().st_size for p in outputs.values())
        logger.info(f"Total output size: {total_size / 1024:.1f} KB")
        
        return outputs


def generate_pretty_json(output_dir: Path):
    """
    Generate human-readable versions of the JSON files for debugging.
    
    Creates files with .pretty.json extension.
    """
    output_dir = Path(output_dir)
    
    for filename in OUTPUT_FILES.values():
        input_path = output_dir / filename
        if not input_path.exists():
            continue
        
        output_path = output_dir / filename.replace('.json', '.pretty.json').replace('.geojson', '.pretty.geojson')
        
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"  Generated {output_path.name}")
