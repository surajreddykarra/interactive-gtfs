'use client';

/**
 * Marker Cluster Component for React-Leaflet
 * 
 * This wraps leaflet.markercluster for use with react-leaflet v4
 */

import { createPathComponent } from '@react-leaflet/core';
import L from 'leaflet';
import 'leaflet.markercluster';

// Extend the type definitions
declare module 'leaflet' {
  interface MarkerClusterGroupOptions {
    chunkedLoading?: boolean;
    maxClusterRadius?: number | ((zoom: number) => number);
    spiderfyOnMaxZoom?: boolean;
    showCoverageOnHover?: boolean;
    zoomToBoundsOnClick?: boolean;
    singleMarkerMode?: boolean;
    disableClusteringAtZoom?: number;
    removeOutsideVisibleBounds?: boolean;
    animate?: boolean;
    animateAddingMarkers?: boolean;
    spiderfyDistanceMultiplier?: number;
    spiderLegPolylineOptions?: L.PolylineOptions;
    polygonOptions?: L.PolylineOptions;
  }
}

interface MarkerClusterGroupProps extends L.MarkerClusterGroupOptions {
  children: React.ReactNode;
}

const createMarkerClusterGroup = (
  props: MarkerClusterGroupProps,
  context: any
) => {
  const clusterProps: L.MarkerClusterGroupOptions = {};
  const { children, ...options } = props;

  // Extract cluster options
  Object.keys(options).forEach((key) => {
    (clusterProps as any)[key] = (options as any)[key];
  });

  const instance = new (L as any).MarkerClusterGroup(clusterProps);

  return {
    instance,
    context: { ...context, layerContainer: instance },
  };
};

const updateMarkerClusterGroup = (
  instance: any,
  props: MarkerClusterGroupProps,
  prevProps: MarkerClusterGroupProps
) => {
  // Marker cluster groups don't have many updateable props
  // Most changes require recreating the layer
};

const MarkerClusterGroup = createPathComponent<
  any,
  MarkerClusterGroupProps
>(createMarkerClusterGroup, updateMarkerClusterGroup);

export default MarkerClusterGroup;
