'use client';

/**
 * Stop Info Panel - Shows details about a selected stop
 */

import { useMemo } from 'react';
import { useTransit } from '@/context/TransitContext';
import type { RouteFeature } from '@/lib/types';
import {
  TRANSIT_ICONS,
  TRANSIT_LABELS,
  formatTimeRange,
} from '@/lib/utils';

interface StopInfoProps {
  stopId: string;
}

export default function StopInfo({ stopId }: StopInfoProps) {
  const { state, selectRoute, getSelectedStopData } = useTransit();

  const stopData = useMemo(() => getSelectedStopData(), [getSelectedStopData, stopId]);

  // Get route details for routes serving this stop
  const routeDetails = useMemo(() => {
    if (!state.data || !stopData) return [];

    const routeIds = stopData.properties.routes;
    return routeIds
      .map((routeId) =>
        state.data!.routes.features.find((r) => r.properties.route_id === routeId)
      )
      .filter((r): r is RouteFeature => r !== undefined);
  }, [state.data, stopData]);

  // Get timetable for this stop
  const stopTimetable = useMemo(() => {
    if (!state.data) return null;
    return state.data.timetable[stopId] || null;
  }, [state.data, stopId]);

  if (!stopData) {
    return (
      <div className="stop-info-panel">
        <p className="text-gray-500">Stop not found</p>
      </div>
    );
  }

  const { properties } = stopData;

  return (
    <div className="stop-info-panel">
      {/* Header */}
      <div className="flex items-start gap-3 mb-4">
        <span className="material-symbols-outlined text-3xl">{TRANSIT_ICONS[properties.transit_type]}</span>
        <div>
          <h3 className="font-semibold text-lg dark:text-white">{properties.name}</h3>
          <span className={`transit-badge ${properties.transit_type}`}>
            {TRANSIT_LABELS[properties.transit_type]}
          </span>
        </div>
      </div>

      {/* Service Hours */}
      <div className="mb-4 p-3 bg-white dark:bg-gray-900 rounded-lg">
        <div className="text-xs text-gray-500 dark:text-gray-400 uppercase mb-1">Service Hours</div>
        <div className="font-medium dark:text-gray-200">
          {formatTimeRange(properties.first_time, properties.last_time)}
        </div>
      </div>

      {/* Routes */}
      <div className="routes-list">
        <div className="text-xs text-gray-500 dark:text-gray-400 uppercase mb-2">
          Routes ({routeDetails.length})
        </div>
        <div className="flex flex-wrap gap-2">
          {routeDetails.map((route) => (
            <button
              key={route.properties.route_id}
              className="route-chip"
              onClick={() => selectRoute(route.properties.route_id)}
              style={{ borderLeftColor: route.properties.color, borderLeftWidth: 3 }}
            >
              <span
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: route.properties.color }}
              />
              <span>{route.properties.name}</span>
            </button>
          ))}
        </div>

        {routeDetails.length === 0 && (
          <p className="text-gray-500 dark:text-gray-400 text-sm">No routes found</p>
        )}
      </div>

      {/* Timetable Preview */}
      {stopTimetable && Object.keys(stopTimetable).length > 0 && (
        <div className="mt-4">
          <div className="text-xs text-gray-500 dark:text-gray-400 uppercase mb-2">Next Departures</div>
          <div className="bg-white dark:bg-gray-900 rounded-lg p-3 max-h-48 overflow-y-auto">
            {Object.entries(stopTimetable)
              .slice(0, 3)
              .map(([routeId, times]) => {
                const route = state.data?.routes.features.find(
                  (r) => r.properties.route_id === routeId
                );
                const weekdayTimes = times.weekday?.slice(0, 5) || [];

                return (
                  <div key={routeId} className="mb-2 last:mb-0">
                    <div
                      className="text-sm font-medium mb-1"
                      style={{ color: route?.properties.color }}
                    >
                      {route?.properties.name || routeId}
                    </div>
                    <div className="flex flex-wrap gap-1">
                      {weekdayTimes.map((time, i) => (
                        <span
                          key={i}
                          className="text-xs bg-gray-100 dark:bg-gray-700 px-2 py-0.5 rounded"
                        >
                          {time}
                        </span>
                      ))}
                      {weekdayTimes.length > 0 && (
                        <span className="text-xs text-gray-400">...</span>
                      )}
                    </div>
                  </div>
                );
              })}
          </div>
        </div>
      )}
    </div>
  );
}
