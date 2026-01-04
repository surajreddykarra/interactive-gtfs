"""
Output Validator - Validates the format of generated JSON/GeoJSON files.

This validates the structure and schema of output files without verifying
the actual data correctness.
"""
import json
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
import logging

from config import OUTPUT_DIR, OUTPUT_FILES

logger = logging.getLogger("transit_preprocessor")


class ValidationResult:
    """Container for validation results."""
    
    def __init__(self, file_name: str):
        self.file_name = file_name
        self.valid = True
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.stats: Dict[str, Any] = {}
    
    def add_error(self, message: str):
        self.valid = False
        self.errors.append(message)
    
    def add_warning(self, message: str):
        self.warnings.append(message)
    
    def __repr__(self):
        status = "✓ VALID" if self.valid else "✗ INVALID"
        return f"{self.file_name}: {status}"


class OutputValidator:
    """Validates the format of generated output files."""
    
    def __init__(self, output_dir: Path = OUTPUT_DIR):
        self.output_dir = Path(output_dir)
        self.results: Dict[str, ValidationResult] = {}
    
    def validate_all(self) -> Tuple[bool, Dict[str, ValidationResult]]:
        """
        Validate all output files.
        
        Returns:
            Tuple of (all_valid, results_dict)
        """
        logger.info("Validating output files...")
        
        # Validate each expected file
        self.results["stops.geojson"] = self.validate_stops_geojson()
        self.results["routes.geojson"] = self.validate_routes_geojson()
        self.results["stop_to_routes.json"] = self.validate_stop_to_routes()
        self.results["route_to_stops.json"] = self.validate_route_to_stops()
        self.results["timetable.json"] = self.validate_timetable()
        self.results["metadata.json"] = self.validate_metadata()
        
        all_valid = all(r.valid for r in self.results.values())
        
        # Log summary
        self._log_summary()
        
        return all_valid, self.results
    
    def _load_json(self, filename: str) -> Tuple[Optional[Any], Optional[str]]:
        """Load and parse a JSON file."""
        file_path = self.output_dir / filename
        
        if not file_path.exists():
            return None, f"File not found: {filename}"
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data, None
        except json.JSONDecodeError as e:
            return None, f"Invalid JSON: {e}"
        except Exception as e:
            return None, f"Error reading file: {e}"
    
    def validate_stops_geojson(self) -> ValidationResult:
        """Validate stops.geojson format."""
        result = ValidationResult("stops.geojson")
        
        data, error = self._load_json("stops.geojson")
        if error:
            result.add_error(error)
            return result
        
        # Check GeoJSON structure
        if not isinstance(data, dict):
            result.add_error("Root must be an object")
            return result
        
        if data.get("type") != "FeatureCollection":
            result.add_error("type must be 'FeatureCollection'")
        
        features = data.get("features")
        if not isinstance(features, list):
            result.add_error("features must be an array")
            return result
        
        result.stats["feature_count"] = len(features)
        
        # Validate each feature (sample first 100)
        required_props = ["stop_id", "name", "agency", "transit_type", "routes"]
        
        for i, feature in enumerate(features[:100]):
            prefix = f"Feature[{i}]"
            
            if not isinstance(feature, dict):
                result.add_error(f"{prefix}: must be an object")
                continue
            
            if feature.get("type") != "Feature":
                result.add_error(f"{prefix}: type must be 'Feature'")
            
            # Validate geometry
            geom = feature.get("geometry")
            if not isinstance(geom, dict):
                result.add_error(f"{prefix}: geometry must be an object")
            elif geom.get("type") != "Point":
                result.add_error(f"{prefix}: geometry.type must be 'Point'")
            elif not isinstance(geom.get("coordinates"), list) or len(geom.get("coordinates", [])) != 2:
                result.add_error(f"{prefix}: geometry.coordinates must be [lon, lat]")
            else:
                coords = geom["coordinates"]
                if not all(isinstance(c, (int, float)) for c in coords):
                    result.add_error(f"{prefix}: coordinates must be numbers")
                elif not (-180 <= coords[0] <= 180 and -90 <= coords[1] <= 90):
                    result.add_warning(f"{prefix}: coordinates out of valid range")
            
            # Validate properties
            props = feature.get("properties")
            if not isinstance(props, dict):
                result.add_error(f"{prefix}: properties must be an object")
                continue
            
            for prop in required_props:
                if prop not in props:
                    result.add_error(f"{prefix}: missing required property '{prop}'")
            
            # Validate property types
            if "routes" in props and not isinstance(props["routes"], list):
                result.add_error(f"{prefix}: routes must be an array")
            
            if "transit_type" in props and props["transit_type"] not in ["metro", "rail", "bus"]:
                result.add_warning(f"{prefix}: unexpected transit_type '{props['transit_type']}'")
        
        if len(features) > 100:
            result.warnings.append(f"Only validated first 100 of {len(features)} features")
        
        return result
    
    def validate_routes_geojson(self) -> ValidationResult:
        """Validate routes.geojson format."""
        result = ValidationResult("routes.geojson")
        
        data, error = self._load_json("routes.geojson")
        if error:
            result.add_error(error)
            return result
        
        if not isinstance(data, dict):
            result.add_error("Root must be an object")
            return result
        
        if data.get("type") != "FeatureCollection":
            result.add_error("type must be 'FeatureCollection'")
        
        features = data.get("features")
        if not isinstance(features, list):
            result.add_error("features must be an array")
            return result
        
        result.stats["feature_count"] = len(features)
        
        required_props = ["route_id", "name", "type", "agency", "color", "stops"]
        
        for i, feature in enumerate(features):
            prefix = f"Feature[{i}]"
            
            if not isinstance(feature, dict):
                result.add_error(f"{prefix}: must be an object")
                continue
            
            if feature.get("type") != "Feature":
                result.add_error(f"{prefix}: type must be 'Feature'")
            
            # Validate geometry
            geom = feature.get("geometry")
            if not isinstance(geom, dict):
                result.add_error(f"{prefix}: geometry must be an object")
            elif geom.get("type") != "LineString":
                result.add_error(f"{prefix}: geometry.type must be 'LineString'")
            elif not isinstance(geom.get("coordinates"), list):
                result.add_error(f"{prefix}: geometry.coordinates must be an array")
            elif len(geom.get("coordinates", [])) < 2:
                result.add_warning(f"{prefix}: LineString has fewer than 2 coordinates")
            
            # Validate properties
            props = feature.get("properties")
            if not isinstance(props, dict):
                result.add_error(f"{prefix}: properties must be an object")
                continue
            
            for prop in required_props:
                if prop not in props:
                    result.add_error(f"{prefix}: missing required property '{prop}'")
            
            if "stops" in props and not isinstance(props["stops"], list):
                result.add_error(f"{prefix}: stops must be an array")
            
            if "color" in props:
                color = props["color"]
                if not isinstance(color, str) or not color.startswith("#"):
                    result.add_warning(f"{prefix}: color should be a hex string")
        
        return result
    
    def validate_stop_to_routes(self) -> ValidationResult:
        """Validate stop_to_routes.json format."""
        result = ValidationResult("stop_to_routes.json")
        
        data, error = self._load_json("stop_to_routes.json")
        if error:
            result.add_error(error)
            return result
        
        if not isinstance(data, dict):
            result.add_error("Root must be an object (stop_id -> route_ids)")
            return result
        
        result.stats["stop_count"] = len(data)
        
        # Validate structure
        for stop_id, routes in list(data.items())[:100]:
            if not isinstance(stop_id, str):
                result.add_error(f"Key must be string, got {type(stop_id)}")
            
            if not isinstance(routes, list):
                result.add_error(f"Value for '{stop_id}' must be an array")
            elif not all(isinstance(r, str) for r in routes):
                result.add_error(f"All route_ids for '{stop_id}' must be strings")
        
        return result
    
    def validate_route_to_stops(self) -> ValidationResult:
        """Validate route_to_stops.json format."""
        result = ValidationResult("route_to_stops.json")
        
        data, error = self._load_json("route_to_stops.json")
        if error:
            result.add_error(error)
            return result
        
        if not isinstance(data, dict):
            result.add_error("Root must be an object (route_id -> stops)")
            return result
        
        result.stats["route_count"] = len(data)
        
        # Validate structure
        for route_id, stops in list(data.items())[:50]:
            if not isinstance(route_id, str):
                result.add_error(f"Key must be string, got {type(route_id)}")
            
            if not isinstance(stops, list):
                result.add_error(f"Value for '{route_id}' must be an array")
                continue
            
            for i, stop in enumerate(stops[:10]):
                if not isinstance(stop, dict):
                    result.add_error(f"'{route_id}'[{i}] must be an object")
                    continue
                
                if "stop_id" not in stop:
                    result.add_error(f"'{route_id}'[{i}] missing 'stop_id'")
                if "name" not in stop:
                    result.add_error(f"'{route_id}'[{i}] missing 'name'")
                if "seq" not in stop:
                    result.add_error(f"'{route_id}'[{i}] missing 'seq'")
        
        return result
    
    def validate_timetable(self) -> ValidationResult:
        """Validate timetable.json format."""
        result = ValidationResult("timetable.json")
        
        data, error = self._load_json("timetable.json")
        if error:
            result.add_error(error)
            return result
        
        if not isinstance(data, dict):
            result.add_error("Root must be an object (stop_id -> route_timetables)")
            return result
        
        result.stats["stop_count"] = len(data)
        
        # Validate structure (sample)
        for stop_id, routes in list(data.items())[:20]:
            if not isinstance(routes, dict):
                result.add_error(f"'{stop_id}' must be an object (route_id -> times)")
                continue
            
            for route_id, times in list(routes.items())[:5]:
                if not isinstance(times, dict):
                    result.add_error(f"'{stop_id}'.'{route_id}' must be an object")
                    continue
                
                # Check for weekday/weekend keys
                if "weekday" not in times and "weekend" not in times:
                    result.add_warning(f"'{stop_id}'.'{route_id}' missing weekday/weekend")
                
                for day_type in ["weekday", "weekend"]:
                    if day_type in times:
                        if not isinstance(times[day_type], list):
                            result.add_error(f"'{stop_id}'.'{route_id}'.{day_type} must be array")
                        elif times[day_type] and not all(isinstance(t, str) for t in times[day_type]):
                            result.add_error(f"'{stop_id}'.'{route_id}'.{day_type} times must be strings")
        
        return result
    
    def validate_metadata(self) -> ValidationResult:
        """Validate metadata.json format."""
        result = ValidationResult("metadata.json")
        
        data, error = self._load_json("metadata.json")
        if error:
            result.add_error(error)
            return result
        
        if not isinstance(data, dict):
            result.add_error("Root must be an object")
            return result
        
        # Check required fields
        required_fields = ["generated_at", "totals", "agencies"]
        for field in required_fields:
            if field not in data:
                result.add_error(f"Missing required field: {field}")
        
        # Validate totals
        if "totals" in data:
            totals = data["totals"]
            if not isinstance(totals, dict):
                result.add_error("totals must be an object")
            else:
                if "stops" not in totals:
                    result.add_error("totals.stops is required")
                if "routes" not in totals:
                    result.add_error("totals.routes is required")
                
                result.stats["total_stops"] = totals.get("stops", 0)
                result.stats["total_routes"] = totals.get("routes", 0)
        
        # Validate agencies
        if "agencies" in data:
            agencies = data["agencies"]
            if not isinstance(agencies, dict):
                result.add_error("agencies must be an object")
            else:
                for agency_code, info in agencies.items():
                    if not isinstance(info, dict):
                        result.add_error(f"agencies.{agency_code} must be an object")
        
        # Validate center coordinates
        if "center" in data:
            center = data["center"]
            if not isinstance(center, list) or len(center) != 2:
                result.add_error("center must be [lat, lon] array")
        
        return result
    
    def _log_summary(self):
        """Log validation summary."""
        total = len(self.results)
        valid = sum(1 for r in self.results.values() if r.valid)
        
        logger.info(f"\nValidation Summary: {valid}/{total} files valid")
        logger.info("-" * 40)
        
        for filename, result in self.results.items():
            status = "✓" if result.valid else "✗"
            logger.info(f"  {status} {filename}")
            
            if result.stats:
                stats_str = ", ".join(f"{k}={v}" for k, v in result.stats.items())
                logger.info(f"      Stats: {stats_str}")
            
            for error in result.errors[:3]:
                logger.error(f"      ERROR: {error}")
            
            if len(result.errors) > 3:
                logger.error(f"      ... and {len(result.errors) - 3} more errors")
            
            for warning in result.warnings[:2]:
                logger.warning(f"      WARN: {warning}")


def validate_output(output_dir: Path = OUTPUT_DIR) -> bool:
    """
    Validate all output files.
    
    Args:
        output_dir: Directory containing output files
        
    Returns:
        True if all files are valid
    """
    validator = OutputValidator(output_dir)
    all_valid, results = validator.validate_all()
    return all_valid


if __name__ == "__main__":
    # Run standalone validation
    import sys
    from config import setup_logging
    
    setup_logging()
    
    output_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else OUTPUT_DIR
    
    if not output_dir.exists():
        logger.error(f"Output directory not found: {output_dir}")
        sys.exit(1)
    
    validator = OutputValidator(output_dir)
    all_valid, results = validator.validate_all()
    
    sys.exit(0 if all_valid else 1)
