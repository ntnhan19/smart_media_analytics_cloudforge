import React, { useRef, useEffect } from 'react';
import { Play } from 'lucide-react';

// Helper: highlight matched text
function HighlightText({ text, query }) {
  if (!query || !query.trim()) return <span>{text}</span>;
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

export default function TranscriptList({ transcript, currentTime, onSeek, searchQuery }) {
  const listRef = useRef(null);
  const activeLineRef = useRef(null);

  useEffect(() => {
    // Auto-scroll to active transcript line
    if (activeLineRef.current && listRef.current) {
      activeLineRef.current.scrollIntoView({
        behavior: 'smooth',
        block: 'nearest',
      });
    }
  }, [currentTime]);

  const formatTime = (time) => {
    const integerPart = Math.floor(time);
    const decimalPart = Math.round((time - integerPart) * 100);
    return `${String(integerPart).padStart(2, '0')}.${String(decimalPart).padStart(2, '0')}`;
  };

  if (transcript.length === 0) {
    return (
      <div className="h-full flex flex-col items-center justify-center text-center p-4">
        <p className="text-[13px] text-white/50">
          No transcripts found for "<span className="text-[#c4b5fd] font-bold">{searchQuery}</span>"
        </p>
      </div>
    );
  }

  return (
    <div 
      ref={listRef}
      className="flex flex-col gap-[6px] h-full overflow-y-auto custom-scrollbar pr-1"
    >
      {transcript.map((line, idx) => {
        const isActive = currentTime >= line.start_sec && currentTime < line.end_sec;
        
        return (
          <div
            key={idx}
            ref={isActive ? activeLineRef : null}
            onClick={() => onSeek(line.start_sec)}
            className={`w-full min-h-[50px] py-[8px] px-[12px] box-border relative rounded-[6px] border cursor-pointer shrink-0 transition-all flex items-center gap-[12px] ${
              isActive 
                ? 'bg-[#2a1f5a]/90 border-[#7B5CF5] shadow-[0_0_10px_rgba(123,92,245,0.4)]' 
                : 'bg-[#0E0B1F] border-[#1e1b35] hover:border-[#7B5CF5]/40 hover:bg-[#16132A]'
            }`}
          >
            {/* Active indicator line */}
            {isActive && (
              <div className="absolute left-0 top-0 bottom-0 w-[4px] bg-[#7B5CF5] rounded-l-[5px]" />
            )}

            {/* Play Button Icon */}
            <div className={`w-[24px] h-[24px] rounded-full flex items-center justify-center flex-shrink-0 transition-colors ${
              isActive ? 'bg-[#7B5CF5] text-white' : 'bg-gray-800 text-gray-400 group-hover:bg-gray-700'
            }`}>
              <Play size={10} fill="currentColor" className="ml-[1px]" />
            </div>

            {/* Time code badge */}
            <div className="flex-shrink-0 bg-[#4F8EF7]/80 rounded-[2px] px-[6px] h-[16px] flex items-center justify-center">
              <span className="font-inter font-normal text-[9px] leading-none text-white whitespace-nowrap">
                {formatTime(line.start_sec)}-{formatTime(line.end_sec)}
              </span>
            </div>

            {/* Transcript text */}
            <p className={`flex-1 font-inter font-normal text-[12px] leading-[15px] ${isActive ? 'text-white' : 'text-gray-300'}`}>
              <HighlightText text={line.text} query={searchQuery} />
            </p>
          </div>
        );
      })}
    </div>
  );
}
