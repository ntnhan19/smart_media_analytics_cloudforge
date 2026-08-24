import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_ENDPOINT || '/api/v1',
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
    // Suppress console error for 404s (expected when library is empty)
    if (error.response && error.response.status !== 404) {
      console.error('API Error:', error);
    }
    return Promise.reject(error);
  }
);

export default api;

export const getPublicStats = async (signal) => {
  const response = await api.get('/public/stats', { signal });
  return response.data;
};

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
  const response = await api.post('/ingest/upload', formData, {
    signal,
    headers: {
      'Content-Type': undefined
    }
  });
  return response.data;
};

export const retryJob = async (jobId) => {
  const response = await api.post(`/ingest/retry/${jobId}`);
  return response.data;
};

export const getAssets = async (signal, limit = 50, offset = 0, projectId = null) => {
  try {
    let url = `/assets?limit=${limit}&offset=${offset}`;
    if (projectId) {
      url += `&project_id=${projectId}`;
    }
    const response = await api.get(url, { signal });
    return response.data;
  } catch (error) {
    if (error.response && error.response.status === 404) {
      return { items: [], total: 0 };
    }
    throw error;
  }
};

export const deleteAsset = async (assetId) => {
  const response = await api.delete(`/assets/${assetId}`);
  return response.data;
};

export const getTags = async (signal) => {
  try {
    const response = await api.get('/search/tags', { signal });
    return response.data;
  } catch (error) {
    if (error.response && error.response.status === 404) {
      return { tags: [], items: [] };
    }
    throw error;
  }
};

export const getAsset = async (assetId, signal) => {
  const response = await api.get(`/assets/${assetId}`, { signal });
  return response.data;
};

export const getAssetScenes = async (assetId, signal) => {
  const response = await api.get(`/assets/${assetId}/scenes`, { signal });
  return response.data;
};

export const searchAssetScenes = async (assetId, query, topK = 10, signal) => {
  const response = await api.get(`/assets/${assetId}/scenes/search`, {
    params: { query, top_k: topK },
    signal
  });
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

export const createClip = async (assetId, startTime, endTime) => {
  const response = await api.post(`/assets/${assetId}/clip`, {
    start_sec: startTime,
    end_sec: endTime
  });
  return response.data;
};

export const toggleFavorite = async (assetId, isFavorite) => {
  const response = await api.patch(`/assets/${assetId}/favorite`, {
    is_favorite: isFavorite
  });
  return response.data;
};
