import React from 'react';
import PropTypes from 'prop-types';
import { Filter, Tag, Target } from 'lucide-react';
import CustomDropdown from '../ui/CustomDropdown';

export default function SearchFilters({
  scoreFilter, onScoreChange,
  tags, activeTags, onToggleTag,
  mediaTypes, activeMediaTypes, onToggleMediaType,
  topK, onTopKChange,
  disabled = false,
  hideScoreAndTopK = false
}) {
  return (
    <div className="flex flex-col gap-3 py-2 border-b border-[#2D2844]">
      <div className="flex flex-wrap items-center gap-3 w-full">
        {/* Confidence Score Filter */}
        {!hideScoreAndTopK && (
          <CustomDropdown
            value={scoreFilter}
            onChange={onScoreChange}
            icon={Target}
            disabled={disabled}
            options={[
              { value: 'all', label: 'All Scores' },
              { value: 'very_high', label: 'Very High (>90%)' },
              { value: 'high', label: 'High (>70%)' },
              { value: 'medium', label: 'Medium (>50%)' },
            ]}
          />
        )}

        {/* Top K Results Filter */}
        {!hideScoreAndTopK && (
          <CustomDropdown
            value={topK?.toString()}
            onChange={onTopKChange}
            icon={Filter}
            disabled={disabled}
            options={[
              { value: '10', label: '10 Results' },
              { value: '20', label: '20 Results' },
              { value: '50', label: '50 Results' },
            ]}
          />
        )}

        {/* Media Types Filter */}
        {mediaTypes && mediaTypes.length > 0 && (
          <div className={`flex items-center gap-2 ${!hideScoreAndTopK ? 'border-l border-gray-700 pl-3 ml-1' : ''} shrink-0`}>
            <div className="flex items-center gap-1.5">
              {mediaTypes.map(type => {
                const isActive = activeMediaTypes.includes(type);
                return (
                  <button
                    key={type}
                    disabled={disabled}
                    onClick={() => onToggleMediaType(type)}
                    className={`px-3 py-1 rounded-md text-[11px] font-medium transition-colors shrink-0 capitalize ${disabled
                        ? (isActive ? 'bg-[#7B5CF5]/50 text-white/50 cursor-not-allowed' : 'bg-gray-800/20 text-gray-700 border border-gray-800 cursor-not-allowed')
                        : (isActive
                          ? 'bg-[#7B5CF5] text-white shadow-[0_0_10px_rgba(123,92,245,0.4)]'
                          : 'bg-gray-800/50 text-gray-400 border border-gray-700 hover:border-gray-500 hover:text-gray-200')
                      }`}
                  >
                    {type}
                  </button>
                );
              })}
            </div>
          </div>
        )}

        {/* Tags Filter */}
        {tags && tags.length > 0 && (
          <div className="flex items-center gap-2 border-l border-gray-700 pl-3 ml-1 shrink-0">
            <Tag className={`w-3.5 h-3.5 ${disabled ? 'text-gray-700' : 'text-gray-500'}`} />
            <div className="flex items-center gap-1.5">
              {tags.map(tag => {
                const isActive = activeTags.includes(tag);
                return (
                  <button
                    key={tag}
                    disabled={disabled}
                    onClick={() => onToggleTag(tag)}
                    className={`px-2.5 py-1 rounded-md text-[11px] font-medium transition-colors shrink-0 ${disabled
                        ? (isActive ? 'bg-[#7B5CF5]/50 text-white/50 cursor-not-allowed' : 'bg-gray-800/20 text-gray-700 border border-gray-800 cursor-not-allowed')
                        : (isActive
                          ? 'bg-[#7B5CF5] text-white shadow-[0_0_10px_rgba(123,92,245,0.4)]'
                          : 'bg-gray-800/50 text-gray-400 border border-gray-700 hover:border-gray-500 hover:text-gray-200')
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
  scoreFilter: PropTypes.string,
  onScoreChange: PropTypes.func,
  tags: PropTypes.arrayOf(PropTypes.string),
  activeTags: PropTypes.arrayOf(PropTypes.string),
  onToggleTag: PropTypes.func,
  mediaTypes: PropTypes.arrayOf(PropTypes.string),
  activeMediaTypes: PropTypes.arrayOf(PropTypes.string),
  onToggleMediaType: PropTypes.func,
  topK: PropTypes.oneOfType([PropTypes.number, PropTypes.string]),
  onTopKChange: PropTypes.func,
  disabled: PropTypes.bool,
  hideScoreAndTopK: PropTypes.bool,
};

SearchFilters.defaultProps = {
  tags: ['beach', 'mountain', 'city', 'nature', 'indoor', 'snow'],
  activeTags: [],
  onToggleTag: () => { },
  mediaTypes: ['video', 'image', 'audio'],
  activeMediaTypes: ['video'],
  onToggleMediaType: () => { },
  topK: 20,
  onTopKChange: () => { },
  disabled: false,
  hideScoreAndTopK: false,
  scoreFilter: 'all',
  onScoreChange: () => { },
};