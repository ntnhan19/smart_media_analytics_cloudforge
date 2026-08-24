import { UploadCloud, X, Play } from 'lucide-react';
import { useState, useRef } from 'react';
import { useQuery } from '@tanstack/react-query';
import { projectsApi } from '../../api/projects';

export default function UploadArea({ onStartIngest, isUploading }) {
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [selectedProjectId, setSelectedProjectId] = useState('');
  const fileInputRef = useRef(null);

  const { data: projectsData } = useQuery({
    queryKey: ['projects'],
    queryFn: projectsApi.list,
  });

  const handleFileChange = (e) => {
    if (e.target.files) {
      setSelectedFiles(Array.from(e.target.files));
    }
  };

  const handleClearAll = () => setSelectedFiles([]);

  const handleRemoveFile = (indexToRemove) => {
    setSelectedFiles(prev => prev.filter((_, i) => i !== indexToRemove));
  };

  const handleStartIngest = () => {
    onStartIngest(selectedFiles, selectedProjectId || null);
    setSelectedFiles([]);
  };

  const totalSize = selectedFiles.reduce((acc, file) => acc + file.size, 0);
  const formattedSize = (totalSize / (1024 * 1024)).toFixed(1) + 'MB';

  return (
    <div className="flex flex-col gap-3 h-full overflow-hidden">
      {/* Box Upload */}
      <div className="border border-dashed border-[#4F8EF7]/50 rounded-lg bg-gray-50 dark:bg-[#120F1D] flex flex-col items-center justify-center p-4 relative transition-colors hover:bg-gray-100 dark:hover:bg-[#4F8EF7]/5 shrink-0">
        <UploadCloud className="w-8 h-8 text-[#7B5CF5] mb-2 transition-colors" />
        <p className="text-gray-900 dark:text-white text-[13px] mb-3 text-center transition-colors">Drag & Drop files and folders here</p>
        <button 
          onClick={() => fileInputRef.current?.click()}
          className="bg-[#7B5CF5] hover:bg-[#6A4BE4] text-white px-6 py-2 rounded text-[12px] font-bold transition-colors"
        >
          Browse Files
        </button>
        <input 
          type="file" 
          multiple 
          accept="video/*" 
          className="hidden" 
          ref={fileInputRef} 
          onChange={handleFileChange} 
        />
        <p className="text-gray-500 dark:text-gray-500 text-[11px] mt-3 transition-colors">Support: MP4, MOV and more</p>
      </div>

      {/* Selected Assets */}
      <div className="border border-gray-200 dark:border-white/5 rounded-lg bg-white dark:bg-[#120F1D] flex flex-col flex-1 min-h-0 overflow-hidden transition-colors shadow-sm dark:shadow-none">
        <div className="p-4 border-b border-gray-200 dark:border-white/5 flex justify-between items-center transition-colors">
          <h3 className="text-gray-900 dark:text-white text-[13px] font-bold transition-colors">Selected Assets</h3>
          <button onClick={handleClearAll} className="text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white text-[11px] transition-colors">Clear All</button>
        </div>

        <div className="flex-1 overflow-y-auto no-scrollbar p-4 space-y-3 min-h-0">
          {selectedFiles.map((f, i) => (
            <div key={i} className="flex items-center gap-3">
              <div className="w-4 h-4 rounded border border-gray-300 dark:border-white/20 bg-[#7B5CF5] flex items-center justify-center shrink-0 transition-colors">
                <svg viewBox="0 0 14 14" fill="none" className="w-3 h-3 text-white"><path d="M11.6666 3.5L5.24992 9.91667L2.33325 7" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/></svg>
              </div>
              <div className="w-[80px] h-[45px] bg-gray-100 dark:bg-[#16132A] rounded overflow-hidden shrink-0 border border-gray-200 dark:border-white/10 relative transition-colors">
                {f.type.startsWith('video/') ? (
                  <video 
                    src={URL.createObjectURL(f)} 
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <div className="absolute inset-0 bg-gradient-to-tr from-blue-500/20 to-purple-500/20"></div>
                )}
              </div>
              <div className="flex flex-col flex-1 min-w-0">
                <span className="text-gray-900 dark:text-white text-[11px] font-medium truncate transition-colors">{f.name}</span>
                <span className="text-gray-500 dark:text-gray-400 text-[10px] truncate transition-colors">{(f.size / (1024*1024)).toFixed(1)}MB</span>
              </div>
              <div className="bg-gray-100 dark:bg-[#16132A] text-gray-600 dark:text-gray-300 text-[9px] px-2 py-0.5 rounded border border-gray-200 dark:border-white/10 shrink-0 transition-colors">
                {f.type || 'MP4'}
              </div>
              <button onClick={() => handleRemoveFile(i)} className="text-gray-400 dark:text-gray-500 hover:text-gray-900 dark:hover:text-white p-1 shrink-0 transition-colors">
                <X className="w-4 h-4" />
              </button>
            </div>
          ))}
        </div>

        {/* Start Ingest Footer */}
        <div className="p-4 border-t border-gray-200 dark:border-white/5 flex flex-col sm:flex-row sm:justify-between items-start sm:items-center gap-3 bg-gray-50 dark:bg-[#16132A]/50 transition-colors">
          <div className="flex flex-col gap-1 w-full sm:w-auto">
            <span className="text-gray-500 dark:text-gray-400 text-[11px] transition-colors">Total {selectedFiles.length} files: {formattedSize}</span>
            <select
              value={selectedProjectId}
              onChange={(e) => setSelectedProjectId(e.target.value)}
              className="text-[11px] w-full sm:w-48 bg-white dark:bg-[#2D2844] border border-gray-200 dark:border-transparent rounded py-1 px-2 focus:outline-none focus:ring-1 focus:ring-sma-purple/50 text-gray-900 dark:text-white"
            >
              <option value="">-- Assign to Project (Optional) --</option>
              {projectsData?.map(p => (
                <option key={p.id} value={p.id}>{p.name}</option>
              ))}
            </select>
          </div>
          <button 
            onClick={handleStartIngest}
            disabled={isUploading || selectedFiles.length === 0}
            className="w-full sm:w-auto justify-center bg-[#7B5CF5] hover:bg-[#6A4BE4] disabled:bg-gray-400 dark:disabled:bg-gray-600 disabled:cursor-not-allowed text-white px-6 py-2 rounded text-[12px] font-bold flex items-center gap-2 transition-colors shrink-0"
          >
            {isUploading ? <span className="animate-spin text-[10px] mr-1">⌛</span> : <Play className="w-3 h-3" />}
            Start Ingest
          </button>
        </div>
      </div>
    </div>
  );
}
