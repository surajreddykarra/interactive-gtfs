/**
 * TypeScript type definitions for Hyderabad Transit Visualization
 */

// ============================================================================
// GeoJSON Types
// ============================================================================

export interface GeoJSONPoint {
  type: 'Point';
  coordinates: [number, number]; // [longitude, latitude]
}

export interface GeoJSONLineString {
  type: 'LineString';
  coordinates: [number, number][];
}

export interface GeoJSONFeature<G, P> {
  type: 'Feature';
  geometry: G;
  properties: P;
}

export interface GeoJSONFeatureCollection<F> {
  type: 'FeatureCollection';
  features: F[];
}

// ============================================================================
// Transit Data Types
// ============================================================================

export type TransitType = 'metro' | 'rail' | 'bus';
export type AgencyCode = 'HMRL' | 'MMTS' | 'TGSRTC';

export interface StopProperties {
  stop_id: string;
  name: string;
  agency: AgencyCode;
  transit_type: TransitType;
  routes: string[];
  route_count: number;
  first_time: string;
  last_time: string;
  stop_code?: string;
  platform_code?: string;
  description?: string;
}

export interface RouteProperties {
  route_id: string;
  name: string;
  short_name: string;
  long_name: string;
  type: number;
  type_name: string;
  agency: AgencyCode;
  color: string;
  text_color: string;
  stops: string[];
  stop_count: number;
  description?: string;
}

export type StopFeature = GeoJSONFeature<GeoJSONPoint, StopProperties>;
export type RouteFeature = GeoJSONFeature<GeoJSONLineString, RouteProperties>;

export type StopsGeoJSON = GeoJSONFeatureCollection<StopFeature>;
export type RoutesGeoJSON = GeoJSONFeatureCollection<RouteFeature>;

// ============================================================================
// Lookup Types
// ============================================================================

export type StopToRoutesMap = Record<string, string[]>;

export interface RouteStopInfo {
  stop_id: string;
  name: string;
  seq: number;
}

export type RouteToStopsMap = Record<string, RouteStopInfo[]>;

export interface TimetableEntry {
  weekday: string[];
  weekend: string[];
}

export type RouteTimetable = Record<string, TimetableEntry>;
export type TimetableData = Record<string, RouteTimetable>;

// ============================================================================
// Metadata Types
// ============================================================================

export interface AgencyStats {
  name: string;
  transit_type: TransitType;
  stop_count: number;
  route_count: number;
  color_default: string;
  files_available?: string[];
  has_shapes?: boolean;
  agency_name?: string;
}

export interface TransitTypeStats {
  stop_count: number;
  route_count: number;
}

export interface Metadata {
  generated_at: string;
  version: string;
  city: string;
  center: [number, number];
  default_zoom: number;
  totals: {
    stops: number;
    routes: number;
  };
  agencies: Record<AgencyCode, AgencyStats>;
  transit_types: Record<TransitType, TransitTypeStats>;
  route_type_names: Record<string, string>;
  files: Record<string, string>;
}

// ============================================================================
// UI State Types
// ============================================================================

export interface FilterState {
  metro: boolean;
  rail: boolean;
  bus: boolean;
}

export interface SelectionState {
  selectedStop: string | null;
  selectedRoute: string | null;
  highlightedRoutes: string[];
}

export interface UIState {
  sidebarOpen: boolean;
  activePanel: 'stops' | 'routes' | 'info';
  searchQuery: string;
}

// ============================================================================
// Component Props Types
// ============================================================================

export interface MapViewport {
  center: [number, number];
  zoom: number;
}

export interface StopMarkerOptions {
  color: string;
  radius: number;
  weight: number;
  fillOpacity: number;
}

export interface RouteLineOptions {
  color: string;
  weight: number;
  opacity: number;
  dashArray?: string;
}

// ============================================================================
// Data Loader Types
// ============================================================================

export interface TransitData {
  stops: StopsGeoJSON;
  routes: RoutesGeoJSON;
  stopToRoutes: StopToRoutesMap;
  routeToStops: RouteToStopsMap;
  timetable: TimetableData;
  metadata: Metadata;
}

export interface DataLoadingState {
  loading: boolean;
  error: string | null;
  data: TransitData | null;
}
