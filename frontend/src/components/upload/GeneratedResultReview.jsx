import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { ExternalLink, CheckCircle2, Clock, ChevronUp, ChevronDown } from 'lucide-react';
import { getAsset, getAssetScenes } from '../../services/api';
import { formatTimestamp } from '../../utils/formatters';

export default function GeneratedResultReview({ isOpen, onToggle, jobId, assetId, status, errorMessage, fileName }) {
  const navigate = useNavigate();
  const displayTitle = fileName ? `(${fileName})` : (jobId ? `(IMG_${jobId.substring(0, 6).toUpperCase()}.mp4)` : '(No Video Selected)');

  const { data: assetData } = useQuery({
    queryKey: ['asset', assetId],
    queryFn: () => getAsset(assetId),
    enabled: !!assetId && isOpen,
  });

  const { data: scenesData } = useQuery({
    queryKey: ['scenes', assetId],
    queryFn: () => getAssetScenes(assetId),
    enabled: !!assetId && isOpen,
  });

  const handleOpenAssets = () => {
    if (assetId) {
      navigate(`/assets/${assetId}`);
    } else {
      alert("Asset is still processing or no asset ID available.");
    }
  };

  const handleOpenAssetsTab = (tabName) => {
    if (assetId) {
      navigate(`/assets/${assetId}`, { state: { activeTab: tabName } });
    } else {
      alert("Asset is still processing or no asset ID available.");
    }
  };

  const getStatusBadge = () => {
    if (!status) return null;

    let colorClass = "border-[#4F8EF7]/60 text-[#4F8EF7]";
    let dotClass = "bg-[#4F8EF7] animate-pulse";
    let text = "Processing";

    if (status === 'failed') {
      colorClass = "border-[#EF4444]/60 text-[#EF4444]";
      dotClass = "bg-[#EF4444]";
      text = "Failed";
    } else if (status === 'completed') {
      colorClass = "border-[#4ADE80]/60 text-[#4ADE80]";
      dotClass = "bg-[#4ADE80]";
      text = "Completed";
    } else if (status === 'queued') {
      colorClass = "border-gray-400/60 text-gray-500 dark:text-gray-400";
      dotClass = "bg-gray-400";
      text = "Queued";
    }

    return (
      <span className={`flex items-center gap-1.5 border text-[11px] font-light px-2.5 py-0.5 rounded ml-2 transition-colors ${colorClass}`}>
        <span className={`w-1.5 h-1.5 rounded-full inline-block ${dotClass}`} />
        {text}
      </span>
    );
  };

  const scenesList = scenesData || [];
  const transcriptsList = assetData?.transcripts_json || [];
  const tagsList = assetData?.tags || [];

  // Calculate transcript completion
  const totalDuration = assetData?.duration || 1;
  const transcribedDuration = transcriptsList.reduce((acc, t) => acc + (t.end - t.start), 0);
  const transcriptPercentage = totalDuration > 0 ? Math.min(100, Math.round((transcribedDuration / totalDuration) * 100)) : 0;

  return (
    <div className="w-full h-full flex flex-col gap-3 overflow-hidden">
      {/* Header Row */}
      <div className="flex items-center justify-between shrink-0">
        <div className="flex items-center gap-3">
          {/* Nút Toggle Panel */}
          <button
            onClick={onToggle}
            className="w-6 h-6 rounded bg-white dark:bg-[#16132A] border border-gray-300 dark:border-[#7B5CF5]/50 flex items-center justify-center hover:bg-gray-50 dark:hover:bg-[#7B5CF5]/20 transition-colors shadow-sm dark:shadow-none"
          >
            {isOpen ? <ChevronDown className="w-4 h-4 text-[#7B5CF5]" /> : <ChevronUp className="w-4 h-4 text-[#7B5CF5]" />}
          </button>

          <h2 className="text-gray-900 dark:text-white text-[14px] font-bold cursor-pointer transition-colors" onClick={onToggle}>
            Generated Result Review{' '}
            {isOpen && <span className="text-gray-500 dark:text-gray-400 font-light text-[12px] transition-colors">{displayTitle}</span>}
          </h2>

          {isOpen && getStatusBadge()}
        </div>

        {isOpen && (
          <button
            onClick={handleOpenAssets}
            disabled={!assetId}
            className="flex items-center gap-2 border border-[#4F8EF7] text-gray-700 dark:text-white text-[12px] font-light px-4 py-1.5 rounded-lg bg-white dark:bg-[#16132A] hover:bg-[#4F8EF7]/10 dark:hover:bg-[#4F8EF7]/20 transition-colors disabled:opacity-50 disabled:cursor-not-allowed shadow-sm dark:shadow-none"
          >
            <ExternalLink className="w-3.5 h-3.5" />
            Open Assets
          </button>
        )}
      </div>

      {/* Nội dung bên dưới chỉ hiện khi mở (isOpen = true) */}
      {isOpen && status === 'failed' ? (
        <div className="flex-1 flex flex-col items-center justify-center border border-[#EF4444]/20 bg-[#EF4444]/5 rounded-xl min-h-[220px] transition-colors">
          <div className="w-12 h-12 rounded-full bg-[#EF4444]/10 flex items-center justify-center mb-3 transition-colors">
            <svg className="w-6 h-6 text-[#EF4444]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <h3 className="text-[#EF4444] text-[16px] font-bold mb-2">AI Processing Failed</h3>
          <p className="text-[#EF4444]/70 text-[13px] text-center max-w-md">
            {errorMessage || "An unexpected error occurred while analyzing this media. Please click the Retry button on the job card to try again."}
          </p>
        </div>
      ) : isOpen && (
        <div className="grid grid-cols-4 gap-4 flex-1 min-h-[220px]">

          {/* Col 1: Scene List */}
          <div className="bg-gray-50 dark:bg-[#120F1D] border border-gray-200 dark:border-[#16132A] rounded-lg flex flex-col overflow-hidden transition-colors shadow-sm dark:shadow-none">
            <div className="flex justify-between items-center px-4 pt-4 pb-3 shrink-0 transition-colors">
              <span className="text-gray-900 dark:text-white text-[12px] font-bold transition-colors">Scenes List</span>
              <button onClick={() => handleOpenAssetsTab('ACTIVE_SCENE')} className="text-[#7B5CF5] text-[10px] hover:underline">View All</button>
            </div>

            <div className="flex-1 overflow-x-auto no-scrollbar px-4 pb-2 flex gap-2">
              {scenesList.length === 0 && <span className="text-gray-500 text-[10px]">No scenes detected yet</span>}
              {scenesList.map((scene) => (
                <div key={scene.scene_id} className="flex flex-col border border-[#4F8EF7]/40 rounded-lg overflow-hidden shrink-0 w-[115px] bg-white dark:bg-[#16132A]/50 transition-all hover:border-[#4F8EF7] shadow-sm dark:shadow-none">
                  {/* Thumbnail part */}
                  <div className="h-[75px] bg-gradient-to-br from-gray-100 dark:from-[#120F1D] to-[#4F8EF7]/10 dark:to-[#4F8EF7]/20 border-b border-[#4F8EF7]/20 flex flex-col justify-end p-1.5 relative overflow-hidden transition-colors">
                    {scene.thumbnail_url && (
                      <img src={scene.thumbnail_url} alt="Scene thumbnail" className="absolute inset-0 w-full h-full object-cover opacity-80" />
                    )}
                    <div className="bg-[#4F8EF7] text-white text-[9px] px-1.5 py-0.5 rounded self-start shadow-md z-10">
                      {formatTimestamp(scene.timestamp_start_sec)}-{formatTimestamp(scene.timestamp_end_sec)}
                    </div>
                  </div>
                  {/* Text part */}
                  <div className="p-2.5 h-[50px] overflow-hidden transition-colors">
                    <p className="text-gray-500 dark:text-white/50 text-[9px] font-light leading-snug line-clamp-2 transition-colors" title={scene.caption}>
                      {scene.caption || "Generating caption..."}
                    </p>
                  </div>
                </div>
              ))}
            </div>

            <div className="h-[46px] border-t border-gray-200 dark:border-white/5 px-4 shrink-0 flex items-center gap-2 transition-colors">
              <div className="flex items-center gap-1.5 border border-[#4ADE80]/20 bg-[#4ADE80]/5 px-2 py-1 rounded-full transition-colors">
                <CheckCircle2 className="w-3 h-3 text-[#4ADE80] fill-[#4ADE80]/20" />
                <span className="text-[#4ADE80] text-[9px] font-light">{scenesList.length} Scenes Detected</span>
              </div>
              <div className="flex items-center gap-1.5 border border-[#4ADE80]/20 bg-[#4ADE80]/5 px-2 py-1 rounded-full transition-colors">
                <CheckCircle2 className="w-3 h-3 text-[#4ADE80] fill-[#4ADE80]/20" />
                <span className="text-[#4ADE80] text-[9px] font-light">{scenesList.filter(s => s.thumbnail_url).length} Thumbnails</span>
              </div>
            </div>
          </div>

          {/* Col 2: Transcript */}
          <div className="bg-gray-50 dark:bg-[#120F1D] border border-gray-200 dark:border-[#16132A] rounded-lg flex flex-col overflow-hidden relative transition-colors shadow-sm dark:shadow-none">
            <div className="absolute top-0 left-0 right-0 h-[2px] bg-gray-200 dark:bg-white/10 rounded-t-lg transition-colors">
              <div className="h-full bg-[#7B5CF5] rounded-t-lg transition-all duration-500" style={{ width: `${transcriptPercentage}%` }} />
            </div>
            <div className="flex justify-between items-center px-4 pt-5 pb-3 shrink-0 transition-colors">
              <span className="text-gray-900 dark:text-white text-[12px] font-bold transition-colors">Transcript <span className="text-[#7B5CF5] font-normal">({transcriptPercentage}%)</span></span>
              <button onClick={() => handleOpenAssetsTab('TRANSCRIPT')} className="text-[#7B5CF5] text-[10px] hover:underline">View All</button>
            </div>
            <div className="flex-1 overflow-y-auto no-scrollbar px-4 space-y-3 pb-2 transition-colors">
              {transcriptsList.length === 0 && <span className="text-gray-500 text-[10px] transition-colors">No transcripts available</span>}
              {transcriptsList.map((row, i) => (
                <div key={i} className="flex gap-2.5 items-start">
                  <div className="bg-[#4F8EF7]/80 text-white text-[7px] px-1.5 py-0.5 rounded shrink-0 mt-0.5">
                    {formatTimestamp(row.start)}-{formatTimestamp(row.end)}
                  </div>
                  <p className="text-gray-600 dark:text-white/70 text-[8px] font-light leading-relaxed transition-colors">{row.text}</p>
                </div>
              ))}
            </div>
            <div className="h-[46px] border-t border-gray-200 dark:border-white/5 px-4 shrink-0 flex items-center justify-between transition-colors">
              <span className="text-[#7B5CF5] text-[10px] font-medium transition-colors">{transcriptPercentage}% Transcribed</span>
              <span className="text-gray-500 dark:text-white/60 text-[10px] transition-colors">Languages: Auto</span>
              <span className="text-gray-500 dark:text-white/60 text-[10px] transition-colors">Speaker: Auto</span>
            </div>
          </div>

          {/* Col 3: AI Captions */}
          <div className="bg-gray-50 dark:bg-[#120F1D] border border-gray-200 dark:border-[#16132A] rounded-lg flex flex-col overflow-hidden transition-colors shadow-sm dark:shadow-none">
            <div className="flex justify-between items-center px-4 pt-4 pb-3 shrink-0 transition-colors">
              <span className="text-gray-900 dark:text-white text-[12px] font-bold transition-colors">
                AI Captions <span className="text-gray-500 dark:text-gray-400 font-light text-[10px] transition-colors">({status === 'completed' ? 'Completed' : 'Processing'})</span>
              </span>
              <button onClick={() => handleOpenAssetsTab('OVERVIEW')} className="text-[#7B5CF5] text-[10px] hover:underline">View All</button>
            </div>
            <div className="flex-1 overflow-y-auto no-scrollbar px-4 space-y-3 pb-2 transition-colors">
              {scenesList.length === 0 && <span className="text-gray-500 text-[10px] transition-colors">Waiting for scenes...</span>}
              {scenesList.map((scene, i) => (
                <div key={scene.scene_id} className="flex items-center gap-2.5">
                  {scene.caption ? (
                    <CheckCircle2 className="w-4 h-4 text-[#4ADE80] shrink-0" />
                  ) : (
                    <Clock className="w-4 h-4 text-[#7B5CF5] shrink-0 animate-pulse" />
                  )}
                  <span className="text-gray-600 dark:text-white/70 text-[10px] truncate transition-colors" title={scene.caption || `Generating captions for scene ${i + 1}..`}>
                    {scene.caption ? `Caption generated for scene ${i + 1}` : `Generating captions for scene ${i + 1}..`}
                  </span>
                </div>
              ))}
            </div>
            <div className="h-[46px] border-t border-gray-200 dark:border-white/5 px-4 shrink-0 flex items-center justify-center transition-colors">
              <span className="text-gray-500 dark:text-white/60 text-[10px] transition-colors">
                {scenesList.filter(s => s.caption).length}/{scenesList.length || 0} Completed
              </span>
            </div>
          </div>

          {/* Col 4: Tags */}
          <div className="bg-gray-50 dark:bg-[#120F1D] border border-gray-200 dark:border-[#16132A] rounded-lg flex flex-col overflow-hidden transition-colors shadow-sm dark:shadow-none">
            <div className="flex justify-between items-center px-4 pt-4 pb-3 shrink-0 transition-colors">
              <span className="text-gray-900 dark:text-white text-[12px] font-bold transition-colors">
                Tags <span className="text-gray-500 dark:text-gray-400 font-light text-[10px] transition-colors">(Auto generated)</span>
              </span>
              <button onClick={() => handleOpenAssetsTab('OVERVIEW')} className="text-[#7B5CF5] text-[10px] hover:underline">View All</button>
            </div>
            <div className="flex-1 overflow-y-auto no-scrollbar px-4 pb-2 transition-colors">
              {tagsList.length === 0 && <span className="text-gray-500 text-[10px] transition-colors">No tags generated</span>}
              <div className="flex flex-wrap gap-2 content-start transition-colors">
                {tagsList.map((tag, i) => {
                  const tagText = typeof tag === 'object' && tag !== null ? tag.name : tag;
                  return (
                    <span key={i} className="border border-[#7B5CF5] text-gray-700 dark:text-white text-[10px] font-bold px-3 py-1 rounded-md hover:bg-gray-100 dark:hover:bg-[#7B5CF5]/10 transition-colors cursor-pointer uppercase">
                      {tagText}
                    </span>
                  );
                })}
              </div>
            </div>
            <div className="h-[46px] border-t border-gray-200 dark:border-white/5 px-4 shrink-0 flex items-center justify-center transition-colors">
              <span className="text-gray-500 dark:text-white/60 text-[10px] transition-colors">
                {tagsList.length} Tags Generated
              </span>
            </div>
          </div>

        </div>
      )}
    </div>
  );
}
