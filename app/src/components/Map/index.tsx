'use client';

/**
 * Main Map Component - Combines all map layers
 */

import { useEffect, useState } from 'react';
import { MapContainer, TileLayer, useMap, useMapEvents, ZoomControl } from 'react-leaflet';
import { useTransit } from '@/context/TransitContext';
import StopLayer from './StopLayer';
import RouteLayer from './RouteLayer';
import {
  HYDERABAD_CENTER,
  DEFAULT_ZOOM,
  MIN_ZOOM,
  MAX_ZOOM,
  TILE_URLS,
  TILE_ATTRIBUTION,
} from '@/lib/utils';

// Component to handle map events
function MapEventHandler() {
  const { clearSelection } = useTransit();

  useMapEvents({
    click: (e) => {
      // Clear selection when clicking on empty map area
      // This is handled by the event not being stopped by markers
    },
  });

  return null;
}

// Component to fit bounds to selection
function SelectionHandler() {
  const map = useMap();
  const { state, getSelectedRouteData, getSelectedStopData } = useTransit();

  // Handle route selection - fit bounds to route
  useEffect(() => {
    if (state.selection.selectedRoute) {
      const routeData = getSelectedRouteData();
      if (routeData?.geometry?.coordinates) {
        const coords = routeData.geometry.coordinates;
        const bounds = coords.map(([lng, lat]) => [lat, lng] as [number, number]);
        if (bounds.length > 0) {
          map.fitBounds(bounds, { padding: [50, 50] });
        }
      }
    }
  }, [state.selection.selectedRoute, map, getSelectedRouteData]);

  // Handle stop selection - zoom to stop with high zoom level
  useEffect(() => {
    if (state.selection.selectedStop) {
      const stopData = getSelectedStopData();
      if (stopData?.geometry?.coordinates) {
        const [lng, lat] = stopData.geometry.coordinates;
        // Use zoom level 17 for good detail when selecting a stop
        map.flyTo([lat, lng], 17, { duration: 0.5 });
      }
    }
  }, [state.selection.selectedStop, map, getSelectedStopData]);

  return null;
}

export default function TransitMap() {
  const { state } = useTransit();
  const [mapReady, setMapReady] = useState(false);

  // Get center from metadata if available
  const center = state.data?.metadata?.center || HYDERABAD_CENTER;
  const zoom = state.data?.metadata?.default_zoom || DEFAULT_ZOOM;

  return (
    <MapContainer
      center={center}
      zoom={zoom}
      minZoom={MIN_ZOOM}
      maxZoom={MAX_ZOOM}
      zoomControl={false}
      className="h-full w-full"
      whenReady={() => setMapReady(true)}
    >
      <ZoomControl position="bottomright" />
      {/* Base map tiles */}
      <TileLayer
        attribution={TILE_ATTRIBUTION}
        url={TILE_URLS.voyager}
      />

      {/* Map event handlers */}
      <MapEventHandler />
      <SelectionHandler />

      {/* Route layer (rendered below stops) */}
      {mapReady && <RouteLayer />}

      {/* Stop layer */}
      {mapReady && <StopLayer />}
    </MapContainer>
  );
}
