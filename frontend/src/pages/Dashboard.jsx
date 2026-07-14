import { useState, useMemo, useEffect } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import MediaCard from '../components/media/MediaCard';
import { Icon } from '@iconify/react';
import { useNavigate } from 'react-router-dom';
import SearchBar from '../components/search/SearchBar';
import SearchFilters from '../components/search/SearchFilters';
import SearchHistory from '../components/search/SearchHistory';
import { getSearchHistory, addSearchHistory, clearSearchHistory } from '../utils/history';

import { getAssets, getTags } from '../services/api';

const removeAccents = (str) => {
  if (!str) return '';
  return str.normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/đ/g, 'd').replace(/Đ/g, 'D');
};

export default function Dashboard() {
  const [currentPage, setCurrentPage] = useState(1);
  const [searchQuery, setSearchQuery] = useState('');
  const [activeTags, setActiveTags] = useState([]);
  const [activeMediaTypes, setActiveMediaTypes] = useState(['video', 'image', 'audio']);
  const [searchHistory, setSearchHistoryState] = useState(getSearchHistory());

  const [sortBy, setSortBy] = useState('newest');
  const [statusFilter, setStatusFilter] = useState('all');
  
  // Bulk selection state
  const [isSelectMode, setIsSelectMode] = useState(false);
  const [selectedAssetIds, setSelectedAssetIds] = useState([]);
  const [isBulkDeleting, setIsBulkDeleting] = useState(false);

  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const { data: tagsData, isLoading: isLoadingTags, isError: isErrorTags, refetch: refetchTags } = useQuery({
    queryKey: ['tags'],
    queryFn: ({ signal }) => getTags(signal),
    staleTime: 5 * 60 * 1000,
  });

  const availableTags = Array.isArray(tagsData) ? tagsData : (tagsData?.tags || []);
  const availableMediaTypes = ['video', 'image', 'audio'];

  const itemsPerPage = 8;
  const offset = (currentPage - 1) * itemsPerPage;

  const { data: assetsData, isLoading, error } = useQuery({
    queryKey: ['assets', currentPage],
    queryFn: ({ signal }) => getAssets(signal, itemsPerPage, offset),
    keepPreviousData: true,
  });

  const assets = useMemo(() => assetsData?.items || [], [assetsData]);
  const totalAssets = assetsData?.total || 0;
  const totalPages = Math.max(1, Math.ceil(totalAssets / itemsPerPage));

  const filteredAssets = useMemo(() => {
    if (!assets) return [];
    let result = [...assets];

    if (activeMediaTypes.length > 0) {
      result = result.filter(asset => asset.media_type && activeMediaTypes.includes(asset.media_type.toLowerCase()));
    }

    if (activeTags.length > 0) {
      result = result.filter(asset => asset.tags && Array.isArray(asset.tags) && asset.tags.some(tag => {
        const tagText = typeof tag === 'object' && tag !== null ? tag.name : tag;
        return typeof tagText === 'string' && activeTags.includes(tagText.toLowerCase());
      }));
    }

    if (searchQuery.trim()) {
      const q = removeAccents(searchQuery.trim().toLowerCase());
      result = result.filter(asset => {
        const nameStr = asset.file_name ? removeAccents(asset.file_name.toLowerCase()) : '';
        const matchName = nameStr.includes(q);
        
        const matchTags = asset.tags && Array.isArray(asset.tags) && asset.tags.some(tag => {
          const tagText = typeof tag === 'object' && tag !== null ? tag.name : tag;
          if (typeof tagText !== 'string') return false;
          const cleanTag = removeAccents(tagText.toLowerCase());
          return cleanTag.includes(q);
        });
        return matchName || matchTags;
      });
    }

    if (statusFilter !== 'all') {
      result = result.filter(asset => {
        const status = asset.status || 'ready';
        if (statusFilter === 'ready') return status === 'ready' || status === 'completed';
        return status === statusFilter;
      });
    }

    // Local Sorting (for current page items)
    result.sort((a, b) => {
      if (sortBy === 'newest') {
        return new Date(b.created_at || 0) - new Date(a.created_at || 0);
      }
      if (sortBy === 'oldest') {
        return new Date(a.created_at || 0) - new Date(b.created_at || 0);
      }
      if (sortBy === 'name_asc') {
        return (a.file_name || '').localeCompare(b.file_name || '');
      }
      return 0;
    });

    return result;
  }, [assets, activeMediaTypes, activeTags, searchQuery, statusFilter, sortBy]);

  const hasNextPage = currentPage < totalPages;

  const handlePageChange = (newPage) => {
    setCurrentPage(newPage);
  };

  useEffect(() => {
    if (assets && assets.length === 0 && currentPage > 1 && !isLoading) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setCurrentPage(prev => Math.max(1, prev - 1));
    }
  }, [assets, currentPage, isLoading]);

  const handleUploadClick = () => {
    navigate('/upload');
  };

  const handleSearchSubmit = (q) => {
    if (q.trim()) {
      const newHist = addSearchHistory(q.trim());
      if (newHist) setSearchHistoryState(newHist);
    }
    setSearchQuery(q);
  };

  const handleSelectHistory = (term) => {
    setSearchQuery(term);
    handleSearchSubmit(term);
  };

  const handleClearHistory = () => {
    clearSearchHistory();
    setSearchHistoryState([]);
  };

  const handleToggleTag = (tag) => {
    setActiveTags(prev => prev.includes(tag) ? prev.filter(t => t !== tag) : [...prev, tag]);
  };

  const handleSelectToggle = (id, selected) => {
    if (selected) {
      setSelectedAssetIds(prev => [...prev, id]);
    } else {
      setSelectedAssetIds(prev => prev.filter(item => item !== id));
    }
  };

  const handleSelectAll = () => {
    if (selectedAssetIds.length === filteredAssets.length) {
      setSelectedAssetIds([]);
    } else {
      setSelectedAssetIds(filteredAssets.map(a => a.asset_id));
    }
  };

  const handleBulkDelete = async () => {
    if (!window.confirm(`Are you sure you want to delete ${selectedAssetIds.length} selected videos?`)) return;
    
    setIsBulkDeleting(true);
    try {
      const { deleteAsset } = await import('../services/api');
      await Promise.all(selectedAssetIds.map(id => deleteAsset(id)));
      
      const currentCount = parseInt(localStorage.getItem('deletedAssetsCount') || '0', 10);
      localStorage.setItem('deletedAssetsCount', (currentCount + selectedAssetIds.length).toString());
      window.dispatchEvent(new Event('assetDeleted'));
      
      showToast(`${selectedAssetIds.length} videos deleted successfully`, 'success');
      setSelectedAssetIds([]);
      setIsSelectMode(false);
      queryClient.invalidateQueries({ queryKey: ['assets'] });
    } catch (err) {
      console.error('Bulk delete error:', err);
      showToast('Failed to delete some videos', 'error');
    } finally {
      setIsBulkDeleting(false);
    }
  };

  const handleToggleMediaType = (type) => {
    setActiveMediaTypes(prev => {
      const next = prev.includes(type) ? prev.filter(t => t !== type) : [...prev, type];
      return next.length === 0 ? ['video'] : next;
    });
  };

  const [toast, setToast] = useState(null);
  const showToast = (message, type = 'success') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3000);
  };

  return (
    <div className="max-w-7xl mx-auto space-y-4 relative h-full flex flex-col">
      {toast && (
        <div className={`fixed top-[20px] right-[20px] z-50 px-4 py-2 rounded shadow-lg text-white font-inter text-sm animate-fade-in-down ${toast.type === 'success' ? 'bg-green-600' : 'bg-red-600'}`}>
          {toast.message}
        </div>
      )}

      {(!assets || assets.length === 0) && !isLoading && !error && currentPage === 1 && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-2 mt-1">
          <div className="bg-white dark:bg-[#16132A] p-2 rounded-xl border border-gray-200 dark:border-[#2D2844] w-60 h-30 transition-colors shadow-sm dark:shadow-none">
            <h3 className="text-gray-500 dark:text-gray-400 font-medium">Total Assets</h3>
            <p className="text-3xl font-bold mt-4 text-gray-900 dark:text-white">{totalAssets}</p>
          </div>
          <div className="bg-white dark:bg-[#16132A] p-2 rounded-xl border border-gray-200 dark:border-[#2D2844] w-60 h-30 transition-colors shadow-sm dark:shadow-none">
            <h3 className="text-gray-500 dark:text-gray-400 font-medium">Storage Used</h3>
            <p className="text-3xl font-bold mt-4 text-gray-900 dark:text-white">0 MB</p>
          </div>
          <div className="bg-white dark:bg-[#16132A] p-2 rounded-xl border border-gray-200 dark:border-[#2D2844] w-60 h-30 transition-colors shadow-sm dark:shadow-none">
            <h3 className="text-gray-500 dark:text-gray-400 font-medium">Recent Searches</h3>
            <p className="text-3xl font-bold mt-4 text-gray-900 dark:text-white">{searchHistory.length}</p>
          </div>
        </div>
      )}

      {isLoading && (
        <div className="flex justify-center items-center py-20">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-sma-purple"></div>
        </div>
      )}

      {error && (
        <div className="bg-red-900/20 border border-red-500/50 text-red-400 p-6 rounded-xl text-center">
          Failed to load assets. Please try again later.
        </div>
      )}

      {!isLoading && !error && (
        <div className="flex-1 min-h-0 flex flex-col">
          {(assets && assets.length > 0) || currentPage > 1 ? (
            <div className="flex flex-col flex-1 h-full min-h-0 w-full">

              {/* KHỐI 1: TÌM KIẾM (Bám sát mép trên) */}
              <div className="bg-white dark:bg-[#16132A] border border-gray-200 dark:border-[#2D2844] rounded-xl p-2.5 shadow-sm mb-3 shrink-0 transition-colors">
                <SearchBar
                  variant="large"
                  value={searchQuery}
                  onChange={setSearchQuery}
                  onSearch={handleSearchSubmit}
                  placeholder="Search your media library..."
                />

                <div className="mt-1">
                  <SearchHistory
                    history={searchHistory}
                    onSelectHistory={handleSelectHistory}
                    onClearHistory={handleClearHistory}
                  />
                </div>

                <SearchFilters
                  sortBy={sortBy}
                  onSortChange={setSortBy}
                  statusFilter={statusFilter}
                  onStatusChange={setStatusFilter}
                  tags={availableTags}
                  activeTags={activeTags}
                  onToggleTag={handleToggleTag}
                  mediaTypes={availableMediaTypes}
                  activeMediaTypes={activeMediaTypes}
                  onToggleMediaType={(type) => setActiveMediaTypes(prev => prev.includes(type) ? prev.filter(t => t !== type) : [...prev, type])}
                  isLoadingTags={isLoadingTags}
                  isErrorTags={isErrorTags}
                  onRetryTags={() => refetchTags()}
                />
              </div>

              <div className="flex items-center justify-between pb-2 mt-1 shrink-0">
                <div className="flex items-center space-x-2">
                  {!isSelectMode ? (
                    <>
                      <h2 className="text-[10px] leading-[12px] font-inter text-gray-900 dark:text-white uppercase tracking-wider transition-colors">RECENT ASSETS</h2>
                      <span className="text-[10px] leading-[12px] font-inter text-gray-500 dark:text-gray-400 transition-colors">{filteredAssets.length} items on this page</span>
                    </>
                  ) : (
                    <div className="flex items-center space-x-2 bg-sma-purple/10 dark:bg-sma-purple/20 px-3 py-1 rounded-md border border-sma-purple/20">
                      <span className="text-xs text-sma-purple dark:text-[#A78BFA] font-medium mr-1">{selectedAssetIds.length} selected</span>
                      <button
                        onClick={handleSelectAll}
                        className="text-xs text-gray-600 hover:text-gray-900 dark:text-gray-300 dark:hover:text-white px-2 transition-colors border-r border-sma-purple/20"
                        disabled={isBulkDeleting}
                      >
                        {selectedAssetIds.length === filteredAssets.length ? 'Deselect All' : 'Select All'}
                      </button>
                      <button
                        onClick={handleBulkDelete}
                        className="flex items-center px-2 py-1 bg-red-500 hover:bg-red-600 text-white text-xs rounded transition-colors disabled:opacity-50 ml-2"
                        disabled={isBulkDeleting || selectedAssetIds.length === 0}
                      >
                        {isBulkDeleting ? <Icon icon="lucide:loader-2" className="animate-spin mr-1 w-3 h-3" /> : <Icon icon="lucide:trash-2" className="mr-1 w-3 h-3" />}
                        Delete
                      </button>
                    </div>
                  )}
                </div>
                
                <div className="flex items-center space-x-3">
                  {!isSelectMode ? (
                    <button
                      onClick={() => setIsSelectMode(true)}
                      className="px-3 py-1.5 text-[11px] font-medium text-gray-700 dark:text-gray-200 bg-white dark:bg-[#16132A] border border-gray-200 dark:border-[#2D2844] rounded-md hover:bg-gray-50 dark:hover:bg-[#2D2844] transition-colors flex items-center gap-1.5"
                    >
                      <Icon icon="lucide:check-square" width="14" height="14" />
                      Select
                    </button>
                  ) : (
                    <button
                      onClick={() => {
                        setIsSelectMode(false);
                        setSelectedAssetIds([]);
                      }}
                      className="px-3 py-1.5 text-[11px] font-medium text-gray-700 dark:text-gray-200 bg-white dark:bg-[#16132A] border border-gray-200 dark:border-[#2D2844] rounded-md hover:bg-gray-50 dark:hover:bg-[#2D2844] transition-colors"
                      disabled={isBulkDeleting}
                    >
                      Cancel
                    </button>
                  )}

                  {/* INLINE PAGINATION */}
                  <div className="flex items-center space-x-3 border-l border-gray-200 dark:border-gray-700 pl-3">
                    <button
                      onClick={() => handlePageChange(currentPage - 1)}
                      disabled={currentPage === 1}
                      className="px-3 py-1.5 text-[11px] font-medium text-gray-700 dark:text-gray-200 bg-white dark:bg-[#16132A] border border-gray-200 dark:border-[#2D2844] rounded-md hover:bg-gray-50 dark:hover:bg-[#2D2844] disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    >
                      Previous
                    </button>
                    <span className="text-[11px] text-gray-500 dark:text-gray-400 font-medium">
                      <span className="text-gray-900 dark:text-white">{currentPage}</span> / {totalPages}
                    </span>
                    <button
                      onClick={() => handlePageChange(currentPage + 1)}
                      disabled={!hasNextPage}
                      className="px-3 py-1.5 text-[11px] font-medium text-gray-700 dark:text-gray-200 bg-white dark:bg-[#16132A] border border-gray-200 dark:border-[#2D2844] rounded-md hover:bg-gray-50 dark:hover:bg-[#2D2844] disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    >
                      Next
                    </button>
                  </div>
                </div>
              </div>

              {/* KHỐI 2: LƯỚI VIDEO (Trọng tâm) */}
              <div className="flex-1 min-h-0 w-full pb-4 pt-1">
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-x-4 gap-y-5 h-full auto-rows-fr">
                  {filteredAssets.map(asset => (
                    <MediaCard 
                      key={asset.asset_id} 
                      {...asset} 
                      showToast={showToast} 
                      selected={selectedAssetIds.includes(asset.asset_id)}
                      onSelectToggle={isSelectMode ? handleSelectToggle : undefined}
                      isSelectMode={isSelectMode}
                    />
                  ))}
                </div>
              </div>

            </div>
          ) : (
            // Empty State Box
            <div className="w-full max-w-[834px] min-h-[526px] mx-auto border-2 border-dashed border-gray-300 dark:border-sma-purple rounded-lg flex flex-col items-center relative mt-4 pt-12 pb-8 px-12 bg-white dark:bg-sma-surface/30 transition-colors shadow-sm dark:shadow-none">
              <div className="mt-[20px] mb-[40px]">
                <Icon icon="lucide:book" width="40" height="40" className="text-gray-700 dark:text-white transition-colors" />
              </div>

              <div className="text-center mb-10">
                <h2 className="text-[36px] leading-[44px] font-bold text-gray-900 dark:text-white font-inter transition-colors">YOUR LIBRARY IS EMPTY</h2>
                <p className="text-[18px] text-gray-500 dark:text-[#A1A1AA] mt-2 font-inter transition-colors">Upload your first video to start using AI-powered search.</p>
              </div>

              <div className="flex flex-col items-center space-y-[57px] w-full h-40">
                <button
                  onClick={handleUploadClick}
                  className="flex items-center justify-center space-x-3 w-[426px] h-[70px] bg-sma-purple/10 dark:bg-sma-purple/20 hover:bg-sma-purple/20 dark:hover:bg-sma-purple/30 transition-colors rounded-lg group relative"
                >
                  <div className="absolute inset-0 rounded-lg border border-sma-purple/0 group-hover:border-sma-purple/50 transition-colors"></div>
                  <Icon icon="lucide:upload" width="44" height="44" className="text-sma-purple dark:text-white transition-colors" />
                  <span className="text-[30px] leading-[44px] font-bold text-sma-purple dark:text-white font-inter transition-colors">Upload for the 1st</span>
                </button>

                <button className="flex items-center justify-center w-[426px] h-[70px] bg-sma-purple/10 dark:bg-sma-purple/20 hover:bg-sma-purple/20 dark:hover:bg-sma-purple/30 transition-colors rounded-[6px] group relative">
                  <div className="absolute inset-0 rounded-[6px] border border-sma-purple/0 group-hover:border-sma-purple/50 transition-colors"></div>
                  <span className="text-[30px] leading-[44px] font-bold text-sma-purple dark:text-white font-inter transition-colors">Watch demo</span>
                </button>
              </div>

              <div className="absolute bottom-[6px] w-full flex justify-between px-[45px] text-gray-600 dark:text-white transition-colors">
                <div className="flex items-center space-x-2">
                  <Icon icon="lucide:shield" width="41" height="41" className="text-gray-400 dark:text-white transition-colors" />
                  <span className="text-[20px] leading-[24px] font-bold font-inter whitespace-nowrap">Local first, private</span>
                </div>
                <div className="flex items-center space-x-2">
                  <Icon icon="lucide:zap" width="41" height="41" className="text-gray-400 dark:text-white transition-colors" />
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