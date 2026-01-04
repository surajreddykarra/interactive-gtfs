'use client';

/**
 * Search Box - Search for stops and routes with transit type filtering
 */

import { useState, useMemo, useCallback, useRef, useEffect } from 'react';
import { useTransit } from '@/context/TransitContext';
import { matchesSearch, TRANSIT_ICONS, TRANSIT_LABELS } from '@/lib/utils';
import type { TransitType } from '@/lib/types';

type SearchCategory = 'all' | 'stops' | 'routes';

interface SearchResult {
  type: 'stop' | 'route';
  id: string;
  name: string;
  transitType: TransitType;
  subtitle?: string;
}

export default function SearchBox() {
  const { state, selectStop, selectRoute, toggleFilter } = useTransit();
  const [query, setQuery] = useState('');
  const [isOpen, setIsOpen] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const [category, setCategory] = useState<SearchCategory>('all');
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLDivElement>(null);

  // Derive active transit filter from context filters
  // 'all' means all types are enabled (or none are), otherwise show the single enabled type
  const activeTransitFilter = useMemo((): TransitType | 'all' => {
    const { metro, rail, bus } = state.filters;
    const enabledCount = [metro, rail, bus].filter(Boolean).length;
    
    // If all are off or all are on, treat as 'all'
    if (enabledCount === 0 || enabledCount === 3) return 'all';
    
    // If exactly one is enabled, return that type
    if (metro && !rail && !bus) return 'metro';
    if (rail && !metro && !bus) return 'rail';
    if (bus && !metro && !rail) return 'bus';
    
    // Multiple but not all - treat as 'all' for search purposes
    return 'all';
  }, [state.filters]);

  // Search results with filtering
  const results = useMemo((): SearchResult[] => {
    if (!state.data) return [];

    const searchResults: SearchResult[] = [];
    const lowerQuery = query.toLowerCase().trim();
    const hasQuery = lowerQuery.length >= 2;

    // Search stops
    if (category === 'all' || category === 'stops') {
      let stopCount = 0;
      const maxStops = category === 'stops' ? 20 : 8;
      
      for (const stop of state.data.stops.features) {
        if (stopCount >= maxStops) break;
        
        // Apply transit type filter from context
        if (activeTransitFilter !== 'all' && stop.properties.transit_type !== activeTransitFilter) {
          continue;
        }
        
        // If no query, show all (up to max); if query, filter by search
        if (!hasQuery || matchesSearch(stop.properties.name, lowerQuery)) {
          searchResults.push({
            type: 'stop',
            id: stop.properties.stop_id,
            name: stop.properties.name,
            transitType: stop.properties.transit_type,
            subtitle: `${stop.properties.route_count} routes`,
          });
          stopCount++;
        }
      }
    }

    // Search routes
    if (category === 'all' || category === 'routes') {
      let routeCount = 0;
      const maxRoutes = category === 'routes' ? 20 : 8;
      
      for (const route of state.data.routes.features) {
        if (routeCount >= maxRoutes) break;
        
        // Apply transit type filter from context
        const routeTransitType = route.properties.type_name as TransitType;
        if (activeTransitFilter !== 'all' && routeTransitType !== activeTransitFilter) {
          continue;
        }
        
        const name = route.properties.name;
        const shortName = route.properties.short_name;
        const longName = route.properties.long_name;

        // If no query, show all (up to max); if query, filter by search
        if (
          !hasQuery ||
          matchesSearch(name, lowerQuery) ||
          matchesSearch(shortName, lowerQuery) ||
          matchesSearch(longName, lowerQuery)
        ) {
          searchResults.push({
            type: 'route',
            id: route.properties.route_id,
            name: route.properties.name,
            transitType: routeTransitType,
            subtitle: `${route.properties.stop_count} stops`,
          });
          routeCount++;
        }
      }
    }

    return searchResults;
  }, [state.data, query, category, activeTransitFilter]);

  // Group results by type for display
  const groupedResults = useMemo(() => {
    const stops = results.filter(r => r.type === 'stop');
    const routes = results.filter(r => r.type === 'route');
    return { stops, routes };
  }, [results]);

  // Handle keyboard navigation
  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (!isOpen || results.length === 0) return;

      switch (e.key) {
        case 'ArrowDown':
          e.preventDefault();
          setSelectedIndex((prev) =>
            prev < results.length - 1 ? prev + 1 : prev
          );
          break;
        case 'ArrowUp':
          e.preventDefault();
          setSelectedIndex((prev) => (prev > 0 ? prev - 1 : prev));
          break;
        case 'Enter':
          e.preventDefault();
          if (selectedIndex >= 0 && selectedIndex < results.length) {
            handleSelect(results[selectedIndex]);
          }
          break;
        case 'Escape':
          setIsOpen(false);
          setSelectedIndex(-1);
          break;
      }
    },
    [isOpen, results, selectedIndex]
  );

  const handleSelect = useCallback(
    (result: SearchResult) => {
      if (result.type === 'stop') {
        selectStop(result.id);
      } else {
        selectRoute(result.id);
      }
      setQuery('');
      setIsOpen(false);
      setSelectedIndex(-1);
    },
    [selectStop, selectRoute]
  );

  // Close on outside click
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (
        inputRef.current &&
        !inputRef.current.contains(e.target as Node) &&
        listRef.current &&
        !listRef.current.contains(e.target as Node)
      ) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Scroll selected item into view
  useEffect(() => {
    if (selectedIndex >= 0 && listRef.current) {
      const items = listRef.current.querySelectorAll('[data-result-item]');
      const selectedElement = items[selectedIndex] as HTMLElement;
      if (selectedElement) {
        selectedElement.scrollIntoView({ block: 'nearest' });
      }
    }
  }, [selectedIndex]);

  const transitTypes: (TransitType | 'all')[] = ['all', 'metro', 'rail', 'bus'];
  const categories: { value: SearchCategory; label: string }[] = [
    { value: 'all', label: 'All' },
    { value: 'stops', label: 'Stops' },
    { value: 'routes', label: 'Routes' },
  ];

  return (
    <div className="search-box-wrapper">
      {/* Filter Tabs */}
      <div className="flex gap-1 mb-2">
        {/* Category filters */}
        <div className="flex bg-gray-100 dark:bg-gray-800 rounded-lg p-0.5 flex-1">
          {categories.map((cat) => (
            <button
              key={cat.value}
              onClick={() => {
                setCategory(cat.value);
                setSelectedIndex(-1);
              }}
              className={`flex-1 px-2 py-1 text-xs font-medium rounded-md transition-colors ${
                category === cat.value
                  ? 'bg-white dark:bg-gray-600 text-gray-900 dark:text-white shadow-sm'
                  : 'text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white'
              }`}
            >
              {cat.label}
            </button>
          ))}
        </div>
      </div>

      {/* Transit Type Filter - Controls both search results and map visibility */}
      <div className="flex gap-1 mb-2">
        {transitTypes.map((type) => (
          <button
            key={type}
            onClick={() => {
              if (type === 'all') {
                // Enable all types
                if (!state.filters.metro) toggleFilter('metro');
                if (!state.filters.rail) toggleFilter('rail');
                if (!state.filters.bus) toggleFilter('bus');
              } else {
                // Toggle to show only this type (disable others, enable this one)
                const isCurrentlySelected = activeTransitFilter === type;
                if (isCurrentlySelected) {
                  // If clicking the already-selected type, go back to 'all'
                  if (!state.filters.metro) toggleFilter('metro');
                  if (!state.filters.rail) toggleFilter('rail');
                  if (!state.filters.bus) toggleFilter('bus');
                } else {
                  // Select only this type
                  if (state.filters.metro && type !== 'metro') toggleFilter('metro');
                  if (state.filters.rail && type !== 'rail') toggleFilter('rail');
                  if (state.filters.bus && type !== 'bus') toggleFilter('bus');
                  if (!state.filters[type]) toggleFilter(type);
                }
              }
              setSelectedIndex(-1);
            }}
            className={`flex-1 px-2 py-1.5 text-xs font-medium rounded-lg transition-colors flex items-center justify-center gap-1 border-2 ${
              activeTransitFilter === type
                ? type === 'all'
                  ? 'bg-gray-700 dark:bg-gray-600 text-white border-transparent'
                  : type === 'metro'
                  ? 'bg-metro/20 text-metro border-metro'
                  : type === 'rail'
                  ? 'bg-rail/20 text-rail border-rail'
                  : 'bg-bus/20 text-bus border-bus'
                : 'bg-transparent text-gray-600 dark:text-gray-300 border-transparent hover:bg-gray-100 dark:hover:bg-gray-800'
            }`}
          >
            {type === 'all' ? (
              'All'
            ) : (
              <>
                <span className="material-symbols-outlined text-base">{TRANSIT_ICONS[type]}</span>
                <span className="hidden sm:inline">{type === 'rail' ? 'MMTS' : type.charAt(0).toUpperCase() + type.slice(1)}</span>
              </>
            )}
          </button>
        ))}
      </div>

      {/* Search Input */}
      <div className="search-box relative">
        <span className="material-symbols-outlined search-icon w-5 h-5 flex items-center justify-center">search</span>

        <input
          ref={inputRef}
          type="text"
          placeholder={`Search ${category === 'all' ? 'stops & routes' : category}${activeTransitFilter !== 'all' ? ` in ${TRANSIT_LABELS[activeTransitFilter]}` : ''}...`}
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            setIsOpen(true);
            setSelectedIndex(-1);
          }}
          onFocus={() => setIsOpen(true)}
          onKeyDown={handleKeyDown}
        />

        {/* Clear button */}
        {query && (
          <button
            onClick={() => {
              setQuery('');
              setSelectedIndex(-1);
              inputRef.current?.focus();
            }}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
          >
            <span className="material-symbols-outlined w-4 h-4 flex items-center justify-center text-sm">close</span>
          </button>
        )}

        {/* Results Dropdown */}
        {isOpen && results.length > 0 && (
          <div
            ref={listRef}
            className="absolute top-full left-0 right-0 mt-1 bg-white dark:bg-gray-900 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 max-h-72 overflow-y-auto z-50"
          >
            {/* Stops Section */}
            {groupedResults.stops.length > 0 && (
              <>
                <div className="px-3 py-1.5 bg-gray-50 dark:bg-gray-800 text-xs font-semibold text-gray-500 dark:text-gray-300 uppercase tracking-wide sticky top-0 flex items-center gap-1">
                  <span className="material-symbols-outlined text-sm">hail</span> Stops ({groupedResults.stops.length})
                </div>
                {groupedResults.stops.map((result, index) => (
                  <button
                    key={`stop-${result.id}`}
                    data-result-item
                    className={`w-full flex items-center gap-3 p-3 text-left hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors ${
                      index === selectedIndex ? 'bg-blue-50 dark:bg-gray-700' : ''
                    }`}
                    onClick={() => handleSelect(result)}
                  >
                    <span className="material-symbols-outlined text-lg">{TRANSIT_ICONS[result.transitType]}</span>
                    <div className="flex-1 min-w-0">
                      <div className="font-medium text-sm truncate dark:text-gray-200">{result.name}</div>
                      <div className="text-xs text-gray-500 dark:text-gray-400">
                        <span className={`inline-block px-1.5 py-0.5 rounded text-white text-[10px] mr-1 ${
                          result.transitType === 'metro' ? 'bg-metro' :
                          result.transitType === 'rail' ? 'bg-rail' : 'bg-bus'
                        }`}>
                          {TRANSIT_LABELS[result.transitType]}
                        </span>
                        {result.subtitle}
                      </div>
                    </div>
                  </button>
                ))}
              </>
            )}

            {/* Routes Section */}
            {groupedResults.routes.length > 0 && (
              <>
                <div className="px-3 py-1.5 bg-gray-50 dark:bg-gray-800 text-xs font-semibold text-gray-500 dark:text-gray-300 uppercase tracking-wide sticky top-0 flex items-center gap-1">
                  <span className="material-symbols-outlined text-sm">route</span> Routes ({groupedResults.routes.length})
                </div>
                {groupedResults.routes.map((result, index) => {
                  const actualIndex = groupedResults.stops.length + index;
                  return (
                    <button
                      key={`route-${result.id}`}
                      data-result-item
                      className={`w-full flex items-center gap-3 p-3 text-left hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors ${
                        actualIndex === selectedIndex ? 'bg-blue-50 dark:bg-gray-700' : ''
                      }`}
                      onClick={() => handleSelect(result)}
                    >
                      <span className="material-symbols-outlined text-lg">{TRANSIT_ICONS[result.transitType]}</span>
                      <div className="flex-1 min-w-0">
                        <div className="font-medium text-sm truncate dark:text-gray-200">{result.name}</div>
                        <div className="text-xs text-gray-500 dark:text-gray-400">
                          <span className={`inline-block px-1.5 py-0.5 rounded text-white text-[10px] mr-1 ${
                            result.transitType === 'metro' ? 'bg-metro' :
                            result.transitType === 'rail' ? 'bg-rail' : 'bg-bus'
                          }`}>
                            {TRANSIT_LABELS[result.transitType]}
                          </span>
                          {result.subtitle}
                        </div>
                      </div>
                    </button>
                  );
                })}
              </>
            )}
          </div>
        )}

        {/* No Results */}
        {isOpen && query.length >= 2 && results.length === 0 && (
          <div className="absolute top-full left-0 right-0 mt-1 bg-white dark:bg-gray-900 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 p-4 text-center text-gray-500 dark:text-gray-400 text-sm z-50">
            No {category === 'all' ? 'results' : category} found 
            {activeTransitFilter !== 'all' && ` in ${TRANSIT_LABELS[activeTransitFilter]}`} 
            {` for "${query}"`}
          </div>
        )}
      </div>
    </div>
  );
}
