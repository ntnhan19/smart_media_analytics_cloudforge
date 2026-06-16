import PropTypes from 'prop-types';
import { Icon } from '@iconify/react';
import FilterDropdown from './FilterDropdown';

export default function FilterBar({ mediaFilter, setMediaFilter, sortOrder, setSortOrder }) {
  return (
    <div className="flex flex-wrap items-center gap-[10px] w-full">
      {/* FILTER */}
      <button className="flex items-center justify-center space-x-[4px] w-[69px] h-[26px] border border-sma-purple rounded-[8px] bg-transparent text-white hover:bg-sma-purple/10 transition-colors">
        <Icon icon="mage:filter" width="16" height="16" />
        <span className="text-[10px] leading-[12px] font-inter uppercase">FILTER</span>
      </button>

      {/* MEDIA */}
      <FilterDropdown 
        className="w-[90px]"
        options={['All', 'video', 'image', 'audio']}
        selected={mediaFilter}
        onChange={setMediaFilter}
      />

      {/* ORIENTATION - Placeholder */}
      <button className="flex items-center justify-between px-[10px] w-[94px] h-[26px] border border-sma-purple rounded-[8px] bg-transparent text-white hover:bg-sma-purple/10 transition-colors">
        <span className="text-[10px] leading-[12px] font-inter uppercase">ORIENTATION</span>
        <Icon icon="tabler:chevron-down" width="14" height="14" />
      </button>

      {/* DATE ADDED - Placeholder */}
      <button className="flex items-center justify-between px-[10px] w-[100px] h-[26px] border border-sma-purple rounded-[8px] bg-transparent text-white hover:bg-sma-purple/10 transition-colors">
        <span className="text-[10px] leading-[12px] font-inter uppercase">DATE ADDED</span>
        <Icon icon="tabler:chevron-down" width="14" height="14" />
      </button>

      {/* RESOLUTION - Placeholder */}
      <button className="flex items-center justify-between px-[10px] w-[97px] h-[26px] border border-sma-purple rounded-[8px] bg-transparent text-white hover:bg-sma-purple/10 transition-colors">
        <span className="text-[10px] leading-[12px] font-inter uppercase">RESOLUTION</span>
        <Icon icon="tabler:chevron-down" width="14" height="14" />
      </button>

      {/* SORT BY */}
      <FilterDropdown 
        className="w-[147px] mr-auto"
        options={['Newest', 'Oldest']}
        selected={sortOrder}
        onChange={setSortOrder}
      />

      {/* VIEW TOGGLE */}
      <div className="flex items-center w-[57px] h-[26px] border border-sma-purple rounded-[8px] overflow-hidden ml-auto">
        <button className="flex-1 h-full flex items-center justify-center hover:bg-sma-purple/20 text-white transition-colors">
          <Icon icon="ep:menu" width="14" height="14" />
        </button>
        <div className="w-[1px] h-full bg-sma-purple"></div>
        <button className="flex-1 h-full flex items-center justify-center hover:bg-sma-purple/20 text-white transition-colors">
          <Icon icon="uiw:menu" width="14" height="14" />
        </button>
      </div>
    </div>
  );
}

FilterBar.propTypes = {
  mediaFilter: PropTypes.string.isRequired,
  setMediaFilter: PropTypes.func.isRequired,
  sortOrder: PropTypes.string.isRequired,
  setSortOrder: PropTypes.func.isRequired,
};
