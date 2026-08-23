import { useState, useEffect } from 'react';
import { useJobs } from '../../contexts/JobContext';
import { retryJob } from '../../services/api';
import { AlertCircle, RotateCcw } from 'lucide-react';

const PANEL_STAGES = [
  { id: 'extracting', name: 'EXTRACTING SCENES', step_keys: ['metadata', 'proxy', 'uploading_to_s3', 'scene_detection'] },
  { id: 'transcribing', name: 'TRANSCRIBING AUDIO', step_keys: ['transcription'] },
  { id: 'captioning', name: 'GENERATING CAPTION', step_keys: ['vision_caption', 'keyframe_extraction', 'keyframe_upload'] },
  { id: 'embedding', name: 'GENERATING EMBEDDING', step_keys: ['embedding', 'persisting_results'] }
];

const getJobStageProgress = (job) => {
  let targets = { extracting: 0, transcribing: 0, captioning: 0, embedding: 0, overall: 0 };
  if (job.status === 'completed') return { extracting: 100, transcribing: 100, captioning: 100, embedding: 100, overall: 100 };
  targets.overall = job.progress || 0;
  const step = job.current_step;
  if (['metadata', 'proxy', 'uploading_to_s3', 'scene_detection'].includes(step)) targets.extracting = job.progress || 10;
  else if (step === 'transcription') { targets.extracting = 100; targets.transcribing = job.progress || 10; }
  else if (['vision_caption', 'keyframe_extraction', 'keyframe_upload'].includes(step)) { targets.extracting = 100; targets.transcribing = 100; targets.captioning = job.progress || 10; }
  else if (['embedding', 'persisting_results'].includes(step)) { targets.extracting = 100; targets.transcribing = 100; targets.captioning = 100; targets.embedding = job.progress || 10; }
  return targets;
};

export default function AIProcessingPanel() {
  const { activeJobs } = useJobs();
  const [isRetrying, setIsRetrying] = useState(false);
  const [smoothStats, setSmoothStats] = useState({
    extracting: { percent: 0, count: 0 }, transcribing: { percent: 0, count: 0 },
    captioning: { percent: 0, count: 0 }, embedding: { percent: 0, count: 0 }, overall: 0
  });

  const totalJobs = activeJobs ? activeJobs.length : 0;
  const failedJobs = activeJobs ? activeJobs.filter(j => j.status === 'failed') : [];

  useEffect(() => {
    if (totalJobs === 0) return;
    let sums = { extracting: 0, transcribing: 0, captioning: 0, embedding: 0, overall: 0 };
    let counts = { extracting: 0, transcribing: 0, captioning: 0, embedding: 0 };

    activeJobs.forEach(job => {
      const p = getJobStageProgress(job);
      sums.extracting += p.extracting; sums.transcribing += p.transcribing;
      sums.captioning += p.captioning; sums.embedding += p.embedding; sums.overall += p.overall;
      if (p.extracting === 100) counts.extracting++;
      if (p.transcribing === 100) counts.transcribing++;
      if (p.captioning === 100) counts.captioning++;
      if (p.embedding === 100) counts.embedding++;
    });

    const targetStats = {
      extracting: { percent: sums.extracting / totalJobs, count: counts.extracting },
      transcribing: { percent: sums.transcribing / totalJobs, count: counts.transcribing },
      captioning: { percent: sums.captioning / totalJobs, count: counts.captioning },
      embedding: { percent: sums.embedding / totalJobs, count: counts.embedding },
      overall: sums.overall / totalJobs
    };

    const interval = setInterval(() => {
      setSmoothStats(prev => {
        const chase = (curr, target) => (curr < target ? Math.min(curr + 15, target) : Math.max(curr - 15, target));
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
    try { await Promise.all(failedJobs.map(job => retryJob(job.job_id))); }
    catch (e) { console.error(e); } finally { setIsRetrying(false); }
  };

  const errorStages = {};
  failedJobs.forEach(job => {
    PANEL_STAGES.forEach(s => { if (s.step_keys.includes(job.current_step)) errorStages[s.id] = true; });
  });

  const statusColor = totalJobs === 0 ? '#6B7280' : (failedJobs.length > 0 ? '#EF4444' : '#4ADE80');

  return (
    <div className="w-[268px] bg-[#7B5CF5]/5 dark:bg-[#7B5CF5]/10 border border-sma-purple/30 dark:border-[#4F8EF7]/50 rounded-[8px] p-[12px] flex flex-col shrink-0 transition-colors">
      <div className="flex items-center justify-between mb-[12px]">
        <h2 className="font-bold text-[10px] text-[#7B5CF5] uppercase truncate mr-2">SMA - AI Processing</h2>
        <div className="flex items-center gap-1.5 shrink-0">
          {failedJobs.length > 0 && (
            <button onClick={handleRetryAll} disabled={isRetrying} className="p-1 bg-[#EF4444]/10 rounded-full border border-[#EF4444]/50">
              <RotateCcw className={`w-2.5 h-2.5 text-[#EF4444] ${isRetrying ? 'animate-spin' : ''}`} />
            </button>
          )}
          <div className="flex items-center gap-[6px] px-2 py-0.5 bg-white dark:bg-[#1A162B] rounded-full border border-gray-200 dark:border-white/5 transition-colors">
            <div className="w-[6px] h-[6px] rounded-full" style={{ backgroundColor: statusColor }}></div>
            <span className="font-medium text-[9px]" style={{ color: statusColor }}>
              {failedJobs.length > 0 ? `${failedJobs.length} FAILED` : `${totalJobs} ACTIVE`}
            </span>
          </div>
        </div>
      </div>

      {totalJobs > 0 && (
        <div className="flex flex-col space-y-[10px]">
          {PANEL_STAGES.map((stage) => {
            const stats = smoothStats[stage.id];
            const hasError = errorStages[stage.id];
            return (
              <div key={stage.id} className="space-y-[4px]">
                <div className="flex justify-between items-center text-gray-900 dark:text-white transition-colors">
                  <div className="flex items-center gap-1">
                    <span className="font-medium text-[9px] uppercase text-gray-500 dark:text-gray-200 transition-colors">{stage.name}</span>
                    {hasError && <AlertCircle className="w-2.5 h-2.5 text-[#EF4444]" />}
                  </div>
                  <span className={`font-bold text-[10px] transition-colors ${hasError ? 'text-[#EF4444]' : 'text-gray-900 dark:text-white'}`}>{Math.floor(stats.percent)}%</span>
                </div>
                <div className="w-full h-[5px] bg-gray-200 dark:bg-[#D9D9D9]/10 rounded-full overflow-hidden transition-colors">
                  <div className={`h-full transition-all duration-300 ${hasError ? 'bg-[#EF4444]' : 'bg-[#7B5CF5]'}`} style={{ width: `${stats.percent}%` }}></div>
                </div>
              </div>
            );
          })}
          <div className="h-[1px] w-full bg-gray-200 dark:bg-white/5 my-1 transition-colors"></div>
          <div className="space-y-[4px]">
            <div className="flex justify-between items-center transition-colors">
              <span className="font-bold text-[10px] uppercase text-[#4ADE80]">GLOBAL PROGRESS</span>
              <span className="font-bold text-[11px] text-[#4ADE80]">{Math.floor(smoothStats.overall)}%</span>
            </div>
            <div className="w-full h-[5px] bg-gray-200 dark:bg-[#D9D9D9]/20 rounded-full overflow-hidden transition-colors">
              <div className="h-full bg-[#4ADE80]" style={{ width: `${smoothStats.overall}%` }}></div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}