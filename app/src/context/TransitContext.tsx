'use client';

/**
 * Transit Context - Global state management for transit data and UI
 */

import React, { createContext, useContext, useReducer, useEffect, ReactNode } from 'react';
import type {
  TransitData,
  FilterState,
  SelectionState,
  TransitType,
  StopFeature,
  RouteFeature,
} from '@/lib/types';
import { loadTransitData } from '@/lib/dataLoader';

// ============================================================================
// State Types
// ============================================================================

interface TransitState {
  // Data
  data: TransitData | null;
  loading: boolean;
  error: string | null;

  // Filters
  filters: FilterState;

  // Selection
  selection: SelectionState;

  // UI
  sidebarOpen: boolean;
  
  // Individual route visibility (empty Set = show all for enabled types)
  visibleRoutes: Set<string>;
}

// ============================================================================
// Action Types
// ============================================================================

type TransitAction =
  | { type: 'SET_DATA'; payload: TransitData }
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_ERROR'; payload: string }
  | { type: 'TOGGLE_FILTER'; payload: TransitType }
  | { type: 'SET_FILTERS'; payload: FilterState }
  | { type: 'SELECT_STOP'; payload: string | null }
  | { type: 'SELECT_ROUTE'; payload: string | null }
  | { type: 'SET_HIGHLIGHTED_ROUTES'; payload: string[] }
  | { type: 'TOGGLE_SIDEBAR' }
  | { type: 'OPEN_SIDEBAR' }
  | { type: 'TOGGLE_ROUTE_VISIBILITY'; payload: string }
  | { type: 'SET_VISIBLE_ROUTES'; payload: Set<string> }
  | { type: 'CLEAR_SELECTION' };

// ============================================================================
// Initial State
// ============================================================================

const initialState: TransitState = {
  data: null,
  loading: true,
  error: null,
  filters: {
    metro: true,
    rail: true,
    bus: true,
  },
  selection: {
    selectedStop: null,
    selectedRoute: null,
    highlightedRoutes: [],
  },
  sidebarOpen: true,
  // Track which individual routes are visible (empty = show all filtered by type)
  visibleRoutes: new Set<string>(),
};

// ============================================================================
// Reducer
// ============================================================================

function transitReducer(state: TransitState, action: TransitAction): TransitState {
  switch (action.type) {
    case 'SET_DATA':
      return { ...state, data: action.payload, loading: false, error: null };

    case 'SET_LOADING':
      return { ...state, loading: action.payload };

    case 'SET_ERROR':
      return { ...state, error: action.payload, loading: false };

    case 'TOGGLE_FILTER':
      return {
        ...state,
        filters: {
          ...state.filters,
          [action.payload]: !state.filters[action.payload],
        },
      };

    case 'SET_FILTERS':
      return { ...state, filters: action.payload };

    case 'SELECT_STOP':
      // When selecting a stop, highlight all routes that serve it and ONLY show those routes
      const stopRoutes = action.payload && state.data
        ? state.data.stopToRoutes[action.payload] || []
        : [];
      return {
        ...state,
        selection: {
          ...state.selection,
          selectedStop: action.payload,
          selectedRoute: null, // Clear route selection
          highlightedRoutes: stopRoutes,
        },
        // When a stop is selected, only show routes that serve it
        visibleRoutes: action.payload ? new Set(stopRoutes) : new Set(),
      };

    case 'SELECT_ROUTE':
      return {
        ...state,
        selection: {
          ...state.selection,
          selectedRoute: action.payload,
          selectedStop: null, // Clear stop selection
          highlightedRoutes: action.payload ? [action.payload] : [],
        },
        // When a route is selected, only show that route
        visibleRoutes: action.payload ? new Set([action.payload]) : new Set(),
      };

    case 'SET_HIGHLIGHTED_ROUTES':
      return {
        ...state,
        selection: {
          ...state.selection,
          highlightedRoutes: action.payload,
        },
      };

    case 'TOGGLE_SIDEBAR':
      return { ...state, sidebarOpen: !state.sidebarOpen };

    case 'OPEN_SIDEBAR':
      return { ...state, sidebarOpen: true };

    case 'TOGGLE_ROUTE_VISIBILITY': {
      const newVisible = new Set(state.visibleRoutes);
      if (newVisible.has(action.payload)) {
        newVisible.delete(action.payload);
      } else {
        newVisible.add(action.payload);
      }
      return { ...state, visibleRoutes: newVisible };
    }

    case 'SET_VISIBLE_ROUTES':
      return { ...state, visibleRoutes: action.payload };

    case 'CLEAR_SELECTION':
      return {
        ...state,
        selection: {
          selectedStop: null,
          selectedRoute: null,
          highlightedRoutes: [],
        },
        // Clear route filter when clearing selection
        visibleRoutes: new Set(),
      };

    default:
      return state;
  }
}

// ============================================================================
// Context
// ============================================================================

interface TransitContextValue {
  state: TransitState;
  dispatch: React.Dispatch<TransitAction>;

  // Convenience methods
  toggleFilter: (type: TransitType) => void;
  selectStop: (stopId: string | null) => void;
  selectRoute: (routeId: string | null) => void;
  clearSelection: () => void;
  toggleSidebar: () => void;
  openSidebar: () => void;
  toggleRouteVisibility: (routeId: string) => void;
  setVisibleRoutes: (routeIds: Set<string>) => void;
  isRouteVisible: (routeId: string) => boolean;

  // Filtered data getters
  getFilteredStops: () => StopFeature[];
  getFilteredRoutes: () => RouteFeature[];
  getSelectedStopData: () => StopFeature | null;
  getSelectedRouteData: () => RouteFeature | null;
}

const TransitContext = createContext<TransitContextValue | null>(null);

// ============================================================================
// Provider
// ============================================================================

interface TransitProviderProps {
  children: ReactNode;
}

export function TransitProvider({ children }: TransitProviderProps) {
  const [state, dispatch] = useReducer(transitReducer, initialState);

  // Load data on mount
  useEffect(() => {
    async function load() {
      try {
        const data = await loadTransitData();
        dispatch({ type: 'SET_DATA', payload: data });
      } catch (err) {
        dispatch({
          type: 'SET_ERROR',
          payload: err instanceof Error ? err.message : 'Failed to load data',
        });
      }
    }

    load();
  }, []);

  // Convenience methods
  const toggleFilter = (type: TransitType) => {
    dispatch({ type: 'TOGGLE_FILTER', payload: type });
  };

  const selectStop = (stopId: string | null) => {
    dispatch({ type: 'SELECT_STOP', payload: stopId });
  };

  const selectRoute = (routeId: string | null) => {
    dispatch({ type: 'SELECT_ROUTE', payload: routeId });
  };

  const clearSelection = () => {
    dispatch({ type: 'CLEAR_SELECTION' });
  };

  const toggleSidebar = () => {
    dispatch({ type: 'TOGGLE_SIDEBAR' });
  };

  const openSidebar = () => {
    dispatch({ type: 'OPEN_SIDEBAR' });
  };

  const toggleRouteVisibility = (routeId: string) => {
    dispatch({ type: 'TOGGLE_ROUTE_VISIBILITY', payload: routeId });
  };

  const setVisibleRoutes = (routeIds: Set<string>) => {
    dispatch({ type: 'SET_VISIBLE_ROUTES', payload: routeIds });
  };

  const isRouteVisible = (routeId: string): boolean => {
    // If no specific routes selected, all routes of enabled types are visible
    if (state.visibleRoutes.size === 0) return true;
    return state.visibleRoutes.has(routeId);
  };

  // Filtered data getters
  const getFilteredStops = (): StopFeature[] => {
    if (!state.data) return [];

    // If a route is selected, only show stops on that route
    if (state.selection.selectedRoute) {
      const routeStops = state.data.routeToStops[state.selection.selectedRoute] || [];
      const routeStopIds = new Set(routeStops.map(s => s.stop_id));
      
      return state.data.stops.features.filter((stop) => {
        const type = stop.properties.transit_type;
        if (!state.filters[type]) return false;
        return routeStopIds.has(stop.properties.stop_id);
      });
    }

    // If a stop is selected, only show stops on the routes that serve the selected stop
    if (state.selection.selectedStop && state.visibleRoutes.size > 0) {
      // Get all stops from all visible routes
      const relevantStopIds = new Set<string>();
      
      // Always include the selected stop
      relevantStopIds.add(state.selection.selectedStop);
      
      // Add all stops from visible routes
      state.visibleRoutes.forEach(routeId => {
        const routeStops = state.data!.routeToStops[routeId] || [];
        routeStops.forEach(s => relevantStopIds.add(s.stop_id));
      });
      
      return state.data.stops.features.filter((stop) => {
        const type = stop.properties.transit_type;
        if (!state.filters[type]) return false;
        return relevantStopIds.has(stop.properties.stop_id);
      });
    }

    // Default: filter by transit type only
    return state.data.stops.features.filter((stop) => {
      const type = stop.properties.transit_type;
      return state.filters[type];
    });
  };

  const getFilteredRoutes = (): RouteFeature[] => {
    if (!state.data) return [];

    return state.data.routes.features.filter((route) => {
      const type = route.properties.type_name as TransitType;
      // First check type filter
      if (!state.filters[type]) return false;
      // Then check individual route visibility (if any routes are specifically selected)
      if (state.visibleRoutes.size > 0) {
        return state.visibleRoutes.has(route.properties.route_id);
      }
      return true;
    });
  };

  const getSelectedStopData = (): StopFeature | null => {
    if (!state.data || !state.selection.selectedStop) return null;

    return (
      state.data.stops.features.find(
        (stop) => stop.properties.stop_id === state.selection.selectedStop
      ) || null
    );
  };

  const getSelectedRouteData = (): RouteFeature | null => {
    if (!state.data || !state.selection.selectedRoute) return null;

    return (
      state.data.routes.features.find(
        (route) => route.properties.route_id === state.selection.selectedRoute
      ) || null
    );
  };

  const value: TransitContextValue = {
    state,
    dispatch,
    toggleFilter,
    selectStop,
    selectRoute,
    clearSelection,
    toggleSidebar,
    openSidebar,
    toggleRouteVisibility,
    setVisibleRoutes,
    isRouteVisible,
    getFilteredStops,
    getFilteredRoutes,
    getSelectedStopData,
    getSelectedRouteData,
  };

  return <TransitContext.Provider value={value}>{children}</TransitContext.Provider>;
}

// ============================================================================
// Hook
// ============================================================================

export function useTransit() {
  const context = useContext(TransitContext);

  if (!context) {
    throw new Error('useTransit must be used within a TransitProvider');
  }

  return context;
}
