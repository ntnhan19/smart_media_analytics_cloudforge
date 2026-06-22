import PropTypes from 'prop-types';
import { useNavigate } from 'react-router-dom';
import { useState } from 'react';
import { Icon } from "@iconify/react";

export default function HeaderBar({ 
  title = "SWEDEN'S TRIP.mp4", 
  showShare = true, 
  showBookmark = true,
  downloadUrl = "/uploads/sweden_trip_2024.mp4"
}) {
  const navigate = useNavigate();
  const [isBookmarked, setIsBookmarked] = useState(false);

  const handleBookmark = () => {
    const newState = !isBookmarked;
    setIsBookmarked(newState);
    if (newState) {
      alert("Đã thêm vào yêu thích!");
    }
  };

  const handleShare = async () => {
    try {
      await navigator.clipboard.writeText(window.location.href);
      alert("Đã copy link để chia sẻ!");
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
    <div className="absolute w-[891px] h-[40px] bg-transparent top-0 left-0 z-10">
      {/* Back Arrow */}
      <button 
        onClick={() => navigate(-1)}
        className="absolute left-[0px] top-[0px] w-[40px] h-[40px] flex items-center justify-center hover:opacity-80 transition-opacity"
      >
        <Icon icon="icons8:arrows-long-left" width="24" height="24" className="text-white" />
      </button>

      {/* Title */}
      <div className="absolute left-[51px] top-[11px] w-[152px] h-[20px] flex items-center">
        <h1 className="font-inter font-normal text-[14px] leading-[17px] text-white m-0 truncate">
          {title}
        </h1>
      </div>

      {/* Icons */}
      {showBookmark && (
        <button 
          onClick={handleBookmark}
          className="absolute left-[764px] top-[12px] w-[24px] h-[24px] flex items-center justify-center hover:opacity-80 transition-opacity"
          title="Bookmark"
        >
          <Icon icon={isBookmarked ? "fluent-emoji-flat:star" : "fluent-emoji-flat:star"} width="20" height="20" className={!isBookmarked ? "grayscale opacity-70" : ""} />
        </button>
      )}
      
      {showShare && (
        <button 
          onClick={handleShare}
          className="absolute left-[815px] top-[12px] w-[24px] h-[24px] flex items-center justify-center hover:opacity-80 transition-opacity" 
          title="Share"
        >
          <Icon icon="material-symbols:share-outline" width="20" height="20" className="text-white" />
        </button>
      )}

      <button 
        onClick={handleDownload}
        className="absolute left-[867px] top-[12px] w-[24px] h-[24px] flex items-center justify-center hover:opacity-80 transition-opacity"
        title="Download video"
      >
        <Icon icon="circum:circle-more" width="20" height="20" className="text-white -rotate-90" />
      </button>
    </div>
  );
}

HeaderBar.propTypes = {
  title: PropTypes.string.isRequired,
  timestamp: PropTypes.string,
  showShare: PropTypes.bool,
  showBookmark: PropTypes.bool,
};
