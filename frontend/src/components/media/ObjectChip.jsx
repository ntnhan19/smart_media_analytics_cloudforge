import React from 'react';

export default function ObjectChip({ obj, onClick, isActive }) {
  if (!obj) return null;

  const count = obj.occurrences?.length || 0;

  return (
    <button
      onClick={() => onClick && onClick(obj)}
      className={`px-[12px] py-[3px] border rounded-[20px] text-[10px] font-bold uppercase tracking-wide transition-all select-none focus:outline-none flex items-center gap-1 ${
        isActive 
          ? 'bg-[#7B5CF5] border-[#7B5CF5] text-white shadow-[0_0_8px_rgba(123,92,245,0.5)]' 
          : 'bg-[#16132A]/40 border-[#7B5CF5]/40 text-white hover:border-[#7B5CF5] hover:bg-[#16132A]/80'
      }`}
    >
      <span>{obj.name}</span>
      {count > 0 && (
        <span className={`text-[8px] px-1 rounded ${
          isActive ? 'bg-white/20 text-white' : 'bg-[#7B5CF5]/20 text-[#c4b5fd]'
        }`}>
          {count}
        </span>
      )}
    </button>
  );
}
