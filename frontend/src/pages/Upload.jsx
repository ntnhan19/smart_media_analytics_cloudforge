import { useState } from 'react';
import { useJobs } from '../contexts/JobContext';
import { uploadMedia } from '../services/api';
import { Upload as UploadIcon, Loader2 } from 'lucide-react';
import IngestQueue from '../components/upload/IngestQueue';

export default function Upload() {
  const [isUploading, setIsUploading] = useState(false);
  const { addJob } = useJobs();

  const handleUpload = async () => {
    setIsUploading(true);
    try {
      // Backend expects a JSON payload with source_path, not a real file
      const payload = {
        source_path: "/app/data/media/demo.mp4",
        options: {
          scene_detection: true,
          transcription: true,
          vision_caption: true,
          whisper_model: "base"
        }
      };
      
      const response = await uploadMedia(payload);
      
      if (response && response.job_id) {
        addJob({
          job_id: response.job_id,
          asset_id: response.asset_id,
          status: 'queued',
          progress: 0,
          current_step: 'Initialize pipeline',
          error_message: null
        });
      }
    } catch (error) {
      console.error('Trigger ingest failed', error);
      alert('Trigger ingest failed: ' + (error.response?.data?.detail || error.message));
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
            Nhấn nút dưới đây để kích hoạt API <code>/api/v1/ingest</code> trên Backend thay vì upload file thật.
          </p>
          
          <button
            onClick={handleUpload}
            disabled={isUploading}
            className="w-full bg-[#4ADE80] hover:bg-[#3BCE70] disabled:bg-gray-600 disabled:cursor-not-allowed text-[#16132A] font-bold py-3 rounded flex items-center justify-center gap-2 transition-colors"
          >
            {isUploading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Triggering...
              </>
            ) : (
              <>
                <UploadIcon className="w-5 h-5" />
                Start Processing Demo
              </>
            )}
          </button>
        </div>

        {/* Cột phải: Ingest Queue (List View) */}
        <div className="flex-1 min-w-[300px]">
          <IngestQueue />
        </div>
      </div>
    </div>
  );
}
