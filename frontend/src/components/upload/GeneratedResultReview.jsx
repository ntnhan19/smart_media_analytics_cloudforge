import React from 'react';
import { useNavigate } from 'react-router-dom';
import { ExternalLink, CheckCircle2, Clock, ChevronUp, ChevronDown } from 'lucide-react';

const mockScenes = [
  { time: '00:00-00:03', desc: 'Aerial view of stone bridge over a calm river surrounded by lush green mountains' },
  { time: '00:03-00:07', desc: 'Aerial view of stone bridge over a calm river surrounded by lush green mountains' },
  { time: '00:07-00:12', desc: 'Aerial view of stone bridge over a calm river surrounded by lush green mountains' },
];

const mockTranscript = [
  { time: '00:00-00:03', text: 'Aerial view of stone bridge over a calm river surrounded by lush green mountains' },
  { time: '00:03-00:07', text: 'Aerial view of stone bridge over a calm river surrounded by lush green mountains' },
  { time: '00:07-00:12', text: 'Aerial view of stone bridge over a calm river surrounded by lush green mountains' },
  { time: '00:12-00:18', text: 'Aerial view of stone bridge over a calm river surrounded by lush green mountains' },
  { time: '00:18-00:25', text: 'Aerial view of stone bridge over a calm river surrounded by lush green mountains' },
  { time: '00:25-00:30', text: 'Aerial view of stone bridge over a calm river surrounded by lush green mountains' },
];

const mockTags = ['BRIDGE', 'NATURE', 'AERIAL', 'RIVER', 'MOUNTAIN', 'LANDSCAPE', 'SCENIC', 'OUTDOOR', 'BRIDGE'];

export default function GeneratedResultReview({ isOpen, onToggle, jobId, assetId }) {
  const navigate = useNavigate();
  const displayTitle = jobId ? `(IMG_${jobId.substring(0, 6).toUpperCase()}.mp4)` : '(No Video Selected)';

  const handleOpenAssets = () => {
    if (assetId) {
      navigate(`/assets/${assetId}`);
    } else {
      alert("Asset is still processing or no asset ID available.");
    }
  };

  return (
    <div className="w-full h-full flex flex-col gap-3 overflow-hidden">
      {/* Header Row */}
      <div className="flex items-center justify-between shrink-0">
        <div className="flex items-center gap-3">
          {/* Nút Toggle Panel */}
          <button 
            onClick={onToggle}
            className="w-6 h-6 rounded bg-[#16132A] border border-[#7B5CF5]/50 flex items-center justify-center hover:bg-[#7B5CF5]/20 transition-colors"
          >
            {isOpen ? <ChevronDown className="w-4 h-4 text-[#7B5CF5]" /> : <ChevronUp className="w-4 h-4 text-[#7B5CF5]" />}
          </button>
          
          <h2 className="text-white text-[14px] font-bold cursor-pointer" onClick={onToggle}>
            Generated Result Review{' '}
            {isOpen && <span className="text-gray-400 font-light text-[12px]">{displayTitle}</span>}
          </h2>
          
          {isOpen && (
            <span className="flex items-center gap-1.5 border border-[#4ADE80]/60 text-[#4ADE80] text-[11px] font-light px-2.5 py-0.5 rounded ml-2">
              <span className="w-1.5 h-1.5 rounded-full bg-[#4ADE80] animate-pulse inline-block" />
              Processing
            </span>
          )}
        </div>
        
        {isOpen && (
          <button 
            onClick={handleOpenAssets}
            disabled={!assetId}
            className="flex items-center gap-2 border border-[#4F8EF7] text-white text-[12px] font-light px-4 py-1.5 rounded-lg bg-[#16132A] hover:bg-[#4F8EF7]/20 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <ExternalLink className="w-3.5 h-3.5" />
            Open Assets
          </button>
        )}
      </div>

      {/* 4 Columns Grid (Chỉ render khi isOpen = true) */}
      {isOpen && (
        <div className="grid grid-cols-4 gap-4 flex-1 min-h-[220px]">

          {/* Col 1: Selected Assets */}
          <div className="bg-[#120F1D] border border-[#16132A] rounded-lg flex flex-col overflow-hidden">
            <div className="flex justify-between items-center px-4 pt-4 pb-3 shrink-0">
              <span className="text-white text-[12px] font-bold">Selected Assets</span>
              <button className="text-[#7B5CF5] text-[10px]">View All</button>
            </div>
            
            <div className="flex-1 overflow-x-auto no-scrollbar px-4 pb-2 flex gap-2">
              {mockScenes.map((scene, i) => (
                <div key={i} className="flex flex-col border border-[#4F8EF7]/40 rounded-lg overflow-hidden shrink-0 w-[115px] bg-[#16132A]/50 transition-all hover:border-[#4F8EF7]">
                  {/* Thumbnail part */}
                  <div className="h-[75px] bg-gradient-to-br from-[#120F1D] to-[#4F8EF7]/20 border-b border-[#4F8EF7]/20 flex flex-col justify-end p-1.5 relative overflow-hidden">
                    <div className="bg-[#4F8EF7] text-white text-[9px] px-1.5 py-0.5 rounded self-start shadow-md">
                      {scene.time}
                    </div>
                  </div>
                  {/* Text part */}
                  <div className="p-2.5 h-[50px] overflow-hidden">
                    <p className="text-white/50 text-[9px] font-light leading-snug line-clamp-2">
                      {scene.desc}
                    </p>
                  </div>
                </div>
              ))}
            </div>

            <div className="border-t border-white/5 px-4 py-3 shrink-0 flex items-center gap-2">
              <div className="flex items-center gap-1.5 border border-[#4ADE80]/20 bg-[#4ADE80]/5 px-2 py-1 rounded-full">
                <CheckCircle2 className="w-3 h-3 text-[#4ADE80] fill-[#4ADE80]/20" />
                <span className="text-[#4ADE80] text-[9px] font-light">3 Scenes Detected</span>
              </div>
              <div className="flex items-center gap-1.5 border border-[#4ADE80]/20 bg-[#4ADE80]/5 px-2 py-1 rounded-full">
                <CheckCircle2 className="w-3 h-3 text-[#4ADE80] fill-[#4ADE80]/20" />
                <span className="text-[#4ADE80] text-[9px] font-light">3 Thumbnails Generated</span>
              </div>
            </div>
          </div>

          {/* Col 2: Transcript */}
          <div className="bg-[#120F1D] border border-[#16132A] rounded-lg flex flex-col overflow-hidden relative">
            <div className="absolute top-0 left-0 right-0 h-[2px] bg-white/10 rounded-t-lg">
              <div className="h-full bg-[#7B5CF5] rounded-t-lg" style={{ width: '68%' }} />
            </div>
            <div className="flex justify-between items-center px-4 pt-5 pb-3 shrink-0">
              <span className="text-white text-[12px] font-bold">Transcript <span className="text-[#7B5CF5] font-normal">(68%)</span></span>
              <button className="text-[#7B5CF5] text-[10px]">View All</button>
            </div>
            <div className="flex-1 overflow-y-auto no-scrollbar px-4 space-y-3 pb-2">
              {mockTranscript.map((row, i) => (
                <div key={i} className="flex gap-2.5 items-start">
                  <div className="bg-[#4F8EF7]/80 text-white text-[7px] px-1.5 py-0.5 rounded shrink-0 mt-0.5">
                    {row.time}
                  </div>
                  <p className="text-white/70 text-[8px] font-light leading-relaxed">{row.text}</p>
                </div>
              ))}
            </div>
            <div className="border-t border-white/5 px-4 py-2.5 shrink-0 flex items-center justify-between">
              <span className="text-[#7B5CF5] text-[8px]">68% Transcribed</span>
              <span className="text-white/60 text-[8px]">Languages: English</span>
              <span className="text-white/60 text-[8px]">Speaker: 2</span>
            </div>
          </div>

          {/* Col 3: AI Captions */}
          <div className="bg-[#120F1D] border border-[#16132A] rounded-lg flex flex-col overflow-hidden">
            <div className="flex justify-between items-center px-4 pt-4 pb-3 shrink-0">
              <span className="text-white text-[12px] font-bold">
                AI Captions <span className="text-gray-400 font-light text-[10px]">(Pending)</span>
              </span>
              <button className="text-[#7B5CF5] text-[10px]">View All</button>
            </div>
            <div className="flex-1 overflow-y-auto no-scrollbar px-4 space-y-3 pb-2">
              {[1, 2, 3, 4, 5].map((i) => (
                <div key={i} className="flex items-center gap-2.5">
                  <Clock className="w-4 h-4 text-[#7B5CF5] shrink-0 animate-pulse" />
                  <span className="text-white/70 text-[10px]">Generating captions for scene {i}..</span>
                </div>
              ))}
            </div>
            <div className="border-t border-white/5 px-4 py-2.5 shrink-0 text-center">
              <span className="text-white/60 text-[10px]">0/5 Completed</span>
            </div>
          </div>

          {/* Col 4: Tags */}
          <div className="bg-[#120F1D] border border-[#16132A] rounded-lg flex flex-col overflow-hidden">
            <div className="flex justify-between items-center px-4 pt-4 pb-3 shrink-0">
              <span className="text-white text-[12px] font-bold">
                Tags <span className="text-gray-400 font-light text-[10px]">(Auto generated)</span>
              </span>
              <button className="text-[#7B5CF5] text-[10px]">View All</button>
            </div>
            <div className="flex-1 overflow-y-auto no-scrollbar px-4 pb-4">
              <div className="flex flex-wrap gap-2 content-start">
                {mockTags.map((tag, i) => (
                  <span key={i} className="border border-[#7B5CF5] text-white text-[10px] font-bold px-3 py-1 rounded-md hover:bg-[#7B5CF5]/10 transition-colors cursor-pointer">
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          </div>

        </div>
      )}
    </div>
  );
}
