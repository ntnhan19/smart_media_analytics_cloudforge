import { useState, useEffect } from 'react';
import { useJobs } from '../../contexts/JobContext';
import { CheckCircle2, Loader2, Clock } from 'lucide-react';

const PIPELINE_STAGES = [
  { id: 'upload', name: 'Upload', desc: 'Uploading files to local system', step_keys: ['uploading_file', 'uploading_to_s3'] },
  { id: 'metadata', name: 'Extract Metadata', desc: 'Reading metadata and file information', step_keys: ['metadata'] }, 
  { id: 'scene', name: 'Scene Detection', desc: 'Detecting scene changes in videos', step_keys: ['scene_detection'] },
  { id: 'thumbnail', name: 'Proxy & Thumbnail', desc: 'Generating thumbnails for each scene', step_keys: ['proxy'] }, 
  { id: 'audio', name: 'Audio Transcription (Whisper)', desc: 'Transcribing speech to text', step_keys: ['transcription'] },
  { id: 'caption', name: 'AI Caption Generation (LlaVa)', desc: 'Generating captions for each scene', step_keys: ['vision_caption', 'keyframe_extraction', 'keyframe_upload'] },
  { id: 'embedding', name: 'Embedding Generation', desc: 'Generating vectors embedding', step_keys: ['embedding'] },
  { id: 'index', name: 'Search Indexing', desc: 'Indexing to vector database', step_keys: ['persisting_results'] } 
];

// Helper to determine stage progress for a single job
const getJobStageProgress = (job) => {
  let targets = { upload: 0, metadata: 0, scene: 0, thumbnail: 0, audio: 0, caption: 0, embedding: 0, index: 0 };

  if (job.status === 'completed') {
    return { upload: 100, metadata: 100, scene: 100, thumbnail: 100, audio: 100, caption: 100, embedding: 100, index: 100 };
  }

  const step = job.current_step;
  
  if (['uploading_file', 'uploading_to_s3'].includes(step)) {
    targets.upload = job.progress || 10;
  } else if (step === 'metadata') {
    targets.upload = 100;
    targets.metadata = job.progress || 10;
  } else if (step === 'scene_detection') {
    targets.upload = 100;
    targets.metadata = 100;
    targets.scene = job.progress || 10;
  } else if (step === 'proxy') {
    targets.upload = 100;
    targets.metadata = 100;
    targets.scene = 100;
    targets.thumbnail = job.progress || 10;
  } else if (step === 'transcription') {
    targets.upload = 100; targets.metadata = 100; targets.scene = 100; targets.thumbnail = 100;
    targets.audio = job.progress || 10;
  } else if (['vision_caption', 'keyframe_extraction', 'keyframe_upload'].includes(step)) {
    targets.upload = 100; targets.metadata = 100; targets.scene = 100; targets.thumbnail = 100; targets.audio = 100;
    targets.caption = job.progress || 10;
  } else if (step === 'embedding') {
    targets.upload = 100; targets.metadata = 100; targets.scene = 100; targets.thumbnail = 100; targets.audio = 100; targets.caption = 100;
    targets.embedding = job.progress || 10;
  } else if (step === 'persisting_results') {
    targets.upload = 100; targets.metadata = 100; targets.scene = 100; targets.thumbnail = 100; targets.audio = 100; targets.caption = 100; targets.embedding = 100;
    targets.index = job.progress || 10;
  }

  // Handle fallback for unknown steps early in the pipeline
  if (step === 'started' || step === 'fetching_data') {
    targets.upload = job.progress || 5;
  }

  return targets;
};

export default function AIPipelineTimeline() {
  const { activeJobs } = useJobs();
  const totalSizeMB = (activeJobs || []).reduce((sum, j) => sum + (j.file_size || 0), 0) / (1024 * 1024);
  const [smoothStats, setSmoothStats] = useState({
    upload: { percent: 0, count: 0 },
    metadata: { percent: 0, count: 0 },
    scene: { percent: 0, count: 0 },
    thumbnail: { percent: 0, count: 0 },
    audio: { percent: 0, count: 0 },
    caption: { percent: 0, count: 0 },
    embedding: { percent: 0, count: 0 },
    index: { percent: 0, count: 0 },
  });

  const totalJobs = activeJobs ? activeJobs.length : 0;

  useEffect(() => {
    if (totalJobs === 0) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setSmoothStats({
        upload: { percent: 0, count: 0 },
        metadata: { percent: 0, count: 0 },
        scene: { percent: 0, count: 0 },
        thumbnail: { percent: 0, count: 0 },
        audio: { percent: 0, count: 0 },
        caption: { percent: 0, count: 0 },
        embedding: { percent: 0, count: 0 },
        index: { percent: 0, count: 0 },
      });
      return;
    }

    let sums = { upload: 0, metadata: 0, scene: 0, thumbnail: 0, audio: 0, caption: 0, embedding: 0, index: 0 };
    let counts = { upload: 0, metadata: 0, scene: 0, thumbnail: 0, audio: 0, caption: 0, embedding: 0, index: 0 };

    activeJobs.forEach(job => {
      const p = getJobStageProgress(job);
      Object.keys(p).forEach(k => {
        sums[k] += p[k];
        if (p[k] === 100) counts[k]++;
      });
    });

    const targetStats = {};
    Object.keys(sums).forEach(k => {
      targetStats[k] = {
        percent: totalJobs > 0 ? sums[k] / totalJobs : 0,
        count: counts[k]
      };
    });

    const interval = setInterval(() => {
      setSmoothStats(prev => {
        const next = { ...prev };
        Object.keys(targetStats).forEach(k => {
          const current = prev[k].percent;
          const target = targetStats[k].percent;
          let newPercent = current;
          if (current < target) newPercent = Math.min(current + 15, target);
          else if (current > target) newPercent = Math.max(current - 15, target);
          next[k] = { percent: newPercent, count: targetStats[k].count };
        });
        return next;
      });
    }, 50);

    return () => clearInterval(interval);
  }, [activeJobs, totalJobs]);

  return (
    <div className="bg-white dark:bg-[#120F1D] border border-gray-200 dark:border-white/5 rounded-lg p-4 h-full flex flex-col relative overflow-hidden min-h-0 transition-colors shadow-sm dark:shadow-none">
      {/* Header */}
      <div className="flex justify-between items-center border-b border-gray-200 dark:border-white/5 pb-4 mb-6 transition-colors">
        <h3 className="text-gray-900 dark:text-white text-[14px] font-bold transition-colors">AI Processing Pipeline</h3>
      </div>

      {/* Stepper */}
      <div className="flex flex-col relative flex-1 overflow-y-auto no-scrollbar min-h-0 pr-2">
        {PIPELINE_STAGES.map((stage, idx) => {
          const stats = smoothStats[stage.id];
          const isCompleted = stats.percent === 100;
          const isProcessing = stats.percent > 0 && stats.percent < 100;
          const isQueued = stats.percent === 0;
          const isLast = idx === PIPELINE_STAGES.length - 1;

          // Xác định trạng thái của node dot
          let dotClass = "w-5 h-5 rounded-full flex items-center justify-center shrink-0 z-10 border-4 border-white dark:border-[#120F1D] transition-colors ";
          if (isCompleted) dotClass += "bg-[#4ADE80]";
          else if (isProcessing) dotClass += "bg-[#7B5CF5] shadow-[0_0_10px_rgba(123,92,245,0.5)] ring-2 ring-[#7B5CF5]/50";
          else dotClass += "bg-gray-300 dark:bg-gray-600";

          return (
            <div key={stage.id} className={`flex gap-4 relative z-10 group ${isLast ? '' : 'mb-6'}`}>
              <div className="mt-0.5 flex flex-col items-center relative">
                <div className={dotClass}></div>
                {!isLast && (
                  <div className="absolute top-5 -bottom-6 w-[2px] bg-gray-200 dark:bg-white/5 z-0 rounded-full transition-colors"></div>
                )}
              </div>
              
              <div className="flex-1">
                <h4 className={`text-[13px] font-bold transition-colors ${isProcessing ? 'text-gray-900 dark:text-white' : 'text-gray-600 dark:text-gray-300'}`}>{stage.name}</h4>
                <p className="text-gray-500 text-[11px] mt-0.5 transition-colors">{stage.desc}</p>
                
                {/* Thanh Progress nếu đang chạy */}
                {isProcessing && (
                  <div className="mt-3 flex items-center gap-3">
                    <div className="w-full h-[3px] bg-gray-200 dark:bg-[#D9D9D9]/10 rounded-full overflow-hidden transition-colors">
                      <div 
                        className="h-full bg-gradient-to-r from-[#4F8EF7] to-[#7B5CF5] transition-all duration-300"
                        style={{ width: `${stats.percent}%` }}
                      ></div>
                    </div>
                  </div>
                )}
              </div>
              
              <div className="flex flex-col items-end shrink-0 pl-4 w-[120px]">
                {/* Trạng thái Icon & Text */}
                {isCompleted && (
                  <>
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-[#4ADE80] text-[10px] font-medium">Completed</span>
                      <CheckCircle2 className="w-5 h-5 text-[#4ADE80] fill-[#4ADE80]/20" />
                    </div>
                    <span className="text-gray-500 text-[10px] transition-colors">
                      {stats.count} files{totalSizeMB > 0 ? `: ${totalSizeMB.toFixed(2)} MB` : ''}
                    </span>
                  </>
                )}
                
                {isProcessing && (
                  <>
                     <div className="flex items-center gap-2 mb-1">
                      <span className="text-gray-900 dark:text-white text-[12px] font-bold transition-colors">{Math.floor(stats.percent)}%</span>
                      <Loader2 className="w-5 h-5 text-[#7B5CF5] animate-spin" />
                    </div>
                    {/* <span className="text-gray-400 text-[10px]">ETA: 00:00:37</span> */}
                  </>
                )}

                {isQueued && (
                  <>
                     <div className="flex items-center gap-2 mb-1">
                      <span className="text-gray-500 dark:text-gray-500 text-[10px] font-medium transition-colors">Queued</span>
                      <div className="w-5 h-5 bg-gray-100 dark:bg-white/10 rounded-full flex items-center justify-center transition-colors">
                        <Clock className="w-3 h-3 text-gray-500 dark:text-white transition-colors" />
                      </div>
                    </div>
                    <span className="text-gray-400 dark:text-gray-600 text-[10px] transition-colors">Waiting to start</span>
                  </>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
