'use client';

/**
 * Route Layer - Renders route polylines on the map
 */

import { useMemo, useCallback } from 'react';
import { Polyline, Tooltip } from 'react-leaflet';
import { useTransit } from '@/context/TransitContext';
import type { RouteFeature, TransitType } from '@/lib/types';
import { getRouteLineOptions, TRANSIT_ICONS } from '@/lib/utils';

interface RoutePolylineProps {
  route: RouteFeature;
  isHighlighted: boolean;
  onClick: (routeId: string) => void;
}

function RoutePolyline({ route, isHighlighted, onClick }: RoutePolylineProps) {
  const { properties, geometry } = route;

  if (!geometry || !geometry.coordinates || geometry.coordinates.length < 2) {
    return null;
  }

  // Convert GeoJSON coordinates [lng, lat] to Leaflet [lat, lng]
  const positions: [number, number][] = geometry.coordinates.map(
    ([lng, lat]) => [lat, lng] as [number, number]
  );

  const transitType = properties.type_name as TransitType;
  const baseOptions = getRouteLineOptions(transitType, properties.color);

  const pathOptions = {
    color: baseOptions.color,
    weight: isHighlighted ? baseOptions.weight + 2 : baseOptions.weight,
    opacity: isHighlighted ? 1 : baseOptions.opacity,
    dashArray: baseOptions.dashArray,
  };

  const handleClick = useCallback(() => {
    onClick(properties.route_id);
  }, [onClick, properties.route_id]);

  return (
    <Polyline
      positions={positions}
      pathOptions={pathOptions}
      eventHandlers={{
        click: handleClick,
      }}
    >
      <Tooltip sticky>
        <span>
          {TRANSIT_ICONS[transitType]} {properties.name}
        </span>
      </Tooltip>
    </Polyline>
  );
}

export default function RouteLayer() {
  const { state, selectRoute, getFilteredRoutes } = useTransit();

  // Re-filter when filters, selection, or visibleRoutes change
  const filteredRoutes = useMemo(
    () => getFilteredRoutes(), 
    [getFilteredRoutes, state.filters, state.selection.selectedStop, state.selection.selectedRoute, state.visibleRoutes]
  );

  // Sort routes so highlighted ones render on top
  const sortedRoutes = useMemo(() => {
    const highlighted = new Set(state.selection.highlightedRoutes);
    return [...filteredRoutes].sort((a, b) => {
      const aHighlighted = highlighted.has(a.properties.route_id);
      const bHighlighted = highlighted.has(b.properties.route_id);
      if (aHighlighted && !bHighlighted) return 1;
      if (!aHighlighted && bHighlighted) return -1;
      return 0;
    });
  }, [filteredRoutes, state.selection.highlightedRoutes]);

  const handleRouteClick = useCallback(
    (routeId: string) => {
      selectRoute(routeId);
    },
    [selectRoute]
  );

  return (
    <>
      {sortedRoutes.map((route) => (
        <RoutePolyline
          key={route.properties.route_id}
          route={route}
          isHighlighted={state.selection.highlightedRoutes.includes(route.properties.route_id)}
          onClick={handleRouteClick}
        />
      ))}
    </>
  );
}
