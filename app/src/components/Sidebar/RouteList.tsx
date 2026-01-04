'use client';

/**
 * Route List - Shows all routes grouped by transit type
 */

import { useMemo, useState } from 'react';
import { useTransit } from '@/context/TransitContext';
import type { RouteFeature, TransitType } from '@/lib/types';
import { TRANSIT_ICONS, TRANSIT_LABELS } from '@/lib/utils';

interface RouteGroupProps {
  transitType: TransitType;
  routes: RouteFeature[];
  expanded: boolean;
  onToggle: () => void;
  onRouteClick: (routeId: string) => void;
  onRouteVisibilityToggle: (routeId: string, e: React.MouseEvent) => void;
  selectedRouteId: string | null;
  isRouteVisible: (routeId: string) => boolean;
  hasRouteFilter: boolean;
}

function RouteGroup({
  transitType,
  routes,
  expanded,
  onToggle,
  onRouteClick,
  onRouteVisibilityToggle,
  selectedRouteId,
  isRouteVisible,
  hasRouteFilter,
}: RouteGroupProps) {
  return (
    <div className="mb-3">
      {/* Group Header */}
      <button
        className="w-full flex items-center justify-between p-3 bg-gray-50 hover:bg-gray-100 dark:bg-gray-900 dark:hover:bg-gray-800 rounded-lg transition-colors"
        onClick={onToggle}
      >
        <div className="flex items-center gap-2">
          <span className="material-symbols-outlined text-xl">{TRANSIT_ICONS[transitType]}</span>
          <span className="font-medium dark:text-gray-200">{TRANSIT_LABELS[transitType]}</span>
          <span className="text-sm text-gray-500 dark:text-gray-400">({routes.length})</span>
        </div>
        <span className={`material-symbols-outlined text-gray-400 transition-transform ${
            expanded ? 'rotate-180' : ''
          }`}>
          expand_more
        </span>
      </button>

      {/* Routes */}
      {expanded && (
        <div className="mt-2 ml-2">
          {routes.map((route) => {
            const routeId = route.properties.route_id;
            const isVisible = isRouteVisible(routeId);
            const isSelected = selectedRouteId === routeId;
            
            return (
              <div
                key={routeId}
                className={`route-item ${isSelected ? 'selected' : ''} ${!isVisible && hasRouteFilter ? 'opacity-40' : ''}`}
                onClick={() => onRouteClick(routeId)}
              >
                {/* Visibility toggle */}
                <button
                  onClick={(e) => onRouteVisibilityToggle(routeId, e)}
                  className="flex-shrink-0 mr-2 transition-colors focus:outline-none"
                  title={isVisible ? 'Hide route' : 'Show route'}
                >
                  <span className={`material-symbols-outlined text-xl ${
                    isVisible || !hasRouteFilter 
                      ? 'text-gray-700 dark:text-gray-300' 
                      : 'text-gray-400 dark:text-gray-600'
                  }`}>
                    {isVisible || !hasRouteFilter ? 'check_box' : 'check_box_outline_blank'}
                  </span>
                </button>
                <div
                  className="route-color-dot"
                  style={{ backgroundColor: route.properties.color }}
                />
                <div className="flex-1 min-w-0">
                  <div className="font-medium text-sm truncate">
                    {route.properties.name}
                  </div>
                  <div className="text-xs text-gray-500">
                    {route.properties.stop_count} stops
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default function RouteList() {
  const { state, selectRoute, toggleRouteVisibility, isRouteVisible } = useTransit();
  const [expandedGroups, setExpandedGroups] = useState<Set<TransitType>>(
    () => new Set<TransitType>()
  );

  // Get ALL routes for enabled types (not filtered by visibleRoutes)
  const allRoutesForTypes = useMemo(() => {
    if (!state.data) return [];
    return state.data.routes.features.filter((route) => {
      const type = route.properties.type_name as TransitType;
      return state.filters[type];
    });
  }, [state.data, state.filters]);

  // Group routes by transit type
  const groupedRoutes = useMemo(() => {
    const groups: Record<TransitType, RouteFeature[]> = {
      metro: [],
      rail: [],
      bus: [],
    };

    allRoutesForTypes.forEach((route) => {
      const type = route.properties.type_name as TransitType;
      if (groups[type]) {
        groups[type].push(route);
      }
    });

    // Sort routes within each group by name
    Object.values(groups).forEach((routes) => {
      routes.sort((a, b) => a.properties.name.localeCompare(b.properties.name));
    });

    return groups;
  }, [allRoutesForTypes]);

  const toggleGroup = (type: TransitType) => {
    setExpandedGroups((prev) => {
      const next = new Set(prev);
      if (next.has(type)) {
        next.delete(type);
      } else {
        next.add(type);
      }
      return next;
    });
  };

  const handleRouteClick = (routeId: string) => {
    selectRoute(routeId);
  };

  const handleRouteVisibilityToggle = (routeId: string, e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent route selection
    toggleRouteVisibility(routeId);
  };

  // Check if we have any route filter active
  const hasRouteFilter = state.visibleRoutes.size > 0;

  // Order of transit types to display
  const transitOrder: TransitType[] = ['metro', 'rail', 'bus'];

  return (
    <div>
      {transitOrder.map((type) => {
        const routes = groupedRoutes[type];
        if (!state.filters[type] || routes.length === 0) return null;

        return (
          <RouteGroup
            key={type}
            transitType={type}
            routes={routes}
            expanded={expandedGroups.has(type)}
            onToggle={() => toggleGroup(type)}
            onRouteClick={handleRouteClick}
            onRouteVisibilityToggle={handleRouteVisibilityToggle}
            selectedRouteId={state.selection.selectedRoute}
            isRouteVisible={isRouteVisible}
            hasRouteFilter={hasRouteFilter}
          />
        );
      })}

      {allRoutesForTypes.length === 0 && (
        <div className="text-center text-gray-500 py-8">
          <p>No routes to display</p>
          <p className="text-sm mt-1">Enable a transit type above</p>
        </div>
      )}
    </div>
  );
}
