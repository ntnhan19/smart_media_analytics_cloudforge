import { useState, useEffect, useMemo } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { searchMedia } from '../services/api';
import { getSearchHistory, addSearchHistory, clearSearchHistory } from '../utils/history';
import SearchBar from '../components/search/SearchBar';
import SearchFilters from '../components/search/SearchFilters';
import SearchHistory from '../components/search/SearchHistory';
import SearchResultList from '../components/search/SearchResultList';
import SearchEmptyState from '../components/search/SearchEmptyState';
import SearchErrorState from '../components/search/SearchErrorState';
import SearchSkeleton from '../components/search/SearchSkeleton';

export default function Search() {
  const [searchParams, setSearchParams] = useSearchParams();
  
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

  const availableTags = ['beach', 'mountain', 'city', 'nature', 'indoor', 'snow'];
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
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 md:p-6 shadow-sm">
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
