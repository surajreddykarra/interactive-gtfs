'use client';

import dynamic from 'next/dynamic';
import { useTransit } from '@/context/TransitContext';
import Sidebar from '@/components/Sidebar';
import FilterControls from '@/components/UI/FilterControls';
import DecryptedText from '@/components/UI/DecryptedText';

// Dynamic import for Map component (no SSR)
const TransitMap = dynamic(() => import('@/components/Map'), {
  ssr: false,
  loading: () => (
    <div className="loading-spinner dark:text-white">
      <div className="spinner border-gray-200 border-t-blue-500"></div>
      <p>Loading map...</p>
    </div>
  ),
});

export default function HomePage() {
  const { state, openSidebar, clearSelection } = useTransit();

  if (state.loading) {
    return (
      <div className="h-screen w-screen flex items-center justify-center bg-gray-50 dark:bg-black">
        <div className="loading-spinner text-center">
          <div className="spinner border-4 border-gray-200 border-t-blue-500 rounded-full w-12 h-12 animate-spin mb-4 mx-auto"></div>
          <p className="text-gray-600 dark:text-gray-300 font-mono">
            <DecryptedText text="Loading Hyderabad Transit..." />
          </p>
        </div>
      </div>
    );
  }

  if (state.error) {
    return (
      <div className="h-screen w-screen flex items-center justify-center bg-gray-50 dark:bg-black">
        <div className="text-center p-8">
          <div className="text-6xl mb-4">😞</div>
          <h1 className="text-2xl font-bold text-gray-800 dark:text-white mb-2">Failed to load data</h1>
          <p className="text-gray-600 dark:text-gray-300 mb-4">{state.error}</p>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Make sure the preprocessor has generated the data files.
          </p>
        </div>
      </div>
    );
  }

  return (
    <main className="h-screen w-screen relative overflow-hidden bg-gray-50 dark:bg-black">
      {/* Map */}
      <div className="absolute inset-0">
        <TransitMap />
      </div>

      {/* Sidebar */}
      <Sidebar />

      {/* Clear Selection Pill (top center) */}
      {(state.selection.selectedStop || state.selection.selectedRoute) && (
        <div className="absolute top-4 left-1/2 -translate-x-1/2 z-[1000]">
          <button
            onClick={clearSelection}
            className="bg-white dark:bg-gray-800 px-4 py-2 rounded-full shadow-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors text-gray-700 dark:text-gray-200 flex items-center gap-2 text-sm font-medium"
          >
            <span className="material-symbols-outlined text-base">close</span>
            Clear
          </button>
        </div>
      )}

      {/* Top Left Controls */}
      <div className="absolute top-4 left-4 z-[1000] flex gap-2">
        {!state.sidebarOpen && (
          <button
            onClick={openSidebar}
            className="bg-white dark:bg-gray-800 p-3 rounded-lg shadow-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors text-gray-700 dark:text-gray-200 flex items-center justify-center"
            aria-label="Open sidebar"
          >
            <span className="material-symbols-outlined">menu</span>
          </button>
        )}
      </div>

      {/* Filter Controls (top right) */}
      <div className="absolute top-4 right-4 z-[1000]">
        <FilterControls />
      </div>
    </main>
  );
}
