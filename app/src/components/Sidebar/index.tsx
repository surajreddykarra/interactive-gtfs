'use client';

/**
 * Sidebar Component - Main navigation and information panel
 */

import { useEffect } from 'react';
import { useTransit } from '@/context/TransitContext';
import StopInfo from './StopInfo';
import RouteInfo from './RouteInfo';
import RouteList from './RouteList';
import SearchBox from '../UI/SearchBox';

export default function Sidebar() {
  const { state, toggleSidebar, clearSelection } = useTransit();
  const { selectedStop, selectedRoute } = state.selection;

  const hasSelection = selectedStop || selectedRoute;

  // Auto-collapse sidebar on mobile when a selection is made
  useEffect(() => {
    if (hasSelection && window.innerWidth <= 768) {
      // Selection made - sidebar will use normal (50%) height via CSS
    }
  }, [hasSelection]);

  return (
    <div className={`sidebar ${!state.sidebarOpen ? 'collapsed' : ''} ${hasSelection ? 'has-selection' : ''}`}>
      {/* Header */}
      <div className="sidebar-header">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold">Hyderabad Transit</h1>
            <p className="text-sm opacity-80">Metro • MMTS • Bus</p>
          </div>
          <button
            onClick={toggleSidebar}
            className="p-2 hover:bg-white/20 rounded-lg transition-colors"
            aria-label="Toggle sidebar"
          >
            <span className="material-symbols-outlined h-5 w-5 flex items-center justify-center sidebar-toggle-icon">
              {state.sidebarOpen ? 'expand_more' : 'expand_less'}
            </span>
            <span className="material-symbols-outlined h-5 w-5 flex items-center justify-center sidebar-toggle-icon-desktop">
              {state.sidebarOpen ? 'chevron_left' : 'chevron_right'}
            </span>
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="sidebar-content">
        {/* Search */}
        <div className="mb-4">
          <SearchBox />
        </div>

        {/* Selected Item Info */}
        {hasSelection && (
          <div className="mb-4">
            <div className="flex items-center justify-between mb-2">
              <h2 className="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide">
                {selectedStop ? 'Selected Stop' : 'Selected Route'}
              </h2>
              <button
                onClick={clearSelection}
                className="text-xs px-2 py-1 rounded bg-gray-100 hover:bg-gray-200 dark:bg-gray-800 dark:hover:bg-gray-700 text-gray-600 dark:text-gray-300 transition-colors font-medium"
              >
                Clear Selection
              </button>
            </div>

            {selectedStop && <StopInfo stopId={selectedStop} />}
            {selectedRoute && <RouteInfo routeId={selectedRoute} />}
          </div>
        )}

        {/* Route List */}
        {!hasSelection && (
          <div>
            <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">
              Routes
            </h2>
            <RouteList />
          </div>
        )}

        {/* Stats Footer */}
        {state.data && (
          <div className="mt-6 pt-4 border-t border-gray-200 dark:border-gray-700">
            <div className="grid grid-cols-3 gap-4 text-center">
              <div>
                <div className="text-2xl font-bold text-metro">
                  {state.data.metadata.agencies.HMRL?.stop_count || 0}
                </div>
                <div className="text-xs text-gray-500">Metro Stops</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-rail">
                  {state.data.metadata.agencies.MMTS?.stop_count || 0}
                </div>
                <div className="text-xs text-gray-500">MMTS Stops</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-bus">
                  {state.data.metadata.agencies.TGSRTC?.stop_count || 0}
                </div>
                <div className="text-xs text-gray-500">Bus Stops</div>
              </div>
            </div>
          </div>
        )}

        {/* Credit */}
        <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700 text-center">
          <a
            href="https://x.com/jarusionn"
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs text-gray-400 hover:text-blue-500 transition-colors"
          >
            made by @jarusionn
          </a>
        </div>
      </div>
    </div>
  );
}
