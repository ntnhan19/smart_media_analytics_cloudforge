import { useState } from 'react';
import PropTypes from 'prop-types';
import { useNavigate } from 'react-router-dom';
import { useQueryClient } from '@tanstack/react-query';
import { Icon } from '@iconify/react';
import { useJobs } from '../../contexts/JobContext';
import { deleteAsset, reingestAsset } from '../../services/api';

const formatDuration = (seconds) => {
  if (!seconds) return '00:00';
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
};

const StatusBadge = ({ status }) => {
  if (!status || status === 'ready' || status === 'completed') return null;

  const colors = {
    queued: 'bg-gray-500',
    processing: 'bg-sma-purple',
    failed: 'bg-red-500'
  };

  const bgClass = colors[status] || 'bg-gray-500';
  return (
    <div className={`absolute top-[8px] right-[12px] px-2 py-1 rounded text-[10px] font-bold text-white uppercase ${bgClass} z-10 shadow-md`}>
      {status}
    </div>
  );
};

StatusBadge.propTypes = {
  status: PropTypes.string
};

export default function MediaCard({
  asset_id,
  file_name,
  media_type,
  thumbnail_url,
  duration,
  duration_sec,
  resolution,
  tags,
  status = 'ready',
  is_favorite = false,
  showToast,
  // Semantic Search Props
  score,
  caption,
  transcript_snippet,
  timestamp_start_sec,
  selected = false,
  onSelectToggle,
  isSelectMode = false
}) {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { activeJobs } = useJobs();
  const [showConfirm, setShowConfirm] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [isReingesting, setIsReingesting] = useState(false);
  const [showMenu, setShowMenu] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  
  // Selection Props
  const selectable = !!onSelectToggle;
  const handleCheckboxClick = (e) => {
    e.stopPropagation();
    if (onSelectToggle) {
      onSelectToggle(asset_id, !selected);
    }
  };

  const actualDuration = duration !== undefined ? duration : duration_sec;
  const timeToShow = timestamp_start_sec !== undefined ? timestamp_start_sec : actualDuration;

  // Find job in context if processing
  const job = activeJobs.find(j => j.asset_id === asset_id && (j.status === 'processing' || j.status === 'queued'));
  const displayProgress = job ? job.progress : (status === 'completed' ? 100 : 0);

  const handleCardClick = (e) => {
    if (e.target.closest('.no-navigate')) return;
    if (timestamp_start_sec !== undefined && timestamp_start_sec !== null) {
      navigate(`/assets/${asset_id}?t=${Math.floor(timestamp_start_sec)}`);
    } else {
      navigate(`/assets/${asset_id}`);
    }
  };

  const handleDelete = async (e) => {
    e.stopPropagation();
    setIsDeleting(true);
    setErrorMsg('');
    try {
      await deleteAsset(asset_id);
      if (showToast) showToast('Video deleted successfully', 'success');

      // Update local storage deleted count for UI display
      const currentCount = parseInt(localStorage.getItem('deletedAssetsCount') || '0', 10);
      localStorage.setItem('deletedAssetsCount', (currentCount + 1).toString());
      window.dispatchEvent(new Event('assetDeleted'));

      queryClient.invalidateQueries({ queryKey: ['assets'] });
    } catch (err) {
      const msg = err.response?.data?.detail || 'Failed to delete video';
      setErrorMsg(msg);
      if (showToast) showToast(msg, 'error');
    } finally {
      setIsDeleting(false);
      setShowConfirm(false);
    }
  };

  const handleReingest = async (e) => {
    e.stopPropagation();
    setIsReingesting(true);
    try {
      await reingestAsset(asset_id);
      if (showToast) showToast('Reingestion requested', 'success');
      // Trigger a refresh
      queryClient.invalidateQueries({ queryKey: ['assets'] });
    } catch (err) {
      if (showToast) showToast('Failed to reingest video', 'error');
    } finally {
      setIsReingesting(false);
    }
  };

  const isProcessing = status === 'processing' || status === 'queued';

  return (
    <div
      className={`w-full h-full min-h-[160px] max-h-[280px] rounded-[8px] border overflow-hidden cursor-pointer flex flex-col relative group transition-all duration-300 ${selected ? 'border-sma-purple shadow-[0_8px_24px_rgba(123,92,245,0.2)] bg-sma-purple/5' : 'border-gray-200 dark:border-sma-purple hover:border-[#7B5CF5] dark:hover:border-sma-purple/80 hover:shadow-[0_8px_24px_rgba(123,92,245,0.12)] bg-white dark:bg-sma-surface shadow-[0_2px_8px_rgba(0,0,0,0.06)] dark:shadow-none'}`}
      onClick={handleCardClick}
    >
      <div className="w-full flex-1 bg-gray-100 dark:bg-gray-900 relative group overflow-hidden">
        {selectable && (
          <div 
            className={`absolute top-[8px] left-[12px] z-20 no-navigate transition-opacity ${selected ? 'opacity-100' : 'opacity-0 group-hover:opacity-100'}`}
            onClick={handleCheckboxClick}
          >
            <div className={`w-5 h-5 rounded-md border flex items-center justify-center transition-colors shadow-sm ${selected ? 'bg-sma-purple border-sma-purple' : 'bg-white/80 border-gray-300 hover:border-sma-purple'}`}>
              {selected && <Icon icon="lucide:check" className="text-white w-3.5 h-3.5" />}
            </div>
          </div>
        )}
        {thumbnail_url ? (
          <img
            src={thumbnail_url}
            alt={file_name}
            className={`absolute inset-0 w-full h-full object-cover ${isProcessing ? 'opacity-50' : ''}`}
          />
        ) : (
          <div className="absolute inset-0 w-full h-full flex items-center justify-center text-gray-400 dark:text-gray-500 text-xs transition-colors">
            {media_type?.toUpperCase() || 'UNKNOWN'}
          </div>
        )}

        {score !== undefined ? (
          <div className="absolute top-[8px] right-[12px] px-2 py-1 bg-green-500/90 rounded text-[10px] font-bold text-white shadow-md z-10 border border-green-400">
            {(score * 100).toFixed(0)}% Match
          </div>
        ) : (
          <StatusBadge status={status} />
        )}

        {is_favorite && (
          <div className="absolute top-[8px] right-[40px] z-10 flex items-center justify-center filter drop-shadow-md">
            <Icon icon="fluent-emoji-flat:star" width="20" height="20" />
          </div>
        )}

        {!selectable && (
          <div className="absolute top-[8px] left-[12px] text-white font-inter text-[13px] drop-shadow-md z-10 flex flex-row items-center gap-1.5 font-medium shadow-black">
            {resolution && <span style={{ textShadow: "1px 1px 2px black" }}>{resolution}</span>}
            <span style={{ textShadow: "1px 1px 2px black" }}>{media_type === 'video' ? 'MP4' : media_type === 'image' ? 'JPG' : 'MP3'}</span>
          </div>
        )}

        {timeToShow !== undefined && timeToShow !== null && (
          <div className="absolute bottom-[8px] right-[12px] bg-black/60 px-1.5 py-0.5 rounded text-white text-[11px] font-inter z-10">
            {formatDuration(timeToShow)}
          </div>
        )}

        <div
          className="absolute bottom-[8px] left-[12px] z-20 no-navigate opacity-0 group-hover:opacity-100 transition-opacity"
        >
          <div className="relative" onMouseLeave={() => setShowMenu(false)}>
            <button
              onClick={(e) => {
                e.stopPropagation();
                setShowMenu(!showMenu);
              }}
              title="Menu"
              className="p-1.5 rounded-full transition-colors shadow-md bg-white/90 dark:bg-black/60 text-gray-800 dark:text-white hover:bg-white"
            >
              <Icon icon="lucide:more-vertical" width="14" height="14" />
            </button>
            {showMenu && (
              <div className="absolute bottom-full left-0 pb-1 z-30">
                <div className="w-32 bg-white dark:bg-[#2D2844] rounded-md shadow-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
                  <button
                    className="w-full text-left px-3 py-2 text-xs text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center gap-2"
                    onClick={(e) => {
                      e.stopPropagation();
                      setShowMenu(false);
                      navigate(`/assets/${asset_id}`);
                    }}
                  >
                    <Icon icon="lucide:info" width="14" height="14" /> View Details
                  </button>
                  {isProcessing && (
                    <button
                      className="w-full text-left px-3 py-2 text-xs text-sma-purple dark:text-[#A78BFA] hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center gap-2"
                      onClick={(e) => {
                        e.stopPropagation();
                        setShowMenu(false);
                        handleReingest(e);
                      }}
                      disabled={isReingesting}
                    >
                      {isReingesting ? <Icon icon="lucide:loader-2" className="animate-spin" width="14" height="14" /> : <Icon icon="lucide:refresh-cw" width="14" height="14" />}
                      Retry
                    </button>
                  )}
                  <button
                    className="w-full text-left px-3 py-2 text-xs text-red-500 hover:bg-red-50 dark:hover:bg-red-900/30 flex items-center gap-2"
                    onClick={(e) => {
                      e.stopPropagation();
                      setShowMenu(false);
                      setShowConfirm(true);
                    }}
                  >
                    <Icon icon="lucide:trash-2" width="14" height="14" /> Delete
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>

        {isProcessing && (
          <div className="absolute bottom-0 left-0 right-0 h-1 bg-gray-200 dark:bg-gray-800 z-10">
            <div
              className="h-full bg-sma-purple transition-all duration-300 ease-linear"
              style={{ width: `${displayProgress}%` }}
            />
          </div>
        )}
      </div>

      <div className="px-3 py-1.5 shrink-0 flex flex-col justify-between items-center w-full gap-1 h-[60px] bg-white dark:bg-sma-surface border-t border-gray-200/60 dark:border-[#2D2844] transition-colors">
        <h3 className="text-[12px] leading-tight text-gray-900 dark:text-white truncate font-inter w-full text-center shrink-0 transition-colors" title={caption || file_name}>
          {caption || file_name}
        </h3>

        {transcript_snippet ? (
          <p className="text-[10px] leading-[14px] text-gray-500 dark:text-gray-400 font-inter line-clamp-2 w-full text-center italic transition-colors" title={transcript_snippet}>
            "{transcript_snippet}"
          </p>
        ) : (
          <div className="flex flex-nowrap overflow-hidden gap-1 items-center justify-center w-full min-h-0">
            {tags && tags.slice(0, 3).map((tag, idx) => {
              const tagText = typeof tag === 'object' ? tag.name : tag;
              const formattedTag = tagText ? tagText.replace(/_/g, ' ') : '';
              return (
                <div key={idx} className="px-1.5 py-[1px] border border-sma-purple/20 dark:border-sma-purple rounded flex items-center justify-center bg-sma-purple/5 dark:bg-sma-purple/10 flex-shrink-1 min-w-0 transition-colors" title={formattedTag}>
                  <span className="text-[10px] leading-tight text-sma-purple dark:text-white font-inter whitespace-nowrap overflow-hidden text-ellipsis block max-w-[50px] transition-colors">{formattedTag}</span>
                </div>
              );
            })}
            {tags && tags.length > 3 && (() => {
              const hiddenTagsText = tags.slice(3).map(t => {
                const tagText = typeof t === 'object' ? t.name : t;
                return tagText ? tagText.replace(/_/g, ' ') : '';
              }).join(', ');
              
              return (
                <div 
                  className="px-1.5 py-[1px] border border-sma-purple/20 dark:border-sma-purple rounded flex items-center justify-center bg-sma-purple/5 dark:bg-sma-purple/10 flex-shrink-0 transition-colors cursor-help"
                  title={`Hidden tags: ${hiddenTagsText}`}
                >
                  <span className="text-[10px] leading-tight text-sma-purple dark:text-white font-inter whitespace-nowrap transition-colors">+{tags.length - 3}</span>
                </div>
              );
            })()}
          </div>
        )}
      </div>

      {showConfirm && (
        <div className="absolute inset-0 bg-black/90 z-30 flex flex-col items-center justify-center p-4 no-navigate">
          <p className="text-white text-sm text-center mb-4 font-inter">Are you sure you want to delete this video?</p>
          <div className="flex space-x-3">
            <button
              onClick={(e) => { e.stopPropagation(); setShowConfirm(false); }}
              className="px-3 py-1.5 bg-gray-700 text-white rounded hover:bg-gray-600 text-xs font-medium"
              disabled={isDeleting}
            >
              Cancel
            </button>
            <button
              onClick={handleDelete}
              className="px-3 py-1.5 bg-red-600 text-white rounded hover:bg-red-500 text-xs font-medium flex items-center"
              disabled={isDeleting}
            >
              {isDeleting ? <Icon icon="lucide:loader-2" className="animate-spin mr-1.5" /> : null}
              Delete
            </button>
          </div>
          {errorMsg && <p className="text-red-400 text-[10px] mt-2 text-center">{errorMsg}</p>}
        </div>
      )}
    </div>
  );
}

MediaCard.propTypes = {
  asset_id: PropTypes.string.isRequired,
  file_name: PropTypes.string.isRequired,
  media_type: PropTypes.string.isRequired,
  thumbnail_url: PropTypes.string,
  duration: PropTypes.number,
  duration_sec: PropTypes.number,
  resolution: PropTypes.string,
  file_size_bytes: PropTypes.number,
  created_at: PropTypes.string,
  tags: PropTypes.arrayOf(PropTypes.any),
  status: PropTypes.string,
  selected: PropTypes.bool,
  onSelectToggle: PropTypes.func
};