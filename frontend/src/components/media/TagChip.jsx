import React from 'react';

export default function TagChip({ tag, onClick, isActive }) {
  if (!tag) return null;

  // Map category to color classes
  let colorClasses = 'border-gray-700 text-gray-300 hover:border-gray-500';
  if (tag.category === 'location') {
    colorClasses = isActive 
      ? 'bg-[#4F8EF7] border-[#4F8EF7] text-white' 
      : 'bg-[#4F8EF7]/10 border-[#4F8EF7]/40 text-[#4F8EF7] hover:bg-[#4F8EF7]/20';
  } else if (tag.category === 'content_type') {
    colorClasses = isActive 
      ? 'bg-[#4ADE80] border-[#4ADE80] text-black' 
      : 'bg-[#4ADE80]/10 border-[#4ADE80]/40 text-[#4ADE80] hover:bg-[#4ADE80]/20';
  } else if (tag.category === 'theme') {
    colorClasses = isActive 
      ? 'bg-[#7B5CF5] border-[#7B5CF5] text-white' 
      : 'bg-[#7B5CF5]/10 border-[#7B5CF5]/40 text-[#c4b5fd] hover:bg-[#7B5CF5]/20';
  }

  return (
    <button
      onClick={() => onClick && onClick(tag.name)}
      className={`px-[10px] py-[2px] border rounded-[4px] text-[10px] font-bold uppercase tracking-wider transition-all select-none focus:outline-none ${colorClasses}`}
    >
      {tag.name}
    </button>
  );
}
