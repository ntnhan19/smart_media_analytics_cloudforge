import { useState, useEffect } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { useJobs } from '../../contexts/JobContext';
import { useIngestWebSocket } from '../../hooks/useIngestWebSocket';
import { retryJob, getAsset } from '../../services/api';
import { X, RotateCcw, Pause, Image as ImageIcon } from 'lucide-react';

const getStepName = (step) => {
  if (!step) return "Queued / Waiting to start";
  const stepMap = {
    'uploading_to_s3': "Uploading files...",
    'scene_detection': "Extracting scenes...",
    'audio_transcription': "Transcribing audio...",
    'frame_analysis': "Generating captions...",
    'embedding': "Generating embeddings..."
  };
  return stepMap[step] || "Processing...";
};

function JobQueueCard({ job, onRemove, isSelected, onClick }) {
  useIngestWebSocket(job.job_id);
  const [isRetrying, setIsRetrying] = useState(false);
  const [displayProgress, setDisplayProgress] = useState(0);
  const queryClient = useQueryClient();
  const { updateJob } = useJobs();

  // Fetch metadata when asset_id is available and step changes
  useEffect(() => {
    if (job.asset_id && (!job.duration || !job.resolution || !job.thumbnail_url)) {
      getAsset(job.asset_id).then(data => {
        if (data && (data.duration || data.resolution || data.thumbnail_url)) {
          updateJob({
            job_id: job.job_id,
            duration: data.duration || job.duration,
            resolution: data.resolution || job.resolution,
            file_size: data.file_size || job.file_size,
            thumbnail_url: data.thumbnail_url || job.thumbnail_url
          });
        }
      }).catch(err => console.error("Failed to fetch asset metadata", err));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [job.asset_id, job.current_step, job.status, job.duration, job.resolution, job.thumbnail_url, job.job_id, updateJob]);

  useEffect(() => {
    const interval = setInterval(() => {
      setDisplayProgress(prev => {
        const target = job.status === 'completed' ? 100 : (job.progress || 0);
        if (prev < target) {
          const step = job.status === 'completed' ? 15 : 5;
          return Math.min(prev + step, target);
        }
        if (prev > target) return target;
        return prev;
      });
    }, 50);
    return () => clearInterval(interval);
  }, [job.progress, job.status]);

  // User manual clear or auto-clear on new job
  useEffect(() => {
    if (job.status === 'completed') {
      // Cập nhật lại list ở Dashboard
      queryClient.invalidateQueries({ queryKey: ['assets'] });
    }
  }, [job.status, job.job_id, queryClient]);

  const handleRetry = async () => {
    setIsRetrying(true);
    try {
      await retryJob(job.job_id);
    } catch (e) {
      console.error("Retry failed", e);
      alert("Failed to retry: " + (e.response?.data?.detail || e.message));
      setIsRetrying(false);
    }
  };

  const isFailed = job.status === 'failed';
  const isCompleted = job.status === 'completed';
  const stepText = isFailed ? "Failed" : (isCompleted ? "Completed" : getStepName(job.current_step));
  const progressColor = isFailed ? '#EF4444' : (isCompleted ? '#4ADE80' : '#7B5CF5');

  const displayTitle = job.file_name ?? `Job #${job.job_id.substring(0,6).toUpperCase()}`;

  return (
    <div 
      onClick={onClick}
      className={`w-full ${isFailed ? 'bg-[#EF4444]/10 border-[#EF4444]' : (isSelected ? 'bg-blue-50 dark:bg-[#7B5CF5]/10 border-[#7B5CF5]' : 'bg-white dark:bg-[#16132A] border-gray-200 dark:border-[#2D2844] hover:bg-gray-50 dark:hover:bg-[#7B5CF5]/5')} border rounded-[8px] flex p-[12px] transition-colors relative cursor-pointer shadow-sm dark:shadow-none`}
    >


      {/* Thumbnail */}
      <div className="w-[100px] h-[60px] bg-gray-100 dark:bg-[#2D2844] rounded-[4px] shrink-0 flex items-center justify-center mr-[16px] overflow-hidden relative transition-colors">
        {job.thumbnail_url ? (
          <img src={job.thumbnail_url} alt="thumbnail" className="w-full h-full object-cover" />
        ) : (
          <ImageIcon className="w-6 h-6 text-gray-400 dark:text-gray-500 transition-colors" />
        )}
      </div>

      {/* Info & Progress */}
      <div className="flex-1 flex flex-col justify-between min-w-0 py-1">
        
        {/* Row 1: Title & Step */}
        <div className="flex justify-between items-start mb-[4px]">
          <h3 className="font-inter font-medium text-[12px] text-gray-900 dark:text-white truncate max-w-[150px] transition-colors">
            {displayTitle}
          </h3>
          <div className="flex items-center gap-1.5 shrink-0">
            <span className="font-inter font-medium text-[11px] truncate transition-colors" style={{ color: progressColor, maxWidth: '120px' }}>
              {stepText}
            </span>
            {(isFailed || isCompleted) && (
              <button 
                aria-label="Dismiss job"
                onClick={(e) => { e.stopPropagation(); onRemove(job.job_id); }} 
                className="text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white bg-gray-100 dark:bg-[#1A162B] rounded-full p-[2px] transition-colors shrink-0"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            )}
          </div>
        </div>

        {/* Row 2: Subtitle & ETA */}
        <div className="flex justify-between items-center mb-[8px]">
          <span className="font-inter font-normal text-[10px] text-gray-500 dark:text-gray-400 truncate max-w-[180px] transition-colors">
            {[
              job.file_size ? `${(job.file_size / (1024*1024)).toFixed(1)}MB` : null, 
              job.duration ? `${Math.floor(job.duration)}s` : null, 
              job.resolution
            ].filter(Boolean).join(' - ') || 'Loading metadata...'}
          </span>
          <span className="font-inter font-normal text-[10px] text-gray-500 dark:text-gray-400 transition-colors">
            {/* ETA hidden for now */}
          </span>
        </div>

        {/* Progress Bar & Buttons */}
        {isFailed ? (
           <div className="flex justify-between items-center mt-1">
             <span className="text-[11px] text-[#EF4444] truncate pr-2 max-w-[200px]" title={job.error_message}>
               {job.error_message || "Unknown error"}
             </span>
             <button 
                aria-label="Retry job"
                onClick={(e) => { e.stopPropagation(); handleRetry(); }}
                disabled={isRetrying}
                className="bg-[#EF4444] text-white p-[4px] rounded disabled:opacity-50 flex items-center justify-center"
              >
                <RotateCcw className={`w-[12px] h-[12px] ${isRetrying ? 'animate-spin' : ''}`} />
              </button>
           </div>
        ) : (
          <div className="flex items-center gap-[12px]">
            <div className="flex-1 h-[4px] bg-gray-200 dark:bg-[#D9D9D9]/20 rounded-full overflow-hidden transition-colors">
              <div 
                className="h-full transition-all duration-300"
                style={{ width: `${displayProgress}%`, backgroundColor: progressColor }}
              />
            </div>
            <span className="font-inter font-medium text-[11px] text-gray-900 dark:text-white w-[28px] text-right transition-colors">
              {Math.floor(displayProgress)}%
            </span>
            {!isCompleted && (
              <div
                role="button"
                aria-label="Pause job"
                tabIndex={0}
                className="w-[20px] h-[20px] bg-gray-800 dark:bg-white rounded-full flex items-center justify-center shrink-0 cursor-pointer transition-colors"
              >
                <Pause className="w-[10px] h-[10px] text-white dark:text-black fill-white dark:fill-black transition-colors" />
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default function IngestQueue({ selectedJobId, onSelectJob }) {
  const { activeJobs, removeJob } = useJobs();

  if (!activeJobs || activeJobs.length === 0) {
    return (
      <div className="w-full flex flex-col items-center justify-center h-[200px] text-gray-500 text-[12px]">
        No jobs in queue
      </div>
    );
  }

  return (
    <div className="w-full flex flex-col max-h-[800px] overflow-y-auto no-scrollbar gap-3">
      {activeJobs.map(job => (
        <JobQueueCard 
          key={job.job_id} 
          job={job} 
          onRemove={removeJob} 
          isSelected={job.job_id === selectedJobId}
          onClick={() => onSelectJob(job.job_id)}
        />
      ))}
    </div>
  );
}
