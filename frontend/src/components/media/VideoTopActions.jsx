import { Star, Share2, Info } from 'lucide-react';

export default function VideoTopActions({ isFavourited, onFavourite, onShare, onInfo }) {
  return (
    <div className="absolute top-4 right-4 flex gap-2 z-10">
      <button 
        onClick={onFavourite}
        className="w-10 h-10 rounded-full bg-black/50 backdrop-blur-md flex items-center justify-center text-white hover:bg-black/70 transition-colors border border-white/10"
        title="Favorite"
      >
        <Star size={18} className={isFavourited ? "text-yellow-400" : ""} fill={isFavourited ? "currentColor" : "none"} />
      </button>
      <button 
        onClick={onShare}
        className="w-10 h-10 rounded-full bg-black/50 backdrop-blur-md flex items-center justify-center text-white hover:bg-black/70 transition-colors border border-white/10"
        title="Share"
      >
        <Share2 size={18} />
      </button>
      <button 
        onClick={onInfo}
        className="w-10 h-10 rounded-full bg-black/50 backdrop-blur-md flex items-center justify-center text-white hover:bg-black/70 transition-colors border border-white/10"
        title="Info"
      >
        <Info size={18} />
      </button>
    </div>
  );
}
