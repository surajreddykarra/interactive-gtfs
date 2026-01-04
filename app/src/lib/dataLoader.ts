/**
 * Data loader for fetching precomputed transit data
 */

import type {
  TransitData,
  StopsGeoJSON,
  RoutesGeoJSON,
  StopToRoutesMap,
  RouteToStopsMap,
  TimetableData,
  Metadata,
} from './types';
import { getDataPath } from './utils';

// Cache for loaded data
let cachedData: TransitData | null = null;

/**
 * Fetch a JSON file from the public data directory
 */
async function fetchJson<T>(filename: string): Promise<T> {
  const path = getDataPath(filename);
  const response = await fetch(path);
  
  if (!response.ok) {
    throw new Error(`Failed to fetch ${filename}: ${response.statusText}`);
  }
  
  return response.json();
}

/**
 * Load all transit data files
 */
export async function loadTransitData(): Promise<TransitData> {
  // Return cached data if available
  if (cachedData) {
    return cachedData;
  }

  // Load all data files in parallel
  const [stops, routes, stopToRoutes, routeToStops, timetable, metadata] = await Promise.all([
    fetchJson<StopsGeoJSON>('stops.geojson'),
    fetchJson<RoutesGeoJSON>('routes.geojson'),
    fetchJson<StopToRoutesMap>('stop_to_routes.json'),
    fetchJson<RouteToStopsMap>('route_to_stops.json'),
    fetchJson<TimetableData>('timetable.json'),
    fetchJson<Metadata>('metadata.json'),
  ]);

  cachedData = {
    stops,
    routes,
    stopToRoutes,
    routeToStops,
    timetable,
    metadata,
  };

  return cachedData;
}

/**
 * Load only stops data (lighter load for initial render)
 */
export async function loadStopsOnly(): Promise<StopsGeoJSON> {
  return fetchJson<StopsGeoJSON>('stops.geojson');
}

/**
 * Load only routes data
 */
export async function loadRoutesOnly(): Promise<RoutesGeoJSON> {
  return fetchJson<RoutesGeoJSON>('routes.geojson');
}

/**
 * Load metadata for initial configuration
 */
export async function loadMetadata(): Promise<Metadata> {
  return fetchJson<Metadata>('metadata.json');
}

/**
 * Clear cached data (useful for testing or forced refresh)
 */
export function clearCache(): void {
  cachedData = null;
}

/**
 * Check if data is already loaded
 */
export function isDataLoaded(): boolean {
  return cachedData !== null;
}

/**
 * Get cached data without loading
 */
export function getCachedData(): TransitData | null {
  return cachedData;
}
