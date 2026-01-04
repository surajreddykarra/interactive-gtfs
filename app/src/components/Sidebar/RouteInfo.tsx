'use client';

/**
 * Route Info Panel - Shows details about a selected route
 */

import { useMemo } from 'react';
import { useTransit } from '@/context/TransitContext';
import {
  TRANSIT_ICONS,
  TRANSIT_LABELS,
} from '@/lib/utils';
import type { TransitType } from '@/lib/types';

interface RouteInfoProps {
  routeId: string;
}

export default function RouteInfo({ routeId }: RouteInfoProps) {
  const { state, selectStop, getSelectedRouteData } = useTransit();

  const routeData = useMemo(() => getSelectedRouteData(), [getSelectedRouteData, routeId]);

  // Get stop details for this route
  const routeStops = useMemo(() => {
    if (!state.data) return [];
    return state.data.routeToStops[routeId] || [];
  }, [state.data, routeId]);

  if (!routeData) {
    return (
      <div className="stop-info-panel">
        <p className="text-gray-500">Route not found</p>
      </div>
    );
  }

  const { properties } = routeData;
  const transitType = properties.type_name as TransitType;

  return (
    <div className="stop-info-panel">
      {/* Header */}
      <div className="flex items-start gap-3 mb-4">
        <div
          className="w-12 h-12 rounded-lg flex items-center justify-center text-white text-xl"
          style={{ backgroundColor: properties.color }}
        >
          <span className="material-symbols-outlined text-2xl">{TRANSIT_ICONS[transitType]}</span>
        </div>
        <div className="flex-1">
          <h3 className="font-semibold text-lg dark:text-white">{properties.name}</h3>
          <span className={`transit-badge ${transitType}`}>
            {TRANSIT_LABELS[transitType]}
          </span>
        </div>
      </div>

      {/* Route Info */}
      {properties.long_name && properties.long_name !== properties.name && (
        <div className="mb-4 p-3 bg-white dark:bg-gray-900 rounded-lg">
          <div className="text-xs text-gray-500 dark:text-gray-400 uppercase mb-1">Route</div>
          <div className="text-sm dark:text-gray-200">{properties.long_name}</div>
        </div>
      )}

      {/* Stops List */}
      <div>
        <div className="text-xs text-gray-500 dark:text-gray-400 uppercase mb-2">
          Stops ({routeStops.length})
        </div>
        <div className="bg-white dark:bg-gray-900 rounded-lg max-h-64 overflow-y-auto">
          {routeStops.map((stop, index) => (
            <button
              key={stop.stop_id}
              className="w-full flex items-center gap-3 p-3 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors text-left border-b border-gray-100 dark:border-gray-800 last:border-b-0"
              onClick={() => selectStop(stop.stop_id)}
            >
              {/* Stop number */}
              <div
                className="w-6 h-6 rounded-full flex items-center justify-center text-xs font-medium text-white flex-shrink-0"
                style={{ backgroundColor: properties.color }}
              >
                {index + 1}
              </div>

              {/* Stop name */}
              <div className="flex-1 min-w-0">
                <div className="text-sm font-medium dark:text-gray-200 truncate">{stop.name}</div>
              </div>

              {/* Terminus indicators */}
              {index === 0 && (
                <span className="text-xs bg-gray-100 dark:bg-gray-800 px-2 py-0.5 rounded text-gray-600 dark:text-gray-400 flex-shrink-0">
                  Start
                </span>
              )}
              {index === routeStops.length - 1 && (
                <span className="text-xs bg-gray-100 dark:bg-gray-800 px-2 py-0.5 rounded text-gray-600 dark:text-gray-400 flex-shrink-0">
                  End
                </span>
              )}
            </button>
          ))}

          {routeStops.length === 0 && (
            <p className="p-3 text-gray-500 text-sm">No stops found</p>
          )}
        </div>
      </div>

      {/* Route Line Preview */}
      <div className="mt-4 flex items-center gap-2">
        <div
          className="h-2 flex-1 rounded-full"
          style={{ backgroundColor: properties.color }}
        />
        <span className="text-xs text-gray-500">{properties.stop_count} stops</span>
      </div>
    </div>
  );
}
