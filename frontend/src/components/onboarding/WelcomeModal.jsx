import { useState, useEffect } from 'react';
import { X, Play, Search, Zap, ChevronRight, Wand2 } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export default function WelcomeModal({ isOpen, onClose }) {
  const [step, setStep] = useState(1);
  const navigate = useNavigate();

  // If closed, reset step
  useEffect(() => {
    if (!isOpen) setStep(1);
  }, [isOpen]);

  if (!isOpen) return null;

  const handleNext = () => {
    if (step < 3) setStep(step + 1);
    else {
      onClose();
      // Wait for modal to close before navigation to avoid jarring transition
      setTimeout(() => navigate('/app?upload=true'), 300);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-gray-900/40 dark:bg-black/60 backdrop-blur-sm transition-opacity"
        onClick={onClose}
      />

      {/* Modal Container */}
      <div className="relative bg-white dark:bg-[#16132a] w-full max-w-lg rounded-3xl shadow-2xl overflow-hidden border border-gray-100 dark:border-white/10 flex flex-col transform transition-all animate-fade-in-up">
        
        {/* Close Button */}
        <button 
          onClick={onClose}
          className="absolute top-4 right-4 z-10 p-2 rounded-full bg-black/5 hover:bg-black/10 dark:bg-white/5 dark:hover:bg-white/10 text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Content Area */}
        <div className="p-8 pb-6 flex-1 flex flex-col items-center text-center">
          
          {/* Step Indicators */}
          <div className="flex gap-2 mb-8">
            {[1, 2, 3].map((i) => (
              <div 
                key={i} 
                className={`h-1.5 rounded-full transition-all duration-300 ${step === i ? 'w-8 bg-sma-purple' : step > i ? 'w-4 bg-sma-purple/40' : 'w-4 bg-gray-200 dark:bg-white/10'}`}
              />
            ))}
          </div>

          {/* Dynamic Content based on step */}
          <div className="w-full relative min-h-[200px] flex flex-col items-center justify-center">
            {step === 1 && (
              <div className="animate-fade-in flex flex-col items-center">
                <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-indigo-100 to-purple-100 dark:from-indigo-500/20 dark:to-purple-500/20 flex items-center justify-center mb-6 shadow-inner">
                  <Play className="w-10 h-10 text-sma-purple" fill="currentColor" />
                </div>
                <h3 className="text-2xl font-bold text-gray-900 dark:text-white mb-3">Welcome to Smart Media Analytics</h3>
                <p className="text-gray-500 dark:text-gray-400 text-sm leading-relaxed max-w-[280px]">
                  Your intelligent media library is ready. Let's transform your unstructured video into searchable data.
                </p>
              </div>
            )}

            {step === 2 && (
              <div className="animate-fade-in flex flex-col items-center">
                <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-blue-100 to-indigo-100 dark:from-blue-500/20 dark:to-indigo-500/20 flex items-center justify-center mb-6 shadow-inner relative">
                  <Wand2 className="w-10 h-10 text-blue-500" />
                  <div className="absolute -top-2 -right-2 bg-white dark:bg-[#16132a] rounded-full p-1 shadow-sm">
                    <Zap className="w-4 h-4 text-amber-500" fill="currentColor" />
                  </div>
                </div>
                <h3 className="text-2xl font-bold text-gray-900 dark:text-white mb-3">Powered by Gemini AI</h3>
                <p className="text-gray-500 dark:text-gray-400 text-sm leading-relaxed max-w-[280px]">
                  Every video you upload is automatically transcribed, analyzed, and tagged using advanced AI models.
                </p>
              </div>
            )}

            {step === 3 && (
              <div className="animate-fade-in flex flex-col items-center">
                <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-emerald-100 to-teal-100 dark:from-emerald-500/20 dark:to-teal-500/20 flex items-center justify-center mb-6 shadow-inner">
                  <Search className="w-10 h-10 text-emerald-500" strokeWidth={2.5} />
                </div>
                <h3 className="text-2xl font-bold text-gray-900 dark:text-white mb-3">Semantic Search</h3>
                <p className="text-gray-500 dark:text-gray-400 text-sm leading-relaxed max-w-[280px]">
                  Don't just search for titles. Search for moments, spoken words, or visual context instantly.
                </p>
              </div>
            )}
          </div>

        </div>

        {/* Footer Actions */}
        <div className="p-6 bg-gray-50 dark:bg-[#110f20] border-t border-gray-100 dark:border-white/5 flex items-center justify-between">
          <button 
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white transition-colors"
          >
            Skip tour
          </button>
          
          <button 
            onClick={handleNext}
            className="flex items-center gap-2 px-6 py-3 rounded-xl bg-gradient-to-r from-sma-purple to-indigo-600 hover:from-purple-600 hover:to-indigo-700 text-white font-medium shadow-lg shadow-sma-purple/20 transition-all hover:scale-105 active:scale-95"
          >
            {step < 3 ? (
              <>Continue <ChevronRight className="w-4 h-4" /></>
            ) : (
              <>Start Uploading <Zap className="w-4 h-4" /></>
            )}
          </button>
        </div>
        
      </div>
    </div>
  );
}
