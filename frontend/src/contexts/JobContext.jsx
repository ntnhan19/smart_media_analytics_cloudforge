import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import PropTypes from 'prop-types';
import { useToast } from './ToastContext';

const JobContext = createContext();

export const JobProvider = ({ children }) => {
  const { showToast } = useToast();
  const [activeJobs, setActiveJobs] = useState(() => {
    try {
      const stored = localStorage.getItem('active_jobs');
      return stored ? JSON.parse(stored) : [];
    } catch (e) {
      console.error('Failed to parse active_jobs from localStorage', e);
      return [];
    }
  });

  // Sync to localStorage whenever activeJobs changes
  useEffect(() => {
    localStorage.setItem('active_jobs', JSON.stringify(activeJobs));
  }, [activeJobs]);

  const addJob = useCallback((job) => {
    setActiveJobs(prev => {
      // Clear completed jobs when a new job starts
      const nonCompleted = prev.filter(j => j.status !== 'completed');

      // Kiểm tra xem job đã tồn tại chưa
      const exists = nonCompleted.find(j => j.job_id === job.job_id);
      if (exists) return nonCompleted;

      return [...nonCompleted, {
        job_id: job.job_id,
        asset_id: job.asset_id || null,
        file_name: job.file_name || null,
        file_size: job.file_size || null,
        duration: job.duration || null,
        resolution: job.resolution || null,
        status: job.status || 'queued',
        progress: job.progress || 0,
        current_step: job.current_step || null,
        error_message: job.error_message || null,
      }];
    });
  }, []);

  const updateJob = useCallback((jobUpdate) => {
    setActiveJobs(prev => {
      const job = prev.find(j => j.job_id === jobUpdate.job_id);
      if (job && job.status !== 'completed' && jobUpdate.status === 'completed') {
        setTimeout(() => showToast(`AI Processing completed for ${job.file_name || 'video'}`, 'success', 5000), 0);
      } else if (job && job.status !== 'failed' && jobUpdate.status === 'failed') {
        setTimeout(() => showToast(`AI Processing failed for ${job.file_name || 'video'}`, 'error', 5000), 0);
      }

      let updated = false;
      const newJobs = prev.map(j => {
        if (j.job_id === jobUpdate.job_id) {
          updated = true;
          return { ...j, ...jobUpdate };
        }
        return j;
      });
      return updated ? newJobs : prev;
    });
  }, [showToast]);

  const removeJob = useCallback((jobId) => {
    setActiveJobs(prev => prev.filter(j => j.job_id !== jobId));
  }, []);

  const clearCompletedJobs = useCallback(() => {
    setActiveJobs(prev => prev.filter(j => j.status !== 'completed'));
  }, []);

  const clearAllFinishedJobs = useCallback(() => {
    setActiveJobs(prev => prev.filter(j => j.status !== 'completed' && j.status !== 'failed'));
  }, []);

  const clearAllJobs = useCallback(() => {
    setActiveJobs([]);
  }, []);

  return (
    <JobContext.Provider value={{ activeJobs, addJob, updateJob, removeJob, clearCompletedJobs, clearAllFinishedJobs, clearAllJobs }}>
      {children}
    </JobContext.Provider>
  );
};

JobProvider.propTypes = {
  children: PropTypes.node.isRequired,
};

// eslint-disable-next-line react-refresh/only-export-components -- useJobs hook is tightly coupled with JobProvider context
export const useJobs = () => {
  const context = useContext(JobContext);
  if (!context) {
    throw new Error('useJobs must be used within a JobProvider');
  }
  return context;
};
