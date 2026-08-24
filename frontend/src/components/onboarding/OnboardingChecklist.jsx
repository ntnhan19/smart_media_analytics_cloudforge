import { useState, useEffect } from 'react';
import { Icon } from '@iconify/react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { getAssets } from '../../services/api';

export default function OnboardingChecklist() {
  const navigate = useNavigate();
  const [isOpen, setIsOpen] = useState(true);
  const [isDismissed, setIsDismissed] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);

  const { data: assets = [] } = useQuery({
    queryKey: ['assets'],
    queryFn: getAssets,
  });

  useEffect(() => {
    const dismissed = localStorage.getItem('onboardingDismissed');
    if (dismissed === 'true') {
      setIsDismissed(true);
    }
    
    const checkSearched = () => {
      if (localStorage.getItem('hasSearched') === 'true') {
        setHasSearched(true);
      }
    };
    
    checkSearched();
    window.addEventListener('storage', checkSearched);
    window.addEventListener('searchPerformed', () => setHasSearched(true));
    
    return () => {
      window.removeEventListener('storage', checkSearched);
      window.removeEventListener('searchPerformed', () => setHasSearched(true));
    };
  }, []);

  if (isDismissed) return null;

  const steps = [
    {
      id: 'upload',
      title: 'Upload first video',
      description: 'Add media to your library',
      isComplete: assets.length > 0,
      action: () => navigate('/app/upload')
    },
    {
      id: 'process',
      title: 'Wait for AI processing',
      description: 'AI extracts scenes & transcribes',
      isComplete: assets.some(a => a.status === 'completed'),
      action: () => navigate('/app/assets')
    },
    {
      id: 'search',
      title: 'Try semantic search',
      description: 'Search using natural language',
      isComplete: hasSearched,
      action: () => navigate('/app/search')
    },
    {
      id: 'favorite',
      title: 'Favorite an asset',
      description: 'Save your best clips',
      isComplete: assets.some(a => a.is_favorite === true),
      action: () => navigate('/app/assets')
    }
  ];

  const completedCount = steps.filter(s => s.isComplete).length;
  const progress = (completedCount / steps.length) * 100;
  
  // If all completed, auto-dismiss after a delay or let user dismiss
  const isAllComplete = completedCount === steps.length;

  const handleDismiss = () => {
    localStorage.setItem('onboardingDismissed', 'true');
    setIsDismissed(true);
  };

  return (
    <div className="fixed bottom-6 right-6 z-40 flex flex-col items-end">
      {isOpen && (
        <div className="bg-white dark:bg-[#16132A] rounded-xl shadow-2xl border border-gray-200 dark:border-gray-700 w-80 mb-4 overflow-hidden animate-fade-in-up">
          <div className="p-4 border-b border-gray-100 dark:border-gray-800 bg-gray-50/50 dark:bg-black/20 flex items-center justify-between">
            <h3 className="font-semibold text-gray-800 dark:text-white text-sm flex items-center gap-2">
              <Icon icon="lucide:rocket" className="text-sma-purple" />
              Getting Started
            </h3>
            <button 
              onClick={() => setIsOpen(false)}
              className="p-1 hover:bg-gray-200 dark:hover:bg-gray-700 rounded text-gray-500 transition-colors"
            >
              <Icon icon="lucide:minus" width="16" />
            </button>
          </div>
          
          <div className="p-4">
            <div className="mb-4">
              <div className="flex justify-between text-xs text-gray-500 dark:text-gray-400 mb-1.5 font-medium">
                <span>{completedCount} of {steps.length} completed</span>
                <span>{Math.round(progress)}%</span>
              </div>
              <div className="h-1.5 w-full bg-gray-100 dark:bg-gray-800 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-sma-purple transition-all duration-500 ease-out"
                  style={{ width: `${progress}%` }}
                />
              </div>
            </div>

            <div className="space-y-3">
              {steps.map((step, index) => (
                <div 
                  key={step.id} 
                  className={`flex gap-3 items-start group ${step.isComplete ? 'opacity-60' : 'cursor-pointer'}`}
                  onClick={() => !step.isComplete && step.action()}
                >
                  <div className={`mt-0.5 w-5 h-5 shrink-0 rounded-full flex items-center justify-center border transition-colors ${
                    step.isComplete 
                      ? 'bg-green-500 border-green-500 text-white' 
                      : 'border-gray-300 dark:border-gray-600 group-hover:border-sma-purple'
                  }`}>
                    {step.isComplete ? (
                      <Icon icon="lucide:check" width="12" />
                    ) : (
                      <span className="text-[10px] font-medium text-gray-500 dark:text-gray-400">{index + 1}</span>
                    )}
                  </div>
                  <div>
                    <h4 className={`text-sm font-medium transition-colors ${step.isComplete ? 'line-through text-gray-500' : 'text-gray-800 dark:text-gray-200 group-hover:text-sma-purple'}`}>
                      {step.title}
                    </h4>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      {step.description}
                    </p>
                  </div>
                </div>
              ))}
            </div>
            
            {isAllComplete && (
              <div className="mt-5 pt-4 border-t border-gray-100 dark:border-gray-800 text-center">
                <p className="text-sm font-medium text-green-600 dark:text-green-400 mb-3">
                  🎉 You're all set!
                </p>
                <button
                  onClick={handleDismiss}
                  className="w-full py-2 bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 text-gray-800 dark:text-white text-xs font-medium rounded-lg transition-colors"
                >
                  Dismiss Checklist
                </button>
              </div>
            )}
          </div>
        </div>
      )}
      
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className="bg-white dark:bg-[#16132A] text-gray-800 dark:text-white shadow-xl border border-gray-200 dark:border-gray-700 rounded-full py-2.5 px-4 font-medium text-sm hover:shadow-2xl transition-all hover:-translate-y-1 flex items-center gap-2"
        >
          <Icon icon="lucide:list-todo" className="text-sma-purple" />
          <span>Setup Guide</span>
          <div className="w-5 h-5 rounded-full bg-sma-purple text-white text-[10px] flex items-center justify-center font-bold">
            {steps.length - completedCount}
          </div>
        </button>
      )}
    </div>
  );
}
