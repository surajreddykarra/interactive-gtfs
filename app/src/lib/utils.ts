/**
 * Utility functions for the transit visualization app
 */

import type { TransitType, AgencyCode, StopMarkerOptions, RouteLineOptions } from './types';

// ============================================================================
// Transit Type Styling
// ============================================================================

export const TRANSIT_COLORS: Record<TransitType, string> = {
  metro: '#E91E63',
  rail: '#9C27B0',
  bus: '#FFC107',
};

export const TRANSIT_LABELS: Record<TransitType, string> = {
  metro: 'Metro Rail',
  rail: 'MMTS Rail',
  bus: 'City Bus',
};

export const TRANSIT_ICONS: Record<TransitType, string> = {
  metro: 'metro',
  rail: 'train',
  bus: 'airport_shuttle',
};

export function getStopMarkerOptions(transitType: TransitType): StopMarkerOptions {
  const baseOptions = {
    fillOpacity: 0.8,
    weight: 2,
  };

  switch (transitType) {
    case 'metro':
      return { ...baseOptions, color: TRANSIT_COLORS.metro, radius: 8 };
    case 'rail':
      return { ...baseOptions, color: TRANSIT_COLORS.rail, radius: 7 };
    case 'bus':
      return { ...baseOptions, color: TRANSIT_COLORS.bus, radius: 4, weight: 1 };
    default:
      return { ...baseOptions, color: '#888888', radius: 5 };
  }
}

export function getRouteLineOptions(transitType: TransitType, color?: string): RouteLineOptions {
  // Metro uses the route's actual color (Blue Line, Green Line, Red Line)
  // Bus and MMTS use fixed colors regardless of route data
  switch (transitType) {
    case 'metro':
      return { color: color || TRANSIT_COLORS.metro, weight: 5, opacity: 0.9 };
    case 'rail':
      // MMTS always purple
      return { color: TRANSIT_COLORS.rail, weight: 4, opacity: 0.8, dashArray: '10, 5' };
    case 'bus':
      // Bus always yellow
      return { color: TRANSIT_COLORS.bus, weight: 2, opacity: 0.6 };
    default:
      return { color: color || '#888888', weight: 3, opacity: 0.7 };
  }
}

// ============================================================================
// Agency Helpers
// ============================================================================

export const AGENCY_NAMES: Record<AgencyCode, string> = {
  HMRL: 'Hyderabad Metro Rail',
  MMTS: 'MMTS Suburban Rail',
  TGSRTC: 'TGSRTC City Bus',
};

export function getAgencyTransitType(agency: AgencyCode): TransitType {
  switch (agency) {
    case 'HMRL':
      return 'metro';
    case 'MMTS':
      return 'rail';
    case 'TGSRTC':
      return 'bus';
    default:
      return 'bus';
  }
}

// ============================================================================
// Time Formatting
// ============================================================================

export function formatTime(time: string): string {
  if (!time) return '--:--';
  return time;
}

export function formatTimeRange(first: string, last: string): string {
  if (!first || !last) return 'Schedule not available';
  return `${formatTime(first)} - ${formatTime(last)}`;
}

// ============================================================================
// Search Helpers
// ============================================================================

export function normalizeSearchString(str: string): string {
  return str.toLowerCase().trim();
}

export function matchesSearch(text: string, query: string): boolean {
  const normalizedText = normalizeSearchString(text);
  const normalizedQuery = normalizeSearchString(query);
  return normalizedText.includes(normalizedQuery);
}

// ============================================================================
// Map Helpers
// ============================================================================

export const HYDERABAD_CENTER: [number, number] = [17.385, 78.4867];
export const DEFAULT_ZOOM = 12;
export const MIN_ZOOM = 10;
export const MAX_ZOOM = 18;

// CARTO basemap tiles
export const TILE_URLS = {
  light: 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',
  dark: 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
  voyager: 'https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png',
};

export const TILE_ATTRIBUTION =
  '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>';

// ============================================================================
// Data Path Helpers
// ============================================================================

export function getDataPath(filename: string): string {
  return `/data/${filename}`;
}

// ============================================================================
// ID Helpers
// ============================================================================

export function parseStopId(prefixedId: string): { agency: AgencyCode; originalId: string } {
  const [agency, ...rest] = prefixedId.split('_');
  return {
    agency: agency as AgencyCode,
    originalId: rest.join('_'),
  };
}

export function parseRouteId(prefixedId: string): { agency: AgencyCode; originalId: string } {
  const [agency, ...rest] = prefixedId.split('_');
  return {
    agency: agency as AgencyCode,
    originalId: rest.join('_'),
  };
}

// ============================================================================
// Sorting Helpers
// ============================================================================

export function sortByTransitType<T extends { transit_type: TransitType }>(items: T[]): T[] {
  const order: TransitType[] = ['metro', 'rail', 'bus'];
  return [...items].sort((a, b) => order.indexOf(a.transit_type) - order.indexOf(b.transit_type));
}

export function sortByName<T extends { name: string }>(items: T[]): T[] {
  return [...items].sort((a, b) => a.name.localeCompare(b.name));
}
