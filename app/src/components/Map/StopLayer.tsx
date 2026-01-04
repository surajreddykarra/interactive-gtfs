'use client';

/**
 * Stop Layer - Renders stop markers on the map
 */

import { useMemo, useCallback, memo } from 'react';
import { CircleMarker, Marker, Popup } from 'react-leaflet';
import L from 'leaflet';
import { useTransit } from '@/context/TransitContext';
import type { StopFeature } from '@/lib/types';
import {
  getStopMarkerOptions,
  TRANSIT_ICONS,
  TRANSIT_LABELS,
  formatTimeRange,
} from '@/lib/utils';

interface StopMarkerProps {
  stop: StopFeature;
  isSelected: boolean;
  onClick: (stopId: string) => void;
  isVisible: boolean;
  routeColor?: string; // For metro stops, use the line color
}

// Create square icon for metro stops
function createSquareIcon(color: string, size: number, isSelected: boolean): L.DivIcon {
  const borderColor = isSelected ? '#000' : color;
  const borderWidth = isSelected ? 3 : 2;
  const actualSize = isSelected ? size + 4 : size;
  
  return L.divIcon({
    className: 'metro-square-marker',
    html: `<div style="
      width: ${actualSize}px;
      height: ${actualSize}px;
      background-color: ${color};
      border: ${borderWidth}px solid ${borderColor};
      border-radius: 2px;
      opacity: ${isSelected ? 1 : 0.8};
    "></div>`,
    iconSize: [actualSize, actualSize],
    iconAnchor: [actualSize / 2, actualSize / 2],
    popupAnchor: [0, -actualSize / 2],
  });
}

// Create triangle icon for MMTS stops
function createTriangleIcon(color: string, size: number, isSelected: boolean): L.DivIcon {
  const borderColor = isSelected ? '#000' : color;
  const borderWidth = isSelected ? 2 : 1;
  const actualSize = isSelected ? size + 4 : size;
  
  // Create an upward-pointing triangle using CSS borders
  return L.divIcon({
    className: 'mmts-triangle-marker',
    html: `<div style="
      width: 0;
      height: 0;
      border-left: ${actualSize / 2}px solid transparent;
      border-right: ${actualSize / 2}px solid transparent;
      border-bottom: ${actualSize}px solid ${color};
      filter: drop-shadow(0 0 ${borderWidth}px ${borderColor});
      opacity: ${isSelected ? 1 : 0.8};
    "></div>`,
    iconSize: [actualSize, actualSize],
    iconAnchor: [actualSize / 2, actualSize],
    popupAnchor: [0, -actualSize],
  });
}

// Memoized stop marker to prevent unnecessary re-renders
const StopMarker = memo(function StopMarker({ stop, isSelected, onClick, isVisible, routeColor }: StopMarkerProps) {
  const { properties, geometry } = stop;
  const position: [number, number] = [geometry.coordinates[1], geometry.coordinates[0]];
  const options = getStopMarkerOptions(properties.transit_type);
  
  // Use route color for metro stops if provided
  const markerColor = routeColor || options.color;

  const handleClick = useCallback(() => {
    onClick(properties.stop_id);
  }, [onClick, properties.stop_id]);

  // Hide marker if not visible (performance optimization)
  if (!isVisible) return null;

  const popupContent = (
    <Popup>
      <div className="min-w-[200px]">
        <div className="flex items-center gap-2 mb-2">
          <span className="material-symbols-outlined text-xl">{TRANSIT_ICONS[properties.transit_type]}</span>
          <span className={`transit-badge ${properties.transit_type}`}>
            {TRANSIT_LABELS[properties.transit_type]}
          </span>
        </div>
        <h3 className="font-semibold text-base mb-1">{properties.name}</h3>
        <p className="text-xs text-gray-500 mb-2">
          {formatTimeRange(properties.first_time, properties.last_time)}
        </p>
        <p className="text-sm text-gray-600">
          {properties.route_count} route{properties.route_count !== 1 ? 's' : ''} serve this stop
        </p>
      </div>
    </Popup>
  );

  // Use square marker for metro stops
  if (properties.transit_type === 'metro') {
    const icon = createSquareIcon(markerColor, 10, isSelected);
    return (
      <Marker
        position={position}
        icon={icon}
        eventHandlers={{
          click: handleClick,
        }}
      >
        {popupContent}
      </Marker>
    );
  }

  // Use triangle marker for MMTS/rail stops
  if (properties.transit_type === 'rail') {
    const icon = createTriangleIcon(markerColor, 12, isSelected);
    return (
      <Marker
        position={position}
        icon={icon}
        eventHandlers={{
          click: handleClick,
        }}
      >
        {popupContent}
      </Marker>
    );
  }

  // Use circle marker for bus stops
  return (
    <CircleMarker
      center={position}
      radius={isSelected ? options.radius + 3 : options.radius}
      pathOptions={{
        color: isSelected ? '#000' : markerColor,
        fillColor: markerColor,
        fillOpacity: isSelected ? 1 : options.fillOpacity,
        weight: isSelected ? 3 : options.weight,
      }}
      eventHandlers={{
        click: handleClick,
      }}
    >
      {popupContent}
    </CircleMarker>
  );
});

export default function StopLayer() {
  const { state, selectStop } = useTransit();

  // Get ALL stops once - only filter by route selection, not by transit type
  // This prevents re-creating DOM elements when toggling filters
  const allStops = useMemo(() => {
    if (!state.data) return [];
    
    // If a route is selected, only show stops on that route
    if (state.selection.selectedRoute) {
      const routeStops = state.data.routeToStops[state.selection.selectedRoute] || [];
      const routeStopIds = new Set(routeStops.map(s => s.stop_id));
      return state.data.stops.features.filter((stop) => routeStopIds.has(stop.properties.stop_id));
    }

    // If a stop is selected and routes are visible, show only relevant stops
    if (state.selection.selectedStop && state.visibleRoutes.size > 0) {
      const relevantStopIds = new Set<string>();
      relevantStopIds.add(state.selection.selectedStop);
      
      state.visibleRoutes.forEach(routeId => {
        const routeStops = state.data!.routeToStops[routeId] || [];
        routeStops.forEach(s => relevantStopIds.add(s.stop_id));
      });
      
      return state.data.stops.features.filter((stop) => relevantStopIds.has(stop.properties.stop_id));
    }

    // Default: return all stops (visibility controlled per-marker)
    return state.data.stops.features;
  }, [state.data, state.selection.selectedRoute, state.selection.selectedStop, state.visibleRoutes]);

  // Separate metro/rail stops from bus stops for different rendering
  const { metroStops, railStops, busStops } = useMemo(() => {
    const metro: StopFeature[] = [];
    const rail: StopFeature[] = [];
    const bus: StopFeature[] = [];

    allStops.forEach((stop) => {
      switch (stop.properties.transit_type) {
        case 'metro':
          metro.push(stop);
          break;
        case 'rail':
          rail.push(stop);
          break;
        case 'bus':
          bus.push(stop);
          break;
      }
    });

    return { metroStops: metro, railStops: rail, busStops: bus };
  }, [allStops]);

  // Create a lookup map for route colors (for metro stops to match their line color)
  const routeColorMap = useMemo(() => {
    if (!state.data) return new Map<string, string>();
    const map = new Map<string, string>();
    state.data.routes.features.forEach((route) => {
      map.set(route.properties.route_id, route.properties.color);
    });
    return map;
  }, [state.data]);

  // Get the color for a metro stop based on its first route
  const getMetroStopColor = useCallback((stop: StopFeature): string | undefined => {
    const routes = stop.properties.routes;
    if (routes && routes.length > 0) {
      return routeColorMap.get(routes[0]);
    }
    return undefined;
  }, [routeColorMap]);

  const handleStopClick = useCallback(
    (stopId: string) => {
      selectStop(stopId);
    },
    [selectStop]
  );

  return (
    <>
      {/* Metro stops (square markers with line color) */}
      {metroStops.map((stop) => (
        <StopMarker
          key={stop.properties.stop_id}
          stop={stop}
          isSelected={state.selection.selectedStop === stop.properties.stop_id}
          onClick={handleStopClick}
          isVisible={state.filters.metro}
          routeColor={getMetroStopColor(stop)}
        />
      ))}

      {/* Rail (MMTS) stops (circle markers) */}
      {railStops.map((stop) => (
        <StopMarker
          key={stop.properties.stop_id}
          stop={stop}
          isSelected={state.selection.selectedStop === stop.properties.stop_id}
          onClick={handleStopClick}
          isVisible={state.filters.rail}
        />
      ))}

      {/* Bus stops (circle markers) */}
      {busStops.map((stop) => (
        <StopMarker
          key={stop.properties.stop_id}
          stop={stop}
          isSelected={state.selection.selectedStop === stop.properties.stop_id}
          onClick={handleStopClick}
          isVisible={state.filters.bus}
        />
      ))}
    </>
  );
}
