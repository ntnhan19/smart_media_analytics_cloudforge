import React, { useState } from 'react';
import { Search as SearchIcon, X } from 'lucide-react';
import PropTypes from 'prop-types';

export default function SearchBar({ 
  value, 
  onChange, 
  onSearch, 
  placeholder, 
  variant = 'large',
  endAdornment = null,
  disabled = false
}) {
  const [isFocused, setIsFocused] = useState(false);

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

  const containerClasses = `relative w-full flex items-center transition-all duration-300 ${isFocused ? 'scale-[1.01]' : 'scale-100'}`;
  
  const iconClasses = `absolute inset-y-0 left-0 flex items-center pointer-events-none transition-colors duration-300 ${
    isLarge ? 'pl-4' : 'pl-3'
  } ${isFocused ? 'text-[#7B5CF5]' : 'text-gray-400'}`;
  
  const iconSizeClasses = isLarge ? 'h-5 w-5' : 'h-4 w-4';

  const inputClasses = `block w-full text-white placeholder-gray-500 focus:outline-none transition-all duration-300 ${
    isLarge 
      ? 'pl-11 pr-36 py-4 bg-[#16132A] border rounded-xl text-base sm:text-lg ' + (isFocused ? 'border-[#7B5CF5] shadow-[0_0_15px_rgba(123,92,245,0.3)]' : 'border-[#2D2844] hover:border-[#7B5CF5]/50')
      : 'pl-10 pr-[70px] py-1.5 bg-[#0E0B1F] border rounded-[6px] text-sm ' + (isFocused ? 'border-[#7B5CF5] shadow-[0_0_10px_rgba(123,92,245,0.3)]' : 'border-[#4F8EF7]/30 hover:border-[#4F8EF7]/70')
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
        onFocus={() => setIsFocused(true)}
        onBlur={() => setIsFocused(false)}
        disabled={disabled}
        className={`${inputClasses} ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
        placeholder={placeholder || "Search media..."}
      />
      
      {isLarge && (
        <div className="absolute inset-y-0 right-0 pr-2 flex items-center gap-2">
          {value && (
            <button
              onClick={handleClear}
              disabled={disabled}
              className={`p-1.5 rounded-full transition-all duration-200 focus:outline-none ${disabled ? 'text-gray-600 cursor-not-allowed' : 'text-gray-400 hover:text-white hover:bg-white/10'}`}
              title="Clear search"
            >
              <X className="w-5 h-5" />
            </button>
          )}
          <button
            onClick={() => onSearch && onSearch(value)}
            disabled={disabled || !value.trim()}
            className={`px-5 py-2.5 rounded-lg font-bold transition-all duration-300 focus:outline-none ${disabled || !value.trim() ? 'bg-[#7B5CF5]/50 text-white/50 cursor-not-allowed' : 'bg-[#7B5CF5] hover:bg-[#6A4CE5] hover:shadow-[0_0_15px_rgba(123,92,245,0.5)] text-white'}`}
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
              disabled={disabled}
              className={`p-1 rounded-full transition-all duration-200 focus:outline-none ${disabled ? 'text-gray-600 cursor-not-allowed' : 'text-gray-400 hover:text-white hover:bg-white/10'}`}
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
