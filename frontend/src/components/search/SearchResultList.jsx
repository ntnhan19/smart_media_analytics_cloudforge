import PropTypes from 'prop-types';
import MediaCard from '../media/MediaCard';

export default function SearchResultList({ results }) {
  if (!results || results.length === 0) {
    return null;
  }

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-x-4 gap-y-5 py-4 auto-rows-fr">
      {results.map((result) => (
        <MediaCard 
          key={`${result.asset_id}-${result.scene?.timestamp_start_sec || 0}`} 
          asset_id={result.asset_id}
          file_name={result.asset_name}
          media_type={result.media_type}
          thumbnail_url={result.scene?.thumbnail_url || result.thumbnail_url}
          tags={result.tags}
          score={result.score}
          caption={result.scene?.caption}
          transcript_snippet={result.scene?.transcript_snippet}
          timestamp_start_sec={result.scene?.timestamp_start_sec}
        />
      ))}
    </div>
  );
}

SearchResultList.propTypes = {
  results: PropTypes.arrayOf(PropTypes.object).isRequired,
};
