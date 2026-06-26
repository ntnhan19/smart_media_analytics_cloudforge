import { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import MediaCard from '../components/media/MediaCard';
import FilterBar from '../components/media/FilterBar';
import Pagination from '../components/media/Pagination';
import { Icon } from '@iconify/react';

import { getAssets } from '../services/api';

export default function Dashboard() {
  const [currentPage, setCurrentPage] = useState(1);
  const [mediaFilter, setMediaFilter] = useState('All');
  const [sortOrder, setSortOrder] = useState('Newest');

  const itemsPerPage = 8;

  const { data: assets, isLoading, error } = useQuery({
    queryKey: ['assets'],
    queryFn: ({ signal }) => getAssets(signal),
  });

  // Client-side filtering and sorting
  const filteredAndSortedAssets = useMemo(() => {
    if (!assets) return [];

    let result = [...assets];

    // Filter by Media Type
    if (mediaFilter !== 'All') {
      result = result.filter(asset => asset.media_type.toLowerCase() === mediaFilter.toLowerCase());
    }

    // Sort
    result.sort((a, b) => {
      const dateA = new Date(a.created_at).getTime();
      const dateB = new Date(b.created_at).getTime();
      return sortOrder === 'Newest' ? dateB - dateA : dateA - dateB;
    });

    return result;
  }, [assets, mediaFilter, sortOrder]);

  // Client-side pagination
  const totalPages = Math.ceil(filteredAndSortedAssets.length / itemsPerPage);
  const paginatedAssets = filteredAndSortedAssets.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  );

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Top Header removed as per design */}

      {/* Stats Cards - Only shown in Empty State */}
      {(!assets || assets.length === 0) && !isLoading && !error && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-2 mt-1">
          <div className="bg-gray-900 p-2 rounded-xl border border-gray-800 w-60 h-30">
            <h3 className="text-gray-400 font-medium">Total Assets</h3>
            <p className="text-3xl font-bold mt-4">0</p>
          </div>
          <div className="bg-gray-900 p-2 rounded-xl border border-gray-800 w-60 h-30">
            <h3 className="text-gray-400 font-medium">Storage Used</h3>
            <p className="text-3xl font-bold mt-4 ">0 MB</p>
          </div>
          <div className="bg-gray-900 p-2 rounded-xl border border-gray-800 w-60 h-30">
            <h3 className="text-gray-400 font-medium">Recent Searches</h3>
            <p className="text-3xl font-bold mt-4">0</p>
          </div>
        </div>
      )}

      {/* Loading state */}
      {isLoading && (
        <div className="flex justify-center items-center py-20">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-sma-purple"></div>
        </div>
      )}

      {/* Error state */}
      {error && (
        <div className="bg-red-900/20 border border-red-500/50 text-red-400 p-6 rounded-xl text-center">
          Failed to load assets. Please try again later.
        </div>
      )}

      {/* Main Content Area */}
      {!isLoading && !error && (
        <div className="mt-6">
          {assets && assets.length > 0 ? (
            <div className="relative flex flex-col space-y-2 min-h-[650px] pb-16">
              {/* Filter Bar (Only shown if assets exist) */}
              <FilterBar 
                mediaFilter={mediaFilter}
                setMediaFilter={setMediaFilter}
                sortOrder={sortOrder}
                setSortOrder={setSortOrder}
              />

              {/* Recent Assets Header */}
              <div className="flex items-center space-x-2 pt-4">
                <h2 className="text-[10px] leading-[12px] font-inter text-white uppercase tracking-wider">RECENT ASSETS</h2>
                <span className="text-[10px] leading-[12px] font-inter text-white">{assets.length}</span>
              </div>

              {/* Asset Grid */}
              <div>
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-x-4 gap-y-6">
                  {paginatedAssets.map(asset => (
                    <MediaCard key={asset.asset_id} {...asset} />
                  ))}
                </div>
              </div>

              {/* Custom Pagination */}
              {totalPages > 0 && (
                <div className="absolute bottom-0 left-0 right-0">
                  <Pagination 
                    currentPage={currentPage} 
                    totalPages={totalPages} 
                    onPageChange={setCurrentPage} 
                  />
                </div>
              )}
            </div>
          ) : (
            // Empty State Box
            <div className="w-full max-w-[834px] min-h-[526px] mx-auto border-2 border-dashed border-sma-purple rounded-lg flex flex-col items-center relative mt-4 pt-12 pb-8 px-12 bg-sma-surface/30">
              <div className="mt-[20px] mb-[40px]">
                <Icon icon="lucide:book" width="40" height="40" className="text-white" />
              </div>

              <div className="text-center mb-10">
                <h2 className="text-[36px] leading-[44px] font-bold text-white font-inter">YOUR LIBRARY IS EMPTY</h2>
                <p className="text-[18px] text-[#A1A1AA] mt-2 font-inter">Upload your first video to start using AI-powered search.</p>
              </div>

              <div className="flex flex-col items-center space-y-[57px] w-full h-40">
                <button className="flex items-center justify-center space-x-3 w-[426px] h-[70px] bg-sma-purple/20 hover:bg-sma-purple/30 transition-colors rounded-lg group relative">
                  <div className="absolute inset-0 rounded-lg border border-sma-purple/0 group-hover:border-sma-purple/50 transition-colors"></div>
                  <Icon icon="lucide:upload" width="44" height="44" className="text-white" />
                  <span className="text-[30px] leading-[44px] font-bold text-white font-inter">Upload for the 1st</span>
                </button>

                <button className="flex items-center justify-center w-[426px] h-[70px] bg-sma-purple/20 hover:bg-sma-purple/30 transition-colors rounded-[6px] group relative">
                  <div className="absolute inset-0 rounded-[6px] border border-sma-purple/0 group-hover:border-sma-purple/50 transition-colors"></div>
                  <span className="text-[30px] leading-[44px] font-bold text-white font-inter">Watch demo</span>
                </button>
              </div>

              <div className="absolute bottom-[6px] w-full flex justify-between px-[45px] text-white">
                <div className="flex items-center space-x-2">
                  <Icon icon="lucide:shield" width="41" height="41" className="text-white" />
                  <span className="text-[20px] leading-[24px] font-bold font-inter whitespace-nowrap">Local first, private</span>
                </div>
                <div className="flex items-center space-x-2">
                  <Icon icon="lucide:zap" width="41" height="41" className="text-white" />
                  <span className="text-[20px] leading-[24px] font-bold font-inter whitespace-nowrap">AI runs on your machine</span>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
