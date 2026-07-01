import { useState } from 'react';
import PropTypes from 'prop-types';
import { useNavigate } from 'react-router-dom';
import { useQueryClient } from '@tanstack/react-query';
import { Icon } from '@iconify/react';
import { useJobs } from '../../contexts/JobContext';
import { deleteAsset } from '../../services/api';

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
  file_size_bytes,
  created_at,
  tags,
  status = 'ready',
  is_favorite = false,
  showToast
}) {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { activeJobs } = useJobs();
  const [showConfirm, setShowConfirm] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  const actualDuration = duration !== undefined ? duration : duration_sec;

  // Find job in context if processing
  const job = activeJobs.find(j => j.asset_id === asset_id && (j.status === 'processing' || j.status === 'queued'));
  const displayProgress = job ? job.progress : (status === 'completed' ? 100 : 0);

  const handleCardClick = (e) => {
    if (e.target.closest('.no-navigate')) return;
    navigate(`/assets/${asset_id}`);
  };

  const handleDelete = async (e) => {
    e.stopPropagation();
    setIsDeleting(true);
    setErrorMsg('');
    try {
      await deleteAsset(asset_id);
      if (showToast) showToast('Xóa video thành công', 'success');

      // Update local storage deleted count for UI display
      const currentCount = parseInt(localStorage.getItem('deletedAssetsCount') || '0', 10);
      localStorage.setItem('deletedAssetsCount', (currentCount + 1).toString());
      window.dispatchEvent(new Event('assetDeleted'));

      queryClient.invalidateQueries({ queryKey: ['assets'] });
    } catch (err) {
      const msg = err.response?.data?.detail || 'Xóa video thất bại';
      setErrorMsg(msg);
      if (showToast) showToast(msg, 'error');
    } finally {
      setIsDeleting(false);
      setShowConfirm(false);
    }
  };

  const isProcessing = status === 'processing' || status === 'queued';

  return (
    <div
      // Thay đổi: H-[210px] thon gọn hơn, an toàn cho 2 dòng grid
      className="w-full h-[210px] rounded-[6px] border border-sma-purple overflow-hidden cursor-pointer hover:border-sma-purple/80 bg-sma-surface flex flex-col relative group"
      onClick={handleCardClick}
    >
      <div className="w-full flex-1 bg-gray-900 relative group overflow-hidden">
        {thumbnail_url ? (
          <img
            src={thumbnail_url}
            alt={file_name}
            className={`absolute inset-0 w-full h-full object-cover ${isProcessing ? 'opacity-50' : ''}`}
          />
        ) : (
          <div className="absolute inset-0 w-full h-full flex items-center justify-center text-gray-500 text-xs">
            {media_type?.toUpperCase() || 'UNKNOWN'}
          </div>
        )}

        <StatusBadge status={status} />

        {is_favorite && (
          <div className="absolute top-[8px] right-[40px] z-10 flex items-center justify-center filter drop-shadow-md">
            <Icon icon="fluent-emoji-flat:star" width="20" height="20" />
          </div>
        )}

        <div className="absolute top-[8px] left-[12px] text-white font-inter text-[13px] drop-shadow-md z-10 flex flex-row items-center gap-1.5 font-medium shadow-black">
          {resolution && <span style={{ textShadow: "1px 1px 2px black" }}>{resolution}</span>}
          <span style={{ textShadow: "1px 1px 2px black" }}>{media_type === 'video' ? 'MP4' : media_type === 'image' ? 'JPG' : 'MP3'}</span>
        </div>

        {actualDuration > 0 && (
          <div className="absolute bottom-[8px] right-[12px] bg-black/60 px-1.5 py-0.5 rounded text-white text-[11px] font-inter z-10">
            {formatDuration(actualDuration)}
          </div>
        )}

        <div
          className="absolute bottom-[8px] left-[12px] z-20 no-navigate opacity-0 group-hover:opacity-100 transition-opacity"
          title={isProcessing ? "Không thể xóa Asset khi đang xử lý." : "Xóa Asset"}
        >
          <button
            onClick={(e) => {
              e.stopPropagation();
              if (!isProcessing) setShowConfirm(true);
            }}
            disabled={isProcessing}
            className={`p-1.5 rounded-full transition-colors shadow-md ${isProcessing
              ? 'bg-gray-800/80 text-gray-500 cursor-not-allowed'
              : 'bg-red-500/80 text-white hover:bg-red-500'
              }`}
          >
            <Icon icon="lucide:trash-2" width="14" height="14" />
          </button>
        </div>

        {isProcessing && (
          <div className="absolute bottom-0 left-0 right-0 h-1 bg-gray-800 z-10">
            <div
              className="h-full bg-sma-purple transition-all duration-300 ease-linear"
              style={{ width: `${displayProgress}%` }}
            />
          </div>
        )}
      </div>

      <div className="px-3 py-1.5 shrink-0 flex flex-col justify-between items-center w-full gap-1 h-[56px] bg-sma-surface border-t border-[#2D2844]">
        <h3 className="text-[12px] leading-tight text-white truncate font-inter w-full text-center shrink-0" title={file_name}>
          {file_name}
        </h3>

        <div className="flex flex-nowrap overflow-hidden gap-1 items-center justify-center w-full min-h-0">
          {tags && tags.slice(0, 3).map((tag, idx) => {
            const tagText = typeof tag === 'object' ? tag.name : tag;
            const formattedTag = tagText ? tagText.replace(/_/g, ' ') : '';
            return (
              <div key={idx} className="px-1.5 py-[1px] border border-sma-purple rounded flex items-center justify-center bg-sma-purple/10 flex-shrink-1 min-w-0" title={formattedTag}>
                <span className="text-[10px] leading-tight text-white font-inter whitespace-nowrap overflow-hidden text-ellipsis block max-w-[50px]">{formattedTag}</span>
              </div>
            );
          })}
          {tags && tags.length > 3 && (
            <div className="px-1.5 py-[1px] border border-sma-purple rounded flex items-center justify-center bg-sma-purple/10 flex-shrink-0">
              <span className="text-[10px] leading-tight text-white font-inter whitespace-nowrap">+{tags.length - 3}</span>
            </div>
          )}
        </div>
      </div>

      {showConfirm && (
        <div className="absolute inset-0 bg-black/90 z-30 flex flex-col items-center justify-center p-4 no-navigate">
          <p className="text-white text-sm text-center mb-4">Bạn có chắc muốn xóa video này?</p>
          <div className="flex space-x-3">
            <button
              onClick={(e) => { e.stopPropagation(); setShowConfirm(false); }}
              className="px-3 py-1 bg-gray-700 text-white rounded hover:bg-gray-600 text-xs"
              disabled={isDeleting}
            >
              Hủy
            </button>
            <button
              onClick={handleDelete}
              className="px-3 py-1 bg-red-600 text-white rounded hover:bg-red-500 text-xs flex items-center"
              disabled={isDeleting}
            >
              {isDeleting ? <Icon icon="lucide:loader-2" className="animate-spin mr-1" /> : null}
              Xóa
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
  status: PropTypes.string
};