import PropTypes from 'prop-types';
import { useNavigate } from 'react-router-dom';
import { useState } from 'react';
import { Icon } from "@iconify/react";

export default function HeaderBar({ 
  title = "SWEDEN'S TRIP.mp4", 
  showShare = true, 
  showBookmark = true,
  isFavorite = undefined,
  onToggleFavorite = undefined,
  downloadUrl = "/uploads/sweden_trip_2024.mp4",
  currentTime = 0
}) {
  const navigate = useNavigate();
  const [isBookmarked, setIsBookmarked] = useState(false);
  const [showToast, setShowToast] = useState(false);

  const currentFavoriteStatus = isFavorite !== undefined ? isFavorite : isBookmarked;

  const handleBookmark = () => {
    if (onToggleFavorite) {
      onToggleFavorite(!currentFavoriteStatus);
    } else {
      setIsBookmarked(!isBookmarked);
    }
  };

  const handleShare = async () => {
    try {
      const url = new URL(window.location.href);
      url.searchParams.set('t', Math.floor(currentTime));
      await navigator.clipboard.writeText(url.toString());
      setShowToast(true);
      setTimeout(() => setShowToast(false), 3000);
    } catch (err) {
      console.error('Failed to copy link: ', err);
    }
  };

  const handleDownload = () => {
    const a = document.createElement('a');
    a.href = downloadUrl;
    a.download = title;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  return (
    <div className="w-full h-[40px] bg-transparent flex items-center justify-between z-10">
      <div className="flex items-center">
        {/* Back Arrow */}
        <button 
          onClick={() => navigate(-1)}
          className="w-[40px] h-[40px] flex items-center justify-center hover:opacity-80 transition-opacity -ml-[8px]"
        >
          <Icon icon="icons8:arrows-long-left" width="24" height="24" className="text-white" />
        </button>

        {/* Title */}
        <h1 className="font-inter font-normal text-[14px] leading-[17px] text-white m-0 truncate max-w-[300px] ml-[3px]">
          {title}
        </h1>
      </div>

      {/* Icons */}
      <div className="flex items-center space-x-6 pr-2 relative">
        {showToast && (
          <div className="absolute top-[35px] right-2 bg-[#7B5CF5] text-white px-3 py-1.5 rounded-[4px] shadow-[0_4px_12px_rgba(0,0,0,0.5)] text-[12px] font-inter font-medium whitespace-nowrap animate-fade-in-down z-50">
            Copied link with timestamp!
          </div>
        )}
        
        {showBookmark && (
          <button 
            onClick={handleBookmark}
            className="w-[24px] h-[24px] flex items-center justify-center hover:opacity-80 transition-opacity"
            title="Bookmark"
          >
            <Icon icon={currentFavoriteStatus ? "fluent-emoji-flat:star" : "fluent-emoji-flat:star"} width="20" height="20" className={!currentFavoriteStatus ? "grayscale opacity-70" : ""} />
          </button>
        )}
        
        {showShare && (
          <button 
            onClick={handleShare}
            className="w-[24px] h-[24px] flex items-center justify-center hover:opacity-80 transition-opacity" 
            title="Share"
          >
            <Icon icon="material-symbols:share-outline" width="20" height="20" className="text-white" />
          </button>
        )}

        <button 
          onClick={handleDownload}
          className="w-[24px] h-[24px] flex items-center justify-center hover:opacity-80 transition-opacity"
          title="Download video"
        >
          <Icon icon="circum:circle-more" width="20" height="20" className="text-white -rotate-90" />
        </button>
      </div>
    </div>
  );
}

HeaderBar.propTypes = {
  title: PropTypes.string.isRequired,
  timestamp: PropTypes.string,
  showShare: PropTypes.bool,
  showBookmark: PropTypes.bool,
};
