import PropTypes from 'prop-types';
import { Filter, Tag, Target } from 'lucide-react';
import CustomDropdown from '../ui/CustomDropdown';

export default function SearchFilters({
  scoreFilter, onScoreChange,
  tags, activeTags, onToggleTag,
  mediaTypes, activeMediaTypes, onToggleMediaType,
  topK, onTopKChange,
  disabled = false,
  hideScoreAndTopK = false,
  isLoadingTags = false,
  isErrorTags = false,
  onRetryTags = () => {}
}) {
  return (
    <div className="flex flex-col gap-3 py-2 border-b border-gray-200 dark:border-[#2D2844] transition-colors">
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
          <div className={`flex items-center gap-2 ${!hideScoreAndTopK ? 'border-l border-gray-300 dark:border-gray-700 pl-3 ml-1 transition-colors' : ''} shrink-0`}>
            <div className="flex items-center gap-1.5">
              {mediaTypes.map(type => {
                const isActive = activeMediaTypes.includes(type);
                return (
                  <button
                    key={type}
                    disabled={disabled}
                    onClick={() => onToggleMediaType(type)}
                    className={`px-3 py-1 rounded-md text-[11px] font-medium transition-colors shrink-0 capitalize ${disabled
                        ? (isActive ? 'bg-[#7B5CF5]/50 text-white/50 cursor-not-allowed' : 'bg-gray-100 dark:bg-gray-800/20 text-gray-400 dark:text-gray-700 border border-gray-200 dark:border-gray-800 cursor-not-allowed')
                        : (isActive
                          ? 'bg-[#7B5CF5] text-white shadow-[0_0_10px_rgba(123,92,245,0.4)]'
                          : 'bg-white dark:bg-gray-800/50 text-gray-600 dark:text-gray-400 border border-gray-300 dark:border-gray-700 hover:border-gray-400 dark:hover:border-gray-500 hover:text-gray-900 dark:hover:text-gray-200')
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
        {isErrorTags ? (
          <div className="flex items-center gap-2 border-l border-gray-300 dark:border-gray-700 pl-3 ml-1 shrink-0 transition-colors">
            <Tag className="w-3.5 h-3.5 text-red-500/70" />
            <button type="button" onClick={onRetryTags} className="text-[11px] font-medium text-red-500 hover:text-red-600 dark:text-red-400 dark:hover:text-red-300 transition-colors flex items-center gap-1 bg-red-50 dark:bg-red-500/10 px-2 py-1 rounded-md">
              Failed to load tags. Click to retry.
            </button>
          </div>
        ) : isLoadingTags ? (
          <div className="flex items-center gap-2 border-l border-gray-300 dark:border-gray-700 pl-3 ml-1 shrink-0 transition-colors">
            <Tag className={`w-3.5 h-3.5 text-gray-400 dark:text-gray-700 transition-colors`} />
            <div className="flex items-center gap-1.5">
              <div className="w-14 h-6 bg-gray-200 dark:bg-gray-800/50 rounded-md animate-pulse transition-colors"></div>
              <div className="w-12 h-6 bg-gray-200 dark:bg-gray-800/50 rounded-md animate-pulse transition-colors"></div>
              <div className="w-16 h-6 bg-gray-200 dark:bg-gray-800/50 rounded-md animate-pulse transition-colors"></div>
            </div>
          </div>
        ) : tags && tags.length > 0 && (
          <div className="flex items-center gap-2 border-l border-gray-300 dark:border-gray-700 pl-3 ml-1 shrink-0 transition-colors">
            <Tag className={`w-3.5 h-3.5 ${disabled ? 'text-gray-400 dark:text-gray-700' : 'text-gray-600 dark:text-gray-500'} transition-colors`} />
            <div className="flex items-center gap-1.5 flex-wrap">
              {tags.map((tagItem, index) => {
                const tagValue = typeof tagItem === 'object' ? tagItem.tag : tagItem;
                const count = typeof tagItem === 'object' ? tagItem.count : null;
                // Fallback key nếu lỡ tagValue bị undefined
                const key = tagValue || `tag-${index}`;
                const isActive = activeTags.includes(tagValue);
                
                return (
                  <button
                    key={key}
                    disabled={disabled}
                    onClick={() => onToggleTag(tagValue)}
                    className={`px-2.5 py-1 rounded-md text-[11px] font-medium transition-colors shrink-0 flex items-center gap-1 ${disabled
                        ? (isActive ? 'bg-[#7B5CF5]/50 text-white/50 cursor-not-allowed' : 'bg-gray-100 dark:bg-gray-800/20 text-gray-400 dark:text-gray-700 border border-gray-200 dark:border-gray-800 cursor-not-allowed')
                        : (isActive
                          ? 'bg-[#7B5CF5] text-white shadow-[0_0_10px_rgba(123,92,245,0.4)]'
                          : 'bg-white dark:bg-gray-800/50 text-gray-600 dark:text-gray-400 border border-gray-300 dark:border-gray-700 hover:border-gray-400 dark:hover:border-gray-500 hover:text-gray-900 dark:hover:text-gray-200')
                      }`}
                  >
                    <span>#{tagValue}</span>
                    {count !== null && (
                      <span className={`text-[9px] px-1 py-0.5 rounded-sm ${isActive ? 'bg-white/20 text-white' : 'bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400'}`}>
                        {count}
                      </span>
                    )}
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
  tags: PropTypes.arrayOf(
    PropTypes.oneOfType([
      PropTypes.string,
      PropTypes.shape({
        tag: PropTypes.string,
        count: PropTypes.number
      })
    ])
  ),
  activeTags: PropTypes.arrayOf(PropTypes.string),
  onToggleTag: PropTypes.func,
  mediaTypes: PropTypes.arrayOf(PropTypes.string),
  activeMediaTypes: PropTypes.arrayOf(PropTypes.string),
  onToggleMediaType: PropTypes.func,
  topK: PropTypes.oneOfType([PropTypes.number, PropTypes.string]),
  onTopKChange: PropTypes.func,
  disabled: PropTypes.bool,
  hideScoreAndTopK: PropTypes.bool,
  isLoadingTags: PropTypes.bool,
  isErrorTags: PropTypes.bool,
  onRetryTags: PropTypes.func,
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
  isLoadingTags: false,
  scoreFilter: 'all',
  onScoreChange: () => { },
};