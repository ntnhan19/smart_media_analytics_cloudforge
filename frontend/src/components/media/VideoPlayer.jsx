import { useRef, useState, useEffect } from 'react';
import { Play, Pause, Volume2, VolumeX, Settings, Captions } from 'lucide-react';

export default function VideoPlayer({ src, seekTimestamp = 0, scenes = [], mediaType = 'video', onTimeUpdate, duration = 120, activeMarkers = [], onPlayStateChange }) {
  const [isPlaying, setIsPlaying] = useState(false);
  
  useEffect(() => {
    if (onPlayStateChange) onPlayStateChange(isPlaying);
  }, [isPlaying, onPlayStateChange]);
  const [currentTime, setCurrentTime] = useState(seekTimestamp);
  const [actualDuration, setActualDuration] = useState(duration);
  const [isMuted, setIsMuted] = useState(false);
  const [showCC, setShowCC] = useState(true);
  const [playbackRate, setPlaybackRate] = useState(1);
  const videoRef = useRef(null);
  
  // Update local state if parent changes seekTimestamp (e.g. from seek clicks)
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setCurrentTime(seekTimestamp);
    if (videoRef.current && videoRef.current.readyState >= 1) { // HAVE_METADATA or higher
      if (Math.abs(videoRef.current.currentTime - seekTimestamp) > 0.5) {
        videoRef.current.currentTime = seekTimestamp;
      }
    }
  }, [seekTimestamp]);

  const handleSeek = (e) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const percentage = x / rect.width;
    const newTime = percentage * actualDuration;
    
    setCurrentTime(newTime);
    if (videoRef.current) {
      videoRef.current.currentTime = newTime;
    }
    if (onTimeUpdate) {
      onTimeUpdate(newTime);
    }
  };

  const togglePlay = () => {
    if (videoRef.current) {
      if (isPlaying) {
        videoRef.current.pause();
      } else {
        videoRef.current.play();
      }
    }
    setIsPlaying(!isPlaying);
  };

  const handleNativeTimeUpdate = () => {
    if (videoRef.current) {
      const time = videoRef.current.currentTime;
      setCurrentTime(time);
      if (onTimeUpdate) onTimeUpdate(time);
    }
  };

  const handleLoadedMetadata = () => {
    if (videoRef.current) {
      setActualDuration(videoRef.current.duration);
      // Ensure we seek to seekTimestamp once metadata is loaded
      if (seekTimestamp > 0) {
        videoRef.current.currentTime = seekTimestamp;
        setCurrentTime(seekTimestamp);
      }
      videoRef.current.playbackRate = playbackRate;
    }
  };

  const toggleMute = () => {
    if (videoRef.current) {
      const nextMuted = !isMuted;
      videoRef.current.muted = nextMuted;
      setIsMuted(nextMuted);
    }
  };

  const toggleCC = () => {
    setShowCC(!showCC);
  };

  const toggleSpeed = () => {
    const nextRate = playbackRate === 1 ? 1.5 : playbackRate === 1.5 ? 2 : 1;
    setPlaybackRate(nextRate);
    if (videoRef.current) {
      videoRef.current.playbackRate = nextRate;
    }
  };

  const handleFullscreen = () => {
    if (videoRef.current) {
      if (videoRef.current.requestFullscreen) {
        videoRef.current.requestFullscreen();
      } else if (videoRef.current.webkitRequestFullscreen) { // Safari
        videoRef.current.webkitRequestFullscreen();
      }
    }
  };

  const playPrevScene = () => {
    if (scenes.length === 0) return;
    // Find the closest scene whose start time is before (currentTime - 1) seconds
    const marginTime = currentTime - 1;
    let targetTime = 0; // fallback to start
    
    for (let i = scenes.length - 1; i >= 0; i--) {
      const start = scenes[i].start_sec ?? scenes[i].timestamp_start_sec;
      if (start < marginTime) {
        targetTime = start;
        break;
      }
    }

    setCurrentTime(targetTime);
    if (videoRef.current) videoRef.current.currentTime = targetTime;
    if (onTimeUpdate) onTimeUpdate(targetTime);
  };

  const playNextScene = () => {
    if (scenes.length === 0) return;
    // Find the first scene whose start time is after (currentTime + 1) seconds
    const marginTime = currentTime + 1;
    let targetTime = null;
    
    for (let i = 0; i < scenes.length; i++) {
      const start = scenes[i].start_sec ?? scenes[i].timestamp_start_sec;
      if (start > marginTime) {
        targetTime = start;
        break;
      }
    }
    
    if (targetTime !== null) {
      setCurrentTime(targetTime);
      if (videoRef.current) videoRef.current.currentTime = targetTime;
      if (onTimeUpdate) onTimeUpdate(targetTime);
    }
  };

  // Keyboard shortcuts
  useEffect(() => {
    if (mediaType !== 'video') return;

    const handleKeyDown = (e) => {
      // Ignore if user is typing in an input
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;

      if (e.code === 'Space') {
        e.preventDefault();
        togglePlay();
      } else if (e.code === 'ArrowRight') {
        let jumpAmount = 10;
        if (actualDuration <= 30) {
          jumpAmount = 2;
        } else if (actualDuration <= 300) {
          jumpAmount = 5;
        }
        const newTime = Math.min(currentTime + jumpAmount, actualDuration);
        setCurrentTime(newTime);
        if (videoRef.current) videoRef.current.currentTime = newTime;
        if (onTimeUpdate) onTimeUpdate(newTime);
      } else if (e.code === 'ArrowLeft') {
        let jumpAmount = 10;
        if (actualDuration <= 30) {
          jumpAmount = 2;
        } else if (actualDuration <= 300) {
          jumpAmount = 5;
        }
        const newTime = Math.max(currentTime - jumpAmount, 0);
        setCurrentTime(newTime);
        if (videoRef.current) videoRef.current.currentTime = newTime;
        if (onTimeUpdate) onTimeUpdate(newTime);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isPlaying, currentTime, actualDuration, mediaType, onTimeUpdate]);

  if (mediaType === 'image') {
    return (
      <div className="w-full h-full bg-black flex items-center justify-center relative rounded-lg overflow-hidden border border-gray-800">
        <img src={src || 'https://placehold.co/1280x720/111/fff?text=Mock+Image'} alt="Mock" className="max-w-full max-h-full object-contain" />
      </div>
    );
  }

  // Support local real video playback if src is present (S3 presigned URLs have query params so endsWith doesn't work)
  const isRealVideo = Boolean(src && src.length > 0);

  return (
    <div className="w-full h-full bg-black rounded-lg overflow-hidden border border-gray-800 relative flex flex-col">
      {/* Video Area */}
      <div className="flex-1 flex flex-col items-center justify-center relative cursor-pointer overflow-hidden bg-black" onClick={togglePlay}>
        
        {isRealVideo ? (
          <video 
            id="main-video-player"
            ref={videoRef}
            src={src}
            crossOrigin="anonymous"
            className="w-full h-full object-contain"
            onTimeUpdate={handleNativeTimeUpdate}
            onLoadedMetadata={handleLoadedMetadata}
            onEnded={() => setIsPlaying(false)}
            onClick={(e) => { e.stopPropagation(); togglePlay(); }}
          />
        ) : (
          <div className="w-full h-full relative">
            <img
              src="https://images.unsplash.com/photo-1520942702018-0862200e6873?w=1280&q=80"
              alt="Mock video frame"
              className="w-full h-full object-cover"
            />
          </div>
        )}
        
      {/* Active scene overlay */}
        {showCC && (() => {
          const activeScene = scenes.find(s => currentTime >= (s.start_sec ?? s.timestamp_start_sec) && currentTime < (s.end_sec ?? s.timestamp_end_sec));
          return activeScene ? (
            <div className="absolute top-[10px] left-[10px] z-20 flex items-center gap-2 bg-black/60 backdrop-blur-sm rounded-[4px] px-[10px] py-[5px]">
              <div className="w-2 h-2 rounded-full bg-[#7B5CF5] animate-pulse" />
              <span className="font-inter font-normal text-[11px] text-white/90 max-w-[240px] truncate">
                {activeScene.description || activeScene.caption}
              </span>
            </div>
          ) : null;
        })()}

        {/* Play/Pause Overlay */}
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          {!isPlaying && (
            <div className="w-16 h-16 bg-white/20 rounded-full flex items-center justify-center backdrop-blur-md border border-white/10 shadow-xl">
              <Play className="w-8 h-8 text-white ml-1" fill="currentColor" />
            </div>
          )}
        </div>
      </div>

      {/* Controls Bar */}
      <div className="relative z-20 h-[56px] bg-[#16132A]/90 border-t border-gray-800/50 px-3 flex items-center gap-2 flex-shrink-0">
        {/* Progress track - full width on top */}
        <div className="absolute left-0 right-0 bottom-[56px] px-3 h-[4px] cursor-pointer" onClick={handleSeek}>
          <div className="w-full h-full bg-gray-700 rounded-full relative">
            <div 
              className="absolute top-0 left-0 h-full bg-[#7B5CF5] rounded-full"
              style={{ width: `${(currentTime / actualDuration) * 100}%` }}
            />
          </div>
        </div>

        {/* Play/Pause */}
        <button onClick={togglePlay} className="text-white hover:text-gray-200 focus:outline-none flex-shrink-0">
          {isPlaying ? <Pause size={18} fill="currentColor" /> : <Play size={18} fill="currentColor" />}
        </button>

        {/* Prev */}
        <button onClick={playPrevScene} className="text-white/80 hover:text-white focus:outline-none flex-shrink-0" title="Previous scene">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
            <path d="M6 6h2v12H6zm3.5 6l8.5 6V6z"/>
          </svg>
        </button>

        {/* Next */}
        <button onClick={playNextScene} className="text-white/80 hover:text-white focus:outline-none flex-shrink-0" title="Next scene">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
            <path d="M6 18l8.5-6L6 6v12zm2.5-6l5.5 4V8L8.5 12zm7-6h2v12h-2z"/>
          </svg>
        </button>

        {/* Volume */}
        <button onClick={toggleMute} className="text-white/80 hover:text-white focus:outline-none flex-shrink-0" title={isMuted ? "Unmute" : "Mute"}>
          {isMuted ? (
            <VolumeX size={18} />
          ) : (
            <Volume2 size={18} />
          )}
        </button>

        {/* Time */}
        <div className="text-xs text-gray-400 font-mono ml-1 flex-shrink-0">
          {Math.floor(currentTime)}s / {Math.floor(actualDuration)}s
        </div>

        {/* Spacer */}
        <div className="flex-1" />

        {/* Seek bar (clickable area in between) */}
        <div className="flex-1 h-[4px] cursor-pointer rounded-full bg-gray-700 relative mx-2" onClick={handleSeek}>
          <div 
            className="absolute top-0 left-0 h-full bg-[#7B5CF5] rounded-full"
            style={{ width: `${(currentTime / actualDuration) * 100}%` }}
          />
          {scenes.map((scene, idx) => (
            <div 
              key={scene.id || scene.scene_id || idx}
              className="absolute top-1/2 -translate-y-1/2 w-1 h-2.5 bg-purple-400/50 rounded-sm"
              style={{ left: `${((scene.start_sec ?? scene.timestamp_start_sec) / actualDuration) * 100}%`, transform: 'translate(-50%, -50%)' }}
              title={`Scene at ${(scene.start_sec ?? scene.timestamp_start_sec)}s`}
            />
          ))}
          {/* Active markers for object occurrences */}
          {activeMarkers.map((marker, idx) => (
            <div 
              key={`marker-${idx}`}
              className="absolute top-1/2 -translate-y-1/2 w-2.5 h-2.5 bg-[#a78bfa] rounded-full border border-[#7B5CF5] shadow-[0_0_6px_#7B5CF5] z-10"
              style={{ left: `${(marker.timestamp_start_sec / actualDuration) * 100}%`, transform: 'translate(-50%, -50%)' }}
              title={`Object at ${marker.timestamp_start_sec}s`}
            />
          ))}
        </div>

        {/* CC */}
        <button onClick={toggleCC} className={`focus:outline-none flex-shrink-0 transition-colors ${showCC ? 'text-[#7B5CF5]' : 'text-white/85 hover:text-white'}`} title="Toggle Captions">
          <Captions size={18} />
        </button>

        {/* Settings / Playback Speed */}
        <button onClick={toggleSpeed} className="text-white/80 hover:text-white focus:outline-none flex-shrink-0 flex items-center gap-1 font-mono text-[10px] font-bold" title="Playback Speed">
          <Settings size={16} />
          <span>{playbackRate}x</span>
        </button>

        {/* Fullscreen */}
        <button onClick={handleFullscreen} className="text-white/80 hover:text-white focus:outline-none flex-shrink-0" title="Fullscreen">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polyline points="15 3 21 3 21 9"/>
            <polyline points="9 21 3 21 3 15"/>
            <line x1="21" y1="3" x2="14" y2="10"/>
            <line x1="3" y1="21" x2="10" y2="14"/>
          </svg>
        </button>
      </div>
    </div>
  );
}
