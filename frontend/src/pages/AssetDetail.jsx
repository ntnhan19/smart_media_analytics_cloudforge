import React, { useState, useEffect } from 'react';
import { useParams, useSearchParams } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import HeaderBar from '../components/layout/HeaderBar';


// Services
import { getAsset, getAssetScenes, getAssetStream, searchMedia, reingestAsset, regenerateInsights } from '../services/api';

// Components
import VideoPlayer from '../components/media/VideoPlayer';
import SceneList from '../components/media/SceneList';
import TranscriptList from '../components/media/TranscriptList';
import AIInsightsPanel from '../components/media/AIInsightsPanel';
import InVideoSearch from '../components/media/InVideoSearch';

import TagChip from '../components/media/TagChip';

import WaveformSync from '../components/media/WaveformSync';

// Mock Data fallbacks
import { transcriptMock, insightMock } from '../mocks/assetDetail';

export default function AssetDetail() {
  const { id } = useParams();
  const [searchParams] = useSearchParams();
  const queryClient = useQueryClient();
  
  // URL Timestamp
  const initialTimestamp = searchParams.get('t') ? parseFloat(searchParams.get('t')) : 0;

  // Local states
  const [currentTime, setCurrentTime] = useState(initialTimestamp);
  const [activeTab, setActiveTab] = useState('OVERVIEW');
  const [searchQuery, setSearchQuery] = useState('');
  const [debouncedQuery, setDebouncedQuery] = useState('');
  const [sortBy, setSortBy] = useState('time');
  const [isPlaying, setIsPlaying] = useState(false);
  
  // Interaction states for AI Insights
  const [activeMarkers, setActiveMarkers] = useState([]);
  const [selectedObjectId, setSelectedObjectId] = useState(null);
  const [selectedTagName, setSelectedTagName] = useState(null);
  const [wsProgress, setWsProgress] = useState(null);

  // Queries
  const { data: assetData, isLoading: isLoadingAsset } = useQuery({
    queryKey: ['asset', id],
    queryFn: () => getAsset(id),
  });

  const { data: scenesData } = useQuery({
    queryKey: ['asset-scenes', id],
    queryFn: () => getAssetScenes(id),
  });

  const { data: streamData } = useQuery({
    queryKey: ['asset-stream', id],
    queryFn: () => getAssetStream(id),
  });

  // Search Mutation
  const searchMutation = useMutation({
    mutationFn: (q) => searchMedia({ query: q, filters: { asset_id: id }, top_k: 10 })
  });

  // Reingest Mutation
  const reingestMutation = useMutation({
    mutationFn: () => reingestAsset(id),
    onMutate: () => {
      setWsProgress({ status: 'queued', progress: 0, message: 'Starting process...' });
    },
    onSuccess: (data) => {
      // Connect to websocket to track progress
      const ws = new WebSocket(`ws://localhost:8000/api/v1/ingest/ws/${data.job_id}`);
      ws.onmessage = (event) => {
        const msg = JSON.parse(event.data);
        setWsProgress({
          status: msg.status,
          progress: msg.progress || 0,
          message: msg.status === 'processing' ? 'Detecting scenes...' : msg.status
        });
        if (msg.status === 'completed') {
          setWsProgress(prev => ({ ...prev, status: 'completed', progress: 100, message: 'Process finished successfully!' }));
          queryClient.invalidateQueries(['asset-scenes', id]);
          setTimeout(() => setWsProgress(null), 2500);
          ws.close();
        } else if (msg.status === 'failed' || msg.status === 'error') {
          setWsProgress(prev => ({ ...prev, status: 'failed', message: msg.error_message || 'Process failed.' }));
          setTimeout(() => setWsProgress(null), 3000);
          ws.close();
        }
      };
      ws.onerror = () => setWsProgress(null);
    },
    onError: () => setWsProgress(null)
  });

  // Regenerate Insights Mutation
  const regenerateMutation = useMutation({
    mutationFn: () => regenerateInsights(id),
    onMutate: () => {
      setWsProgress({ status: 'queued', progress: 0, message: 'Regenerating AI insights...' });
    },
    onSuccess: (data) => {
      // Connect to websocket to track progress
      const ws = new WebSocket(`ws://localhost:8000/api/v1/ingest/ws/${data.job_id}`);
      ws.onmessage = (event) => {
        const msg = JSON.parse(event.data);
        setWsProgress({
          status: msg.status,
          progress: msg.progress || 0,
          message: msg.status === 'processing' ? 'Analyzing media...' : msg.status
        });
        if (msg.status === 'completed') {
          setWsProgress(prev => ({ ...prev, status: 'completed', progress: 100, message: 'AI Insights regenerated!' }));
          queryClient.invalidateQueries(['asset', id]);
          setTimeout(() => setWsProgress(null), 2500);
          ws.close();
        } else if (msg.status === 'failed' || msg.status === 'error') {
          setWsProgress(prev => ({ ...prev, status: 'failed', message: msg.error_message || 'Process failed.' }));
          setTimeout(() => setWsProgress(null), 3000);
          ws.close();
        }
      };
      ws.onerror = () => setWsProgress(null);
    },
    onError: () => setWsProgress(null)
  });

  useEffect(() => {
    let handler;
    if (!searchQuery.trim()) {
      handler = setTimeout(() => {
        setDebouncedQuery('');
      }, 0);
      return () => clearTimeout(handler);
    }
    handler = setTimeout(() => {
      setDebouncedQuery(searchQuery);
      searchMutation.mutate(searchQuery);
    }, 400);
    return () => clearTimeout(handler);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchQuery]);

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
        handleSeek(obj.occurrences[0].timestamp_start_sec);
      }
    }
  };

  const handleDetectScenes = () => {
    reingestMutation.mutate();
  };



  // Ensure mock fallbacks if API structure differs during development
  const asset = assetData?.asset || assetData || {};
  const scenes = scenesData?.scenes || scenesData || [];
  const streamUrl = streamData?.stream_url || asset.file_path; // Fallback to file_path if stream API not ready

  // Use search results if searching, otherwise use all scenes
  const searchResults = searchMutation.data?.results || [];
  
  const filteredScenes = React.useMemo(() => {
    if (debouncedQuery.trim() && searchResults.length > 0) {
      // Map search results back to scene items based on timestamp/scene info
      return searchResults.map(r => r.scene).filter(Boolean).map(s => ({
        id: s.scene_id,
        start_sec: s.timestamp_start_sec,
        end_sec: s.timestamp_start_sec + 5, // Rough estimate if missing
        thumbnail: s.thumbnail_url,
        description: s.caption,
        subtitle: s.transcript_snippet
      }));
    }

    return scenes.map(s => ({
      id: s.scene_id,
      start_sec: s.timestamp_start_sec,
      end_sec: s.timestamp_end_sec || s.timestamp_start_sec + 5,
      thumbnail: s.thumbnail_url,
      description: s.caption,
      subtitle: s.transcript_snippet
    })).filter(scene => {
      if (selectedTagName) {
        const tagLower = selectedTagName.toLowerCase();
        const hasTagInDesc = scene.description?.toLowerCase().includes(tagLower);
        const hasTagInSub = scene.subtitle?.toLowerCase().includes(tagLower);
        if (!hasTagInDesc && !hasTagInSub) return false;
      }
      return true;
    });
  }, [debouncedQuery, selectedTagName, scenes, searchResults]);

  const sortedScenes = React.useMemo(() => {
    return [...filteredScenes].sort((a, b) => {
      if (sortBy === 'relevance' && debouncedQuery.trim()) {
        const aDescMatch = a.description?.toLowerCase().includes(debouncedQuery.toLowerCase());
        const bDescMatch = b.description?.toLowerCase().includes(debouncedQuery.toLowerCase());
        if (aDescMatch && !bDescMatch) return -1;
        if (!aDescMatch && bDescMatch) return 1;
      }
      return a.start_sec - b.start_sec;
    });
  }, [filteredScenes, sortBy, debouncedQuery]);

  const filteredTranscript = transcriptMock; // Still mocked unless backend provides transcripts array in Asset

  if (isLoadingAsset) {
    return <div className="flex h-screen items-center justify-center text-white">Loading Asset...</div>;
  }

  return (
    <div className="flex flex-col h-screen bg-[#0E0B1F] overflow-hidden relative">
      {wsProgress && (
        <div className="absolute inset-0 bg-black/60 backdrop-blur-sm z-50 flex flex-col items-center justify-center">
          <div className="bg-[#16132A] p-8 rounded-xl border border-sma-purple/30 shadow-2xl flex flex-col items-center max-w-sm w-full">
            <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-sma-purple mb-4"></div>
            <h3 className="text-white font-inter font-bold text-lg mb-2 capitalize">{wsProgress.status}</h3>
            <p className="text-gray-300 font-inter text-sm mb-6 text-center">{wsProgress.message || 'Processing...'}</p>
            <div className="w-full bg-black/50 rounded-full h-2 mb-2 overflow-hidden border border-white/5">
              <div 
                className="bg-sma-purple h-2 rounded-full transition-all duration-300 ease-out" 
                style={{ width: `${Math.max(5, wsProgress.progress || 0)}%` }}
              ></div>
            </div>
            <div className="text-xs text-gray-400 font-mono self-end">{Math.round(wsProgress.progress || 0)}%</div>
          </div>
        </div>
      )}

      <div className="flex-1 px-[25px] pt-[20px] pb-[16px] overflow-hidden">
        <div className="flex gap-[26px] h-full">
          
          {/* Left Column */}
          <div className="flex-1 flex flex-col h-full min-w-0">
            {/* Header */}
            <div className="flex-shrink-0 h-[40px] relative flex justify-between items-center">
              <HeaderBar title={asset.title || asset.file_name} currentTime={currentTime} />
            </div>
            
            {/* Video Player Area */}
            <div className="relative rounded-[6px] overflow-hidden bg-black flex-shrink-0 border border-gray-800 shadow-xl w-full mt-[12px]" style={{height: 'calc(100vh - 365px)', minHeight: '260px', maxHeight: '420px'}}>
              <VideoPlayer 
                src={streamUrl}
                initialTimestamp={initialTimestamp || currentTime}
                scenes={scenes}
                mediaType={asset.mediaType || 'video'}
                onTimeUpdate={handleTimeUpdate}
                duration={asset.duration || 120}
                activeMarkers={activeMarkers}
                onPlayStateChange={setIsPlaying}
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
                  <div>

                    <AIInsightsPanel 
                      insight={insightMock} // Using mock fallback for now unless API returns insights
                      onObjectClick={handleObjectClick} 
                      selectedObjectId={selectedObjectId} 
                      onTagClick={handleTagClick} 
                      selectedTagName={selectedTagName} 
                      currentTime={currentTime} 
                      onRegenerate={() => regenerateMutation.mutate()}
                      isRegenerating={regenerateMutation.isLoading}
                    />
                  </div>
                )}

                {(activeTab === 'OVERVIEW' || activeTab === 'TRANSCRIPT') && (
                  <div className="relative w-full h-auto mt-[8px] flex gap-[12px]">
                    {/* AI Caption Box */}
                    <div className="flex-1 min-h-[110px] border border-[#7B5CF5] rounded-[6px] box-border p-[10px] relative">
                      <span className="font-inter font-bold text-[12px] leading-[15px] text-white block mb-1">
                        AI CAPTION
                      </span>
                      <p className="font-inter font-normal text-[12px] leading-[15px] text-white">
                        {asset.ai_caption || 'No caption available'}
                      </p>
                    </div>

                    {/* Tags Box */}
                    <div className="w-[240px] min-h-[110px] border border-[#7B5CF5] rounded-[6px] box-border p-[10px] relative flex-shrink-0">
                      <span className="font-inter font-bold text-[12px] leading-[15px] text-white block mb-1">
                        TAGS
                      </span>
                      <div className="flex flex-wrap gap-[5px]">
                        {(asset.tags || []).map((tag, idx) => (
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
                        <span className="text-gray-300">{asset.file_name}</span>
                      </div>
                      <div className="flex justify-between border-b border-gray-800 pb-2">
                        <span className="text-gray-500">File Size</span>
                        <span className="text-gray-300">{asset.file_size}</span>
                      </div>
                      <div className="flex justify-between border-b border-gray-800 pb-2">
                        <span className="text-gray-500">Duration</span>
                        <span className="text-gray-300">{asset.duration}s</span>
                      </div>
                      <div className="flex justify-between border-b border-gray-800 pb-2">
                        <span className="text-gray-500">Resolution</span>
                        <span className="text-gray-300">{asset.resolution}</span>
                      </div>
                      <div className="flex justify-between border-b border-gray-800 pb-2">
                        <span className="text-gray-500">Created At</span>
                        <span className="text-gray-300">{new Date(asset.created_at).toLocaleDateString()}</span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
            
          </div>

          {/* Right Column */}
          {asset.mediaType !== 'image' && (
            <div className="w-[380px] flex flex-col bg-[rgba(126,26,249,0.72)] shadow-[0px_4px_4px_rgba(0,0,0,0.25)] rounded-[6px] flex-shrink-0 p-[8px] gap-[8px]">
              
              {/* Top Search */}
              <div className="flex-shrink-0">
                <InVideoSearch 
                  assetId={id} 
                  onSeekVideo={handleSeek}
                  searchQuery={searchQuery}
                  onSearchChange={setSearchQuery}
                  isSearching={searchMutation.isLoading}
                />
              </div>

              {/* Showing Count and Sort Option */}
              <div className="flex items-center justify-between text-[11px] text-white/70 px-[6px] py-[2px] border-b border-white/10 shrink-0 pb-[4px]">
                <span>
                  {activeTab === 'TRANSCRIPT' 
                    ? `Showing ${filteredTranscript.length} lines`
                    : `Showing ${sortedScenes.length} scenes`
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
                  <WaveformSync
                    streamUrl={streamUrl}
                    currentTime={currentTime}
                    onSeek={handleSeek}
                    isPlaying={isPlaying}
                    onTogglePlay={() => setIsPlaying(!isPlaying)}
                  />
                ) : (
                  <div className="w-full py-[8px] flex items-center justify-center border border-dashed border-[#7B5CF5]/30 rounded-[6px] bg-[#16132A]/20">
                    <button 
                      onClick={handleDetectScenes}
                      disabled={reingestMutation.isLoading}
                      className="text-[11px] font-inter font-medium text-gray-400 hover:text-white transition-colors flex items-center gap-1.5"
                    >
                      {reingestMutation.isLoading ? (
                        <span className="w-3 h-3 border-2 border-[#7B5CF5] border-t-transparent rounded-full animate-spin" />
                      ) : null}
                      <span>Showing {sortedScenes.length} scenes · <span className="text-[#c4b5fd] hover:text-white font-bold hover:underline">Detect more</span></span>
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
