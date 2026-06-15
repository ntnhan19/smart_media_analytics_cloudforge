import React from 'react';
import { Search as SearchIcon, X } from 'lucide-react';
import PropTypes from 'prop-types';

export default function SearchBar({ 
  value, 
  onChange, 
  onSearch, 
  placeholder, 
  variant = 'large',
  endAdornment = null 
}) {
  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && onSearch) {
      onSearch(value);
    }
  };

  const handleClear = () => {
    onChange('');
    if (onSearch) {
      onSearch('');
    }
  };

  const isLarge = variant === 'large';

  const containerClasses = "relative w-full flex items-center";
  
  const iconClasses = `absolute inset-y-0 left-0 flex items-center pointer-events-none ${
    isLarge ? 'pl-4' : 'pl-3'
  }`;
  
  const iconSizeClasses = `text-gray-500 ${
    isLarge ? 'h-5 w-5' : 'h-4 w-4'
  }`;

  const inputClasses = `block w-full text-gray-100 placeholder-gray-500 focus:outline-none transition-shadow ${
    isLarge 
      ? 'pl-11 pr-36 py-4 bg-gray-900 border border-gray-700 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent text-base sm:text-lg'
      : 'pl-10 pr-[70px] py-1.5 bg-[#0E0B1F] border border-[#4F8EF7]/30 rounded-[6px] focus:border-[#4F8EF7] text-sm'
  }`;

  return (
    <div className={containerClasses}>
      <div className={iconClasses}>
        <SearchIcon className={iconSizeClasses} />
      </div>
      
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={handleKeyDown}
        className={inputClasses}
        placeholder={placeholder || "Search media..."}
      />
      
      {isLarge && (
        <div className="absolute inset-y-0 right-0 pr-2 flex items-center gap-2">
          {value && (
            <button
              onClick={handleClear}
              className="p-1.5 text-gray-500 hover:text-gray-300 hover:bg-gray-800 rounded-full transition-colors focus:outline-none"
              title="Clear search"
            >
              <X className="w-5 h-5" />
            </button>
          )}
          <button
            onClick={() => onSearch && onSearch(value)}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-gray-900 focus:ring-blue-500"
          >
            Search
          </button>
        </div>
      )}

      {!isLarge && (
        <div className="absolute right-2 flex items-center gap-1">
          {value && (
            <button
              onClick={handleClear}
              className="p-1 text-gray-500 hover:text-gray-300 rounded-full transition-colors focus:outline-none"
              title="Clear search"
            >
              <X className="w-4 h-4" />
            </button>
          )}
          {endAdornment && <div>{endAdornment}</div>}
        </div>
      )}
    </div>
  );
}

SearchBar.propTypes = {
  value: PropTypes.string.isRequired,
  onChange: PropTypes.func.isRequired,
  onSearch: PropTypes.func,
  placeholder: PropTypes.string,
  variant: PropTypes.oneOf(['large', 'compact']),
  endAdornment: PropTypes.node,
};
