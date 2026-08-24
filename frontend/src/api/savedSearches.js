import api from '../services/api';

export const savedSearchesApi = {
  list: async () => {
    const response = await api.get(`/saved-searches/`);
    return response.data;
  },
  create: async (queryText) => {
    const response = await api.post(`/saved-searches/`, { query_text: queryText });
    return response.data;
  },
  delete: async (id) => {
    await api.delete(`/saved-searches/${id}`);
  }
};
