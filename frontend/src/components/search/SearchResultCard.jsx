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
    caption,
    transcript_snippet
  } = scene || {};

  const handleClick = (e) => {
    if (e.target.closest('.no-navigate')) return;
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
      className="w-full max-w-[218px] h-[240px] rounded-[6px] border border-sma-purple overflow-hidden cursor-pointer hover:border-sma-purple/80 bg-sma-surface flex flex-col relative group"
    >
      {/* Thumbnail Area */}
      <div className="w-full h-[157px] bg-gray-900 flex-shrink-0 relative">
        {thumbnail_url && !imgError ? (
          <img 
            src={thumbnail_url} 
            alt={asset_name || 'Thumbnail'} 
            onError={() => setImgError(true)}
            className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
          />
        ) : (
          <div className="w-full h-full flex flex-col items-center justify-center text-gray-500 gap-2">
            <FallbackIcon className="w-10 h-10 opacity-50" />
            <span className="text-[10px] font-bold uppercase tracking-wider">{media_type || 'Media'}</span>
          </div>
        )}

        {/* Top badge: Match Score */}
        <div className="absolute top-[8px] right-[12px] px-2 py-1 bg-green-500/90 rounded text-[10px] font-bold text-white shadow-md z-10 border border-green-400">
          {formattedScore} Match
        </div>

        {/* Overlay text for Format */}
        <div className="absolute top-[8px] left-[12px] text-white font-inter text-[15px] drop-shadow-md z-10 flex flex-row items-center gap-1.5 font-medium shadow-black">
          <span style={{textShadow: "1px 1px 2px black"}}>{media_type === 'video' ? 'MP4' : media_type === 'image' ? 'JPG' : 'MP3'}</span>
        </div>

        {/* Bottom badge: Timestamp */}
        {formattedTime && (
          <div className="absolute bottom-[8px] right-[12px] bg-black/60 px-1.5 py-0.5 rounded text-white text-[11px] font-inter z-10">
            {formattedTime}
          </div>
        )}
      </div>

      {/* Content Area */}
      <div className="px-[12px] pt-[12px] flex-1 flex flex-col items-center">
        <h3 className="text-[14px] leading-[18px] text-white truncate font-inter w-full text-center" title={caption || asset_name}>
          {caption || asset_name}
        </h3>
        
        {transcript_snippet ? (
          <p className="text-[11px] leading-[14px] text-[#A1A1AA] font-inter line-clamp-2 w-full text-center mt-1 italic" title={transcript_snippet}>
            "{transcript_snippet}"
          </p>
        ) : (
          <div className="mt-auto pb-[12px] flex flex-wrap gap-[6px] items-center justify-center w-full pt-1">
            {tags && tags.slice(0, 3).map((tag, idx) => {
              const tagText = typeof tag === 'object' && tag !== null ? tag.name : tag;
              return (
                <div key={idx} className="px-[8px] py-[2px] border border-sma-purple rounded-[4px] flex items-center justify-center bg-sma-purple/10">
                  <span className="text-[12px] leading-[14px] text-white font-inter truncate max-w-[60px]">{tagText}</span>
                </div>
              );
            })}
            {tags && tags.length > 3 && (
              <div className="px-[8px] py-[2px] border border-sma-purple rounded-[4px] flex items-center justify-center bg-sma-purple/10">
                <span className="text-[12px] leading-[14px] text-white font-inter">+{tags.length - 3}</span>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

SearchResultCard.propTypes = {
  result: PropTypes.shape({
    asset_id: PropTypes.string.isRequired,
    asset_name: PropTypes.string,
    media_type: PropTypes.string,
    score: PropTypes.number,
    tags: PropTypes.arrayOf(PropTypes.any),
    scene: PropTypes.shape({
      timestamp_start_sec: PropTypes.number,
      thumbnail_url: PropTypes.string,
      caption: PropTypes.string,
      transcript_snippet: PropTypes.string,
    }),
  }).isRequired,
};
