import { useState, useEffect } from 'react';
import { useJobs } from '../../contexts/JobContext';
import { retryJob } from '../../services/api';
import { AlertCircle, RotateCcw } from 'lucide-react';

const MOCK_STAGES = [
  { id: 'extracting', name: 'EXTRACTING SCENES', step_keys: ['uploading_to_s3', 'scene_detection'] },
  { id: 'transcribing', name: 'TRANSCRIBING AUDIO', step_keys: ['audio_transcription'] },
  { id: 'captioning', name: 'GENERATING CAPTION', step_keys: ['frame_analysis'] },
  { id: 'embedding', name: 'GENERATING EMBEDDING', step_keys: ['embedding'] }
];

// Helper to determine stage progress for a single job
const getJobStageProgress = (job) => {
  let targets = { extracting: 0, transcribing: 0, captioning: 0, embedding: 0, overall: 0 };

  if (job.status === 'completed') {
    return { extracting: 100, transcribing: 100, captioning: 100, embedding: 100, overall: 100 };
  }

  targets.overall = job.progress || 0;
  const step = job.current_step;

  // Pipeline order: uploading -> scene_detection -> audio_transcription -> frame_analysis -> embedding
  if (step === 'uploading_to_s3' || step === 'scene_detection') {
    targets.extracting = job.progress || 10;
  } else if (step === 'audio_transcription') {
    targets.extracting = 100;
    targets.transcribing = job.progress || 10;
  } else if (step === 'frame_analysis') {
    targets.extracting = 100;
    targets.transcribing = 100;
    targets.captioning = job.progress || 10;
  } else if (step === 'embedding') {
    targets.extracting = 100;
    targets.transcribing = 100;
    targets.captioning = 100;
    targets.embedding = job.progress || 10;
  }

  return targets;
};

export default function AIProcessingPanel() {
  const { activeJobs } = useJobs();
  const [isRetrying, setIsRetrying] = useState(false);
  const [smoothStats, setSmoothStats] = useState({
    extracting: { percent: 0, count: 0 },
    transcribing: { percent: 0, count: 0 },
    captioning: { percent: 0, count: 0 },
    embedding: { percent: 0, count: 0 },
    overall: 0
  });

  const totalJobs = activeJobs ? activeJobs.length : 0;
  const failedJobs = activeJobs ? activeJobs.filter(j => j.status === 'failed') : [];

  // Calculate aggregated stats
  useEffect(() => {
    if (totalJobs === 0) return;

    let sums = { extracting: 0, transcribing: 0, captioning: 0, embedding: 0, overall: 0 };
    let counts = { extracting: 0, transcribing: 0, captioning: 0, embedding: 0 };

    activeJobs.forEach(job => {
      const p = getJobStageProgress(job);
      sums.extracting += p.extracting;
      sums.transcribing += p.transcribing;
      sums.captioning += p.captioning;
      sums.embedding += p.embedding;
      sums.overall += p.overall;

      if (p.extracting === 100) counts.extracting++;
      if (p.transcribing === 100) counts.transcribing++;
      if (p.captioning === 100) counts.captioning++;
      if (p.embedding === 100) counts.embedding++;
    });

    const targetStats = {
      extracting: { percent: totalJobs > 0 ? sums.extracting / totalJobs : 0, count: counts.extracting },
      transcribing: { percent: totalJobs > 0 ? sums.transcribing / totalJobs : 0, count: counts.transcribing },
      captioning: { percent: totalJobs > 0 ? sums.captioning / totalJobs : 0, count: counts.captioning },
      embedding: { percent: totalJobs > 0 ? sums.embedding / totalJobs : 0, count: counts.embedding },
      overall: totalJobs > 0 ? sums.overall / totalJobs : 0
    };

    const interval = setInterval(() => {
      setSmoothStats(prev => {
        const chase = (current, target) => {
          if (current < target) return Math.min(current + 3, target);
          if (current > target) return target; // jump down instantly if jobs removed
          return current;
        };
        return {
          extracting: { percent: chase(prev.extracting.percent, targetStats.extracting.percent), count: targetStats.extracting.count },
          transcribing: { percent: chase(prev.transcribing.percent, targetStats.transcribing.percent), count: targetStats.transcribing.count },
          captioning: { percent: chase(prev.captioning.percent, targetStats.captioning.percent), count: targetStats.captioning.count },
          embedding: { percent: chase(prev.embedding.percent, targetStats.embedding.percent), count: targetStats.embedding.count },
          overall: chase(prev.overall, targetStats.overall)
        };
      });
    }, 50);

    return () => clearInterval(interval);
  }, [activeJobs, totalJobs]);

  const handleRetryAll = async () => {
    if (failedJobs.length === 0) return;
    setIsRetrying(true);
    try {
      const promises = failedJobs.map(job => retryJob(job.job_id));
      await Promise.all(promises);
    } catch (error) {
      console.error("Retry all failed", error);
    } finally {
      setIsRetrying(false);
    }
  };

  // Determine which stages have errors
  const errorStages = {};
  if (totalJobs > 0) {
    failedJobs.forEach(job => {
      let matched = false;
      MOCK_STAGES.forEach(stage => {
        if (stage.step_keys.includes(job.current_step)) {
          errorStages[stage.id] = true;
          matched = true;
        }
      });
      // Fallback if step is not recognized (e.g., 'Initialize pipeline') or null
      if (!matched) {
        errorStages['extracting'] = true;
      }
    });
  }

  const hasFailed = failedJobs.length > 0;
  const statusColor = totalJobs === 0 ? '#6B7280' : (hasFailed ? '#EF4444' : '#4ADE80'); // Gray when idle


  return (
    <div className="w-[268px] flex flex-col items-center">
      <div className="w-full bg-[#7B5CF5]/10 border border-[#4F8EF7]/50 rounded-[8px] flex flex-col p-[16px] shrink-0 mb-4 transition-colors relative overflow-hidden">

        {/* Glow effect on top */}
        <div className="absolute top-0 left-0 w-full h-[2px] bg-gradient-to-r from-transparent via-[#7B5CF5] to-transparent opacity-50"></div>

        {/* Header */}
        <div className="flex items-center justify-between mb-[20px]">
          <h2 className="font-inter font-bold text-[12px] leading-[15px] text-[#7B5CF5] uppercase tracking-wide whitespace-nowrap truncate mr-2">
            SMA - AI Processing
          </h2>
          <div className="flex items-center gap-1.5 shrink-0">
            {hasFailed && (
              <button
                onClick={handleRetryAll}
                disabled={isRetrying}
                className="flex items-center justify-center w-[20px] h-[20px] bg-[#EF4444]/10 hover:bg-[#EF4444]/20 border border-[#EF4444]/50 rounded-full transition-colors shrink-0"
                title="Retry all failed"
              >
                <RotateCcw className={`w-2.5 h-2.5 text-[#EF4444] ${isRetrying ? 'animate-spin' : ''}`} />
              </button>
            )}
            <div className="flex items-center gap-[6px] shrink-0 px-2 py-1 bg-[#1A162B] rounded-full border border-white/5 shadow-inner">
              <div className={`w-[6px] h-[6px] rounded-full ${hasFailed ? 'animate-pulse' : ''}`} style={{ backgroundColor: statusColor }}></div>
              <span className="font-inter font-medium text-[9px]" style={{ color: statusColor }}>
                {hasFailed ? `${failedJobs.length} FAILED` : `${totalJobs} ACTIVE`}
              </span>
            </div>
          </div>
        </div>

        {/* Stages */}
        <div className="flex flex-col space-y-[14px]">
          {MOCK_STAGES.map((stage) => {
            const stats = smoothStats[stage.id];
            const hasError = errorStages[stage.id];

            return (
              <div key={stage.id} className="space-y-[6px]">
                <div className="flex justify-between items-end text-white">
                  <div className="flex items-center gap-1.5">
                    <span className="font-inter font-medium text-[10px] leading-[12px] uppercase text-gray-200">
                      {stage.name}
                    </span>
                    {hasError && (
                      <AlertCircle className="w-3 h-3 text-[#EF4444] animate-pulse" title="Bottleneck error here!" />
                    )}
                  </div>
                  <div className="flex items-baseline gap-1">
                    <span className="font-inter font-normal text-[9px] text-gray-400">
                      ({stats.count}/{totalJobs > 0 ? totalJobs : 0})
                    </span>
                    <span className={`font-inter font-bold text-[11px] w-[28px] text-right ${hasError ? 'text-[#EF4444]' : 'text-white'}`}>
                      {Math.floor(stats.percent)}%
                    </span>
                  </div>
                </div>
                <div className="w-full h-[6px] bg-[#D9D9D9]/10 rounded-full overflow-hidden relative">
                  <div
                    className={`h-full transition-all duration-300 ${hasError ? 'bg-[#EF4444]' : 'bg-[#7B5CF5]'}`}
                    style={{ width: `${stats.percent}%` }}
                  />
                </div>
              </div>
            );
          })}

          {/* Divider */}
          <div className="h-[1px] w-full bg-white/10 my-2"></div>

          {/* Overall Progress */}
          <div className="space-y-[6px] pt-1">
            <div className="flex justify-between items-center text-white">
              <span className="font-inter font-bold text-[11px] uppercase text-[#4ADE80]">
                GLOBAL PROGRESS
              </span>
              <span className="font-inter font-bold text-[12px] text-[#4ADE80]">
                {Math.floor(smoothStats.overall)}%
              </span>
            </div>
            <div className="w-full h-[6px] bg-[#D9D9D9]/20 rounded-full overflow-hidden shadow-[0_0_10px_rgba(74,222,128,0.15)]">
              <div
                className="h-full transition-all duration-300 bg-[#4ADE80]"
                style={{ width: `${smoothStats.overall}%` }}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

