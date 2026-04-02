// src/services/api.js
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
  getAll: (userId) => api.get(`/accounts/${userId}`),
  
  // Get a single account for a user
  getById: (userId, accountId) => api.get(`/accounts/${userId}/${accountId}`),
  
  // Create new account
  create: (accountData) => api.post('/accounts', accountData),
  
  // Delete account
  delete: (accountId) => api.delete(`/accounts/${accountId}`),
};

export const analyticsAPI = {
  // Triggers the Random Forest forecasting model
  getForecast: (userId) => api.get(`/transactions/forecast/${userId}`),
  
  // Get existing transactions
  getHistory: () => api.get('/transactions'),
};

export const agentAPI = {
  // Sends a message to the local Llama AI agent and receives a task-oriented response.
  ask: (message) => api.post('/api/chat', { message }),
};