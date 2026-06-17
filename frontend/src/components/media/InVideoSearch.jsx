import React, { useState, useCallback } from 'react';
import { Search } from 'lucide-react';
import { transcriptMock, sceneMock } from '../../mocks/assetDetail';

// Helper: highlight matched text
function HighlightText({ text, query }) {
  if (!query.trim()) return <span>{text}</span>;
  const parts = text.split(new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi'));
  return (
    <>
      {parts.map((part, i) =>
        part.toLowerCase() === query.toLowerCase() ? (
          <mark key={i} className="bg-[#7B5CF5]/40 text-[#c4b5fd] px-0.5 rounded not-italic">{part}</mark>
        ) : (
          <span key={i}>{part}</span>
        )
      )}
    </>
  );
}

function formatTime(sec) {
  const m = Math.floor(sec / 60).toString().padStart(2, '0');
  const s = Math.floor(sec % 60).toString().padStart(2, '0');
  return `${m}:${s}`;
}

export default function InVideoSearch({ assetId, onSeekVideo, searchQuery, onSearchChange, isSearching }) {
  return (
    <div className="flex flex-col">
      {/* Search Title */}
      <p className="font-inter font-bold text-[16px] leading-[19px] text-white mb-[8px]">
        Semantic Search In Video
      </p>

      {/* Search Input */}
      <div className="relative flex items-center">
        <Search className="absolute left-[10px] text-gray-400 pointer-events-none" size={16} />
        <input
          type="text"
          placeholder="bridge..."
          value={searchQuery}
          onChange={(e) => onSearchChange(e.target.value)}
          className={`w-full bg-[#0E0B1F] border rounded-[6px] py-[10px] pl-[34px] pr-[34px] text-[14px] transition-all focus:outline-none placeholder-gray-500/70 ${
            searchQuery 
              ? 'text-[#7B5CF5] font-bold border-[#7B5CF5] bg-[#16132A]/20' 
              : 'text-white/60 font-normal border-[#1e1b35]'
          }`}
        />
        {/* Loading Spinner */}
        {isSearching && (
          <div className="absolute right-[34px] w-3.5 h-3.5 border-2 border-[#7B5CF5] border-t-transparent rounded-full animate-spin" />
        )}
        {/* Filter icon */}
        <button className="absolute right-[10px] text-gray-400 hover:text-white">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3" />
          </svg>
        </button>
      </div>
    </div>
  );
}
