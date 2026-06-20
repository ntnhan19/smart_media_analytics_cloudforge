import { useState } from 'react';
import { useJobs } from '../contexts/JobContext';
import { uploadMedia } from '../services/api';
import { Upload as UploadIcon, Loader2, Play } from 'lucide-react';
import IngestQueue from '../components/upload/IngestQueue';

export default function Upload() {
  const [isUploading, setIsUploading] = useState(false);
  const { addJob, clearAllFinishedJobs } = useJobs();

  const handleUpload = async (count = 1) => {
    setIsUploading(true);
    
    // Quét sạch sẽ các job cũ (cả xanh lẫn đỏ) trước khi bắt đầu mẻ mới
    clearAllFinishedJobs();

    try {
      // Gửi n request đồng thời để test đa luồng
      const promises = Array.from({ length: count }).map(async (_, index) => {
        const isFake = count > 1 && index === count - 1; 
        
        // CỐ TÌNH: Ép hệ thống nhét 1 thẻ báo lỗi trực tiếp vào Frontend mà không cần gọi API
        // để đảm bảo 100% bạn thấy được UI báo đỏ
        if (isFake) {
          addJob({
            job_id: `fail-mock-${Date.now()}`,
            asset_id: "mock-asset-id",
            status: 'failed',
            progress: 15,
            current_step: 'scene_detection',
            error_message: 'Video file corrupted or missing'
          });
          return;
        }

        const payload = {
          source_path: `/app/data/media/demo.mp4`,
          options: {
            scene_detection: true,
            transcription: true,
            vision_caption: true,
            whisper_model: "base"
          }
        };
        
        try {
          const response = await uploadMedia(payload);
          if (response && response.job_id) {
            addJob({
              job_id: response.job_id,
              asset_id: response.asset_id,
              status: 'queued',
              progress: 0,
              current_step: 'uploading_to_s3',
              error_message: null
            });
          }
        } catch (err) {
          console.error('Individual upload failed:', err);
        }
      });

      await Promise.all(promises);
    } catch (error) {
      console.error('Trigger ingest failed', error);
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="text-white p-6 max-w-6xl mx-auto">
      <h1 className="text-2xl font-bold mb-8">Trigger Ingest Pipeline</h1>
      
      <div className="flex flex-col lg:flex-row gap-8">
        {/* Cột trái: Mock Upload */}
        <div className="max-w-md w-full shrink-0 bg-[#16132A] border border-[#4F8EF7] rounded-lg p-6 h-fit">
          <p className="text-gray-400 mb-6 text-sm">
            Nhấn các nút dưới đây để kích hoạt API <code>/api/v1/ingest</code> trên Backend.
          </p>
          
          <div className="flex flex-col gap-4">
            <button
              onClick={() => handleUpload(1)}
              disabled={isUploading}
              className="w-full bg-[#4ADE80] hover:bg-[#3BCE70] disabled:bg-gray-600 disabled:cursor-not-allowed text-[#16132A] font-bold py-3 rounded flex items-center justify-center gap-2 transition-colors"
            >
              {isUploading ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <UploadIcon className="w-5 h-5" />
              )}
              {isUploading ? 'Triggering...' : 'Start 1 Demo Job'}
            </button>

            <button
              onClick={() => handleUpload(3)}
              disabled={isUploading}
              className="w-full bg-[#7B5CF5] hover:bg-[#6A4BE4] disabled:bg-gray-600 disabled:cursor-not-allowed text-white font-bold py-3 rounded flex items-center justify-center gap-2 transition-colors"
            >
              {isUploading ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <Play className="w-5 h-5" />
              )}
              {isUploading ? 'Triggering...' : 'Start 3 Jobs (Include 1 Fake to test Error)'}
            </button>
          </div>
        </div>

        {/* Cột phải: Ingest Queue (List View) */}
        <div className="flex-1 min-w-[300px]">
          <IngestQueue />
        </div>
      </div>
    </div>
  );
}
