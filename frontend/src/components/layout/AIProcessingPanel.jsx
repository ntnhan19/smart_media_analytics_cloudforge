import { useState, useEffect } from 'react';
import PropTypes from 'prop-types';

const MOCK_STAGES = [
  { id: 'extracting', name: 'EXTRACTING SCENES' },
  { id: 'transcribing', name: 'TRANSCRIBING AUDIO' },
  { id: 'embedding', name: 'GENERATING EMBEDDING' },
  { id: 'captioning', name: 'GENERATING CAPTION (LlaVA)' }
];

export default function AIProcessingPanel({ jobId }) {
  const [status, setStatus] = useState('connected');
  const [progress, setProgress] = useState({
    overall: 0,
    stages: MOCK_STAGES.map(s => ({ ...s, progress: 0, status: 'pending' })),
  });

  useEffect(() => {
    if (!jobId) return;

    setStatus('in_progress');
    let currentStageIndex = 0;
    
    const interval = setInterval(() => {
      setProgress(prev => {
        if (currentStageIndex >= MOCK_STAGES.length) {
          clearInterval(interval);
          setStatus('completed');
          return { ...prev, overall: 100 };
        }

        const currentStage = prev.stages[currentStageIndex];
        let nextStageProgress = currentStage.progress + 10;
        
        const newStages = [...prev.stages];
        
        if (nextStageProgress >= 100) {
          newStages[currentStageIndex] = { ...currentStage, progress: 100, status: 'completed' };
          currentStageIndex++;
        } else {
          newStages[currentStageIndex] = { ...currentStage, progress: nextStageProgress, status: 'in_progress' };
        }

        const overall = Math.floor(newStages.reduce((acc, curr) => acc + curr.progress, 0) / MOCK_STAGES.length);

        return {
          ...prev,
          overall,
          stages: newStages
        };
      });
    }, 500);

    return () => clearInterval(interval);
  }, [jobId]);

  if (!jobId) return null;

  return (
    <div className="w-[268px] bg-[#7B5CF5]/20 border border-[#4F8EF7] rounded-[6px] flex flex-col p-[12px] shrink-0 mb-4">
      <div className="flex items-center justify-between mb-[16px]">
        <h2 className="font-inter font-normal text-[12px] leading-[15px] text-[#7B5CF5]">
          SMA - AI PROCESSING
        </h2>
        <div className="flex items-center gap-[4px]">
          <div className="w-[7.7px] h-[7.7px] bg-[#4ADE80] rounded-full"></div>
          <span className="font-inter font-normal text-[10px] leading-[12px] text-[#4ADE80]">
            active
          </span>
        </div>
      </div>

      <div className="flex flex-col space-y-[12px]">
        {progress.stages.map((stage) => (
          <div key={stage.id} className="space-y-[6px]">
            <div className="flex justify-between items-center text-white">
              <span className="font-inter font-normal text-[10px] sm:text-[11px] leading-[13px]">
                {stage.name}
              </span>
              <span className="font-inter font-normal text-[11px] leading-[13px]">
                {stage.progress}%
              </span>
            </div>
            <div className="w-full h-[5px] bg-[#D9D9D9] rounded-[6px] overflow-hidden">
              <div 
                className="h-full transition-all duration-300 bg-[#7B5CF5]"
                style={{ width: `${stage.progress}%` }}
              />
            </div>
          </div>
        ))}
        
        {/* Overall Progress */}
        <div className="space-y-[6px] pt-[4px]">
          <div className="flex justify-between items-center text-white">
            <span className="font-inter font-normal text-[10px] sm:text-[11px] leading-[13px]">
              OVERALL PROGRESS
            </span>
            <span className="font-inter font-normal text-[11px] leading-[13px]">
              {progress.overall}%
            </span>
          </div>
          <div className="w-full h-[5px] bg-[#D9D9D9] rounded-[6px] overflow-hidden">
            <div 
              className="h-full transition-all duration-300 bg-[#4ADE80]"
              style={{ width: `${progress.overall}%` }}
            />
          </div>
        </div>
      </div>
    </div>
  );
}

AIProcessingPanel.propTypes = {
  jobId: PropTypes.string,
};

