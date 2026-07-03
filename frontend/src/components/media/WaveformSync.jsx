import { useRef, useEffect, useState } from 'react';
import WaveSurfer from 'wavesurfer.js';
import { Play, Pause, AudioLines } from 'lucide-react';

export default function WaveformSync({ streamUrl, currentTime, onSeek, isPlaying, onTogglePlay }) {
  const containerRef = useRef(null);
  const wavesurfer = useRef(null);
  const isUserInteracting = useRef(false);
  const [isReady, setIsReady] = useState(false);
  const [hasError, setHasError] = useState(false);

  useEffect(() => {
    if (!containerRef.current) return;

    setIsReady(false);
    setHasError(false);

    // Destroy previous instance
    if (wavesurfer.current) {
      wavesurfer.current.destroy();
      wavesurfer.current = null;
    }

    if (!streamUrl) return;

    wavesurfer.current = WaveSurfer.create({
      container: containerRef.current,
      waveColor: 'rgba(196, 181, 253, 0.7)',
      progressColor: '#7B5CF5',
      cursorColor: 'rgba(255, 255, 255, 0.8)',
      barWidth: 3,
      barGap: 2,
      barRadius: 3,
      height: 36,
      interact: true,
      normalize: true,
      // Do NOT use media: element to avoid blob URL errors
      // Instead load directly and mute WaveSurfer's audio output
      backend: 'WebAudio',
    });

    // Mute wavesurfer completely — video player handles audio
    wavesurfer.current.setVolume(0);
    wavesurfer.current.setMuted(true);

    wavesurfer.current.on('ready', () => {
      setIsReady(true);
    });

    wavesurfer.current.on('error', (err) => {
      // Ignore AbortError - it's expected when component unmounts during load
      if (err?.name === 'AbortError' || String(err).includes('abort')) return;
      console.warn('WaveSurfer error:', err);
      setHasError(true);
    });

    // Seek video when user clicks waveform
    wavesurfer.current.on('seek', (progress) => {
      if (isUserInteracting.current && onSeek) {
        const duration = wavesurfer.current.getDuration();
        onSeek(progress * duration);
      }
    });

    try {
      wavesurfer.current.load(streamUrl);
    } catch (err) {
      if (err?.name !== 'AbortError') {
        console.warn('WaveSurfer load error:', err);
        // eslint-disable-next-line react-hooks/set-state-in-effect
        setHasError(true);
      }
    }


    return () => {
      if (wavesurfer.current) {
        wavesurfer.current.destroy();
        wavesurfer.current = null;
      }
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [streamUrl]);

  // Sync waveform playhead to video currentTime (without controlling audio)
  useEffect(() => {
    if (!wavesurfer.current || !isReady) return;
    const duration = wavesurfer.current.getDuration();
    if (duration > 0) {
      const diff = Math.abs(wavesurfer.current.getCurrentTime() - currentTime);
      if (diff > 0.3 && !isUserInteracting.current) {
        wavesurfer.current.seekTo(currentTime / duration);
      }
    }
  }, [currentTime, isReady]);

  const handleTogglePlay = () => {
    const mediaEl = document.getElementById('main-video-player');
    if (mediaEl) {
      if (mediaEl.paused) mediaEl.play();
      else mediaEl.pause();
    } else if (onTogglePlay) {
      onTogglePlay();
    }
  };

  return (
    <div className="w-full h-[56px] bg-[#0E0B1F] border border-[#1e1b35] rounded-[6px] px-[12px] flex items-center gap-[12px] shrink-0">
      {/* Play/Pause button */}
      <button
        onClick={handleTogglePlay}
        className="w-[30px] h-[30px] rounded-full bg-white text-[#0E0B1F] flex items-center justify-center hover:bg-gray-200 transition-colors shrink-0"
      >
        {isPlaying ? <Pause size={12} fill="currentColor" /> : <Play size={12} fill="currentColor" className="ml-[1px]" />}
      </button>

      {/* Waveform area */}
      <div className="flex-1 relative h-[36px]">
        {/* Loading placeholder */}
        {!isReady && !hasError && streamUrl && (
          <div className="absolute inset-0 flex items-center justify-center gap-2">
            <div className="flex items-end gap-[3px] h-full py-[4px]">
              {[...Array(32)].map((_, i) => (
                <div
                  key={i}
                  className="bg-white/20 rounded-full animate-pulse"
                  style={{
                    width: 3,
                    height: `${20 + Math.sin(i * 0.8) * 14}px`,
                    animationDelay: `${i * 30}ms`,
                  }}
                />
              ))}
            </div>
          </div>
        )}

        {/* No stream URL fallback */}
        {!streamUrl && (
          <div className="absolute inset-0 flex items-center gap-2 text-white/30">
            <AudioLines size={14} />
            <span className="text-[11px] font-inter">No audio stream available</span>
          </div>
        )}

        {/* Error fallback */}
        {hasError && (
          <div className="absolute inset-0 flex items-center gap-2 text-white/30">
            <AudioLines size={14} />
            <span className="text-[11px] font-inter">Waveform unavailable</span>
          </div>
        )}

        {/* WaveSurfer container */}
        <div
          ref={containerRef}
          className={`w-full h-full transition-opacity duration-300 ${isReady ? 'opacity-100' : 'opacity-0'}`}
          onMouseDown={() => { isUserInteracting.current = true; }}
          onMouseUp={() => { isUserInteracting.current = false; }}
          onMouseLeave={() => { isUserInteracting.current = false; }}
        />
      </div>
    </div>
  );
}
