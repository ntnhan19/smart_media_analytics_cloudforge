import { useState, useMemo, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import MediaCard from '../components/media/MediaCard';
import { Icon } from '@iconify/react';
import { useNavigate } from 'react-router-dom';
import SearchBar from '../components/search/SearchBar';
import SearchFilters from '../components/search/SearchFilters';
import SearchHistory from '../components/search/SearchHistory';
import { getSearchHistory, addSearchHistory, clearSearchHistory } from '../utils/history';

import { getAssets, getTags } from '../services/api';

export default function Dashboard() {
  const [currentPage, setCurrentPage] = useState(1);
  const [searchQuery, setSearchQuery] = useState('');
  const [activeTags, setActiveTags] = useState([]);
  const [activeMediaTypes, setActiveMediaTypes] = useState(['video', 'image', 'audio']);
  const [searchHistory, setSearchHistoryState] = useState(getSearchHistory());

  const [scoreFilter, setScoreFilter] = useState('all');
  const [topK, setTopK] = useState(20);

  const navigate = useNavigate();

  const { data: tagsData, isLoading: isLoadingTags } = useQuery({
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
      result = result.filter(asset => asset.tags && Array.isArray(asset.tags) && asset.tags.some(tag => activeTags.includes(tag.toLowerCase())));
    }

    return result;
  }, [assets, activeMediaTypes, activeTags]);

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
      navigate(`/search?q=${encodeURIComponent(q.trim())}`);
    }
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
                  scoreFilter={scoreFilter}
                  onScoreChange={setScoreFilter}
                  tags={availableTags}
                  activeTags={activeTags}
                  onToggleTag={handleToggleTag}
                  mediaTypes={availableMediaTypes}
                  activeMediaTypes={activeMediaTypes}
                  onToggleMediaType={handleToggleMediaType}
                  topK={topK}
                  onTopKChange={setTopK}
                  isLoadingTags={isLoadingTags}
                />
              </div>

              <div className="flex items-center space-x-2 pb-1.5 shrink-0">
                <h2 className="text-[10px] leading-[12px] font-inter text-gray-900 dark:text-white uppercase tracking-wider transition-colors">RECENT ASSETS</h2>
                <span className="text-[10px] leading-[12px] font-inter text-gray-500 dark:text-gray-400 transition-colors">{filteredAssets.length} items on this page</span>
              </div>

              {/* KHỐI 2: LƯỚI VIDEO (Trọng tâm) 
                  Thay đổi: flex-1 flex flex-col justify-start để thẻ nằm gần title RECENT ASSETS 
              */}
              <div className="flex-1 min-h-0 flex flex-col justify-start w-full pb-4 pt-2">
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-x-4 gap-y-5">
                  {filteredAssets.map(asset => (
                    <MediaCard key={asset.asset_id} {...asset} showToast={showToast} />
                  ))}
                </div>
              </div>

              {/* KHỐI 3: PAGINATION FOOTER (Mỏ neo dưới)
                  Thay đổi: mt-auto đẩy sát đáy, cộng thêm viền border-t để chia tách rõ ràng khu vực 
              */}
              <div className="shrink-0 mt-auto pt-3 pb-3 w-full border-t border-gray-200 dark:border-[#2D2844] flex items-center justify-center space-x-4 transition-colors">
                <button
                  onClick={() => handlePageChange(currentPage - 1)}
                  disabled={currentPage === 1}
                  className="px-4 py-2 text-[12px] leading-[14px] font-inter text-gray-700 dark:text-white bg-transparent border border-gray-300 dark:border-sma-purple rounded-lg hover:bg-gray-100 dark:hover:bg-sma-purple/10 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  Previous
                </button>

                <span className="text-[12px] leading-[14px] text-gray-500 dark:text-gray-400 px-4 font-inter transition-colors">
                  Page <span className="text-gray-900 dark:text-white font-medium">{currentPage}</span> of <span className="text-gray-900 dark:text-white font-medium">{totalPages}</span>
                </span>

                <button
                  onClick={() => handlePageChange(currentPage + 1)}
                  disabled={!hasNextPage}
                  className="px-4 py-2 text-[12px] leading-[14px] font-inter text-gray-700 dark:text-white bg-transparent border border-gray-300 dark:border-sma-purple rounded-lg hover:bg-gray-100 dark:hover:bg-sma-purple/10 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  Next
                </button>
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