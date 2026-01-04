# Hyderabad Interactive Transit Visualization

An interactive map visualization of Hyderabad's public transit system, including Metro Rail (HMRL), Suburban Rail (MMTS), and City Bus (TGSRTC) networks.

![Transit Map Preview](docs/preview.png)

## Features

- 🗺️ **Interactive Map** - Leaflet-based map with smooth pan/zoom
- 🚇 **Multi-Modal Transit** - View Metro, MMTS, and Bus routes together
- 📍 **Stop Information** - Click any stop to see routes and schedules
- 🛤️ **Route Visualization** - Select routes to see their path and stops
- 🔍 **Search** - Find stops and routes by name
- 🎛️ **Filter Controls** - Toggle transit types on/off
- 📱 **Responsive Design** - Works on desktop and mobile

## Architecture

```
interactive-transit/
├── data/                    # Raw GTFS zip files
├── scripts/                 # Python preprocessing pipeline
│   ├── main.py             # Entry point
│   ├── gtfs_extractor.py   # Extract GTFS from zips
│   ├── gtfs_validator.py   # Validate GTFS data
│   ├── stop_processor.py   # Process stop data
│   ├── route_processor.py  # Process route geometries
│   ├── timetable_processor.py  # Process schedules
│   └── output_generator.py # Generate JSON/GeoJSON
└── app/                    # Next.js frontend application
    ├── public/data/        # Preprocessed JSON/GeoJSON
    └── src/
        ├── app/            # Next.js pages
        ├── components/     # React components
        ├── context/        # State management
        └── lib/            # Utilities and types
```

## Quick Start

### Prerequisites

- Python 3.9+
- Node.js 18+
- npm or yarn

### 1. Clone and Setup

```bash
git clone https://github.com/your-username/interactive-transit.git
cd interactive-transit
```

### 2. Download GTFS Data

Download the GTFS zip files from Telangana Open Data and place them in the `data/` folder:

- [HMRL (Metro)](https://hmrl.co.in/open-data/)
- [MMTS (Suburban Rail)](https://forms.gle/wyAsszAVSGyS7CE36)
- [TGSRTC (Bus)](https://www.tgsrtc.telangana.gov.in/open-data/)

### 3. Run Preprocessor

```bash
cd scripts
pip install -r requirements.txt
python main.py --output ../app/public/data
```

This will generate:
- `stops.geojson` - All transit stops
- `routes.geojson` - Route geometries
- `stop_to_routes.json` - Stop-to-route lookup
- `route_to_stops.json` - Route-to-stop lookup
- `timetable.json` - Schedule data
- `metadata.json` - System metadata

### 4. Run Frontend

```bash
cd app
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### 5. Build for Production

```bash
cd app
npm run build
```

The static site will be generated in `app/out/`.

## Deployment

### Vercel (Recommended)

1. Push your code to GitHub
2. Connect your repo to [Vercel](https://vercel.com)
3. Vercel will automatically detect Next.js and deploy

### Other Static Hosts

The app exports as a static site. Deploy the `app/out/` folder to:
- Netlify
- GitHub Pages
- Cloudflare Pages
- Any static file host

## Data Sources

| Source | Type | Provider | Update Frequency |
|--------|------|----------|-----------------|
| HMRL | Metro Rail | Hyderabad Metro Rail Limited | Monthly |
| MMTS | Suburban Rail | South Central Railway | Quarterly |
| TGSRTC | City Bus | Telangana State Road Transport Corp | Monthly |

All data is provided under the [Open Government License - India](https://data.gov.in/sites/default/files/Gazette_Notification_OGDL.pdf).

## Technologies Used

### Frontend
- [Next.js 14](https://nextjs.org/) - React framework
- [React-Leaflet](https://react-leaflet.js.org/) - Leaflet integration
- [Tailwind CSS](https://tailwindcss.com/) - Styling
- [TypeScript](https://www.typescriptlang.org/) - Type safety

### Preprocessing
- [Python](https://python.org/) - Data processing
- [Pandas](https://pandas.pydata.org/) - Data manipulation
- [Shapely](https://shapely.readthedocs.io/) - Geometry operations

### Maps
- [Leaflet.js](https://leafletjs.com/) - Map library
- [CARTO Basemaps](https://carto.com/basemaps/) - Tiles

## Project Structure

### Output Files

| File | Size (approx) | Description |
|------|---------------|-------------|
| `stops.geojson` | ~200KB | All stop locations and metadata |
| `routes.geojson` | ~500KB | Route geometries and properties |
| `stop_to_routes.json` | ~50KB | Stop ID → Route IDs mapping |
| `route_to_stops.json` | ~100KB | Route ID → Stop sequence |
| `timetable.json` | ~1MB | Full schedule data |
| `metadata.json` | ~5KB | System statistics |

### Component Structure

```
components/
├── Map/
│   ├── index.tsx          # Main map container
│   ├── StopLayer.tsx      # Stop markers
│   ├── RouteLayer.tsx     # Route polylines
│   └── MarkerClusterGroup.tsx  # Clustering for bus stops
├── Sidebar/
│   ├── index.tsx          # Sidebar container
│   ├── StopInfo.tsx       # Stop details panel
│   ├── RouteInfo.tsx      # Route details panel
│   └── RouteList.tsx      # Route listing
└── UI/
    ├── FilterControls.tsx # Transit type toggles
    └── SearchBox.tsx      # Search autocomplete
```

## Configuration

### Preprocessing Options

```bash
python main.py --help
```

| Option | Description |
|--------|-------------|
| `--input` | Input directory with GTFS zips |
| `--output` | Output directory for JSON files |
| `--pretty` | Generate human-readable JSON |
| `--feeds` | Process only specific feeds |

### Environment Variables

Create `.env.local` in the `app/` directory:

```env
# Optional: Custom base path for deployment
NEXT_PUBLIC_BASE_PATH=/hyderabad-transit
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is open source. The transit data is provided under the Open Government License - India.

## Acknowledgments

- [Telangana Open Data Portal](https://data.telangana.gov.in/)
- [Hyderabad Metro Rail Limited](https://hmrl.co.in/)
- [South Central Railway](https://scr.indianrailways.gov.in/)
- [TGSRTC](https://www.tgsrtc.telangana.gov.in/)
- [World Resources Institute](https://wri.org/) - GTFS data partnership

## Roadmap

- [ ] Isochrone visualization (walking distance)
- [ ] Fare calculator
- [ ] Journey planner
- [ ] Real-time vehicle positions (when available)
- [ ] PWA support for offline use
- [ ] Multi-language support (Telugu, Hindi)
