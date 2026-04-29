import axios from 'axios';

// Create axios instance with base URL for Flask backend
const API_BASE_URL = 'http://127.0.0.1:5000';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add JWT to headers
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Auth API endpoints
export const authAPI = {
  signup: (userData) => api.post('/auth/signup', userData),
  login: (credentials) => api.post('/auth/login', credentials),
};

// Transactions API endpoints
export const transactionsAPI = {
  // Get all transactions with filters
  getAll: () => api.get('/transactions'),
  
  // Get single transaction
  getById: (id) => api.get(`/transactions/${id}`),
  
  // Create new transaction
  create: (transactionData) => api.post('/transactions', transactionData),
  
  // Update transaction
  update: (id, transactionData) => api.put(`/transactions/${id}`, transactionData),
  
  // Delete single transaction
  delete: (id) => api.delete(`/transactions/${id}`),
  
  // Delete multiple transactions
  deleteMultiple: (ids) => api.post('/transactions/delete-multiple', { ids }),
  
  // Upload CSV file
  uploadCSV: (formData) => api.post('/transactions/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  }),
};

export const accountsAPI = {
  // Get all accounts for a user
  getAll: () => api.get('/accounts'),
  
  // Get a single account for a user
  getById: (accountId) => api.get(`/accounts/${accountId}`),
  
  // Create new account
  create: (accountData) => api.post('/accounts', accountData),
  
  // Delete account
  delete: (accountId) => api.delete(`/accounts/${accountId}`),
};

export const analyticsAPI = {
  // Triggers the Random Forest forecasting model
  getForecast: () => api.get('/transactions/forecast'),
  
  // Get existing transactions
  getHistory: () => api.get('/transactions'),
};

export const agentAPI = {
  // Sends a message to the local Llama AI agent and receives a task-oriented response.
  ask: (message) => api.post('/api/chat', { message }),
};

export default api;