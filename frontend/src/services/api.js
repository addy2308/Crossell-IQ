import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000,
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Prediction API
export const predictionAPI = {
  getPrediction: (customerId) => 
    api.post('/predictions/predict', { customer_id: customerId }),
  getAgentQueue: (agentId, limit = 10) => 
    api.get(`/predictions/agent-queue?agent_id=${agentId}&limit=${limit}`),
  submitFeedback: (feedback) => 
    api.post('/predictions/feedback', feedback),
  getHistory: (customerId, limit = 10) =>
    api.get(`/predictions/history/${customerId}?limit=${limit}`),
};

// Dashboard API
export const dashboardAPI = {
  getKPIs: () => api.get('/dashboard/kpis'),
  getRevenueTrend: (period = 'weekly', weeks = 12) => 
    api.get(`/dashboard/revenue-trend?period=${period}&weeks=${weeks}`),
  getSegmentDistribution: () => api.get('/dashboard/segment-distribution'),
  getModelPerformance: () => api.get('/dashboard/model-performance'),
};

// Agent API
export const agentAPI = {
  getMe: () => api.get('/agents/me'),
  getPerformance: (agentId, days = 30) => 
    api.get(`/agents/performance?agent_id=${agentId}&days=${days}`),
  getLeaderboard: (days = 30) => 
    api.get(`/agents/leaderboard?days=${days}`),
};

// Model API
export const modelAPI = {
  getFeatureImportance: () => api.get('/models/feature-importance'),
  getMetrics: () => api.get('/models/metrics'),
  getSegmentProfiles: () => api.get('/models/segment-profiles'),
};

export default api;