import { useState, useEffect, useMemo } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { searchMedia, getTags } from '../services/api';
import { getSearchHistory, addSearchHistory, clearSearchHistory } from '../utils/history';
import { Icon } from '@iconify/react';
import { useToast } from '../contexts/ToastContext';
import SearchBar from '../components/search/SearchBar';
import SearchFilters from '../components/search/SearchFilters';
import SearchHistory from '../components/search/SearchHistory';
import SearchResultList from '../components/search/SearchResultList';
import SearchEmptyState from '../components/search/SearchEmptyState';
import SearchErrorState from '../components/search/SearchErrorState';
import SearchSkeleton from '../components/search/SearchSkeleton';

export default function Search() {
  const [searchParams, setSearchParams] = useSearchParams();
  const { showToast } = useToast();
  
  const urlQ = searchParams.get('q') || '';
  const urlScore = searchParams.get('score') || 'all';
  const urlTags = useMemo(() => searchParams.get('tags') ? searchParams.get('tags').split(',') : [], [searchParams]);
  const urlMediaType = useMemo(() => searchParams.get('media_type') ? searchParams.get('media_type').split(',') : ['video'], [searchParams]);
  const urlTopK = parseInt(searchParams.get('top_k')) || 20;

  const [searchQuery, setSearchQuery] = useState(urlQ);
  const [scoreFilter, setScoreFilter] = useState(urlScore);
  const [activeTags, setActiveTags] = useState(urlTags);
  const [activeMediaTypes, setActiveMediaTypes] = useState(urlMediaType);
  const [topK, setTopK] = useState(urlTopK);
  const [validationError, setValidationError] = useState('');

  const [searchHistory, setSearchHistory] = useState(getSearchHistory());

  const { data: tagsData, isLoading: isLoadingTags, isError: isErrorTags, refetch: refetchTags } = useQuery({
    queryKey: ['tags'],
    queryFn: ({ signal }) => getTags(signal),
    staleTime: 5 * 60 * 1000,
  });

  const availableTags = Array.isArray(tagsData) ? tagsData : (tagsData?.tags || []);
  const availableMediaTypes = ['video', 'image', 'audio'];

  const hasValidSearch = Boolean(urlQ.trim() && urlQ.length <= 500);

  // Payload matches backend Pydantic schema strictly
  const payload = useMemo(() => {
    const filters = {};
    if (urlTags.length > 0) filters.tags = urlTags;
    if (urlMediaType.length > 0) filters.media_type = urlMediaType;
    
    return {
      query: urlQ.trim(),
      filters: filters,
      top_k: urlTopK
    };
  }, [urlQ, urlTags, urlMediaType, urlTopK]);

  const { data, isFetching, error, refetch } = useQuery({
    queryKey: ['search', payload],
    queryFn: ({ signal }) => searchMedia(payload, signal),
    enabled: hasValidSearch,
    retry: 0,
    refetchOnWindowFocus: false,
    onSuccess: () => {
       if (payload.query) {
         const newHist = addSearchHistory(payload.query);
         if (newHist) setSearchHistory(newHist);
       }
    }
  });

  const applySearch = (newQ, newScore, newTags, newMedia, newTopK) => {
    if (newQ.length > 500) {
      setValidationError('Query cannot exceed 500 characters.');
      return;
    }
    setValidationError('');
    
    if (!newQ.trim()) {
      setSearchParams({});
      return;
    }

    const params = {};
    params.q = newQ.trim();
    if (newScore !== 'all') params.score = newScore;
    if (newTags.length > 0) params.tags = newTags.join(',');
    if (newMedia.length > 0) params.media_type = newMedia.join(',');
    if (newTopK !== 20) params.top_k = newTopK;

    setSearchParams(params);
  };

  const handleSearchSubmit = (q) => {
    if (q.length > 500) return;
    applySearch(q, scoreFilter, activeTags, activeMediaTypes, topK);
  };

  const handleClearHistory = () => {
    clearSearchHistory();
    setSearchHistory([]);
  };

  const handleSelectHistory = (term) => {
    setSearchQuery(term);
    applySearch(term, scoreFilter, activeTags, activeMediaTypes, topK);
  };

  const handleToggleTag = (tag) => {
    const newTags = activeTags.includes(tag) ? activeTags.filter(t => t !== tag) : [...activeTags, tag];
    setActiveTags(newTags);
    applySearch(searchQuery, scoreFilter, newTags, activeMediaTypes, topK);
  };

  const handleToggleMediaType = (type) => {
    const newMedia = activeMediaTypes.includes(type) ? activeMediaTypes.filter(t => t !== type) : [...activeMediaTypes, type];
    // Ensure at least one is selected, if they deselect all, fallback to ['video']
    const finalMedia = newMedia.length === 0 ? ['video'] : newMedia;
    setActiveMediaTypes(finalMedia);
    applySearch(searchQuery, scoreFilter, activeTags, finalMedia, topK);
  };

  const onScoreChange = (v) => { setScoreFilter(v); applySearch(searchQuery, v, activeTags, activeMediaTypes, topK); };
  
  const onTopKChange = (v) => { 
    const intV = parseInt(v);
    setTopK(intV); 
    applySearch(searchQuery, scoreFilter, activeTags, activeMediaTypes, intV); 
  };

  useEffect(() => {
    const handler = setTimeout(() => {
      // Only update if URL param changed externally
      if (searchQuery !== urlQ) setSearchQuery(urlQ);
      if (scoreFilter !== urlScore) setScoreFilter(urlScore);
      if (JSON.stringify(activeTags) !== JSON.stringify(urlTags)) setActiveTags(urlTags);
      if (JSON.stringify(activeMediaTypes) !== JSON.stringify(urlMediaType)) setActiveMediaTypes(urlMediaType);
      if (topK !== urlTopK) setTopK(urlTopK);
    }, 0);
    return () => clearTimeout(handler);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [urlQ, urlScore, searchParams.get('tags'), searchParams.get('media_type'), urlTopK]);

  let errorMessage = '';
  if (error) {
    if (error.response?.status === 400) errorMessage = 'Query không hợp lệ';
    else errorMessage = 'Search service unavailable. Please try again later.';
  }

  const isDisabled = isFetching && hasValidSearch;
  let results = data?.results || [];
  
  // Apply score filter locally since backend doesn't support it directly in filters yet
  if (scoreFilter !== 'all') {
    results = results.filter(item => {
      if (scoreFilter === 'very_high') return item.score > 0.9;
      if (scoreFilter === 'high') return item.score > 0.7;
      if (scoreFilter === 'medium') return item.score > 0.5;
      return true;
    });
  }

  const processingTime = data?.processing_time_ms;

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Page Header (Consistent Header) */}
      <div className="flex items-center justify-between mb-2 mt-2">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-sma-purple/10 rounded-xl">
            <Icon icon="lucide:search" width="24" height="24" className="text-sma-purple" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900 leading-tight">Semantic Search</h1>
            <p className="text-sm text-gray-500 font-medium">Find the exact scene using natural language.</p>
          </div>
        </div>
      </div>

      <div className="bg-white border border-gray-200 rounded-xl p-4 md:p-6 shadow-sm mb-4">
        <div className="flex gap-3">
          <div className="flex-1">
            <SearchBar 
              variant="large"
              value={searchQuery}
              onChange={(v) => {
                setSearchQuery(v);
                if (v.length > 500) setValidationError('Query cannot exceed 500 characters.');
                else setValidationError('');
              }}
              onSearch={handleSearchSubmit}
              placeholder="e.g. 'sunset over the ocean', 'person riding a bike'"
              disabled={isDisabled}
            />
          </div>
          <button 
            onClick={async () => {
              if (!searchQuery.trim()) return;
              try {
                // Need to import savedSearchesApi and useToast
                const { savedSearchesApi } = await import('../api/savedSearches');
                await savedSearchesApi.create(searchQuery.trim());
                // Show toast
                showToast('Search saved successfully!', 'success');
              } catch (e) {
                console.error(e);
                showToast('Failed to save search', 'error');
              }
            }}
            disabled={isDisabled || !searchQuery.trim()}
            className={`shrink-0 flex items-center justify-center px-4 rounded-xl transition-all ${searchQuery.trim() ? 'bg-sma-purple text-white hover:bg-[#6044DD] shadow-md' : 'bg-gray-100 text-gray-400 border border-gray-200 cursor-not-allowed'}`}
            title="Save Search"
          >
            <Icon icon="lucide:bookmark" width="20" className="mr-2" />
            <span className="font-semibold">Save</span>
          </button>
        </div>
        {validationError && <p className="text-red-500 text-sm mt-2 ml-2 font-medium">{validationError}</p>}
        
        <div className="mt-4">
          <SearchHistory 
            history={searchHistory}
            onSelectHistory={handleSelectHistory}
            onClearHistory={handleClearHistory}
          />
        </div>

        <SearchFilters 
          scoreFilter={scoreFilter} onScoreChange={onScoreChange}
          tags={availableTags} activeTags={activeTags} onToggleTag={handleToggleTag}
          mediaTypes={availableMediaTypes} activeMediaTypes={activeMediaTypes} onToggleMediaType={handleToggleMediaType}
          topK={topK} onTopKChange={onTopKChange}
          disabled={isDisabled}
          isLoadingTags={isLoadingTags}
          isErrorTags={isErrorTags}
          onRetryTags={refetchTags}
        />
      </div>

      <div className="min-h-[400px]">
        {isFetching && <SearchSkeleton />}
        
        {!isFetching && error && (
          <SearchErrorState error={errorMessage} onRetry={() => refetch()} />
        )}
        
        {!isFetching && !error && hasValidSearch && results.length === 0 && (
          <SearchEmptyState />
        )}
        
        {!isFetching && !error && hasValidSearch && results.length > 0 && (
          <div className="space-y-4">
            {processingTime !== undefined && (
              <p className="text-sm text-gray-400 font-medium">Found {results.length} results in {processingTime}ms</p>
            )}
            <SearchResultList results={results} />
          </div>
        )}

        {!hasValidSearch && (
          <div className="pt-12">
            <SearchEmptyState message="Enter a search term or apply filters to start exploring your media library." />
          </div>
        )}
      </div>
    </div>
  );
}
