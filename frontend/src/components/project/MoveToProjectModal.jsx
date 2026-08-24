import { useState } from 'react';
import { Icon } from '@iconify/react';
import { useQuery } from '@tanstack/react-query';
import { projectsApi } from '../../api/projects';

export default function MoveToProjectModal({ isOpen, onClose, onSubmit, isLoading, selectedCount = 1 }) {
  const [selectedProject, setSelectedProject] = useState('');

  const { data: projects, isLoading: isLoadingProjects } = useQuery({
    queryKey: ['projects'],
    queryFn: projectsApi.list,
    enabled: isOpen
  });

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm transition-opacity">
      <div className="bg-white dark:bg-[#1A1630] rounded-2xl w-full max-w-md shadow-xl overflow-hidden border border-gray-100 dark:border-[#2D2844]">
        <div className="p-6">
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-lg font-bold text-gray-900 dark:text-white flex items-center gap-2">
              <Icon icon="lucide:folder-input" className="text-sma-purple" width="24" />
              Move to Project
            </h3>
            <button 
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 transition-colors"
            >
              <Icon icon="lucide:x" width="20" />
            </button>
          </div>
          
          <div className="space-y-4">
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Select a project to move {selectedCount} {selectedCount === 1 ? 'asset' : 'assets'} into.
            </p>
            
            {isLoadingProjects ? (
              <div className="flex justify-center py-4">
                <Icon icon="lucide:loader-2" className="animate-spin text-sma-purple w-6 h-6" />
              </div>
            ) : (
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">Project</label>
                <select
                  value={selectedProject}
                  onChange={(e) => setSelectedProject(e.target.value)}
                  className="w-full px-4 py-2.5 bg-gray-50 dark:bg-[#2D2844] border border-gray-200 dark:border-transparent rounded-xl focus:outline-none focus:ring-2 focus:ring-sma-purple/50 text-gray-900 dark:text-white"
                >
                  <option value="">Select a project...</option>
                  <option value="none">-- No Project (Remove from project) --</option>
                  {projects?.map(p => (
                    <option key={p.id} value={p.id}>{p.name}</option>
                  ))}
                </select>
              </div>
            )}
          </div>

          <div className="mt-8 flex gap-3 justify-end">
            <button
              onClick={onClose}
              className="px-4 py-2 rounded-xl text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-[#2D2844] transition-colors font-medium"
            >
              Cancel
            </button>
            <button
              onClick={() => {
                if (selectedProject) onSubmit(selectedProject === 'none' ? null : selectedProject);
              }}
              disabled={!selectedProject || isLoading}
              className="px-5 py-2 rounded-xl bg-sma-purple text-white hover:bg-[#6044DD] transition-colors font-medium shadow-sm disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {isLoading && <Icon icon="lucide:loader-2" className="animate-spin" />}
              Move
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
