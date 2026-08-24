import axios from 'axios';
import { API_URL } from '../config';

export const projectsApi = {
  list: async () => {
    const response = await axios.get(`${API_URL}/projects/`);
    return response.data;
  },
  create: async (data) => {
    const response = await axios.post(`${API_URL}/projects/`, data);
    return response.data;
  },
  update: async (id, data) => {
    const response = await axios.put(`${API_URL}/projects/${id}`, data);
    return response.data;
  },
  delete: async (id) => {
    await axios.delete(`${API_URL}/projects/${id}`);
  },
  assignAsset: async (assetId, projectId) => {
    const response = await axios.patch(`${API_URL}/assets/${assetId}/project`, { project_id: projectId });
    return response.data;
  }
};
