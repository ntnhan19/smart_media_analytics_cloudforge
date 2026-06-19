import React, { useState } from 'react';
import { useParams } from 'react-router-dom';
import HeaderBar from '../components/layout/HeaderBar';
import { Play } from 'lucide-react';

// Components
import VideoPlayer from '../components/media/VideoPlayer';
import SceneList from '../components/media/SceneList';
import TranscriptList from '../components/media/TranscriptList';
import AIInsightsPanel from '../components/media/AIInsightsPanel';
import InVideoSearch from '../components/media/InVideoSearch';
import MatchBadge from '../components/media/MatchBadge';
import DetectMoreScenesButton from '../components/media/DetectMoreScenesButton';
import TagChip from '../components/media/TagChip';
import ObjectChip from '../components/media/ObjectChip';

// Mock Data
import { assetMock, sceneMock, transcriptMock, insightMock } from '../mocks/assetDetail';

function WaveformPlayer() {
  const bars = Array.from({ length: 42 }, (_, i) => {
    const heights = [8, 12, 16, 24, 28, 20, 16, 12, 16, 24, 32, 28, 20, 16, 24, 28, 20, 12, 8, 16, 20, 24, 28, 16, 12, 16, 24, 32, 28, 20, 16, 24, 28, 20, 12, 8, 16, 20, 24, 28, 16, 12];
    return heights[i % heights.length];
  });

  return (
    <div className="w-full h-[52px] bg-[#0E0B1F] border border-[#1e1b35] rounded-[6px] px-[12px] flex items-center gap-[12px] shrink-0">
      <button className="w-[30px] h-[30px] rounded-full bg-white text-[#0E0B1F] flex items-center justify-center hover:bg-gray-200 transition-colors shrink-0">
        <Play size={12} fill="currentColor" className="ml-[1px]" />
      </button>
      <div className="flex-1 h-[32px] flex items-center justify-between gap-[3px]">
        {bars.map((h, i) => (
          <div 
            key={i} 
            className="flex-1 bg-white/40 hover:bg-[#7B5CF5] transition-colors rounded-[1px]" 
            style={{ height: `${h}px` }} 
          />
        ))}
      </div>
    </div>
  );
}

export default function AssetDetail() {
  const { id } = useParams();
  
  // Local states
  const [currentTime, setCurrentTime] = useState(0);
  const [activeTab, setActiveTab] = useState('OVERVIEW');
  const [isFavourited, setIsFavourited] = useState(false);
  const [isDetecting, setIsDetecting] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [debouncedQuery, setDebouncedQuery] = useState('');
  const [sortBy, setSortBy] = useState('time');
  
  // Interaction states for AI Insights
  const [activeMarkers, setActiveMarkers] = useState([]);
  const [selectedObjectId, setSelectedObjectId] = useState(null);
  const [selectedTagName, setSelectedTagName] = useState(null);

  // Handlers
  const handleSeek = (timeSec) => {
    setCurrentTime(timeSec);
  };

  const handleTimeUpdate = (timeSec) => {
    setCurrentTime(timeSec);
  };

  const handleTagClick = (tagName) => {
    setSelectedTagName(prev => prev === tagName ? null : tagName);
  };

  const handleObjectClick = (obj) => {
    if (selectedObjectId === obj.name) {
      setSelectedObjectId(null);
      setActiveMarkers([]);
    } else {
      setSelectedObjectId(obj.name);
      setActiveMarkers(obj.occurrences || []);
      if (obj.occurrences && obj.occurrences.length > 0) {
        handleSeek(obj.occurrences[0].timestamp_start);
      }
    }
  };

  const handleDetectScenes = () => {
    setIsDetecting(true);
    setTimeout(() => setIsDetecting(false), 2000);
  };

  // Debounce search query to simulate API loading
  React.useEffect(() => {
    if (!searchQuery.trim()) {
      setDebouncedQuery('');
      setIsSearching(false);
      return;
    }
    setIsSearching(true);
    const handler = setTimeout(() => {
      setDebouncedQuery(searchQuery);
      setIsSearching(false);
    }, 400);
    return () => clearTimeout(handler);
  }, [searchQuery]);

  // Filter & Sort scenes/transcripts based on query, tag and sortBy
  const filteredScenes = React.useMemo(() => {
    return sceneMock.filter(scene => {
      // Filter by selected tag name if any
      if (selectedTagName) {
        const tagLower = selectedTagName.toLowerCase();
        const hasTagInDesc = scene.description.toLowerCase().includes(tagLower);
        const hasTagInSub = scene.subtitle?.toLowerCase().includes(tagLower);
        if (!hasTagInDesc && !hasTagInSub) return false;
      }
      if (!debouncedQuery.trim()) return true;
      const descMatch = scene.description.toLowerCase().includes(debouncedQuery.toLowerCase());
      const transMatch = transcriptMock.some(t => 
        t.start_sec >= scene.start_sec && 
        t.end_sec <= scene.end_sec && 
        t.text.toLowerCase().includes(debouncedQuery.toLowerCase())
      );
      return descMatch || transMatch;
    });
  }, [debouncedQuery, selectedTagName]);

  const sortedScenes = React.useMemo(() => {
    return [...filteredScenes].sort((a, b) => {
      if (sortBy === 'relevance' && debouncedQuery.trim()) {
        const aDescMatch = a.description.toLowerCase().includes(debouncedQuery.toLowerCase());
        const bDescMatch = b.description.toLowerCase().includes(debouncedQuery.toLowerCase());
        if (aDescMatch && !bDescMatch) return -1;
        if (!aDescMatch && bDescMatch) return 1;
      }
      return a.start_sec - b.start_sec;
    });
  }, [filteredScenes, sortBy, debouncedQuery]);

  const filteredTranscript = React.useMemo(() => {
    return transcriptMock.filter(t => {
      if (!debouncedQuery.trim()) return true;
      return t.text.toLowerCase().includes(debouncedQuery.toLowerCase());
    });
  }, [debouncedQuery]);

  return (
    <div className="flex flex-col h-screen bg-[#0E0B1F] overflow-hidden">
      <div className="flex-1 px-[25px] pt-[20px] pb-[16px] overflow-hidden">
        <div className="flex gap-[26px] h-full">
          
          {/* Left Column */}
          <div className="flex-1 flex flex-col h-full min-w-0">
            {/* Header */}
            <div className="flex-shrink-0 h-[40px] relative">
              <HeaderBar title={assetMock.title} />
            </div>
            
            {/* Video Player Area */}
            <div className="relative rounded-[6px] overflow-hidden bg-black flex-shrink-0 border border-gray-800 shadow-xl w-full mt-[12px]" style={{height: 'calc(100vh - 365px)', minHeight: '260px', maxHeight: '420px'}}>

              
              <VideoPlayer 
                src={assetMock.file_path}
                initialTimestamp={currentTime}
                scenes={sceneMock}
                mediaType={assetMock.mediaType}
                onTimeUpdate={handleTimeUpdate}
                duration={assetMock.duration}
                activeMarkers={activeMarkers}
              />
            </div>

            {/* Tabs Area */}
            <div className="flex-1 mt-[10px] flex flex-col overflow-hidden">
              {/* Tabs Header */}
              <div className="flex relative">
                <div className="flex gap-2">
                  {['OVERVIEW', 'TRANSCRIPT', 'METADATA', 'AI_INSIGHTS'].map((tab) => (
                    <button
                       key={tab}
                       onClick={() => setActiveTab(tab)}
                       className="w-[85px] h-[32px] flex items-center justify-center relative focus:outline-none group"
                    >
                      <span className={`font-inter font-normal text-[11px] leading-[14px] ${
                        activeTab === tab ? 'text-white' : 'text-gray-400 group-hover:text-gray-200'
                      }`}>
                        {tab.replace('_', ' ')}
                      </span>
                      {activeTab === tab && (
                        <div className="absolute bottom-0 left-[8px] right-[8px] h-0 border border-[#7B5CF5]"></div>
                      )}
                    </button>
                  ))}
                </div>

                {/* SCENES Button on the right of tabs */}
                <div className="absolute right-0 top-[2px]">
                  <div className={`w-[80px] h-[30px] bg-[#4F8EF7]/70 border border-[#16132A] rounded-[2px] shadow-[0px_4px_4px_rgba(69,39,152,0.25)] flex items-center justify-center transition-all ${
                    activeTab === 'TRANSCRIPT' ? 'opacity-30 pointer-events-none' : 'opacity-100'
                  }`}>
                    <span className="font-inter font-bold text-[13px] text-[#DDDDDD] uppercase tracking-wide">
                      SCENES
                    </span>
                  </div>
                </div>
              </div>

              {/* Tabs Content */}
              <div className="flex-1 overflow-y-auto py-2 px-4 custom-scrollbar">
                {activeTab === 'AI_INSIGHTS' && (
                  <AIInsightsPanel 
                    insight={insightMock} 
                    onObjectClick={handleObjectClick} 
                    selectedObjectId={selectedObjectId} 
                    onTagClick={handleTagClick} 
                    selectedTagName={selectedTagName} 
                    currentTime={currentTime} 
                  />
                )}

                {(activeTab === 'OVERVIEW' || activeTab === 'TRANSCRIPT') && (
                  <div className="relative w-full h-auto mt-[8px] flex gap-[12px]">
                    {/* AI Caption Box */}
                    <div className="flex-1 min-h-[110px] border border-[#7B5CF5] rounded-[6px] box-border p-[10px] relative">
                      <span className="font-inter font-bold text-[12px] leading-[15px] text-white block mb-1">
                        AI CAPTION
                      </span>
                      <p className="font-inter font-normal text-[12px] leading-[15px] text-white">
                        {assetMock.ai_caption}
                      </p>
                    </div>

                    {/* Tags Box */}
                    <div className="w-[240px] min-h-[110px] border border-[#7B5CF5] rounded-[6px] box-border p-[10px] relative flex-shrink-0">
                      <span className="font-inter font-bold text-[12px] leading-[15px] text-white block mb-1">
                        TAGS
                      </span>
                      <div className="flex flex-wrap gap-[5px]">
                        {assetMock.tags.map((tag, idx) => (
                          <TagChip 
                            key={idx} 
                            tag={tag} 
                            onClick={handleTagClick} 
                            isActive={selectedTagName === tag.name} 
                          />
                        ))}
                      </div>
                    </div>
                  </div>
                )}

                {activeTab === 'METADATA' && (
                  <div>
                    <h4 className="font-medium text-white mb-4">File Information</h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-4 text-sm">
                      <div className="flex justify-between border-b border-gray-800 pb-2">
                        <span className="text-gray-500">File Name</span>
                        <span className="text-gray-300">{assetMock.file_name}</span>
                      </div>
                      <div className="flex justify-between border-b border-gray-800 pb-2">
                        <span className="text-gray-500">File Size</span>
                        <span className="text-gray-300">{assetMock.file_size}</span>
                      </div>
                      <div className="flex justify-between border-b border-gray-800 pb-2">
                        <span className="text-gray-500">Duration</span>
                        <span className="text-gray-300">{assetMock.duration}s</span>
                      </div>
                      <div className="flex justify-between border-b border-gray-800 pb-2">
                        <span className="text-gray-500">Resolution</span>
                        <span className="text-gray-300">{assetMock.resolution}</span>
                      </div>
                      <div className="flex justify-between border-b border-gray-800 pb-2">
                        <span className="text-gray-500">Created At</span>
                        <span className="text-gray-300">{new Date(assetMock.created_at).toLocaleDateString()}</span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
            
          </div>

          {/* Right Column */}
          {assetMock.mediaType !== 'image' && (
            <div className="w-[380px] flex flex-col bg-[rgba(126,26,249,0.72)] shadow-[0px_4px_4px_rgba(0,0,0,0.25)] rounded-[6px] flex-shrink-0 p-[8px] gap-[8px]">
              
              {/* Top Search */}
              <div className="flex-shrink-0">
                <InVideoSearch 
                  assetId={assetMock.id} 
                  onSeekVideo={handleSeek}
                  searchQuery={searchQuery}
                  onSearchChange={setSearchQuery}
                  isSearching={isSearching}
                />
              </div>

              {/* Showing Count and Sort Option */}
              <div className="flex items-center justify-between text-[11px] text-white/70 px-[6px] py-[2px] border-b border-white/10 shrink-0 pb-[4px]">
                <span>
                  {activeTab === 'TRANSCRIPT' 
                    ? `Showing ${filteredTranscript.length} of ${transcriptMock.length} lines`
                    : `Showing ${sortedScenes.length} of ${sceneMock.length} scenes`
                  }
                </span>
                <div className="flex items-center gap-[4px]">
                  <span>Sort by:</span>
                  <select 
                    value={sortBy} 
                    onChange={(e) => setSortBy(e.target.value)}
                    className="bg-transparent border-none text-[#7B5CF5] font-bold focus:outline-none cursor-pointer text-[11px]"
                  >
                    <option value="time" className="bg-[#0E0B1F]">Time</option>
                    <option value="relevance" className="bg-[#0E0B1F]">Relevance</option>
                  </select>
                </div>
              </div>

              {/* Timeline/Scenes or Transcript List */}
              <div className="flex-1 overflow-hidden">
                {activeTab === 'TRANSCRIPT' ? (
                  <TranscriptList 
                    transcript={filteredTranscript} 
                    currentTime={currentTime} 
                    onSeek={handleSeek}
                    searchQuery={debouncedQuery}
                  />
                ) : (
                  <SceneList 
                    scenes={sortedScenes} 
                    currentTime={currentTime} 
                    onSeek={handleSeek}
                    searchQuery={debouncedQuery}
                  />
                )}
              </div>
              
              {/* Detect Button or Waveform Player */}
              <div className="flex-shrink-0">
                {activeTab === 'TRANSCRIPT' ? (
                  <WaveformPlayer />
                ) : (
                  <div className="w-full py-[8px] flex items-center justify-center border border-dashed border-[#7B5CF5]/30 rounded-[6px] bg-[#16132A]/20">
                    <button 
                      onClick={handleDetectScenes}
                      disabled={isDetecting}
                      className="text-[11px] font-inter font-medium text-gray-400 hover:text-white transition-colors flex items-center gap-1.5"
                    >
                      {isDetecting ? (
                        <span className="w-3 h-3 border-2 border-[#7B5CF5] border-t-transparent rounded-full animate-spin" />
                      ) : null}
                      <span>Showing {sortedScenes.length} of 23 scenes · <span className="text-[#c4b5fd] hover:text-white font-bold hover:underline">Detect more</span></span>
                    </button>
                  </div>
                )}
              </div>
            </div>
          )}

        </div>
      </div>
    </div>
  );
}
