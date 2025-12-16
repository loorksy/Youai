import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export const api = {
  dashboard: {
    getStats: () => axios.get(`${API}/dashboard/stats`),
    getRecentVideos: (limit = 5) => axios.get(`${API}/videos/recent?limit=${limit}`)
  },
  videos: {
    create: (data) => axios.post(`${API}/videos/create`, data),
    getAll: () => axios.get(`${API}/videos`),
    getOne: (id) => axios.get(`${API}/videos/${id}`),
    delete: (id) => axios.delete(`${API}/videos/${id}`)
  },
  settings: {
    updateApiKeys: (service, credentials) => axios.post(`${API}/settings/api-keys`, { service, credentials }),
    testConnection: (service) => axios.post(`${API}/settings/test-connection?service=${service}`),
    getSavedKeys: () => axios.get(`${API}/settings/api-keys`)
  },
  analytics: {
    getOverview: () => axios.get(`${API}/analytics/overview`),
    getTopVideos: (limit = 10) => axios.get(`${API}/analytics/top-videos?limit=${limit}`)
  },
  trends: {
    get: () => axios.get(`${API}/trends`),
    search: (keyword) => axios.get(`${API}/trends/search?keyword=${encodeURIComponent(keyword)}`)
  },
  campaigns: {
    getAll: () => axios.get(`${API}/campaigns`)
  }
};

export default api;
