'use client';

/**
 * Filter Controls - Toggle visibility of transit types
 */

import { useTransit } from '@/context/TransitContext';
import { TRANSIT_ICONS, TRANSIT_LABELS } from '@/lib/utils';
import type { TransitType } from '@/lib/types';

export default function FilterControls() {
  const { state, toggleFilter } = useTransit();

  const transitTypes: TransitType[] = ['metro', 'rail', 'bus'];

  return (
    <div className="flex flex-col gap-2 p-2 transition-colors">
      {transitTypes.map((type) => (
        <button
          key={type}
          className={`filter-btn ${type} ${state.filters[type] ? 'active' : ''}`}
          onClick={() => toggleFilter(type)}
          title={`Toggle ${TRANSIT_LABELS[type]}`}
        >
          <span className="material-symbols-outlined text-lg">{TRANSIT_ICONS[type]}</span>
          <span className="hidden sm:inline">{type === 'rail' ? 'MMTS' : type.charAt(0).toUpperCase() + type.slice(1)}</span>
        </button>
      ))}
    </div>
  );
}
