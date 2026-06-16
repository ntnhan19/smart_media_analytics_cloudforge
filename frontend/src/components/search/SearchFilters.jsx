import React from 'react';
import PropTypes from 'prop-types';
import { Filter, Tag, Clock, Calendar, Target } from 'lucide-react';
import CustomDropdown from '../ui/CustomDropdown';

export default function SearchFilters({ 
  scoreFilter, onScoreChange,
  durationFilter, onDurationChange,
  dateFilter, onDateChange,
  tags, activeTags, onToggleTag 
}) {
  return (
    <div className="flex flex-col gap-4 py-4 border-b border-gray-800">
      <div className="flex items-center gap-2 text-sm font-medium text-gray-400">
        <Filter className="w-4 h-4" />
        <span>Filters</span>
      </div>
      
      <div className="flex flex-wrap items-center gap-4 w-full">
        {/* Confidence Score Filter */}
        <CustomDropdown
          value={scoreFilter}
          onChange={onScoreChange}
          icon={Target}
          options={[
            { value: 'all', label: 'All Scores' },
            { value: 'very_high', label: 'Very High (>90%)' },
            { value: 'high', label: 'High (>70%)' },
            { value: 'medium', label: 'Medium (>50%)' },
          ]}
        />

        {/* Duration Filter */}
        <CustomDropdown
          value={durationFilter}
          onChange={onDurationChange}
          icon={Clock}
          options={[
            { value: 'all', label: 'Any Duration' },
            { value: 'short', label: 'Short (< 1m)' },
            { value: 'medium', label: 'Medium (1m - 5m)' },
            { value: 'long', label: 'Long (> 5m)' },
          ]}
        />

        {/* Date Filter */}
        <CustomDropdown
          value={dateFilter}
          onChange={onDateChange}
          icon={Calendar}
          options={[
            { value: 'all', label: 'Any Date' },
            { value: 'today', label: 'Today' },
            { value: 'this_week', label: 'This Week' },
            { value: 'this_month', label: 'This Month' },
          ]}
        />

        {/* Tags Filter */}
        {tags && tags.length > 0 && (
          <div className="flex items-center gap-2 border-l border-gray-700 pl-4 ml-2 shrink-0">
            <Tag className="w-4 h-4 text-gray-500" />
            <div className="flex items-center gap-2">
              {tags.map(tag => {
                const isActive = activeTags.includes(tag);
                return (
                  <button
                    key={tag}
                    onClick={() => onToggleTag(tag)}
                    className={`px-3 py-1 rounded-md text-xs font-medium transition-colors shrink-0 ${
                      isActive
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-800/50 text-gray-400 border border-gray-700 hover:border-gray-500 hover:text-gray-200'
                    }`}
                  >
                    #{tag}
                  </button>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

SearchFilters.propTypes = {
  scoreFilter: PropTypes.string.isRequired,
  onScoreChange: PropTypes.func.isRequired,
  durationFilter: PropTypes.string.isRequired,
  onDurationChange: PropTypes.func.isRequired,
  dateFilter: PropTypes.string.isRequired,
  onDateChange: PropTypes.func.isRequired,
  tags: PropTypes.arrayOf(PropTypes.string),
  activeTags: PropTypes.arrayOf(PropTypes.string),
  onToggleTag: PropTypes.func,
};

SearchFilters.defaultProps = {
  tags: ['beach', 'mountain', 'city', 'nature', 'indoor', 'snow'],
  activeTags: [],
  onToggleTag: () => {},
};
