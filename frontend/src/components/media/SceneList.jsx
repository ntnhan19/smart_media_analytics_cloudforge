import React, { useRef, useEffect, useState } from 'react';
import { Scissors, Loader2 } from 'lucide-react';
import { createClip } from '../../services/api';

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

const formatTime = (time) => {
  const integerPart = Math.floor(time);
  const decimalPart = Math.round((time - integerPart) * 100);
  return `${String(integerPart).padStart(2, '0')}.${String(decimalPart).padStart(2, '0')}`;
};

export default function SceneList({ assetId, scenes, currentTime, onSeek, searchQuery }) {
  const listRef = useRef(null);
  const activeSceneRef = useRef(null);
  const [clippingId, setClippingId] = useState(null);

  useEffect(() => {
    // Auto-scroll to active scene
    if (activeSceneRef.current && listRef.current) {
      activeSceneRef.current.scrollIntoView({
        behavior: 'smooth',
        block: 'nearest',
      });
    }
  }, [currentTime]);

  const handleCreateClip = async (e, scene) => {
    e.stopPropagation(); // Prevent triggering onSeek
    if (!assetId) return;
    
    setClippingId(scene.id);
    try {
      const result = await createClip(assetId, scene.start_sec, scene.end_sec);
      if (result.clip_url) {
        // Automatically trigger download
        const a = document.createElement('a');
        a.href = result.clip_url;
        a.download = `clip_${scene.start_sec.toFixed(1)}_${scene.end_sec.toFixed(1)}.mp4`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
      }
    } catch (error) {
      console.error("Failed to create clip:", error);
      alert("Error creating clip. Please try again.");
    } finally {
      setClippingId(null);
    }
  };

  if (scenes.length === 0) {
    return (
      <div className="h-full flex flex-col items-center justify-center text-center p-4">
        <p className="text-[13px] text-white/50">
          No scenes found for "<span className="text-[#c4b5fd] font-bold">{searchQuery}</span>"
        </p>
      </div>
    );
  }

  return (
    <div 
      ref={listRef}
      className="flex flex-col gap-[6px] h-full overflow-y-auto custom-scrollbar pr-1"
    >
      {scenes.map((scene) => {
        const isActive = currentTime >= scene.start_sec && currentTime < scene.end_sec;
        
        // Use backend provided subtitle or transcript snippet
        const subtitleText = scene.subtitle || scene.transcript_snippet;
        const hasTranscriptMatch = subtitleText && searchQuery && searchQuery.trim() && subtitleText.toLowerCase().includes(searchQuery.toLowerCase());
        const isClipping = clippingId === scene.id;

        return (
          <div
            key={scene.id}
            ref={isActive ? activeSceneRef : null}
            onClick={() => onSeek(scene.start_sec)}
            className={`group w-full min-h-[90px] py-[6px] box-border relative rounded-[6px] border-2 cursor-pointer shrink-0 transition-all flex items-center gap-[10px] px-[10px] ${
              isActive 
                ? 'bg-[#2a1f5a] border-[#7B5CF5] shadow-[0_0_12px_rgba(123,92,245,0.6)]' 
                : 'bg-[#0E0B1F] border-[#1e1b35] hover:border-[#7B5CF5]/50 hover:bg-[#16132A]'
            }`}
          >
            {/* Active left bar indicator */}
            {isActive && (
              <div className="absolute left-0 top-0 bottom-0 w-[4px] bg-[#7B5CF5] rounded-l-[4px]" />
            )}

            {/* Thumbnail */}
            <div className="w-[100px] h-[68px] rounded-[4px] overflow-hidden flex-shrink-0 ml-1 relative">
              <img src={scene.thumbnail} alt="" className="w-full h-full object-cover" />
              <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                <button 
                  onClick={(e) => handleCreateClip(e, scene)}
                  disabled={isClipping}
                  className="bg-[#7B5CF5] text-white p-1.5 rounded-full hover:bg-[#6a4ce2] transition-colors shadow-lg disabled:opacity-50"
                  title="Create Clip"
                >
                  {isClipping ? <Loader2 size={14} className="animate-spin" /> : <Scissors size={14} />}
                </button>
              </div>
            </div>
            
            {/* Content */}
            <div className="flex-1 flex flex-col gap-[4px] min-w-0">
              {/* Badges row */}
              <div className="flex items-center justify-between">
                <div className="bg-[#4F8EF7]/80 rounded-[2px] px-[6px] h-[16px] flex items-center justify-center">
                  <span className="font-inter font-normal text-[9px] leading-none text-white whitespace-nowrap">
                    {formatTime(scene.start_sec)}-{formatTime(scene.end_sec)}
                  </span>
                </div>
                <div className="bg-[#4ADE80]/20 rounded-[4px] px-[6px] h-[16px] flex items-center justify-center">
                  <span className="font-inter font-normal text-[9px] leading-none text-[#4ADE80] whitespace-nowrap">
                    98% Match
                  </span>
                </div>
              </div>

              {/* Main description */}
              <p className={`font-inter font-normal text-[12px] leading-[15px] line-clamp-2 ${isActive ? 'text-white' : 'text-white/90'}`}>
                <HighlightText text={scene.description} query={searchQuery} />
              </p>

              {/* Subtitle / Transcript */}
              {subtitleText && !hasTranscriptMatch && (
                <p className="font-inter font-normal text-[11px] leading-[13px] text-gray-400 italic truncate">
                  {subtitleText}
                </p>
              )}

              {/* Matching Transcript explanation */}
              {hasTranscriptMatch && (
                <p className="font-inter font-normal text-[10px] leading-[12px] text-purple-300 mt-0.5 italic flex items-center gap-1 min-w-0">
                  <span className="shrink-0 bg-purple-900/40 px-1 rounded text-[8px] border border-purple-800/60 font-bold not-italic">Transcript Match</span>
                  <span className="truncate">"<HighlightText text={subtitleText} query={searchQuery} />"</span>
                </p>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
