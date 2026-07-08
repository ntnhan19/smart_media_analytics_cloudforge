import { Search } from 'lucide-react';

export default function InVideoSearch({ searchQuery, onSearchChange, isSearching }) {
  return (
    <div className="flex flex-col">
      {/* Search Title */}
      <p className="font-inter font-bold text-[16px] leading-[19px] text-gray-900 dark:text-white mb-[8px] transition-colors">
        Semantic Search In Video
      </p>

      {/* Search Input */}
      <div className="relative flex items-center">
        <Search className="absolute left-[10px] text-gray-400 dark:text-gray-500 pointer-events-none" size={16} />
        <input
          type="text"
          placeholder="bridge..."
          value={searchQuery}
          onChange={(e) => onSearchChange(e.target.value)}
          className={`w-full bg-white dark:bg-[#0E0B1F] border rounded-[6px] py-[10px] pl-[34px] pr-[34px] text-[14px] transition-all focus:outline-none placeholder-gray-400 dark:placeholder-gray-500 ${
            searchQuery 
              ? 'text-[#7B5CF5] font-bold border-[#7B5CF5] bg-[#7B5CF5]/5 dark:bg-[#16132A]/20' 
              : 'text-gray-700 dark:text-white/60 font-normal border-gray-300 dark:border-[#1e1b35]'
          }`}
        />
        {/* Loading Spinner */}
        {isSearching && (
          <div className="absolute right-[34px] w-3.5 h-3.5 border-2 border-[#7B5CF5] border-t-transparent rounded-full animate-spin" />
        )}
        {/* Filter icon */}
        <button className="absolute right-[10px] text-gray-400 hover:text-gray-700 dark:hover:text-white transition-colors">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3" />
          </svg>
        </button>
      </div>
    </div>
  );
}
