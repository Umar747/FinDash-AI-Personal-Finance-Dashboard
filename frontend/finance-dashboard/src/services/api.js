// src/services/api.js
import axios from 'axios';

// Create axios instance with base URL for Flask backend
const API_BASE_URL = 'http://localhost:5000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Transactions API endpoints
export const transactionsAPI = {
  // Get all transactions with filters
  getAll: (filters = {}) => api.get('/transactions', { params: filters }),
  
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

// Mock data for development (remove when backend is ready)
export const mockTransactions = [
  {
    id: 1,
    date: '2024-01-15',
    description: 'Amazon Online Purchase',
    amount: -49.99,
    category: 'Shopping',
    account: 'HSBC Current',
    type: 'debit',
  },
  {
    id: 2,
    date: '2024-01-14',
    description: 'Tesco Supermarket',
    amount: -78.45,
    category: 'Groceries',
    account: 'HSBC Current',
    type: 'debit',
  },
  {
    id: 3,
    date: '2024-01-13',
    description: 'Salary Deposit',
    amount: 2500.00,
    category: 'Income',
    account: 'HSBC Current',
    type: 'credit',
  },
  {
    id: 4,
    date: '2024-01-12',
    description: 'Uber Ride',
    amount: -15.50,
    category: 'Transport',
    account: 'HSBC Current',
    type: 'debit',
  },
  {
    id: 5,
    date: '2024-01-11',
    description: 'Netflix Subscription',
    amount: -10.99,
    category: 'Entertainment',
    account: 'HSBC Current',
    type: 'debit',
  },
  {
    id: 6,
    date: '2024-01-10',
    description: 'Pret A Manger',
    amount: -8.75,
    category: 'Food & Dining',
    account: 'HSBC Current',
    type: 'debit',
  },
  {
    id: 7,
    date: '2024-01-09',
    description: 'Gym Membership',
    amount: -32.00,
    category: 'Health & Fitness',
    account: 'HSBC Current',
    type: 'debit',
  },
  {
    id: 8,
    date: '2024-01-08',
    description: 'Freelance Payment',
    amount: 500.00,
    category: 'Income',
    account: 'HSBC Current',
    type: 'credit',
  },
];