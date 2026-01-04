"""
Hyderabad Transit Preprocessor - Main Entry Point

This script processes GTFS data from Hyderabad's three transit systems
(HMRL, MMTS, TGSRTC) and generates optimized JSON/GeoJSON files for
frontend visualization.

Usage:
    python main.py
    python main.py --input ../data --output ../app/public/data
    python main.py --pretty  # Also generate human-readable versions
"""
import argparse
import sys
from pathlib import Path
from typing import Dict, Any
import logging

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))

from config import DATA_DIR, OUTPUT_DIR, FEEDS, setup_logging
from gtfs_extractor import GTFSExtractor
from gtfs_validator import validate_all_feeds
from stop_processor import StopProcessor
from route_processor import RouteProcessor
from timetable_processor import TimetableProcessor
from output_generator import OutputGenerator, generate_pretty_json
from output_validator import OutputValidator


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Process GTFS data for Hyderabad transit visualization"
    )
    parser.add_argument(
        "--input", "-i",
        type=Path,
        default=DATA_DIR,
        help="Input directory containing GTFS zip files"
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=OUTPUT_DIR,
        help="Output directory for generated JSON/GeoJSON files"
    )
    parser.add_argument(
        "--pretty", "-p",
        action="store_true",
        help="Also generate human-readable pretty-printed JSON files"
    )
    parser.add_argument(
        "--skip-validation",
        action="store_true",
        help="Skip GTFS validation step"
    )
    parser.add_argument(
        "--feeds",
        nargs="+",
        choices=list(FEEDS.keys()),
        help="Process only specific feeds (default: all)"
    )
    
    return parser.parse_args()


def main():
    """Main processing pipeline."""
    args = parse_args()
    logger = setup_logging()
    
    logger.info("=" * 60)
    logger.info("Hyderabad Transit Preprocessor")
    logger.info("=" * 60)
    logger.info(f"Input directory: {args.input}")
    logger.info(f"Output directory: {args.output}")
    
    # Ensure output directory exists
    args.output.mkdir(parents=True, exist_ok=True)
    
    # =========================================================================
    # Step 1: Extract GTFS data
    # =========================================================================
    logger.info("\n[1/6] Extracting GTFS data...")
    
    extractor = GTFSExtractor(data_dir=args.input)
    
    try:
        feeds = extractor.extract_all()
    except Exception as e:
        logger.error(f"Failed to extract GTFS data: {e}")
        return 1
    finally:
        extractor.cleanup()
    
    if not feeds:
        logger.error("No GTFS feeds were extracted successfully")
        return 1
    
    # Filter feeds if requested
    if args.feeds:
        feeds = {k: v for k, v in feeds.items() if k in args.feeds}
        logger.info(f"Processing selected feeds: {', '.join(feeds.keys())}")
    
    # =========================================================================
    # Step 2: Validate GTFS data
    # =========================================================================
    if not args.skip_validation:
        logger.info("\n[2/6] Validating GTFS data...")
        validation_results = validate_all_feeds(feeds)
        
        # Check for fatal errors
        failed_feeds = [code for code, (valid, _, _) in validation_results.items() if not valid]
        
        if failed_feeds:
            logger.warning(f"Validation failed for: {', '.join(failed_feeds)}")
            logger.warning("Continuing with available data...")
    else:
        logger.info("\n[2/6] Skipping validation...")
    
    # =========================================================================
    # Step 3: Process stops
    # =========================================================================
    logger.info("\n[3/6] Processing stops...")
    
    stop_processor = StopProcessor()
    stops = stop_processor.process_all_feeds(feeds)
    
    if not stops:
        logger.error("No stops were processed")
        return 1
    
    stop_to_routes = stop_processor.get_stop_to_routes_map()
    
    # =========================================================================
    # Step 4: Process routes
    # =========================================================================
    logger.info("\n[4/6] Processing routes...")
    
    route_processor = RouteProcessor()
    routes = route_processor.process_all_feeds(feeds)
    
    if not routes:
        logger.warning("No routes were processed")
    
    route_to_stops = route_processor.get_route_to_stops_map()
    
    # =========================================================================
    # Step 5: Process timetable
    # =========================================================================
    logger.info("\n[5/7] Processing timetable...")
    
    timetable_processor = TimetableProcessor()
    timetable = timetable_processor.process_all_feeds(feeds)
    
    # =========================================================================
    # Step 6: Generate output files
    # =========================================================================
    logger.info("\n[6/7] Generating output files...")
    
    # Gather feed info for metadata
    feeds_info: Dict[str, Any] = {}
    for agency_code, feed in feeds.items():
        feeds_info[agency_code] = {
            "files_available": feed.available_files,
            "has_shapes": feed.shapes is not None and len(feed.shapes) > 0,
        }
        if feed.agency is not None and len(feed.agency) > 0:
            agency_row = feed.agency.iloc[0]
            if "agency_name" in agency_row:
                feeds_info[agency_code]["agency_name"] = str(agency_row["agency_name"])
    
    output_generator = OutputGenerator(output_dir=args.output)
    outputs = output_generator.generate_all(
        stops=stops,
        routes=routes,
        stop_to_routes=stop_to_routes,
        route_to_stops=route_to_stops,
        timetable=timetable,
        feeds_info=feeds_info
    )
    
    # Generate pretty versions if requested
    if args.pretty:
        logger.info("\nGenerating pretty-printed JSON files...")
        generate_pretty_json(args.output)
    
    # =========================================================================
    # Step 7: Validate output files
    # =========================================================================
    logger.info("\n[7/7] Validating output files...")
    
    validator = OutputValidator(output_dir=args.output)
    all_valid, validation_results = validator.validate_all()
    
    if not all_valid:
        logger.warning("Some output files have validation issues - check warnings above")
    
    # =========================================================================
    # Summary
    # =========================================================================
    logger.info("\n" + "=" * 60)
    logger.info("Processing complete!")
    logger.info("=" * 60)
    logger.info(f"Total stops: {len(stops)}")
    logger.info(f"Total routes: {len(routes)}")
    logger.info(f"Output files generated in: {args.output}")
    logger.info("")
    logger.info("Files generated:")
    for name, path in outputs.items():
        size_kb = path.stat().st_size / 1024
        logger.info(f"  - {path.name}: {size_kb:.1f} KB")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
