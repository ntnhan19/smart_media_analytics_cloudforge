import { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import MediaCard from '../components/media/MediaCard';
import { Icon } from '@iconify/react';
import { getAssets } from '../services/api';

export default function Favourites() {
  const { data: assetsData, isLoading } = useQuery({
    queryKey: ['assets'],
    queryFn: () => getAssets(null, 100, 0),
    retry: false,
    refetchOnWindowFocus: false,
  });

  const rawAssets = assetsData?.items || [];

  // For this MVP, we simulate favourites via localStorage
  const getFavouriteIds = () => {
    try {
      return JSON.parse(localStorage.getItem('favouriteIds') || '[]');
    } catch {
      return [];
    }
  };

  const favouriteIds = getFavouriteIds();
  const assets = rawAssets.filter(a => favouriteIds.includes(a.asset_id));

  return (
    <div className="max-w-7xl mx-auto space-y-4 relative min-h-full flex flex-col p-2">
      <div className="flex items-center justify-between mb-6 mt-2">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-sma-purple/10 rounded-xl">
            <Icon icon="lucide:heart" width="24" height="24" className="text-sma-purple" />
          </div>
          <div>
            <h1 className="text-2xl font-bold font-inter text-gray-900 dark:text-white tracking-tight">Favourites</h1>
            <p className="text-sm font-inter text-gray-500 dark:text-gray-400">Your most important media assets</p>
          </div>
        </div>
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
            <div className="w-16 h-16 rounded-full bg-red-50 dark:bg-red-500/10 flex items-center justify-center mb-4">
              <Icon icon="lucide:heart" width="32" height="32" className="text-red-300 dark:text-red-500/50" />
            </div>
            <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-2">No Favourites Yet</h2>
            <p className="text-gray-500 dark:text-gray-400 text-sm mb-6">
              Click the heart icon on any media card to add it to your favourites.
            </p>
            <a href="/app/assets" className="px-6 py-2.5 bg-sma-purple text-white rounded-lg font-medium shadow-sm hover:bg-[#6b4ce6] transition-colors inline-flex items-center gap-2">
              <Icon icon="lucide:layout-grid" width="18" height="18" />
              Go to Library
            </a>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 pb-20">
          {assets.map((asset) => (
            <MediaCard
              key={asset.asset_id}
              {...asset}
              isFavorite={true}
            />
          ))}
        </div>
      )}
    </div>
  );
}
