import { useState, useEffect } from 'react';
import { useJobs } from '../../contexts/JobContext';
import { useIngestWebSocket } from '../../hooks/useIngestWebSocket';

const MOCK_STAGES = [
  { id: 'extracting', name: 'EXTRACTING SCENES' },
  { id: 'transcribing', name: 'TRANSCRIBING AUDIO' },
  { id: 'embedding', name: 'GENERATING EMBEDDING' },
  { id: 'captioning', name: 'GENERATING CAPTION (LlaVA)' }
];

function JobProgressCard({ job }) {
  useIngestWebSocket(job.job_id);

  const [displayProgress, setDisplayProgress] = useState({
    overall: 0,
    extracting: 0,
    transcribing: 0,
    embedding: 0,
    captioning: 0
  });

  useEffect(() => {
    let targets = { extracting: 0, transcribing: 0, embedding: 0, captioning: 0, overall: 0 };
    
    if (job.status === 'completed') {
      targets = { extracting: 100, transcribing: 100, embedding: 100, captioning: 100, overall: 100 };
    } else if (job.status !== 'failed') {
      targets.overall = job.progress || 0;
      const step = job.current_step;
      
      if (step === 'uploading_to_s3') {
        targets.extracting = 20;
      } else if (step === 'scene_detection') {
        targets.extracting = 85;
      } else if (step === 'audio_transcription') {
        targets.extracting = 100;
        targets.transcribing = 85;
      } else if (step === 'frame_analysis') {
        targets.extracting = 100;
        targets.transcribing = 100;
        targets.captioning = 85;
      } else if (step === 'embedding') {
        targets.extracting = 100;
        targets.transcribing = 100;
        targets.captioning = 100;
        targets.embedding = 85;
      }
    }

    const interval = setInterval(() => {
      setDisplayProgress(prev => {
        const chase = (current, target) => {
          if (current < target) return Math.min(current + 5, target);
          if (current > target) return target;
          return current;
        };
        return {
          extracting: chase(prev.extracting, targets.extracting),
          transcribing: chase(prev.transcribing, targets.transcribing),
          embedding: chase(prev.embedding, targets.embedding),
          captioning: chase(prev.captioning, targets.captioning),
          overall: job.status === 'completed' ? 100 : Math.floor(job.progress || prev.overall)
        };
      });
    }, 100);

    return () => clearInterval(interval);
  }, [job.current_step, job.status, job.progress]);

  const isActive = job.status !== 'completed' && job.status !== 'failed';
  const statusColor = job.status === 'failed' ? '#EF4444' : (isActive ? '#4ADE80' : '#A78BFA');
  const statusText = job.status === 'failed' ? 'failed' : (isActive ? 'active' : 'completed');

  return (
    <div className="w-[268px] bg-[#7B5CF5]/20 border border-[#4F8EF7] rounded-[6px] flex flex-col p-[12px] shrink-0 mb-4 transition-colors">
      <div className="flex items-center justify-between mb-[16px]">
        <h2 className="font-inter font-normal text-[12px] leading-[15px] text-[#7B5CF5] truncate max-w-[150px] uppercase">
          SMA - AI PROCESSING
        </h2>
        <div className="flex items-center gap-[4px] shrink-0">
          <div className="w-[7.7px] h-[7.7px] rounded-full" style={{ backgroundColor: statusColor }}></div>
          <span className="font-inter font-normal text-[10px] leading-[12px]" style={{ color: statusColor }}>
            {statusText}
          </span>
        </div>
      </div>

      <div className="flex flex-col space-y-[12px]">
        {MOCK_STAGES.map((stage) => {
          const val = displayProgress[stage.id];
          return (
            <div key={stage.id} className="space-y-[6px]">
              <div className="flex justify-between items-center text-white">
                <span className="font-inter font-normal text-[10px] sm:text-[11px] leading-[13px] uppercase">
                  {stage.name}
                </span>
                <span className="font-inter font-normal text-[11px] leading-[13px]">
                  {val}%
                </span>
              </div>
              <div className="w-full h-[5px] bg-[#D9D9D9] rounded-[6px] overflow-hidden">
                <div 
                  className="h-full transition-all duration-300 bg-[#7B5CF5]"
                  style={{ width: `${val}%` }}
                />
              </div>
            </div>
          );
        })}
        
        {/* Overall Progress */}
        <div className="space-y-[6px] pt-[4px]">
          <div className="flex justify-between items-center text-white">
            <span className="font-inter font-normal text-[10px] sm:text-[11px] leading-[13px] uppercase">
              OVERALL PROGRESS
            </span>
            <span className="font-inter font-normal text-[11px] leading-[13px]">
              {displayProgress.overall}%
            </span>
          </div>
          <div className="w-full h-[5px] bg-[#D9D9D9] rounded-[6px] overflow-hidden">
            <div 
              className="h-full transition-all duration-300"
              style={{ width: `${displayProgress.overall}%`, backgroundColor: statusColor }}
            />
          </div>
        </div>
      </div>
    </div>
  );
}

export default function AIProcessingPanel() {
  const { activeJobs } = useJobs();

  if (!activeJobs || activeJobs.length === 0) return null;

  // Lấy job mới nhất để luôn chỉ hiển thị 1 khung cố định
  const latestJob = activeJobs[activeJobs.length - 1];

  return (
    <div className="w-full flex flex-col items-center">
      <JobProgressCard key={latestJob.job_id} job={latestJob} />
    </div>
  );
}

