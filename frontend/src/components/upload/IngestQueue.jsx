import { useState, useEffect } from 'react';
import { useJobs } from '../../contexts/JobContext';
import { useIngestWebSocket } from '../../hooks/useIngestWebSocket';
import { retryJob } from '../../services/api';
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

function JobQueueCard({ job, onRemove }) {
  useIngestWebSocket(job.job_id);
  const [isRetrying, setIsRetrying] = useState(false);
  const [displayProgress, setDisplayProgress] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setDisplayProgress(prev => {
        const target = job.status === 'completed' ? 100 : (job.progress || 0);
        if (prev < target) return Math.min(prev + 2, target);
        if (prev > target) return target;
        return prev;
      });
    }, 100);
    return () => clearInterval(interval);
  }, [job.progress, job.status]);

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

  const displayTitle = `IMG_${job.job_id.substring(0,6).toUpperCase()}.mp4`;

  return (
    <div className={`w-full ${isFailed ? 'bg-[#EF4444]/10 border-[#EF4444]' : 'bg-[#16132A] border-[#2D2844]'} border rounded-[8px] flex p-[12px] mb-[12px] transition-colors relative`}>
      {isFailed && (
        <button onClick={() => onRemove(job.job_id)} className="absolute top-[4px] right-[4px] text-gray-400 hover:text-white bg-[#1A162B] rounded-full p-[2px]">
          <X className="w-4 h-4" />
        </button>
      )}

      {/* Thumbnail */}
      <div className="w-[100px] h-[60px] bg-[#2D2844] rounded-[4px] shrink-0 flex items-center justify-center mr-[16px] overflow-hidden">
        <ImageIcon className="w-6 h-6 text-gray-500" />
      </div>

      {/* Info & Progress */}
      <div className="flex-1 flex flex-col justify-between min-w-0 py-1">
        
        {/* Row 1: Title & Step */}
        <div className="flex justify-between items-start mb-[4px]">
          <h3 className="font-inter font-medium text-[12px] text-white truncate max-w-[150px]">
            {displayTitle}
          </h3>
          <span className="font-inter font-medium text-[11px] truncate" style={{ color: progressColor, maxWidth: '120px' }}>
            {stepText}
          </span>
        </div>

        {/* Row 2: Subtitle & ETA */}
        <div className="flex justify-between items-center mb-[8px]">
          <span className="font-inter font-normal text-[10px] text-gray-400 truncate max-w-[180px]">
            215MB - 00:01:09 - 1920x1080
          </span>
          <span className="font-inter font-normal text-[10px] text-gray-400">
            {isCompleted ? '' : (isFailed ? '' : `ETA: 00:40`)}
          </span>
        </div>

        {/* Progress Bar & Buttons */}
        {isFailed ? (
           <div className="flex justify-between items-center mt-1">
             <span className="text-[11px] text-[#EF4444] truncate pr-2 max-w-[200px]" title={job.error_message}>
               {job.error_message || "Unknown error"}
             </span>
             <button 
                onClick={handleRetry}
                disabled={isRetrying}
                className="bg-[#EF4444] text-white p-[4px] rounded disabled:opacity-50 flex items-center justify-center"
              >
                <RotateCcw className={`w-[12px] h-[12px] ${isRetrying ? 'animate-spin' : ''}`} />
              </button>
           </div>
        ) : (
          <div className="flex items-center gap-[12px]">
            <div className="flex-1 h-[4px] bg-[#D9D9D9]/20 rounded-full overflow-hidden">
              <div 
                className="h-full transition-all duration-300"
                style={{ width: `${displayProgress}%`, backgroundColor: progressColor }}
              />
            </div>
            <span className="font-inter font-medium text-[11px] text-white w-[28px] text-right">
              {Math.floor(displayProgress)}%
            </span>
            {!isCompleted && (
              <div className="w-[20px] h-[20px] bg-white rounded-full flex items-center justify-center shrink-0 cursor-pointer">
                <Pause className="w-[10px] h-[10px] text-black fill-black" />
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default function IngestQueue() {
  const { activeJobs, removeJob, clearCompletedJobs } = useJobs();

  if (!activeJobs || activeJobs.length === 0) return null;

  return (
    <div className="w-full flex flex-col items-center bg-[#0B0914] p-4 rounded-lg border border-[#2D2844]">
      <div className="w-full flex justify-between items-center mb-[16px]">
        <h2 className="font-inter font-bold text-[14px] text-white">INgest Queue</h2>
        <span 
          onClick={clearCompletedJobs}
          className="font-inter font-normal text-[12px] text-gray-400 cursor-pointer hover:text-white transition-colors"
        >
          Clear Completed
        </span>
      </div>

      <div className="w-full flex flex-col items-center max-h-[600px] overflow-y-auto no-scrollbar">
        {activeJobs.map(job => (
          <JobQueueCard key={job.job_id} job={job} onRemove={removeJob} />
        ))}
      </div>
    </div>
  );
}
