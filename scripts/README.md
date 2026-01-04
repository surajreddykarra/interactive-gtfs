# Hyderabad Transit Preprocessor

This directory contains Python scripts for preprocessing GTFS data from Hyderabad's transit systems.

## Overview

The preprocessor extracts data from GTFS zip files for:
- **HMRL** - Hyderabad Metro Rail Limited (Metro)
- **MMTS** - Multi-Modal Transport System (Suburban Rail)
- **TGSRTC** - Telangana State Road Transport Corporation (Bus)

It generates optimized JSON/GeoJSON files for use in a Leaflet.js-based visualization frontend.

## Setup

### Requirements
- Python 3.9+
- pip

### Installation

```bash
cd scripts
pip install -r requirements.txt
```

## Usage

### Basic Usage

Process all GTFS feeds in the default data directory:

```bash
python main.py
```

### Custom Input/Output Directories

```bash
python main.py --input ../data --output ../app/public/data
```

### Generate Human-Readable Output

For debugging, generate pretty-printed JSON files:

```bash
python main.py --pretty
```

### Process Specific Feeds Only

```bash
python main.py --feeds HMRL MMTS
```

### Skip Validation

```bash
python main.py --skip-validation
```

## Output Files

The preprocessor generates the following files in the output directory:

| File | Description |
|------|-------------|
| `stops.geojson` | GeoJSON FeatureCollection of all transit stops |
| `routes.geojson` | GeoJSON FeatureCollection of route shapes |
| `stop_to_routes.json` | Lookup: stop_id → [route_id, ...] |
| `route_to_stops.json` | Lookup: route_id → [{stop_id, name, seq}, ...] |
| `timetable.json` | Schedule data: stop_id → route_id → {weekday, weekend} |
| `metadata.json` | Statistics and configuration for the frontend |

## Data Format

### stops.geojson

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Point",
        "coordinates": [78.47538, 17.37534]
      },
      "properties": {
        "stop_id": "HMRL_MGBS",
        "name": "MGBS Metro Station",
        "agency": "HMRL",
        "transit_type": "metro",
        "routes": ["HMRL_RED", "HMRL_BLUE"],
        "first_time": "05:30",
        "last_time": "23:00"
      }
    }
  ]
}
```

### routes.geojson

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "LineString",
        "coordinates": [[78.475, 17.375], ...]
      },
      "properties": {
        "route_id": "HMRL_RED",
        "name": "Red Line",
        "type": 1,
        "type_name": "metro",
        "agency": "HMRL",
        "color": "#FF0000",
        "stops": ["HMRL_MIYAPUR", "HMRL_JNTU", ...]
      }
    }
  ]
}
```

## File Structure

```
scripts/
├── main.py              # Entry point and CLI
├── config.py            # Configuration constants
├── gtfs_extractor.py    # Extracts GTFS from zip files
├── gtfs_validator.py    # Validates GTFS data
├── stop_processor.py    # Processes stop data
├── route_processor.py   # Processes route data and geometries
├── timetable_processor.py  # Processes schedule data
├── output_generator.py  # Generates JSON/GeoJSON output
├── utils.py             # Utility functions
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## GTFS Reference

### Route Types
| Code | Type |
|------|------|
| 0 | Tram |
| 1 | Metro |
| 2 | Rail |
| 3 | Bus |

### ID Prefixing
All IDs are prefixed with agency code to ensure uniqueness:
- `HMRL_` for Metro
- `MMTS_` for Suburban Rail
- `TGSRTC_` for Bus

### Time Format
- All times normalized to 24-hour format (HH:MM)
- Times > 24:00:00 in GTFS are wrapped to standard time
- Timezone: Asia/Kolkata (IST)

## Troubleshooting

### Missing shapes.txt
Some feeds may not include `shapes.txt`. In this case, route geometries are generated from stop coordinates.

### Encoding Issues
The extractor tries multiple encodings (UTF-8, UTF-8-BOM, Latin-1, CP1252) to handle various file formats.

### Validation Warnings
Warnings are logged but don't stop processing. Review the output for any data quality issues.

## License

Open Government License - India (based on GTFS data sources)
