import { useState, useEffect, useMemo, useRef } from 'react';
import { useParams, useSearchParams, useLocation } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import HeaderBar from '../components/layout/HeaderBar';


// Services
import { getAsset, getAssetScenes, getAssetStream, searchAssetScenes, reingestAsset, regenerateInsights, toggleFavorite } from '../services/api';

// Components
import VideoPlayer from '../components/media/VideoPlayer';
import SceneList from '../components/media/SceneList';
import TranscriptList from '../components/media/TranscriptList';
import AIInsightsPanel from '../components/media/AIInsightsPanel';
import InVideoSearch from '../components/media/InVideoSearch';

import TagChip from '../components/media/TagChip';

import WaveformSync from '../components/media/WaveformSync';


export default function AssetDetail() {
  const { id } = useParams();
  const [searchParams] = useSearchParams();
  const queryClient = useQueryClient();
  
  // URL Timestamp
  const initialTimestamp = searchParams.get('t') ? parseFloat(searchParams.get('t')) : 0;

  // Local states
  const [currentTime, setCurrentTime] = useState(initialTimestamp);
  const [seekTimestamp, setSeekTimestamp] = useState(initialTimestamp);
  const location = useLocation();
  const [activeTab, setActiveTab] = useState(location.state?.activeTab || 'OVERVIEW');
  const [rightSidebarMode, setRightSidebarMode] = useState('scenes'); // 'scenes' or 'transcript'
  const [showAllAssetTags, setShowAllAssetTags] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [debouncedQuery, setDebouncedQuery] = useState('');
  const [sortBy, setSortBy] = useState('time');
  const [isPlaying, setIsPlaying] = useState(false);
  
  const transcriptScrollRef = useRef(null);
  const activeTranscriptLineRef = useRef(null);
  
  // Interaction states for AI Insights
  const [activeMarkers, setActiveMarkers] = useState([]);
  const [selectedObjectId, setSelectedObjectId] = useState(null);
  const [selectedTagName, setSelectedTagName] = useState(null);
  const [wsProgress, setWsProgress] = useState(null);

  // Sync transcript scrolling
  useEffect(() => {
    if (activeTab === 'TRANSCRIPT' && activeTranscriptLineRef.current && transcriptScrollRef.current) {
      activeTranscriptLineRef.current.scrollIntoView({
        behavior: 'smooth',
        block: 'center',
      });
    }
  }, [currentTime, activeTab]);

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
    mutationFn: (q) => searchAssetScenes(id, q, 10)
  });

  // Favorite Mutation
  const favoriteMutation = useMutation({
    mutationFn: (isFav) => toggleFavorite(id, isFav),
    onSuccess: () => {
      queryClient.invalidateQueries(['asset', id]);
      queryClient.invalidateQueries(['assets']);
    }
  });

  // Reingest Mutation
  const reingestMutation = useMutation({
    mutationFn: () => reingestAsset(id),
    onMutate: () => {
      setWsProgress({ status: 'queued', progress: 0, message: 'Starting process...' });
    },
    onSuccess: (data) => {
      // Connect to websocket to track progress
      const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${wsProtocol}//${window.location.host}/api/v1/ingest/ws/${data.job_id}`;
      const ws = new WebSocket(wsUrl);
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
      const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${wsProtocol}//${window.location.host}/api/v1/ingest/ws/${data.job_id}`;
      const ws = new WebSocket(wsUrl);
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
    setSeekTimestamp(timeSec);
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
  const scenes = useMemo(() => scenesData?.scenes || scenesData || [], [scenesData]);
  const streamUrl = streamData?.stream_url || asset.file_path; // Fallback to file_path if stream API not ready

  // Use search results if searching, otherwise use all scenes
  const searchResults = useMemo(() => Array.isArray(searchMutation.data) ? searchMutation.data : [], [searchMutation.data]);
  
  const filteredScenes = useMemo(() => {
    if (debouncedQuery.trim() && searchResults.length > 0) {
      // Map search results (List[SceneResponse]) directly to component format
      return searchResults.map(s => ({
        id: s.scene_id,
        start_sec: s.timestamp_start_sec,
        end_sec: s.timestamp_end_sec || s.timestamp_start_sec + 5,
        thumbnail: s.thumbnail_url,
        description: s.caption,
        subtitle: s.transcript_snippet,
        tags: s.tags
      }));
    }

    return scenes.map(s => ({
      id: s.scene_id,
      start_sec: s.timestamp_start_sec,
      end_sec: s.timestamp_end_sec || s.timestamp_start_sec + 5,
      thumbnail: s.thumbnail_url,
      description: s.caption,
      subtitle: s.transcript_snippet,
      tags: s.tags
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

  const sortedScenes = useMemo(() => {
    if (sortBy === 'relevance' && debouncedQuery.trim() && searchResults.length > 0) {
      return filteredScenes; // Backend already sorted by vector distance!
    }
    return [...filteredScenes].sort((a, b) => a.start_sec - b.start_sec);
  }, [filteredScenes, sortBy, debouncedQuery, searchResults]);

  const filteredTranscript = (asset?.transcripts_json || []).map(line => ({
    ...line,
    start_sec: line.start !== undefined ? line.start : line.start_sec,
    end_sec: line.end !== undefined ? line.end : line.end_sec
  }));

  if (isLoadingAsset) {
    return <div className="flex h-screen items-center justify-center text-white">Loading Asset...</div>;
  }

  return (
    <div className="flex flex-col h-screen bg-[#F8F9FA] dark:bg-[#0E0B1F] text-gray-900 dark:text-white overflow-hidden relative transition-colors">
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
              <HeaderBar 
                title={asset.title || asset.file_name} 
                currentTime={currentTime}
                isFavorite={asset.is_favorite}
                onToggleFavorite={(isFav) => favoriteMutation.mutate(isFav)}
              />
            </div>
            
            {/* Video Player Area */}
            <div className="relative rounded-[6px] overflow-hidden bg-black flex-shrink-0 border border-gray-200 dark:border-gray-800 shadow-xl w-full mt-[12px]" style={{height: 'calc(100vh - 365px)', minHeight: '260px', maxHeight: '420px'}}>
              <VideoPlayer 
                src={streamUrl}
                seekTimestamp={seekTimestamp}
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
                  {['OVERVIEW', 'ACTIVE_SCENE', 'TRANSCRIPT', 'METADATA', 'AI_INSIGHTS'].map((tab) => (
                    <button
                       key={tab}
                       onClick={() => setActiveTab(tab)}
                       className="w-[85px] h-[32px] flex items-center justify-center relative focus:outline-none group"
                    >
                      <span className={`font-inter font-normal text-[11px] leading-[14px] transition-colors ${
                        activeTab === tab ? 'text-gray-900 dark:text-white font-bold' : 'text-gray-500 dark:text-gray-400 group-hover:text-gray-700 dark:group-hover:text-gray-200'
                      }`}>
                        {tab.replace('_', ' ')}
                      </span>
                      {activeTab === tab && (
                        <div className="absolute bottom-0 left-[8px] right-[8px] h-[2px] bg-[#7B5CF5] rounded-full"></div>
                      )}
                    </button>
                  ))}
                </div>

              </div>

              {/* Tabs Content */}
              <div className={`flex-1 py-2 px-4 custom-scrollbar ${activeTab === 'TRANSCRIPT' ? 'overflow-hidden flex flex-col' : 'overflow-y-auto'}`}>
                {activeTab === 'AI_INSIGHTS' && (
                  <div>

                    <AIInsightsPanel 
                      insight={{
                        summary: asset.summary || "No summary generated yet.",
                        objects: asset.objects || [],
                        moods: asset.moods || [],
                        best_for: asset.best_for || []
                      }}
                      scenes={sortedScenes}
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

                {activeTab === 'ACTIVE_SCENE' && (() => {
                  const activeScene = sortedScenes.find(s => currentTime >= s.start_sec && currentTime < s.end_sec) || sortedScenes[0];
                  if (!activeScene) return <div className="p-4 text-gray-500 text-sm">No scene data available.</div>;
                  return (
                    <div className="w-full flex gap-[12px] mt-[8px]">
                      {/* Left: Thumbnail & Time */}
                      <div className="w-[180px] flex-shrink-0 flex flex-col gap-2">
                        <div className="w-full aspect-video bg-gray-100 dark:bg-gray-800 rounded-lg overflow-hidden border border-gray-200 dark:border-gray-800">
                          <img src={activeScene.thumbnail} className="w-full h-full object-cover" alt="Scene Thumbnail" />
                        </div>
                        <div className="bg-[#7B5CF5]/10 text-[#7B5CF5] text-center py-1 rounded-[4px] text-[11px] font-bold font-mono">
                          {activeScene.start_sec.toFixed(2)}s - {activeScene.end_sec.toFixed(2)}s
                        </div>
                      </div>

                      {/* Right: Details */}
                      <div className="flex-1 flex flex-col gap-3 min-h-[110px] bg-white dark:bg-[#120F24] border border-[#7B5CF5]/30 dark:border-[#7B5CF5] rounded-[6px] p-[12px] shadow-[0_4px_16px_rgba(123,92,245,0.06)] dark:shadow-none overflow-y-auto max-h-[220px] custom-scrollbar">
                        <div>
                          <span className="font-inter font-bold text-[11px] leading-[15px] text-gray-900 dark:text-white block mb-1 uppercase">AI Caption</span>
                          <p className="font-inter font-normal text-[12px] leading-[18px] text-gray-700 dark:text-gray-300">
                            {activeScene.description || 'No caption'}
                          </p>
                        </div>
                        
                        {activeScene.subtitle && (
                          <div>
                            <span className="font-inter font-bold text-[11px] leading-[15px] text-gray-900 dark:text-white block mb-1 uppercase">Transcript Snippet</span>
                            <p className="font-inter font-normal text-[12px] leading-[18px] text-gray-500 dark:text-gray-400 italic">
                              "{activeScene.subtitle}"
                            </p>
                          </div>
                        )}

                        <div>
                          <span className="font-inter font-bold text-[11px] leading-[15px] text-gray-900 dark:text-white block mb-1 uppercase">Scene Tags</span>
                          <div className="flex flex-wrap gap-[6px]">
                            {(activeScene.tags || []).length > 0 ? (
                              activeScene.tags.map((tag, idx) => {
                                const tagObj = typeof tag === 'string' ? { name: tag, category: 'theme' } : tag;
                                return (
                                  <TagChip 
                                    key={idx} 
                                    tag={tagObj} 
                                    onClick={handleTagClick} 
                                    isActive={selectedTagName === tagObj.name} 
                                  />
                                );
                              })
                            ) : (
                              <span className="text-[11px] text-gray-500">No tags</span>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                })()}

                {activeTab === 'OVERVIEW' && (
                  <div className="relative w-full h-auto mt-[8px] flex gap-[12px]">
                    {/* AI Caption Box */}
                    <div className="flex-1 min-h-[110px] bg-white dark:bg-[#120F24] border border-[#7B5CF5]/30 dark:border-[#7B5CF5] rounded-[6px] box-border p-[10px] relative transition-all shadow-[0_4px_16px_rgba(123,92,245,0.06)] dark:shadow-none">
                      <span className="font-inter font-bold text-[12px] leading-[15px] text-gray-900 dark:text-white block mb-1 transition-colors">
                        AI CAPTION
                      </span>
                      <p className="font-inter font-normal text-[12px] leading-[15px] text-gray-700 dark:text-gray-300 transition-colors">
                        {asset.summary || 'No caption available'}
                      </p>
                    </div>

                    {/* Tags Box */}
                    <div className="w-[300px] min-h-[110px] max-h-[180px] overflow-y-auto custom-scrollbar bg-white dark:bg-[#120F24] border border-[#7B5CF5]/30 dark:border-[#7B5CF5] rounded-[6px] box-border p-[10px] relative flex-shrink-0 transition-all shadow-[0_4px_16px_rgba(123,92,245,0.06)] dark:shadow-none">
                      <span className="font-inter font-bold text-[12px] leading-[15px] text-gray-900 dark:text-white block mb-2 transition-colors">
                        TAGS
                      </span>
                      <div className="flex flex-wrap gap-[5px]">
                        {(() => {
                          const allTags = asset.tags || [];
                          const visibleTags = showAllAssetTags ? allTags : allTags.slice(0, 7);
                          const hiddenCount = allTags.length - visibleTags.length;
                          
                          return (
                            <>
                              {visibleTags.map((tag, idx) => (
                                <TagChip 
                                  key={idx} 
                                  tag={typeof tag === 'string' ? { name: tag, category: 'theme' } : tag} 
                                  onClick={handleTagClick} 
                                  isActive={selectedTagName === (typeof tag === 'string' ? tag : tag.name)} 
                                />
                              ))}
                              
                              {hiddenCount > 0 && !showAllAssetTags && (
                                <button 
                                  onClick={() => setShowAllAssetTags(true)}
                                  className="text-[10px] text-[#7B5CF5] dark:text-[#c4b5fd] font-bold hover:underline ml-1 px-2 py-1 bg-[#7B5CF5]/10 rounded-[4px]"
                                >
                                  +{hiddenCount} MORE
                                </button>
                              )}
                              {showAllAssetTags && allTags.length > 7 && (
                                <button 
                                  onClick={() => setShowAllAssetTags(false)}
                                  className="text-[10px] text-gray-500 font-bold hover:underline ml-1 px-2 py-1 bg-gray-100 dark:bg-gray-800 rounded-[4px]"
                                >
                                  SHOW LESS
                                </button>
                              )}
                            </>
                          );
                        })()}
                      </div>
                    </div>
                  </div>
                )}

                {activeTab === 'TRANSCRIPT' && (
                  <div className="w-full flex-1 min-h-0 bg-white dark:bg-[#120F24] border border-[#7B5CF5]/30 dark:border-[#7B5CF5] rounded-[6px] p-[16px] shadow-[0_4px_16px_rgba(123,92,245,0.06)] dark:shadow-none flex flex-col">
                    <h4 className="font-inter font-bold text-[12px] leading-[15px] text-gray-900 dark:text-white mb-4 uppercase tracking-wide shrink-0">
                      Transcript Viewer
                    </h4>
                    
                    <div ref={transcriptScrollRef} className="flex-1 overflow-y-auto custom-scrollbar pr-2 flex flex-col gap-[12px]">
                      {filteredTranscript && filteredTranscript.length > 0 ? (
                        filteredTranscript.map((t, idx) => {
                          const isActive = currentTime >= t.start_sec && currentTime < t.end_sec;
                          
                          return (
                            <div 
                              key={idx} 
                              ref={isActive ? activeTranscriptLineRef : null}
                              className="flex w-full justify-start group transition-all"
                            >
                              <div className="flex w-full max-w-[90%] gap-[12px] flex-row">
                                
                                {/* Time Marker */}
                                <div className="w-[45px] shrink-0 pt-[8px] text-[10px] font-mono text-gray-400 group-hover:text-[#7B5CF5] transition-colors">
                                  {t.start_sec.toFixed(1)}s
                                </div>
                                
                                {/* Message Bubble */}
                                <div className="flex-1 flex flex-col items-start">
                                  <div 
                                    className={`px-[12px] py-[8px] rounded-[6px] text-[13px] leading-[22px] transition-all cursor-pointer ${
                                      isActive ? 'bg-[#7B5CF5]/10 border-l-[3px] border-[#7B5CF5]' : 'bg-transparent border-l-[3px] border-transparent hover:bg-gray-50 dark:hover:bg-white/5'
                                    }`}
                                    onClick={() => handleSeek(t.start_sec)}
                                  >
                                    <span className={`${isActive ? 'text-[#7B5CF5] dark:text-[#c4b5fd] font-medium' : 'text-gray-700 dark:text-gray-300'}`}>
                                      {t.text}
                                    </span>
                                  </div>
                                </div>
                              </div>
                            </div>
                          );
                        })
                      ) : (
                        <p className="text-gray-500 text-[12px]">No transcript data available for this media.</p>
                      )}
                    </div>
                  </div>
                )}

                {activeTab === 'METADATA' && (
                  <div className="bg-white dark:bg-[#120F24] border border-gray-200 dark:border-white/5 rounded-lg p-5 transition-all shadow-[0_4px_16px_rgba(0,0,0,0.04)] dark:shadow-none w-full">
                    <h4 className="font-medium text-gray-900 dark:text-white mb-4 transition-colors">File Information</h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-4 text-sm">
                      <div className="flex justify-between border-b border-gray-200 dark:border-gray-800 pb-2 transition-colors">
                        <span className="text-gray-500">File Name</span>
                        <span className="text-gray-800 dark:text-gray-300 font-medium transition-colors">{asset.file_name}</span>
                      </div>
                      <div className="flex justify-between border-b border-gray-200 dark:border-gray-800 pb-2 transition-colors">
                        <span className="text-gray-500">File Size</span>
                        <span className="text-gray-800 dark:text-gray-300 font-medium transition-colors">{asset.file_size}</span>
                      </div>
                      <div className="flex justify-between border-b border-gray-200 dark:border-gray-800 pb-2 transition-colors">
                        <span className="text-gray-500">Duration</span>
                        <span className="text-gray-800 dark:text-gray-300 font-medium transition-colors">{asset.duration}s</span>
                      </div>
                      <div className="flex justify-between border-b border-gray-200 dark:border-gray-800 pb-2 transition-colors">
                        <span className="text-gray-500">Resolution</span>
                        <span className="text-gray-800 dark:text-gray-300 font-medium transition-colors">{asset.resolution}</span>
                      </div>
                      <div className="flex justify-between border-b border-gray-200 dark:border-gray-800 pb-2 transition-colors">
                        <span className="text-gray-500">Created At</span>
                        <span className="text-gray-800 dark:text-gray-300 font-medium transition-colors">{new Date(asset.created_at).toLocaleDateString()}</span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
            
          </div>

          {/* Right Column */}
          {asset.mediaType !== 'image' && (
            <div className="w-[380px] flex flex-col bg-white dark:bg-[#120F24] border border-gray-200 dark:border-[#2D2844] shadow-[0_4px_24px_rgba(0,0,0,0.06)] dark:shadow-none rounded-[6px] flex-shrink-0 p-[8px] gap-[8px] transition-all">
              
              {/* Sidebar Toggle Buttons */}
              <div className="flex w-full rounded-[4px] overflow-hidden border border-[#7B5CF5]/30 dark:border-[#7B5CF5]/40 shadow-sm flex-shrink-0">
                <button
                  onClick={() => setRightSidebarMode('scenes')}
                  className={`flex-1 py-1.5 font-inter font-bold text-[11px] uppercase tracking-wide transition-colors ${
                    rightSidebarMode === 'scenes'
                      ? 'bg-[#7B5CF5]/10 text-[#7B5CF5] dark:text-[#c4b5fd]'
                      : 'bg-transparent text-gray-500 hover:bg-[#7B5CF5]/5 dark:hover:bg-[#7B5CF5]/10'
                  }`}
                >
                  SCENES
                </button>
                <button
                  onClick={() => setRightSidebarMode('transcript')}
                  className={`flex-1 py-1.5 font-inter font-bold text-[11px] uppercase tracking-wide transition-colors ${
                    rightSidebarMode === 'transcript'
                      ? 'bg-[#7B5CF5]/10 text-[#7B5CF5] dark:text-[#c4b5fd]'
                      : 'bg-transparent text-gray-500 hover:bg-[#7B5CF5]/5 dark:hover:bg-[#7B5CF5]/10'
                  }`}
                >
                  TRANSCRIPT
                </button>
              </div>

              {/* Top Search */}
              <div className="flex-shrink-0">
                <InVideoSearch 
                  searchQuery={searchQuery}
                  onSearchChange={setSearchQuery}
                  isSearching={searchMutation.isLoading}
                />
              </div>

              {/* Showing Count and Sort Option */}
              <div className="flex items-center justify-between text-[11px] text-gray-500 dark:text-white/70 px-[6px] py-[2px] border-b border-gray-200 dark:border-white/10 shrink-0 pb-[4px] transition-colors">
                <span>
                  {rightSidebarMode === 'transcript' 
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
                    <option value="time" className="bg-white dark:bg-[#0E0B1F] text-gray-700 dark:text-white">Time</option>
                    <option value="relevance" className="bg-white dark:bg-[#0E0B1F] text-gray-700 dark:text-white">Relevance</option>
                  </select>
                </div>
              </div>

              {/* Timeline/Scenes or Transcript List */}
              <div className="flex-1 overflow-hidden">
                {rightSidebarMode === 'transcript' ? (
                  <TranscriptList 
                    transcript={filteredTranscript} 
                    currentTime={currentTime} 
                    onSeek={handleSeek}
                    searchQuery={debouncedQuery}
                  />
                ) : (
                  <SceneList 
                    assetId={id}
                    scenes={sortedScenes} 
                    currentTime={currentTime} 
                    onSeek={handleSeek}
                    searchQuery={debouncedQuery}
                  />
                )}
              </div>
              
              {/* Detect Button or Waveform Player */}
              <div className="flex-shrink-0">
                {rightSidebarMode === 'transcript' ? (
                  <WaveformSync
                    streamUrl={streamUrl}
                    currentTime={currentTime}
                    onSeek={handleSeek}
                    isPlaying={isPlaying}
                    onTogglePlay={() => setIsPlaying(!isPlaying)}
                  />
                ) : (
                  <div className="w-full py-[8px] flex items-center justify-center border border-dashed border-[#7B5CF5]/30 dark:border-[#7B5CF5]/40 rounded-[6px] bg-[#7B5CF5]/5 dark:bg-[#16132A]/20 transition-colors">
                    <button 
                      onClick={handleDetectScenes}
                      disabled={reingestMutation.isLoading}
                      className="text-[11px] font-inter font-medium text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors flex items-center gap-1.5"
                    >
                      {reingestMutation.isLoading ? (
                        <span className="w-3 h-3 border-2 border-[#7B5CF5] border-t-transparent rounded-full animate-spin" />
                      ) : null}
                      <span>Showing {sortedScenes.length} scenes · <span className="text-[#7B5CF5] dark:text-[#c4b5fd] hover:text-gray-900 dark:hover:text-white font-bold hover:underline transition-colors">Detect more</span></span>
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
