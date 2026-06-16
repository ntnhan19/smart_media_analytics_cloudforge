import React, { useState } from 'react';
import PropTypes from 'prop-types';
import { useNavigate } from 'react-router-dom';
import { Image as ImageIcon, Video, Music } from 'lucide-react';
import { formatScore, formatTimestamp } from '../../utils/formatters';

export default function SearchResultCard({ result }) {
  const navigate = useNavigate();
  const [imgError, setImgError] = useState(false);

  const {
    asset_id,
    asset_name,
    media_type,
    score,
    tags,
    scene
  } = result;

  const {
    timestamp_start_sec,
    thumbnail_url,
    caption
  } = scene || {};

  const handleClick = () => {
    // Navigate with query param for timestamp according to contract
    if (timestamp_start_sec !== undefined && timestamp_start_sec !== null) {
      navigate(`/assets/${asset_id}?t=${timestamp_start_sec}`);
    } else {
      navigate(`/assets/${asset_id}`);
    }
  };

  const formattedScore = formatScore(score);
  const formattedTime = timestamp_start_sec !== undefined && timestamp_start_sec !== null
    ? formatTimestamp(timestamp_start_sec) 
    : null;

  // Determine fallback icon based on media_type
  let FallbackIcon = ImageIcon;
  if (media_type === 'video') FallbackIcon = Video;
  else if (media_type === 'audio') FallbackIcon = Music;

  return (
    <div 
      onClick={handleClick}
      className="group flex flex-col bg-gray-900 border border-gray-800 rounded-xl overflow-hidden hover:border-blue-500 hover:shadow-lg hover:shadow-blue-500/10 cursor-pointer transition-all duration-300 transform hover:-translate-y-1"
    >
      {/* Thumbnail Area */}
      <div className="relative aspect-video bg-gray-800 flex items-center justify-center overflow-hidden">
        {thumbnail_url && !imgError ? (
          <img 
            src={thumbnail_url} 
            alt={asset_name || 'Thumbnail'} 
            onError={() => setImgError(true)}
            className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
          />
        ) : (
          <div className="flex flex-col items-center justify-center text-gray-500 gap-2">
            <FallbackIcon className="w-10 h-10 opacity-50" />
            <span className="text-xs font-medium uppercase tracking-wider">{media_type || 'Media'}</span>
          </div>
        )}

        {/* Top badges */}
        <div className="absolute top-2 right-2 flex items-center gap-2">
          <div className="px-2 py-1 bg-black/60 backdrop-blur-sm rounded-md text-xs font-bold text-green-400 border border-green-500/30">
            {formattedScore} Match
          </div>
        </div>

        {/* Bottom badges */}
        <div className="absolute bottom-2 right-2 flex items-center gap-2">
          {formattedTime && (
            <div className="px-2 py-1 bg-black/60 backdrop-blur-sm rounded-md text-xs font-medium text-white">
              {formattedTime}
            </div>
          )}
        </div>
      </div>

      {/* Content Area */}
      <div className="p-4 flex flex-col flex-1">
        <h3 className="text-sm font-medium text-gray-100 line-clamp-2 mb-2 group-hover:text-blue-400 transition-colors" title={caption}>
          {caption || 'No caption available'}
        </h3>
        
        <div className="mt-auto pt-3 border-t border-gray-800/50 flex flex-col gap-2">
          <div className="flex items-center justify-between text-xs text-gray-400">
            <span className="truncate pr-2 font-medium" title={asset_name}>
              {asset_name || 'Unknown file'}
            </span>
          </div>
          
          {tags && tags.length > 0 && (
            <div className="flex items-center gap-1.5 overflow-x-auto no-scrollbar pb-1">
              {tags.slice(0, 3).map((tag, idx) => (
                <span key={idx} className="px-1.5 py-0.5 bg-gray-800/50 text-gray-400 rounded text-[10px] whitespace-nowrap">
                  #{tag}
                </span>
              ))}
              {tags.length > 3 && (
                <span className="text-[10px] text-gray-500">+{tags.length - 3}</span>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

SearchResultCard.propTypes = {
  result: PropTypes.shape({
    asset_id: PropTypes.string.isRequired,
    asset_name: PropTypes.string,
    media_type: PropTypes.string,
    thumbnail_url: PropTypes.string,
    score: PropTypes.number,
    timestamp_start_sec: PropTypes.number,
    caption: PropTypes.string,
    tags: PropTypes.arrayOf(PropTypes.string),
  }).isRequired,
};
