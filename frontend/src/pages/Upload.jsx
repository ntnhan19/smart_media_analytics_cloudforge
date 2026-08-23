import { useState } from 'react';
import { useJobs } from '../contexts/JobContext';
import { uploadMediaFile } from '../services/api';
import IngestQueue from '../components/upload/IngestQueue';
import UploadArea from '../components/upload/UploadArea';
import AIPipelineTimeline from '../components/upload/AIPipelineTimeline';
import GeneratedResultReview from '../components/upload/GeneratedResultReview';
import { Settings, Plus, ChevronDown } from 'lucide-react';

export default function Upload() {
  const [isUploading, setIsUploading] = useState(false);
  const [isReviewOpen, setIsReviewOpen] = useState(false);
  const [selectedJobId, setSelectedJobId] = useState(null);
  const { activeJobs, addJob, clearAllFinishedJobs, clearAllJobs } = useJobs();

  const selectedJob = activeJobs?.find(j => j.job_id === selectedJobId);
  const selectedAssetId = selectedJob?.asset_id;

  const handleSelectJob = (jobId) => {
    setSelectedJobId(jobId);
    setIsReviewOpen(true); // Tự động mở panel khi click vào queue
  };

  const handleUpload = async (files) => {
    // Prevent synthetic events from being treated as files
    if (!files || files.type === 'click' || files._reactName === 'onClick') return;

    // Ensure files is an array (handles FileList if passed directly)
    const filesArray = Array.isArray(files) ? files : Array.from(files);
    if (filesArray.length === 0) return;

    setIsUploading(true);
    clearAllFinishedJobs();
    try {
      await Promise.all(
        filesArray.map(async (f) => {
          try {
            // Sử dụng API upload file vật lý mới đã có ở BE
            const res = await uploadMediaFile(
              f,
              { scene_detection: true, transcription: true, vision_caption: true, whisper_model: 'base' }
            );
            if (res?.job_id) addJob({ job_id: res.job_id, asset_id: res.asset_id ?? null, file_name: f.name, file_size: f.size, status: 'queued', progress: 0, current_step: null, error_message: null });
          } catch (e) { console.error(e); }
        })
      );
    } finally { setIsUploading(false); }
  };

  return (
    <div className="h-full overflow-hidden text-gray-900 dark:text-white font-inter flex flex-col gap-2 transition-colors">

      {/* ── HEADER BAR ── */}
      <div className="shrink-0 flex items-center justify-between py-1">
        {/* Left: Title */}
        <div>
          <h1 className="text-[15px] font-bold leading-tight">Upload Media</h1>
          <p className="text-[10px] text-gray-500 dark:text-gray-400 leading-tight transition-colors">Add your media to your local library</p>
        </div>

      </div>

      {/* Divider line */}
      <div className="shrink-0 h-px bg-gray-200 dark:bg-white/5 transition-colors" />

      {/* ── MAIN GRID WRAPPER ── */}
      <div
        className="flex-1 min-h-0 overflow-hidden"
        style={{
          display: 'grid',
          gridTemplateRows: isReviewOpen ? '59.5fr 40.5fr' : '1fr auto',
          gap: '10px'
        }}
      >
        {/* ROW 1: 3 CỘT CHÍNH */}
        <div className="min-h-0 overflow-hidden grid grid-cols-3 gap-3">

          {/* Cột 1: Upload Files */}
          <div className="min-h-0 overflow-hidden flex flex-col gap-2">
            <h2 className="text-[11px] font-bold shrink-0">
              1. <span className="text-[#7B5CF5] underline underline-offset-4">Upload Files</span>
            </h2>
            <div className="flex-1 min-h-0 overflow-hidden">
              <UploadArea onStartIngest={handleUpload} isUploading={isUploading} />
            </div>
          </div>

          {/* Cột 2: Configure AI */}
          <div className="min-h-0 overflow-hidden flex flex-col gap-2">
            <h2 className="text-[11px] font-bold shrink-0 flex items-center gap-1">
              <span>2. {activeJobs?.length > 0 ? <span className="text-[#7B5CF5] underline underline-offset-4">Configure AI</span> : "Configure AI"}</span>
              <span title="View Pipeline Docs" className="cursor-pointer text-gray-400 hover:text-gray-600 dark:hover:text-gray-300">
                <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><path d="M12 17h.01"/></svg>
              </span>
            </h2>
            <div className="flex-1 min-h-0 overflow-hidden">
              <AIPipelineTimeline />
            </div>
          </div>

          {/* Cột 3: Ingest Queue */}
          <div className="min-h-0 overflow-hidden flex flex-col gap-2">
            <h2 className="text-[11px] font-bold shrink-0">
              3. {activeJobs?.length > 0 ? <span className="text-[#7B5CF5] underline underline-offset-4">Review {"&"} Complete</span> : "Review & Complete"}
            </h2>
            <div className="flex-1 min-h-0 overflow-hidden bg-white dark:bg-[#120F1D] border border-gray-200 dark:border-white/5 rounded-lg flex flex-col transition-colors shadow-sm dark:shadow-none">
              <div className="flex justify-between items-center px-4 pt-3 pb-2 shrink-0 border-b border-gray-200 dark:border-white/5 transition-colors">
                <span className="text-[12px] font-bold">Ingest Queue</span>
                <button onClick={clearAllJobs} className="text-[10px] text-[#EF4444] hover:text-[#F87171] transition-colors">
                  Clear Queue
                </button>
              </div>
              <div className="flex-1 min-h-0 overflow-y-auto no-scrollbar px-3 py-2">
                <IngestQueue selectedJobId={selectedJobId} onSelectJob={handleSelectJob} />
              </div>
              <div className="px-4 py-2 border-t border-gray-200 dark:border-white/5 shrink-0 transition-colors">
                <button className="text-[10px] text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white flex items-center gap-1 transition-colors">
                  View all completed
                  <svg width="8" height="5" viewBox="0 0 10 6" fill="none"><path d="M1 1L5 5L9 1" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" /></svg>
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* ── ROW 2: Generated Result Review ── */}
        <div className="min-h-0 overflow-hidden border-t border-gray-200 dark:border-white/5 pt-2 transition-colors">
          <GeneratedResultReview
            isOpen={isReviewOpen}
            onToggle={() => setIsReviewOpen(!isReviewOpen)}
            jobId={selectedJobId}
            assetId={selectedAssetId}
            fileName={selectedJob?.file_name}
            status={selectedJob?.status}
            errorMessage={selectedJob?.error_message}
          />
        </div>
      </div>

    </div>
  );
}
