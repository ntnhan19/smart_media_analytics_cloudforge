import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import SearchBar from '../components/search/SearchBar';
import SearchFilters from '../components/search/SearchFilters';
import SearchHistory from '../components/search/SearchHistory';
import SearchResultList from '../components/search/SearchResultList';
import SearchEmptyState from '../components/search/SearchEmptyState';
import SearchErrorState from '../components/search/SearchErrorState';
import SearchSkeleton from '../components/search/SearchSkeleton';
import { mockSearchResults } from '../mocks/searchResults';

export default function Search() {
  const [searchParams, setSearchParams] = useSearchParams();
  const initialQuery = searchParams.get('q') || '';

  const [searchQuery, setSearchQuery] = useState(initialQuery);
  const [scoreFilter, setScoreFilter] = useState('all');
  const [durationFilter, setDurationFilter] = useState('all');
  const [dateFilter, setDateFilter] = useState('all');
  const [activeTags, setActiveTags] = useState([]);
  const [topK, setTopK] = useState(20);
  const [searchHistory, setSearchHistory] = useState(['sunset over the ocean', 'mountain hiking', 'neon city']);
  
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [results, setResults] = useState([]);
  const [hasSearched, setHasSearched] = useState(false);

  const availableTags = ['beach', 'mountain', 'city', 'nature', 'indoor', 'snow'];

  // Trigger search on mount if there's an initial query
  useEffect(() => {
    if (initialQuery) {
      handleSearch(initialQuery);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Trigger search when filters change
  useEffect(() => {
    if (searchQuery.trim() || scoreFilter !== 'all' || durationFilter !== 'all' || dateFilter !== 'all' || activeTags.length > 0) {
      handleSearch(searchQuery);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [scoreFilter, durationFilter, dateFilter, activeTags]);

  const handleSearch = (query) => {
    // If everything is cleared, reset to initial state
    if (!query.trim() && scoreFilter === 'all' && durationFilter === 'all' && dateFilter === 'all' && activeTags.length === 0) {
      setResults([]);
      setHasSearched(false);
      setSearchParams({});
      return;
    }
    
    // Update URL query param to reflect current search
    if (query.trim() !== searchParams.get('q')) {
      setSearchParams(query.trim() ? { q: query.trim() } : {});
    }

    setIsLoading(true);
    setError(null);
    setHasSearched(true);
    
    // Add to history if new
    if (query.trim() && !searchHistory.includes(query.trim())) {
      setSearchHistory(prev => [query.trim(), ...prev].slice(0, 5));
    }

    // Simulate API delay
    setTimeout(() => {
      try {
        let filtered = [...mockSearchResults];
        
        // Simple mock filtering logic for demonstration
        if (query.trim()) {
           let textQuery = query.toLowerCase();
           
           // Extract hashtags from the typed query (e.g., "#beach #sunset")
           const hashTagsMatch = textQuery.match(/#(\w+)/g);
           const typedTags = hashTagsMatch ? hashTagsMatch.map(t => t.slice(1)) : [];
           
           // Remove hashtags from text query so it doesn't mess up text matching
           if (typedTags.length > 0) {
             textQuery = textQuery.replace(/#(\w+)/g, '').trim();
           }

           // Strictly filter by typed tags first (MUST contain all typed tags)
           if (typedTags.length > 0) {
             filtered = filtered.filter(item => 
               item.tags && typedTags.every(typedTag => item.tags.includes(typedTag))
             );
           }

           // Then filter by remaining text query
           if (textQuery) {
             filtered = filtered.filter(item => 
               (item.scene?.caption && item.scene.caption.toLowerCase().includes(textQuery)) ||
               (item.asset_name && item.asset_name.toLowerCase().includes(textQuery)) ||
               (item.tags && item.tags.some(tag => tag.toLowerCase().includes(textQuery)))
             );
           }
           
           if (filtered.length === 0) {
             filtered = [...mockSearchResults].sort(() => 0.5 - Math.random());
           }
        }

        // Apply Confidence Score Filter
        if (scoreFilter !== 'all') {
          filtered = filtered.filter(item => {
            if (scoreFilter === 'very_high') return item.score > 0.9;
            if (scoreFilter === 'high') return item.score > 0.7;
            if (scoreFilter === 'medium') return item.score > 0.5;
            return true;
          });
        }

        // Apply Duration Filter
        if (durationFilter !== 'all') {
          filtered = filtered.filter(item => {
            const dur = item.video_duration || 0;
            if (durationFilter === 'short') return dur < 60;
            if (durationFilter === 'medium') return dur >= 60 && dur <= 300;
            if (durationFilter === 'long') return dur > 300;
            return true;
          });
        }

        // Apply Date Filter
        if (dateFilter !== 'all') {
          const now = new Date();
          filtered = filtered.filter(item => {
            if (!item.ingested_at) return false;
            const date = new Date(item.ingested_at);
            const diffDays = (now - date) / (1000 * 60 * 60 * 24);
            if (dateFilter === 'today') return diffDays <= 1;
            if (dateFilter === 'this_week') return diffDays <= 7;
            if (dateFilter === 'this_month') return diffDays <= 30;
            return true;
          });
        }

        // Apply Tags
        if (activeTags.length > 0) {
          filtered = filtered.filter(item => 
            item.tags && item.tags.some(tag => activeTags.includes(tag))
          );
        }

        // Apply Top K mock
        filtered = filtered.slice(0, topK);

        setResults(filtered);
      } catch (err) {
        setError('Failed to fetch results. Please try again.');
      } finally {
        setIsLoading(false);
      }
    }, 1000); // 1s delay
  };

  const handleToggleTag = (tag) => {
    setActiveTags(prev => 
      prev.includes(tag) 
        ? prev.filter(t => t !== tag)
        : [...prev, tag]
    );
  };

  const handleClearHistory = () => {
    setSearchHistory([]);
  };

  const handleSelectHistory = (term) => {
    setSearchQuery(term);
    handleSearch(term);
  };

  return (
    <div className="max-w-7xl mx-auto space-y-6">

      
      {/* Search Input Area */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 md:p-6 shadow-sm">
        <SearchBar 
          variant="large"
          value={searchQuery}
          onChange={setSearchQuery}
          onSearch={handleSearch}
          placeholder="e.g. 'sunset over the ocean', 'person riding a bike'"
        />
        
        <div className="mt-4">
          <SearchHistory 
            history={searchHistory}
            onSelectHistory={handleSelectHistory}
            onClearHistory={handleClearHistory}
          />
        </div>

        <SearchFilters 
          scoreFilter={scoreFilter} onScoreChange={setScoreFilter}
          durationFilter={durationFilter} onDurationChange={setDurationFilter}
          dateFilter={dateFilter} onDateChange={setDateFilter}
          tags={availableTags}
          activeTags={activeTags}
          onToggleTag={handleToggleTag}
        />
      </div>

      {/* Results Area */}
      <div className="min-h-[400px]">
        {isLoading && <SearchSkeleton />}
        
        {!isLoading && error && (
          <SearchErrorState error={error} onRetry={() => handleSearch(searchQuery)} />
        )}
        
        {!isLoading && !error && hasSearched && results.length === 0 && (
          <SearchEmptyState />
        )}
        
        {!isLoading && !error && hasSearched && results.length > 0 && (
          <SearchResultList results={results} />
        )}

        {!hasSearched && (
          <div className="pt-12">
            <SearchEmptyState message="Enter a search term or apply filters to start exploring your media library." />
          </div>
        )}
      </div>
    </div>
  );
}
