import PropTypes from 'prop-types';
import { useNavigate } from 'react-router-dom';

export default function MediaCard({
  asset_id,
  file_name,
  media_type,
  thumbnail_url,
  duration_sec,
  resolution,
  file_size_bytes,
  ingested_at,
  tags
}) {
  const navigate = useNavigate();

  const handleCardClick = () => {
    navigate(`/assets/${asset_id}`);
  };

  return (
    <div
      className="w-full max-w-[218px] h-[230px] rounded-[6px] border border-sma-purple overflow-hidden cursor-pointer hover:border-sma-purple/80 bg-sma-surface flex flex-col relative mx-auto"
      onClick={handleCardClick}
    >
      <div className="w-full h-[157px] bg-gray-900 flex-shrink-0 relative">
        {thumbnail_url ? (
          <img
            src={thumbnail_url}
            alt={file_name}
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-gray-500 text-xs">
            {media_type.toUpperCase()}
          </div>
        )}
        
        {/* Overlay text for resolution and format */}
        <div className="absolute top-[8px] left-[12px] text-black font-inter text-[15px] drop-shadow-md">
          {resolution && <span>{resolution} </span>}
          <span>{media_type === 'video' ? 'MP4' : media_type === 'image' ? 'JPG' : 'MP3'}</span>
        </div>
      </div>

      <div className="px-[12px] pt-[12px] flex-1 flex flex-col items-center">
        <h3 className="text-[14px] leading-[18px] text-white truncate font-inter w-full text-center" title={file_name}>
          {file_name}
        </h3>
        
        <div className="mt-auto pb-[14px] flex flex-wrap gap-[6px] items-center justify-center w-full">
          {/* User Tags */}
          {tags && tags.slice(0, 3).map(tag => (
            <div key={tag} className="px-[8px] py-[2px] border border-sma-purple rounded-[4px] flex items-center justify-center">
              <span className="text-[12px] leading-[14px] text-white font-inter">{tag}</span>
            </div>
          ))}
          {/* +N Tag */}
          {tags && tags.length > 3 && (
            <div className="px-[8px] py-[2px] border border-sma-purple rounded-[4px] flex items-center justify-center">
              <span className="text-[12px] leading-[14px] text-white font-inter">+{tags.length - 3}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

MediaCard.propTypes = {
  asset_id: PropTypes.string.isRequired,
  file_name: PropTypes.string.isRequired,
  media_type: PropTypes.oneOf(['video', 'image', 'audio']).isRequired,
  thumbnail_url: PropTypes.string,
  duration_sec: PropTypes.number,
  resolution: PropTypes.string,
  file_size_bytes: PropTypes.number,
  ingested_at: PropTypes.string,
  tags: PropTypes.arrayOf(PropTypes.string),
};
