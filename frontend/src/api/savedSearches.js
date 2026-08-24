import axios from 'axios';
import { API_URL } from '../config';

export const savedSearchesApi = {
  list: async () => {
    const response = await axios.get(`${API_URL}/saved-searches/`);
    return response.data;
  },
  create: async (queryText) => {
    const response = await axios.post(`${API_URL}/saved-searches/`, { query_text: queryText });
    return response.data;
  },
  delete: async (id) => {
    await axios.delete(`${API_URL}/saved-searches/${id}`);
  }
};
