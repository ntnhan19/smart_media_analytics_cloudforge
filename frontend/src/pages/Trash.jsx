import { useState, useEffect } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import MediaCard from '../components/media/MediaCard';
import { Icon } from '@iconify/react';
import { getAssets, deleteAsset } from '../services/api';

export default function Trash() {
  const queryClient = useQueryClient();
  const [toast, setToast] = useState(null);
  const [isEmptying, setIsEmptying] = useState(false);

  const { data: assetsData, isLoading } = useQuery({
    queryKey: ['assets'],
    queryFn: () => getAssets(null, 100, 0),
    retry: false,
    refetchOnWindowFocus: false,
  });

  const rawAssets = assetsData?.items || [];

  const getTrashedIds = () => {
    try {
      return JSON.parse(localStorage.getItem('trashedIds') || '[]');
    } catch {
      return [];
    }
  };

  const trashedIds = getTrashedIds();
  const assets = rawAssets.filter(a => trashedIds.includes(a.asset_id));

  const showToast = (message, type = 'success') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3000);
  };

  const handleRestore = (id) => {
    const newTrashed = trashedIds.filter(tid => tid !== id);
    localStorage.setItem('trashedIds', JSON.stringify(newTrashed));
    queryClient.invalidateQueries({ queryKey: ['assets'] });
    showToast('Video restored successfully');
  };

  const handleEmptyTrash = async () => {
    if (!window.confirm(`Are you sure you want to permanently delete ${assets.length} items? This cannot be undone.`)) return;
    
    setIsEmptying(true);
    try {
      // Physically delete from backend
      await Promise.all(assets.map(a => deleteAsset(a.asset_id)));
      localStorage.setItem('trashedIds', '[]');
      queryClient.invalidateQueries({ queryKey: ['assets'] });
      showToast('Trash emptied completely', 'success');
    } catch (error) {
      console.error(error);
      showToast('Failed to empty some items', 'error');
    } finally {
      setIsEmptying(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto space-y-4 relative min-h-full flex flex-col p-2">
      {toast && (
        <div className={`fixed top-[20px] right-[20px] z-50 px-4 py-2 rounded shadow-lg text-white font-inter text-sm animate-fade-in-down ${toast.type === 'success' ? 'bg-green-600' : 'bg-red-600'}`}>
          {toast.message}
        </div>
      )}

      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6 mt-2">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-gray-100 dark:bg-gray-800 rounded-xl">
            <Icon icon="lucide:trash-2" width="24" height="24" className="text-gray-500 dark:text-gray-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold font-inter text-gray-900 dark:text-white tracking-tight">Trash</h1>
            <p className="text-sm font-inter text-gray-500 dark:text-gray-400">Items here will be deleted permanently after 30 days</p>
          </div>
        </div>
        
        {assets.length > 0 && (
          <button
            onClick={handleEmptyTrash}
            disabled={isEmptying}
            className="flex items-center justify-center gap-2 px-4 py-2 bg-white dark:bg-[#1a1b26] border border-red-200 dark:border-red-500/30 text-red-600 dark:text-red-400 rounded-lg hover:bg-red-50 dark:hover:bg-red-500/10 transition-colors font-medium text-sm disabled:opacity-50"
          >
            <Icon icon="lucide:alert-triangle" width="16" height="16" />
            {isEmptying ? 'Emptying...' : 'Empty Trash'}
          </button>
        )}
      </div>

      {isLoading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {[1, 2, 3, 4].map(n => (
            <div key={n} className="animate-pulse bg-gray-200 dark:bg-[#1a1b26] rounded-2xl aspect-video" />
          ))}
        </div>
      ) : assets.length === 0 ? (
        <div className="flex-1 flex flex-col items-center justify-center pb-12 w-full">
          <div className="w-full max-w-[600px] mx-auto text-center p-10 bg-white dark:bg-[#1a1b26] border border-gray-100 dark:border-white/5 shadow-sm rounded-2xl flex flex-col items-center">
            <div className="w-16 h-16 rounded-full bg-gray-50 dark:bg-gray-800 flex items-center justify-center mb-4">
              <Icon icon="lucide:trash" width="32" height="32" className="text-gray-300 dark:text-gray-600" />
            </div>
            <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-2">Trash is empty</h2>
            <p className="text-gray-500 dark:text-gray-400 text-sm mb-6">
              No items have been deleted recently.
            </p>
            <a href="/app/assets" className="px-6 py-2.5 bg-gray-100 hover:bg-gray-200 dark:bg-white/10 dark:hover:bg-white/20 text-gray-700 dark:text-white rounded-lg font-medium transition-colors inline-flex items-center gap-2">
              <Icon icon="lucide:layout-grid" width="18" height="18" />
              View Library
            </a>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 pb-20 opacity-75">
          {assets.map((asset) => (
            <div key={asset.asset_id} className="relative group">
              <MediaCard {...asset} />
              <div className="absolute inset-0 bg-white/50 dark:bg-black/50 backdrop-blur-[2px] rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                <button
                  onClick={() => handleRestore(asset.asset_id)}
                  className="px-4 py-2 bg-sma-purple text-white rounded-lg font-medium shadow-lg hover:scale-105 transition-transform flex items-center gap-2"
                >
                  <Icon icon="lucide:rotate-ccw" width="16" height="16" /> Restore
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
