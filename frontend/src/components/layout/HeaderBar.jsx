import PropTypes from 'prop-types';
import { useNavigate } from 'react-router-dom';
import { useState } from 'react';
import { Icon } from "@iconify/react";

export default function HeaderBar({ 
  title = "SWEDEN'S TRIP.mp4", 
  showShare = true, 
  showBookmark = true 
}) {
  const navigate = useNavigate();
  const [isBookmarked, setIsBookmarked] = useState(false);

  return (
    <header className="h-[40px] px-[12px] flex items-center justify-between bg-[#16132A] text-white">
      <div className="flex items-center gap-[11px]">
        <button 
          onClick={() => navigate(-1)}
          className="flex items-center justify-center hover:opacity-80 transition-opacity"
        >
          <Icon icon="icons8:arrows-long-left" width="40" height="40" className="text-white" />
        </button>
        <h1 className="font-inter font-normal text-[14px] leading-[17px] text-white">
          {title}
        </h1>
      </div>

      <div className="flex items-center gap-[28px] pr-[12px]">
        {showBookmark && (
          <button 
            onClick={() => setIsBookmarked(!isBookmarked)}
            className="flex items-center justify-center hover:opacity-80 transition-opacity"
            title="Bookmark"
          >
            <Icon icon="fluent-emoji-flat:star" width="24" height="24" />
          </button>
        )}
        
        {showShare && (
          <button 
            className="flex items-center justify-center hover:opacity-80 transition-opacity" 
            title="Share"
          >
            <Icon icon="material-symbols:share-outline" width="24" height="24" className="text-white" />
          </button>
        )}

        <button 
          className="flex items-center justify-center hover:opacity-80 transition-opacity"
          title="More options"
        >
          <Icon icon="circum:circle-more" width="24" height="24" className="text-white -rotate-90" />
        </button>
      </div>
    </header>
  );
}

HeaderBar.propTypes = {
  title: PropTypes.string.isRequired,
  timestamp: PropTypes.string,
  showShare: PropTypes.bool,
  showBookmark: PropTypes.bool,
};
