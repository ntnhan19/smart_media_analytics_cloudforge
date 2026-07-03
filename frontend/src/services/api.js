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

export const uploadMediaFile = async (file, options, signal) => {
  const formData = new FormData();
  formData.append('file', file);
  if (options) {
    formData.append('options', JSON.stringify(options));
  }
  const response = await axios.post('/api/v1/ingest/upload', formData, {
    signal,
  });
  return response.data;
};

export const retryJob = async (jobId) => {
  const response = await api.post(`/ingest/retry/${jobId}`);
  return response.data;
};

export const getAssets = async (signal, limit = 50, offset = 0) => {
  const response = await api.get(`/assets?limit=${limit}&offset=${offset}`, { signal });
  return response.data;
};

export const deleteAsset = async (assetId) => {
  const response = await api.delete(`/assets/${assetId}`);
  return response.data;
};

export const getTags = async (signal) => {
  const response = await api.get('/tags', { signal });
  return response.data;
};

export const getAsset = async (assetId, signal) => {
  const response = await api.get(`/assets/${assetId}`, { signal });
  return response.data;
};

export const getAssetScenes = async (assetId, signal) => {
  const response = await api.get(`/assets/${assetId}/scenes`, { signal });
  return response.data;
};

export const reingestAsset = async (assetId, options = {}) => {
  const response = await api.post(`/assets/${assetId}/reingest`, options);
  return response.data;
};

export const regenerateInsights = async (assetId) => {
  const response = await api.post(`/assets/${assetId}/regenerate-insights`);
  return response.data;
};

export const getAssetStream = async (assetId, signal) => {
  const response = await api.get(`/media/stream/${assetId}`, { signal });
  return response.data; // Expected to return { stream_url: "..." }
};

export const createClip = async (assetId, startTime, endTime, sceneId) => {
  const response = await api.post(`/clips`, {
    asset_id: assetId,
    start_time_sec: startTime,
    end_time_sec: endTime,
    scene_id: sceneId
  });
  return response.data;
};

export const toggleFavorite = async (assetId, isFavorite) => {
  const response = await api.patch(`/assets/${assetId}/favorite`, {
    is_favorite: isFavorite
  });
  return response.data;
};
