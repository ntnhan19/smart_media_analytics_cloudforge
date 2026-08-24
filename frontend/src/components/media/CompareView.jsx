import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getAssetStream, getAsset } from '../../services/api';
import VideoPlayer from './VideoPlayer';
import { Icon } from '@iconify/react';

const CompareVideoItem = ({ assetId }) => {
  const { data: streamData, isLoading: isLoadingStream } = useQuery({
    queryKey: ['asset-stream', assetId],
    queryFn: () => getAssetStream(assetId),
  });

  const { data: assetData, isLoading: isLoadingAsset } = useQuery({
    queryKey: ['asset', assetId],
    queryFn: () => getAsset(assetId),
  });

  if (isLoadingStream || isLoadingAsset) {
    return (
      <div className="flex-1 min-h-[300px] flex items-center justify-center bg-gray-100 dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800">
        <Icon icon="lucide:loader-2" className="animate-spin w-8 h-8 text-sma-purple" />
      </div>
    );
  }

  if (!streamData?.stream_url) {
    return (
      <div className="flex-1 min-h-[300px] flex items-center justify-center bg-gray-100 dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 text-gray-500">
        Failed to load media
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-2 h-full">
      <div className="flex-1 min-h-[300px] relative rounded-lg overflow-hidden bg-black shadow-lg border border-gray-200 dark:border-gray-700">
        <VideoPlayer 
          src={streamData.stream_url} 
          mediaType={assetData?.media_type || 'video'} 
          duration={assetData?.duration || 0}
        />
      </div>
      <div className="bg-white dark:bg-[#16132A] p-3 rounded-lg border border-gray-200 dark:border-[#2D2844] shadow-sm">
        <h3 className="font-semibold text-sm truncate" title={assetData?.file_name}>
          {assetData?.file_name || 'Loading...'}
        </h3>
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
          {assetData?.media_type?.toUpperCase()} {assetData?.resolution && `• ${assetData.resolution}`}
        </p>
      </div>
    </div>
  );
};

export default function CompareView({ assetIds, onClose }) {
  // Determine layout based on count
  const count = assetIds.length;
  let gridCols = "grid-cols-1";
  if (count === 2) gridCols = "grid-cols-2";
  else if (count === 3) gridCols = "grid-cols-3";
  else if (count >= 4) gridCols = "grid-cols-2 lg:grid-cols-2"; // 2x2 grid

  return (
    <div className="fixed inset-0 z-50 bg-gray-100 dark:bg-[#0F0D15] flex flex-col overflow-hidden">
      {/* Header */}
      <div className="h-16 px-6 border-b border-gray-200 dark:border-gray-800 bg-white dark:bg-[#16132A] flex items-center justify-between shrink-0">
        <div className="flex items-center gap-3">
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white"
          >
            <Icon icon="lucide:arrow-left" width="20" />
          </button>
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
            <Icon icon="lucide:split-square-horizontal" className="text-sma-purple" />
            Compare Mode
          </h2>
          <span className="text-sm text-gray-500 bg-gray-100 dark:bg-gray-800 px-2 py-1 rounded-md">
            {count} assets
          </span>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto p-4 md:p-6">
        <div className={`grid ${gridCols} gap-6 w-full max-w-7xl mx-auto h-full auto-rows-[minmax(400px,_1fr)]`}>
          {assetIds.slice(0, 4).map(id => (
            <CompareVideoItem key={id} assetId={id} />
          ))}
        </div>
        {count > 4 && (
          <div className="text-center mt-6 text-sm text-gray-500 pb-4">
            Showing first 4 assets only.
          </div>
        )}
      </div>
    </div>
  );
}
