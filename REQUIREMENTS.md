# Hyderabad Interactive Transit Visualization - Requirements Document

## Project Overview

A static, precomputed interactive visualization of Hyderabad's public transit system covering:
- **HMRL** - Hyderabad Metro Rail (3 lines: Red, Blue, Green)
- **MMTS** - Multi-Modal Transport System (Suburban Rail)
- **TGSRTC** - Telangana State Road Transport Corporation (City Buses)

## Goals

1. **Zero server-side computation** - All data precomputed as JSON/GeoJSON
2. **Fast client-side rendering** - Optimized for Leaflet.js visualization
3. **Interactive exploration** - Select stops, routes, and view connections
4. **Unified view** - All three transit systems on a single map

---

## Data Sources

| Source | Type | Files Available | Last Updated |
|--------|------|-----------------|--------------|
| HMRL | Metro Rail | agency, calendar, fare_attributes, fare_rules, routes, shapes, stop_times, stops, trips | Jan 2026 |
| MMTS | Suburban Rail | agency, calendar, routes, stop_times, stops, trips | Feb 2023 |
| TGSRTC | City Bus | agency, calendar, routes, stop_times, stops, trips | Dec 2025 |

### GTFS Files Structure (per spec)

| File | Required | Description |
|------|----------|-------------|
| `agency.txt` | ✅ | Transit agency info |
| `stops.txt` | ✅ | Stop locations (lat/lng, name, id) |
| `routes.txt` | ✅ | Route definitions (id, name, type, color) |
| `trips.txt` | ✅ | Individual trips per route |
| `stop_times.txt` | ✅ | Arrival/departure times per stop per trip |
| `calendar.txt` | Conditional | Weekly service schedule |
| `calendar_dates.txt` | Conditional | Service exceptions |
| `shapes.txt` | Optional | Route geometry for map display |
| `fare_attributes.txt` | Optional | Fare information |
| `fare_rules.txt` | Optional | Fare rules per route |
| `transfers.txt` | Optional | Transfer rules between stops |
| `frequencies.txt` | Optional | Headway-based schedules |

---

## Functional Requirements

### MVP Features

#### F1: Stop Information Panel
- Click on any stop marker to see:
  - Stop name and ID
  - List of all routes serving this stop
  - Color-coded by transit type (Metro/MMTS/Bus)
  - First and last service time for each route
  - Optional: Service frequency per hour

#### F2: Route Visualization
- Select a route from dropdown/list to:
  - Highlight the route path on map (GeoJSON LineString)
  - Show all stops on that route in sequence
  - Display route metadata (name, type, color, agency)
  - Show terminus stations

#### F3: Filter by Transit Type
- Toggle visibility of:
  - Metro Rail (HMRL) - typically shown in red/blue/green by line
  - Suburban Rail (MMTS) - distinct color
  - City Bus (TGSRTC) - distinct color/icon

#### F4: Search Functionality
- Search stops by name
- Search routes by number/name
- Autocomplete suggestions

### Optional Features (Post-MVP)

#### F5: Isochrones (Walking Distance)
- 10-minute walking radius from selected stop
- Precomputed polygons using Geoapify API
- Toggle isochrone layer on/off

#### F6: Timetable View
- Full schedule for a selected stop/route combination
- Grouped by day type (weekday/weekend)

---

## Non-Functional Requirements

### Performance
- Initial page load < 3 seconds (excluding map tiles)
- GeoJSON files < 2MB each (gzipped)
- Coordinate precision: 5 decimal places (≈1.1m accuracy)

### Compatibility
- Modern browsers (Chrome, Firefox, Safari, Edge)
- Mobile responsive design
- Works offline after initial load (PWA optional)

### Hosting
- Static site deployable on Vercel/Netlify
- No backend server required
- All data fetched as static JSON/GeoJSON

---

## Technical Architecture

```
interactive-transit/
├── data/                          # Raw GTFS zip files (input)
│   ├── Telangana_opendata_gtfs_hmrl_*.zip
│   ├── Telangana_opendata_gtfs_TGSRTC_*.zip
│   └── Open_Data_MMTS_Hyd.zip
│
├── scripts/                       # Python preprocessing scripts
│   ├── requirements.txt           # Python dependencies
│   ├── config.py                  # Configuration constants
│   ├── gtfs_parser.py            # GTFS extraction & validation
│   ├── preprocessor.py           # Main preprocessing pipeline
│   ├── stop_processor.py         # Stop data processing
│   ├── route_processor.py        # Route data processing
│   ├── timetable_processor.py    # Schedule processing
│   └── utils.py                  # Helper functions
│
├── app/                          # Next.js frontend application
│   ├── public/
│   │   └── data/                 # Precomputed JSON/GeoJSON output
│   │       ├── stops.geojson
│   │       ├── routes.geojson
│   │       ├── stop_to_routes.json
│   │       ├── route_to_stops.json
│   │       ├── timetable.json
│   │       └── metadata.json
│   ├── src/
│   │   ├── app/                  # Next.js app router
│   │   ├── components/           # React components
│   │   └── lib/                  # Utilities
│   ├── package.json
│   └── next.config.js
│
└── README.md
```

---

## Precomputed Output Files Specification

### 1. `stops.geojson`
GeoJSON FeatureCollection of all stops across all feeds.

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
        "routes": ["RED_LINE", "BLUE_LINE"],
        "first_time": "05:30",
        "last_time": "23:00",
        "frequency": { "peak": 5, "offpeak": 10 }
      }
    }
  ]
}
```

### 2. `routes.geojson`
GeoJSON FeatureCollection of route shapes.

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "LineString",
        "coordinates": [[78.475, 17.375], [78.480, 17.380], ...]
      },
      "properties": {
        "route_id": "RED_LINE",
        "route_name": "Red Line",
        "route_type": 1,
        "route_type_name": "metro",
        "agency": "HMRL",
        "color": "#FF0000",
        "text_color": "#FFFFFF",
        "stops": ["STOP_1", "STOP_2", "STOP_3"],
        "stop_count": 27
      }
    }
  ]
}
```

### 3. `stop_to_routes.json`
Lookup map from stop_id to array of route_ids.

```json
{
  "HMRL_MGBS": ["RED_LINE", "BLUE_LINE"],
  "MMTS_SECUNDERABAD": ["MMTS_1", "MMTS_2", "MMTS_3"],
  "TGSRTC_STOP_123": ["BUS_10", "BUS_20", "BUS_30"]
}
```

### 4. `route_to_stops.json`
Lookup map from route_id to ordered array of stops with details.

```json
{
  "RED_LINE": [
    { "stop_id": "STOP_1", "name": "Miyapur", "seq": 1 },
    { "stop_id": "STOP_2", "name": "JNTU", "seq": 2 }
  ]
}
```

### 5. `timetable.json`
Schedule data keyed by stop_id, then route_id.

```json
{
  "HMRL_MGBS": {
    "RED_LINE": {
      "weekday": ["05:30", "05:35", "05:40", ...],
      "weekend": ["06:00", "06:10", "06:20", ...]
    }
  }
}
```

### 6. `metadata.json`
Feed metadata and statistics.

```json
{
  "generated_at": "2026-01-04T12:00:00Z",
  "feeds": {
    "HMRL": {
      "agency_name": "Hyderabad Metro Rail Limited",
      "stop_count": 57,
      "route_count": 3,
      "last_updated": "2026-01-03"
    },
    "MMTS": { ... },
    "TGSRTC": { ... }
  },
  "totals": {
    "stops": 1500,
    "routes": 200
  },
  "transit_types": {
    "0": "tram",
    "1": "metro",
    "2": "rail",
    "3": "bus"
  }
}
```

---

## GTFS Route Types Reference

| Code | Type | Used By |
|------|------|---------|
| 0 | Tram/Light Rail | - |
| 1 | Subway/Metro | HMRL |
| 2 | Rail | MMTS |
| 3 | Bus | TGSRTC |
| 4 | Ferry | - |
| 5 | Cable Car | - |
| 6 | Gondola | - |
| 7 | Funicular | - |

---

## Data Validation Rules

1. **Required Columns Check** - Ensure all GTFS required columns exist
2. **Coordinate Validation** - lat in [-90, 90], lng in [-180, 180]
3. **Time Format** - Normalize to HH:MM:SS (handle times > 24:00:00)
4. **Missing Shapes Fallback** - Generate route shapes from stop sequences if shapes.txt missing
5. **Duplicate Detection** - Remove duplicate stops/routes
6. **ID Prefixing** - Prefix all IDs with agency code to ensure uniqueness

---

## UI/UX Requirements

### Map Styling
- Base map: CARTO light/dark tiles
- Metro lines: Thick colored lines (3-4px)
- MMTS lines: Medium dashed lines (2-3px)
- Bus routes: Thin lines (1-2px), shown on zoom

### Stop Markers
- Metro: Circle markers with line color
- MMTS: Train icon markers
- Bus: Small circle markers (clustered when zoomed out)

### Interactions
- Click stop: Open info popup with routes
- Click route in list: Highlight on map
- Hover route on map: Show route name tooltip

### Responsive Design
- Desktop: Side panel + map
- Mobile: Bottom sheet + map
- Collapsible route list

---

## Dependencies

### Python (Preprocessing)
- `pandas` - Data manipulation
- `gtfs-kit` or `partridge` - GTFS parsing
- `shapely` - Geometry operations
- `geojson` - GeoJSON output

### JavaScript (Frontend)
- `next` - React framework
- `react-leaflet` - Leaflet React bindings
- `leaflet` - Map library
- `leaflet.markercluster` - Marker clustering

---

## Timezone

All times normalized to **IST (Asia/Kolkata, UTC+5:30)** in 24-hour format.

---

## Success Criteria

1. ✅ All three GTFS feeds parsed and validated
2. ✅ Precomputed JSON files < 5MB total (uncompressed)
3. ✅ Map loads and displays all stops within 2 seconds
4. ✅ Stop selection shows correct routes
5. ✅ Route selection highlights correct path
6. ✅ Filter toggles work correctly
7. ✅ Deployable to Vercel as static site
