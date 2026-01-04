# Hyderabad Transit Visualization - Implementation Plan

## Overview

This document outlines the step-by-step implementation plan for building the interactive transit visualization. The project is divided into two main phases:

1. **Phase 1: Data Preprocessing** (Python)
2. **Phase 2: Frontend Application** (Next.js + Leaflet)

---

## Phase 1: Data Preprocessing (Python)

### Timeline: Steps 1-8

### Step 1: Project Setup
**Duration:** 30 minutes

```
scripts/
├── requirements.txt
├── config.py
├── main.py
└── README.md
```

**Tasks:**
- [x] Create `scripts/` directory
- [x] Create `requirements.txt` with dependencies
- [x] Create `config.py` with paths and constants
- [x] Set up logging configuration

**Dependencies:**
```
pandas>=2.0.0
gtfs-kit>=5.2.0
shapely>=2.0.0
geojson>=3.0.0
pyproj>=3.5.0
```

---

### Step 2: GTFS Extraction
**Duration:** 1 hour

**File:** `scripts/gtfs_extractor.py`

**Tasks:**
- [x] Extract each ZIP file to temporary directory
- [x] Detect available files per feed
- [x] Load CSV files into pandas DataFrames
- [x] Handle encoding issues (UTF-8, Latin-1)

**Input:**
```
data/
├── Telangana_opendata_gtfs_hmrl_*.zip
├── Telangana_opendata_gtfs_TGSRTC_*.zip
└── Open_Data_MMTS_Hyd.zip
```

**Output:** In-memory DataFrames for each feed

---

### Step 3: GTFS Validation
**Duration:** 1 hour

**File:** `scripts/gtfs_validator.py`

**Tasks:**
- [x] Validate required columns exist per GTFS spec
- [x] Check coordinate ranges for stops
- [x] Validate time formats in stop_times
- [x] Log warnings for missing optional files
- [x] Fail gracefully with clear error messages

**Required Columns:**
| File | Required Columns |
|------|-----------------|
| agency.txt | agency_id, agency_name, agency_url, agency_timezone |
| stops.txt | stop_id, stop_name, stop_lat, stop_lon |
| routes.txt | route_id, route_short_name or route_long_name, route_type |
| trips.txt | route_id, service_id, trip_id |
| stop_times.txt | trip_id, arrival_time, departure_time, stop_id, stop_sequence |

---

### Step 4: Stop Processing
**Duration:** 1.5 hours

**File:** `scripts/stop_processor.py`

**Tasks:**
- [x] Parse stops.txt from each feed
- [x] Prefix stop_ids with agency code (HMRL_, MMTS_, TGSRTC_)
- [x] Round coordinates to 5 decimal places
- [x] Calculate routes per stop (join with stop_times → trips → routes)
- [x] Calculate first/last service times per stop per route
- [x] Determine transit type from route_type

**Algorithm for routes-per-stop:**
```python
# Pseudocode
for each stop in stops:
    trips_at_stop = stop_times[stop_times.stop_id == stop.stop_id].trip_id
    routes_at_stop = trips[trips.trip_id.isin(trips_at_stop)].route_id.unique()
    stop.routes = routes_at_stop
```

---

### Step 5: Route Processing
**Duration:** 2 hours

**File:** `scripts/route_processor.py`

**Tasks:**
- [x] Parse routes.txt from each feed
- [x] Prefix route_ids with agency code
- [x] Extract route metadata (name, type, color)
- [x] Build stop sequence for each route from stop_times
- [x] Generate GeoJSON LineString from shapes.txt (if available)
- [x] **Fallback:** If no shapes.txt, create LineString from stop coordinates

**Shape Fallback Algorithm:**
```python
if 'shapes.txt' not in feed:
    # Get representative trip for route
    trip = trips[trips.route_id == route_id].iloc[0]
    
    # Get stops in order
    stop_sequence = stop_times[stop_times.trip_id == trip.trip_id]
    stop_sequence = stop_sequence.sort_values('stop_sequence')
    
    # Build LineString from stop coordinates
    coords = []
    for stop_id in stop_sequence.stop_id:
        stop = stops[stops.stop_id == stop_id]
        coords.append([stop.stop_lon, stop.stop_lat])
    
    route_shape = LineString(coords)
```

---

### Step 6: Timetable Processing
**Duration:** 1.5 hours

**File:** `scripts/timetable_processor.py`

**Tasks:**
- [x] Parse stop_times.txt and calendar.txt
- [x] Normalize times (handle times > 24:00:00 → next day)
- [x] Group by stop_id, route_id, day_type
- [x] Sort times and deduplicate
- [x] Calculate service frequency (trips per hour)

**Time Normalization:**
```python
def normalize_time(gtfs_time):
    """Convert '25:30:00' to '01:30' (next day implied)"""
    h, m, s = map(int, gtfs_time.split(':'))
    h = h % 24  # Wrap around midnight
    return f"{h:02d}:{m:02d}"
```

**Service Days Detection:**
```python
# From calendar.txt
weekday_services = calendar[
    (calendar.monday == 1) | 
    (calendar.tuesday == 1) | 
    ... 
    (calendar.friday == 1)
].service_id

weekend_services = calendar[
    (calendar.saturday == 1) | 
    (calendar.sunday == 1)
].service_id
```

---

### Step 7: GeoJSON Output Generation
**Duration:** 1 hour

**File:** `scripts/output_generator.py`

**Tasks:**
- [x] Generate `stops.geojson` - FeatureCollection of Points
- [x] Generate `routes.geojson` - FeatureCollection of LineStrings
- [x] Generate `stop_to_routes.json` - Lookup dictionary
- [x] Generate `route_to_stops.json` - Lookup dictionary
- [x] Generate `timetable.json` - Nested schedule dictionary
- [x] Generate `metadata.json` - Feed statistics

**Coordinate Precision:**
```python
# 5 decimal places = ~1.1m precision (sufficient for transit)
def round_coords(coords, precision=5):
    return [round(c, precision) for c in coords]
```

---

### Step 8: Main Pipeline & CLI
**Duration:** 1 hour

**File:** `scripts/main.py`

**Tasks:**
- [x] Command-line interface for running preprocessing
- [x] Progress logging
- [x] Error handling and reporting
- [x] Output directory configuration

**Usage:**
```bash
cd scripts
python main.py --input ../data --output ../app/public/data
```

---

## Phase 2: Frontend Application (Next.js)

### Timeline: Steps 9-16

### Step 9: Next.js Project Setup
**Duration:** 30 minutes

**Tasks:**
- [x] Initialize Next.js app with TypeScript
- [x] Configure for static export
- [x] Set up folder structure
- [x] Install dependencies

```bash
npx create-next-app@latest app --typescript --tailwind --app --src-dir
cd app
npm install leaflet react-leaflet @types/leaflet
npm install leaflet.markercluster @types/leaflet.markercluster
```

**Folder Structure:**
```
app/
├── public/
│   └── data/           # Precomputed JSON/GeoJSON
├── src/
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx
│   │   └── globals.css
│   ├── components/
│   │   ├── Map/
│   │   ├── Sidebar/
│   │   └── UI/
│   ├── hooks/
│   ├── lib/
│   │   ├── types.ts
│   │   └── utils.ts
│   └── context/
├── next.config.js
└── package.json
```

---

### Step 10: TypeScript Types & Data Loading
**Duration:** 1 hour

**File:** `src/lib/types.ts`

**Tasks:**
- [x] Define TypeScript interfaces for all data structures
- [x] Create data loading utilities
- [x] Set up context providers for global state

**Types:**
```typescript
interface Stop {
  stop_id: string;
  name: string;
  lat: number;
  lng: number;
  agency: 'HMRL' | 'MMTS' | 'TGSRTC';
  transit_type: 'metro' | 'rail' | 'bus';
  routes: string[];
  first_time: string;
  last_time: string;
}

interface Route {
  route_id: string;
  name: string;
  type: number;
  type_name: string;
  agency: string;
  color: string;
  stops: string[];
  geometry: GeoJSON.LineString;
}
```

---

### Step 11: Base Map Component
**Duration:** 2 hours

**File:** `src/components/Map/BaseMap.tsx`

**Tasks:**
- [x] Set up Leaflet map with React-Leaflet
- [x] Configure CARTO basemap tiles
- [x] Set initial view to Hyderabad center
- [x] Handle SSR issues (dynamic import)
- [x] Add zoom controls

**Map Configuration:**
```typescript
const HYDERABAD_CENTER: [number, number] = [17.385, 78.4867];
const DEFAULT_ZOOM = 12;
const MIN_ZOOM = 10;
const MAX_ZOOM = 18;

// CARTO Light Basemap
const TILE_URL = 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png';
```

---

### Step 12: Stop Layer Component
**Duration:** 2 hours

**File:** `src/components/Map/StopLayer.tsx`

**Tasks:**
- [x] Load stops.geojson
- [x] Render stops as circle markers
- [x] Color-code by transit type
- [x] Implement marker clustering for bus stops
- [x] Add click handler for stop selection
- [x] Show popup with stop info

**Marker Styling:**
```typescript
const STOP_STYLES = {
  metro: { color: '#E91E63', radius: 8, weight: 2 },
  rail: { color: '#2196F3', radius: 7, weight: 2 },
  bus: { color: '#4CAF50', radius: 4, weight: 1 },
};
```

---

### Step 13: Route Layer Component
**Duration:** 2 hours

**File:** `src/components/Map/RouteLayer.tsx`

**Tasks:**
- [x] Load routes.geojson
- [x] Render routes as polylines
- [x] Style by transit type and route color
- [x] Implement route highlight on selection
- [x] Add hover tooltip with route name
- [x] Handle visibility based on filters

**Route Styling:**
```typescript
const ROUTE_STYLES = {
  metro: { weight: 5, opacity: 0.9 },
  rail: { weight: 4, opacity: 0.8, dashArray: '10, 5' },
  bus: { weight: 2, opacity: 0.6 },
};
```

---

### Step 14: Sidebar & Info Panel
**Duration:** 3 hours

**Files:**
- `src/components/Sidebar/Sidebar.tsx`
- `src/components/Sidebar/StopInfo.tsx`
- `src/components/Sidebar/RouteInfo.tsx`
- `src/components/Sidebar/RouteList.tsx`

**Tasks:**
- [x] Create collapsible sidebar layout
- [x] Stop info panel showing routes
- [x] Route info panel showing stops
- [x] Route list grouped by transit type
- [x] Search functionality

**Stop Info Panel Content:**
```
┌─────────────────────────────┐
│ 📍 MGBS Metro Station       │
│ ─────────────────────────── │
│ HMRL Metro                  │
│                             │
│ Routes serving this stop:   │
│  🔴 Red Line (05:30-23:00)  │
│  🔵 Blue Line (05:30-23:00) │
│                             │
│ [View Timetable]            │
└─────────────────────────────┘
```

---

### Step 15: Filter Controls
**Duration:** 1.5 hours

**File:** `src/components/UI/FilterControls.tsx`

**Tasks:**
- [x] Toggle buttons for Metro/MMTS/Bus
- [x] State management with React Context
- [x] Visual feedback for active filters
- [x] Persistence (localStorage)

**UI Design:**
```
┌─────────────────────────────┐
│ 🚇 Metro  🚆 MMTS  🚌 Bus   │
│  [ON]      [ON]     [OFF]   │
└─────────────────────────────┘
```

---

### Step 16: Search Component
**Duration:** 1.5 hours

**File:** `src/components/UI/SearchBox.tsx`

**Tasks:**
- [x] Search input with autocomplete
- [x] Search stops by name
- [x] Search routes by name/number
- [x] Keyboard navigation
- [x] Pan to selected result

---

## Phase 3: Integration & Polish

### Step 17: Connect Data Pipeline to Frontend
**Duration:** 1 hour

**Tasks:**
- [x] Run preprocessing scripts
- [x] Copy output to `app/public/data/`
- [x] Verify data loads correctly
- [x] Test all interactions

---

### Step 18: Responsive Design
**Duration:** 2 hours

**Tasks:**
- [x] Mobile layout (bottom sheet instead of sidebar)
- [x] Touch-friendly interactions
- [x] Breakpoint testing

---

### Step 19: Performance Optimization
**Duration:** 1 hour

**Tasks:**
- [x] Lazy load GeoJSON data
- [x] Implement marker clustering
- [x] Minimize re-renders
- [x] Analyze bundle size

---

### Step 20: Deployment Setup
**Duration:** 30 minutes

**Tasks:**
- [x] Configure `next.config.js` for static export
- [x] Set up Vercel deployment
- [x] Add build scripts to package.json

**next.config.js:**
```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export',
  images: { unoptimized: true },
  basePath: process.env.BASE_PATH || '',
};

module.exports = nextConfig;
```

---

## File Checklist

### Python Scripts (`scripts/`)
- [ ] `requirements.txt`
- [ ] `config.py`
- [ ] `main.py`
- [ ] `gtfs_extractor.py`
- [ ] `gtfs_validator.py`
- [ ] `stop_processor.py`
- [ ] `route_processor.py`
- [ ] `timetable_processor.py`
- [ ] `output_generator.py`
- [ ] `utils.py`
- [ ] `README.md`

### Next.js App (`app/`)
- [ ] `package.json`
- [ ] `next.config.js`
- [ ] `tsconfig.json`
- [ ] `tailwind.config.js`
- [ ] `src/app/layout.tsx`
- [ ] `src/app/page.tsx`
- [ ] `src/app/globals.css`
- [ ] `src/lib/types.ts`
- [ ] `src/lib/utils.ts`
- [ ] `src/lib/dataLoader.ts`
- [ ] `src/context/TransitContext.tsx`
- [ ] `src/components/Map/index.tsx`
- [ ] `src/components/Map/BaseMap.tsx`
- [ ] `src/components/Map/StopLayer.tsx`
- [ ] `src/components/Map/RouteLayer.tsx`
- [ ] `src/components/Sidebar/index.tsx`
- [ ] `src/components/Sidebar/StopInfo.tsx`
- [ ] `src/components/Sidebar/RouteInfo.tsx`
- [ ] `src/components/Sidebar/RouteList.tsx`
- [ ] `src/components/UI/FilterControls.tsx`
- [ ] `src/components/UI/SearchBox.tsx`

### Output Data (`app/public/data/`)
- [ ] `stops.geojson`
- [ ] `routes.geojson`
- [ ] `stop_to_routes.json`
- [ ] `route_to_stops.json`
- [ ] `timetable.json`
- [ ] `metadata.json`

---

## Estimated Total Time

| Phase | Duration |
|-------|----------|
| Phase 1: Preprocessing | ~9 hours |
| Phase 2: Frontend | ~15 hours |
| Phase 3: Polish | ~4.5 hours |
| **Total** | **~28.5 hours** |

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Missing shapes.txt in MMTS/TGSRTC | Generate from stop coordinates |
| Large bus dataset slows rendering | Implement marker clustering, simplify geometries |
| Coordinate precision issues | Validate coordinates during preprocessing |
| Time format inconsistencies | Comprehensive time parsing with fallbacks |
| Mobile performance | Reduce visible markers at low zoom, virtualize lists |

---

## Next Steps

1. **Start with Step 1** - Set up Python preprocessing project
2. **Extract and explore** - Manually examine one GTFS ZIP to understand data quality
3. **Iterative approach** - Process one feed (HMRL) end-to-end first, then add others
4. **Test early** - Generate sample GeoJSON and visualize in simple HTML before full app
