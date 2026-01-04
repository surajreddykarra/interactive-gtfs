"""
GTFS Extractor - Extracts and loads GTFS data from zip files.
"""
import zipfile
import pandas as pd
from pathlib import Path
from typing import Dict, Optional, List, Any
import shutil
import logging
import gc
import time

from config import DATA_DIR, TEMP_DIR, FEEDS, GTFS_REQUIRED_COLUMNS, GTFS_OPTIONAL_FILES

logger = logging.getLogger("transit_preprocessor")


class GTFSFeed:
    """Container for a single GTFS feed's data."""
    
    def __init__(self, agency_code: str, config: dict):
        self.agency_code = agency_code
        self.config = config
        self.name = config["name"]
        self.transit_type = config["transit_type"]
        self.route_type = config["route_type"]
        self.color_default = config["color_default"]
        
        # DataFrames for each GTFS file
        self.agency: Optional[pd.DataFrame] = None
        self.stops: Optional[pd.DataFrame] = None
        self.routes: Optional[pd.DataFrame] = None
        self.trips: Optional[pd.DataFrame] = None
        self.stop_times: Optional[pd.DataFrame] = None
        self.calendar: Optional[pd.DataFrame] = None
        self.calendar_dates: Optional[pd.DataFrame] = None
        self.shapes: Optional[pd.DataFrame] = None
        self.fare_attributes: Optional[pd.DataFrame] = None
        self.fare_rules: Optional[pd.DataFrame] = None
        self.transfers: Optional[pd.DataFrame] = None
        self.frequencies: Optional[pd.DataFrame] = None
        
        # Metadata
        self.available_files: List[str] = []
        self.zip_path: Optional[Path] = None
        
    def __repr__(self):
        return f"GTFSFeed({self.agency_code}: {len(self.available_files)} files)"


class GTFSExtractor:
    """Extracts and loads GTFS data from zip files."""
    
    def __init__(self, data_dir: Path = DATA_DIR, temp_dir: Path = TEMP_DIR):
        self.data_dir = Path(data_dir)
        self.temp_dir = Path(temp_dir)
        self.feeds: Dict[str, GTFSFeed] = {}
        
    def find_zip_files(self) -> Dict[str, Path]:
        """
        Find GTFS zip files in the data directory.
        
        Returns:
            Dictionary mapping agency codes to zip file paths
        """
        zip_files = {}
        
        if not self.data_dir.exists():
            raise FileNotFoundError(f"Data directory not found: {self.data_dir}")
        
        all_zips = list(self.data_dir.glob("*.zip"))
        logger.info(f"Found {len(all_zips)} zip files in {self.data_dir}")
        
        for agency_code, config in FEEDS.items():
            pattern = config["pattern"].lower()
            
            for zip_path in all_zips:
                if pattern in zip_path.name.lower():
                    zip_files[agency_code] = zip_path
                    logger.info(f"  {agency_code}: {zip_path.name}")
                    break
            else:
                logger.warning(f"  {agency_code}: No matching zip file found")
        
        return zip_files
    
    def extract_feed(self, agency_code: str, zip_path: Path) -> GTFSFeed:
        """
        Extract and load a single GTFS feed from a zip file.
        
        Args:
            agency_code: Agency identifier
            zip_path: Path to the zip file
            
        Returns:
            Loaded GTFSFeed object
        """
        config = FEEDS[agency_code]
        feed = GTFSFeed(agency_code, config)
        feed.zip_path = zip_path
        
        # Create temp extraction directory
        extract_dir = self.temp_dir / agency_code
        extract_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Extracting {agency_code} from {zip_path.name}...")
        
        try:
            # Extract zip
            with zipfile.ZipFile(zip_path, 'r') as zf:
                zf.extractall(extract_dir)
            
            # Find the directory containing GTFS files
            # Some zips have files in root, others in a subdirectory
            gtfs_dir = self._find_gtfs_directory(extract_dir)
            
            if gtfs_dir is None:
                raise FileNotFoundError(f"No GTFS files found in {zip_path.name}")
            
            # Load each GTFS file
            feed.available_files = self._list_gtfs_files(gtfs_dir)
            logger.info(f"  Found files: {', '.join(feed.available_files)}")
            
            # Load required files
            feed.agency = self._load_csv(gtfs_dir / "agency.txt")
            feed.stops = self._load_csv(gtfs_dir / "stops.txt")
            feed.routes = self._load_csv(gtfs_dir / "routes.txt")
            feed.trips = self._load_csv(gtfs_dir / "trips.txt")
            feed.stop_times = self._load_csv(gtfs_dir / "stop_times.txt")
            
            # Load conditional/optional files
            feed.calendar = self._load_csv(gtfs_dir / "calendar.txt")
            feed.calendar_dates = self._load_csv(gtfs_dir / "calendar_dates.txt")
            feed.shapes = self._load_csv(gtfs_dir / "shapes.txt")
            feed.fare_attributes = self._load_csv(gtfs_dir / "fare_attributes.txt")
            feed.fare_rules = self._load_csv(gtfs_dir / "fare_rules.txt")
            feed.transfers = self._load_csv(gtfs_dir / "transfers.txt")
            feed.frequencies = self._load_csv(gtfs_dir / "frequencies.txt")
            
            # Log statistics
            self._log_feed_stats(feed)
            
        finally:
            # Force garbage collection to release file handles
            gc.collect()
            time.sleep(0.1)
            
            # Cleanup temp directory with retry
            if extract_dir.exists():
                for attempt in range(3):
                    try:
                        shutil.rmtree(extract_dir)
                        break
                    except PermissionError:
                        gc.collect()
                        time.sleep(0.2 * (attempt + 1))
        
        return feed
    
    def _find_gtfs_directory(self, extract_dir: Path) -> Optional[Path]:
        """
        Find the directory containing GTFS txt files.
        
        Some zips have files in root, others in a subdirectory.
        """
        # Check root directory
        if (extract_dir / "stops.txt").exists():
            return extract_dir
        
        # Check subdirectories
        for subdir in extract_dir.iterdir():
            if subdir.is_dir():
                if (subdir / "stops.txt").exists():
                    return subdir
                # Check one level deeper
                for subsubdir in subdir.iterdir():
                    if subsubdir.is_dir() and (subsubdir / "stops.txt").exists():
                        return subsubdir
        
        return None
    
    def _list_gtfs_files(self, gtfs_dir: Path) -> List[str]:
        """List all GTFS txt files in a directory."""
        return [f.name for f in gtfs_dir.glob("*.txt")]
    
    def _load_csv(self, file_path: Path) -> Optional[pd.DataFrame]:
        """
        Load a GTFS CSV file with proper handling of encodings.
        
        Args:
            file_path: Path to the CSV file
            
        Returns:
            DataFrame or None if file doesn't exist
        """
        if not file_path.exists():
            return None
        
        # Try different encodings
        encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
        
        for encoding in encodings:
            try:
                df = pd.read_csv(
                    file_path,
                    encoding=encoding,
                    dtype=str,  # Load all as strings initially
                    keep_default_na=False,  # Don't convert empty strings to NaN
                )
                # Clean column names (remove BOM, whitespace)
                df.columns = df.columns.str.strip().str.replace('\ufeff', '')
                return df
            except UnicodeDecodeError:
                continue
            except Exception as e:
                logger.warning(f"Error loading {file_path.name}: {e}")
                continue
        
        logger.error(f"Failed to load {file_path.name} with any encoding")
        return None
    
    def _log_feed_stats(self, feed: GTFSFeed):
        """Log statistics about a loaded feed."""
        stats = []
        if feed.agency is not None:
            stats.append(f"agencies={len(feed.agency)}")
        if feed.stops is not None:
            stats.append(f"stops={len(feed.stops)}")
        if feed.routes is not None:
            stats.append(f"routes={len(feed.routes)}")
        if feed.trips is not None:
            stats.append(f"trips={len(feed.trips)}")
        if feed.stop_times is not None:
            stats.append(f"stop_times={len(feed.stop_times)}")
        if feed.shapes is not None:
            stats.append(f"shape_points={len(feed.shapes)}")
        
        logger.info(f"  Stats: {', '.join(stats)}")
    
    def extract_all(self) -> Dict[str, GTFSFeed]:
        """
        Extract all available GTFS feeds.
        
        Returns:
            Dictionary mapping agency codes to GTFSFeed objects
        """
        zip_files = self.find_zip_files()
        
        for agency_code, zip_path in zip_files.items():
            try:
                self.feeds[agency_code] = self.extract_feed(agency_code, zip_path)
            except Exception as e:
                logger.error(f"Failed to extract {agency_code}: {e}")
        
        logger.info(f"Successfully extracted {len(self.feeds)} feeds")
        return self.feeds
    
    def cleanup(self):
        """Remove temporary extraction directory."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
            logger.info("Cleaned up temporary files")
