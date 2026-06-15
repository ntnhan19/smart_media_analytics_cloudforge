import React from 'react';
import PropTypes from 'prop-types';
import SearchResultCard from './SearchResultCard';

export default function SearchResultList({ results }) {
  if (!results || results.length === 0) {
    return null;
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 py-6">
      {results.map((result) => (
        <SearchResultCard 
          key={`${result.asset_id}-${result.scene?.timestamp_start_sec || 0}`} 
          result={result} 
        />
      ))}
    </div>
  );
}

SearchResultList.propTypes = {
  results: PropTypes.arrayOf(PropTypes.object).isRequired,
};
