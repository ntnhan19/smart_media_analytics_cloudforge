import { useState } from 'react';
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
      className="w-full h-full min-h-[160px] max-h-[280px] rounded-[8px] border border-gray-200 dark:border-sma-purple overflow-hidden cursor-pointer hover:border-[#7B5CF5] dark:hover:border-sma-purple/80 hover:shadow-[0_8px_24px_rgba(123,92,245,0.12)] bg-white dark:bg-sma-surface flex flex-col relative group shadow-[0_2px_8px_rgba(0,0,0,0.06)] dark:shadow-none transition-all duration-300"
    >
      {/* Thumbnail Area */}
      <div className="w-full flex-1 bg-gray-100 dark:bg-gray-900 relative group overflow-hidden">
        {thumbnail_url && !imgError ? (
          <img 
            src={thumbnail_url} 
            alt={asset_name || 'Thumbnail'} 
            onError={() => setImgError(true)}
            className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
          />
        ) : (
          <div className="absolute inset-0 w-full h-full flex flex-col items-center justify-center text-gray-400 dark:text-gray-500 gap-2 transition-colors">
            <FallbackIcon className="w-8 h-8 opacity-50" />
            <span className="text-[10px] font-bold uppercase tracking-wider">{media_type || 'Media'}</span>
          </div>
        )}

        {/* Top badge: Match Score */}
        <div className="absolute top-[8px] right-[12px] px-2 py-1 bg-green-500/90 rounded text-[10px] font-bold text-white shadow-md z-10">
          {formattedScore} Match
        </div>

        {/* Overlay text for Format */}
        <div className="absolute top-[8px] left-[12px] text-white font-inter text-[13px] drop-shadow-md z-10 flex flex-row items-center gap-1.5 font-medium shadow-black">
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
      <div className="px-3 py-2 shrink-0 flex flex-col items-center w-full gap-1 h-[64px] bg-white dark:bg-sma-surface border-t border-gray-200/60 dark:border-[#2D2844] transition-colors">
        <h3 className="text-[12px] leading-tight text-gray-900 dark:text-white truncate font-inter w-full text-center shrink-0 transition-colors" title={caption || asset_name}>
          {caption || asset_name}
        </h3>
        
        {transcript_snippet ? (
          <p className="text-[10px] leading-[14px] text-gray-500 dark:text-gray-400 font-inter line-clamp-2 w-full text-center italic transition-colors" title={transcript_snippet}>
            "{transcript_snippet}"
          </p>
        ) : (
          <div className="flex flex-nowrap overflow-hidden gap-1 items-center justify-center w-full min-h-0 pt-0.5">
            {tags && tags.slice(0, 3).map((tag, idx) => {
              const tagText = typeof tag === 'object' && tag !== null ? tag.name : tag;
              const formattedTag = tagText ? tagText.replace(/_/g, ' ') : '';
              return (
                <div key={idx} className="px-1.5 py-[1px] border border-sma-purple/20 dark:border-sma-purple rounded flex items-center justify-center bg-sma-purple/5 dark:bg-sma-purple/10 flex-shrink-1 min-w-0 transition-colors" title={formattedTag}>
                  <span className="text-[10px] leading-tight text-sma-purple dark:text-white font-inter whitespace-nowrap overflow-hidden text-ellipsis block max-w-[50px] transition-colors">{formattedTag}</span>
                </div>
              );
            })}
            {tags && tags.length > 3 && (
              <div className="px-1.5 py-[1px] border border-sma-purple/20 dark:border-sma-purple rounded flex items-center justify-center bg-sma-purple/5 dark:bg-sma-purple/10 flex-shrink-0 transition-colors">
                <span className="text-[10px] leading-tight text-sma-purple dark:text-white font-inter whitespace-nowrap transition-colors">+{tags.length - 3}</span>
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
