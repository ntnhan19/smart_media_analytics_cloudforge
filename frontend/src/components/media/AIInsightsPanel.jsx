import React, { useState } from 'react';
import { Loader2, RotateCw } from 'lucide-react';
import TagChip from './TagChip';
import ObjectChip from './ObjectChip';
export default function AIInsightsPanel({ insight, scenes = [], onObjectClick, selectedObjectId, onTagClick, selectedTagName, currentTime = 0, onRegenerate, isRegenerating = false }) {
  const [showAllObjects, setShowAllObjects] = useState(false);

  if (!insight) return null;

  // Find active scene based on currentTime
  const activeScene = scenes.find(s => currentTime >= (s.start_sec || s.timestamp_start_sec) && currentTime < (s.end_sec || s.timestamp_end_sec));
  const sceneLabel = activeScene
    ? `Analyzing scene ${(activeScene.start_sec || activeScene.timestamp_start_sec).toFixed(2)} – ${(activeScene.end_sec || activeScene.timestamp_end_sec).toFixed(2)}`
    : `Analyzing scene 00.00 – 01.60`;

  // Filter objects based on confidence > 0.6
  const objectsWithConfidence = insight.objects.map(obj => {
    const maxConfidence = obj.occurrences?.reduce((max, occ) => Math.max(max, occ.confidence), 0) || 0;
    return { ...obj, maxConfidence };
  });

  const highConfidenceObjects = objectsWithConfidence.filter(obj => obj.maxConfidence > 0.6);
  const lowConfidenceObjects = objectsWithConfidence.filter(obj => obj.maxConfidence <= 0.6);

  const visibleObjects = showAllObjects
    ? [...highConfidenceObjects, ...lowConfidenceObjects]
    : highConfidenceObjects;

  return (
    <div className="border border-[#7B5CF5] rounded-[6px] py-[10px] px-[14px] bg-[#0E0B1F]/30 w-full box-border">
      {/* Panel Header */}
      <div className="flex items-center justify-between mb-[6px]">
        <div className="flex items-baseline gap-[10px]">
          <h3 className="font-inter font-bold text-[13px] text-white leading-none uppercase tracking-wider">
            AI Insights
          </h3>
          {/* Analyzing Scene Contextual Label */}
          <span className="text-[10px] text-[#c4b5fd]/80 font-mono">
            {sceneLabel}
          </span>
        </div>
        <button
          onClick={onRegenerate}
          disabled={isRegenerating}
          className="bg-[#7B5CF5] hover:bg-[#6c4ee0] disabled:bg-[#7B5CF5]/50 text-white text-[10px] font-bold px-[10px] py-[4px] rounded-full flex items-center gap-[4px] transition-all"
        >
          {isRegenerating ? (
            <Loader2 size={10} className="animate-spin" />
          ) : (
            <>
              <span>Regenerate</span>
              <RotateCw size={10} />
            </>
          )}
        </button>
      </div>



      {/* Divider */}
      <div className="h-[1px] bg-gray-800/80 mb-[10px] w-full" />

      {/* Grid Layout (2 Columns + Divider) */}
      <div className="grid grid-cols-[1fr_auto_1fr] gap-[20px] items-start">
        {/* Left Column */}
        <div className="flex flex-col">
          <h4 className="font-inter font-bold text-[12px] text-white tracking-wide mb-[6px]">
            SUMMARY
          </h4>
          <p className="font-inter font-normal text-[12px] leading-[17px] text-white/90 mb-[10px]">
            {insight.summary}
          </p>

          <h4 className="font-inter font-bold text-[12px] text-white tracking-wide mb-[6px]">
            OBJECTS
          </h4>
          <div className="flex flex-wrap gap-[6px] items-center">
            {visibleObjects.map((obj, idx) => (
              <ObjectChip
                key={idx}
                obj={obj}
                onClick={onObjectClick}
                isActive={selectedObjectId === obj.name}
              />
            ))}

            {lowConfidenceObjects.length > 0 && (
              <button
                onClick={() => setShowAllObjects(!showAllObjects)}
                className="text-[9px] font-bold text-[#c4b5fd] hover:text-white transition-colors underline focus:outline-none ml-1 uppercase"
              >
                {showAllObjects ? 'Show less' : `Show more (${lowConfidenceObjects.length})`}
              </button>
            )}
          </div>
        </div>

        {/* Vertical Separator */}
        <div className="w-[1px] bg-gray-800/80 self-stretch min-h-[120px]" />

        {/* Right Column */}
        <div className="flex flex-col">
          <h4 className="font-inter font-bold text-[12px] text-white tracking-wide mb-[6px]">
            MOOD
          </h4>
          <div className="space-y-[8px] mb-[10px]">
            {insight.moods.map((mood, idx) => (
              <div key={idx} className="flex items-center gap-[10px]">
                <span className="w-[80px] text-[11px] font-bold text-gray-500 uppercase tracking-wider shrink-0">
                  {mood.label}
                </span>
                <div className="flex-1 h-[6px] bg-gray-800 rounded-full overflow-hidden relative">
                  <div
                    className="h-full bg-[#7B5CF5] rounded-full"
                    style={{ width: `${mood.score * 100}%` }}
                  />
                </div>
                <span className="text-gray-400 text-[10px] font-bold w-[28px] text-right shrink-0">
                  {Math.round(mood.score * 100)}%
                </span>
              </div>
            ))}
          </div>

          <div className="flex items-center gap-[10px] mt-[12px]">
            <h4 className="font-inter font-bold text-[12px] text-white tracking-wide shrink-0">
              BEST FOR
            </h4>
            <div className="flex flex-wrap gap-[6px]">
              {insight.best_for.map((tag, idx) => (
                <TagChip
                  key={idx}
                  tag={tag}
                  onClick={onTagClick}
                  isActive={selectedTagName === tag.name}
                />
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
