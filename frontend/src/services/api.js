import axios from 'axios';

const api = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (axios.isCancel(error)) {
      return Promise.reject(error);
    }
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);

export default api;

export const searchMedia = async (payload, signal) => {
  const response = await api.post('/search', payload, {
    signal,
  });
  return response.data;
};

export const uploadMedia = async (payload, signal) => {
  const response = await api.post('/ingest', payload, {
    signal,
  });
  return response.data;
};

export const retryJob = async (jobId) => {
  const response = await api.post(`/ingest/retry/${jobId}`);
  return response.data;
};
