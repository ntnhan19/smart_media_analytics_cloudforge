import { useState, useMemo, useEffect } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import MediaCard from '../components/media/MediaCard';
import { Icon } from '@iconify/react';
import { useNavigate } from 'react-router-dom';
import SearchBar from '../components/search/SearchBar';
import SearchFilters from '../components/search/SearchFilters';
import SearchHistory from '../components/search/SearchHistory';
import { getSearchHistory, addSearchHistory, clearSearchHistory } from '../utils/history';

import { getAssets } from '../services/api';

export default function Dashboard() {
  const [currentPage, setCurrentPage] = useState(1);
  const [searchQuery, setSearchQuery] = useState('');
  const [activeTags, setActiveTags] = useState([]);
  const [activeMediaTypes, setActiveMediaTypes] = useState(['video', 'image', 'audio']);
  const [searchHistory, setSearchHistoryState] = useState(getSearchHistory());

  // Dummy state for score and topK since we just want to match the UI of the Search page exactly
  const [scoreFilter, setScoreFilter] = useState('all');
  const [topK, setTopK] = useState(20);

  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const availableTags = ['beach', 'mountain', 'city', 'nature', 'indoor', 'snow'];
  const availableMediaTypes = ['video', 'image', 'audio'];

  const itemsPerPage = 8;
  const offset = (currentPage - 1) * itemsPerPage;

  const { data: assets, isLoading, error } = useQuery({
    queryKey: ['assets', currentPage],
    queryFn: ({ signal }) => getAssets(signal, itemsPerPage, offset),
    keepPreviousData: true,
  });

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

  const hasNextPage = assets && assets.length === itemsPerPage;

  const handlePageChange = (newPage) => {
    setCurrentPage(newPage);
  };

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
    <div className="max-w-7xl mx-auto space-y-6 relative">
      {/* Toast Notification */}
      {toast && (
        <div className={`fixed top-[20px] right-[20px] z-50 px-4 py-2 rounded shadow-lg text-white font-inter text-sm animate-fade-in-down ${toast.type === 'success' ? 'bg-green-600' : 'bg-red-600'}`}>
          {toast.message}
        </div>
      )}

      {/* Stats Cards - Only shown in Empty State */}
      {(!assets || assets.length === 0) && !isLoading && !error && currentPage === 1 && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-2 mt-1">
          <div className="bg-[#16132A] p-2 rounded-xl border border-[#2D2844] w-60 h-30">
            <h3 className="text-gray-400 font-medium">Total Assets</h3>
            <p className="text-3xl font-bold mt-4">0</p>
          </div>
          <div className="bg-[#16132A] p-2 rounded-xl border border-[#2D2844] w-60 h-30">
            <h3 className="text-gray-400 font-medium">Storage Used</h3>
            <p className="text-3xl font-bold mt-4 ">0 MB</p>
          </div>
          <div className="bg-[#16132A] p-2 rounded-xl border border-[#2D2844] w-60 h-30">
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
        <div className="mt-0">
          {assets && assets.length > 0 ? (
            <div className="flex flex-col space-y-2 pb-8">
              
              {/* Centralized Search & Filters on Dashboard */}
              <div className="bg-[#16132A] border border-[#2D2844] rounded-xl p-4 md:p-6 shadow-sm mb-2">
                <SearchBar 
                  variant="large"
                  value={searchQuery}
                  onChange={setSearchQuery}
                  onSearch={handleSearchSubmit}
                  placeholder="Search your media library..."
                />
                
                <div className="mt-4">
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
                />
              </div>

              {/* Recent Assets Header */}
              <div className="flex items-center space-x-2 pt-0 pb-1">
                <h2 className="text-[10px] leading-[12px] font-inter text-white uppercase tracking-wider">RECENT ASSETS</h2>
                <span className="text-[10px] leading-[12px] font-inter text-white">{filteredAssets.length} items on this page</span>
              </div>

              {/* Asset Grid */}
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-x-4 gap-y-6 mt-2">
                {filteredAssets.map(asset => (
                  <MediaCard key={asset.asset_id} {...asset} showToast={showToast} />
                ))}
              </div>

              {/* Custom Pagination - CSS fixed by moving out of absolute positioning */}
              <div className="flex items-center justify-center space-x-4 pt-8">
                <button
                  onClick={() => handlePageChange(currentPage - 1)}
                  disabled={currentPage === 1}
                  className="px-4 py-2 text-[12px] leading-[14px] font-inter text-white bg-transparent border border-sma-purple rounded-lg hover:bg-sma-purple/10 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  Previous
                </button>
                
                <span className="text-[12px] leading-[14px] text-gray-400 px-4 font-inter">
                  Page <span className="text-white font-medium">{currentPage}</span>
                </span>

                <button
                  onClick={() => handlePageChange(currentPage + 1)}
                  disabled={!hasNextPage}
                  className="px-4 py-2 text-[12px] leading-[14px] font-inter text-white bg-transparent border border-sma-purple rounded-lg hover:bg-sma-purple/10 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  Next
                </button>
              </div>
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
                <button 
                  onClick={handleUploadClick}
                  className="flex items-center justify-center space-x-3 w-[426px] h-[70px] bg-sma-purple/20 hover:bg-sma-purple/30 transition-colors rounded-lg group relative"
                >
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
