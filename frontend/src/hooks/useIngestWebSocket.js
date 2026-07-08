import { useEffect } from 'react';
import { useJobs } from '../contexts/JobContext';
import { useQueryClient } from '@tanstack/react-query';

const WS_BASE_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/api/v1/ingest/ws';

export const useIngestWebSocket = (jobId) => {
  const { updateJob } = useJobs();
  const queryClient = useQueryClient();

  useEffect(() => {
    if (!jobId) return;

    let isActive = true;
    let ws = null;
    let reconnectTimeout = null;

    const connect = () => {
      if (!isActive) return;

      try {
        ws = new WebSocket(`${WS_BASE_URL}/${jobId}`);

        ws.onopen = () => {
          if (!isActive) {
            ws.close();
            return;
          }
          // Connected successfully
        };

        ws.onmessage = (event) => {
          if (!isActive) return;
          try {
            const data = JSON.parse(event.data);
            // updateJob tự động merge dữ liệu nên chỉ cần gửi những trường nhận được
            if (data.status || data.progress !== undefined || data.current_step) {
              updateJob({
                job_id: jobId,
                ...(data.status && { status: data.status }),
                ...(data.progress !== undefined && { progress: data.progress }),
                ...(data.current_step && { current_step: data.current_step }),
                ...(data.error_message && { error_message: data.error_message }),
              });
              
              if (data.status === 'completed') {
                queryClient.invalidateQueries({ queryKey: ['assets'] });
              }
            }
          } catch (err) {
            console.error(`[WebSocket] Failed to parse message for job ${jobId}`, err);
          }
        };

        ws.onclose = () => {
          if (!isActive) return;
          reconnectTimeout = setTimeout(connect, 5000);
        };

        ws.onerror = (error) => {
          if (!isActive) return;
          console.error(`[WebSocket] Error for job ${jobId}:`, error);
          // Let onclose handle the reconnect
        };
      } catch (err) {
        if (!isActive) return;
        console.error(`[WebSocket] Connection failed for job ${jobId}`, err);
        reconnectTimeout = setTimeout(connect, 5000);
      }
    };

    connect();

    return () => {
      isActive = false;
      if (reconnectTimeout) {
        clearTimeout(reconnectTimeout);
      }
      if (ws) {
        ws.onclose = null;
        ws.onerror = null;
        ws.onmessage = null;
        ws.onopen = null;
        if (ws.readyState === WebSocket.CONNECTING) {
          // Chờ kết nối xong rồi mới đóng để tránh lỗi đỏ khó chịu trên Chrome
          ws.onopen = () => ws.close();
        } else if (ws.readyState === WebSocket.OPEN) {
          ws.close();
        }
      }
    };
  }, [jobId, updateJob, queryClient]);
};
