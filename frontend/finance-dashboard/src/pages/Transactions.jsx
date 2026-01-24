// src/pages/Transactions.jsx
import React, { useState, useEffect } from 'react';
import TransactionForm from '../components/TransactionForm';
import TransactionTable from '../components/TransactionTable';
import CsvUploader from '../components/CsvUploader';
import { transactionsAPI } from '../services/api';
import './Transactions.css';

const Transactions = () => {
  const [transactions, setTransactions] = useState([]);
  const [selectedRows, setSelectedRows] = useState([]);
  const [filters, setFilters] = useState({
    startDate: '',
    endDate: '',
    category: '',
    search: '',
  });

  const fetchTransactions = async () => {
    try {
      const response = await transactionsAPI.getAll();
      setTransactions(response.data.transactions);
    } catch (error) {
      console.error('Error fetching transactions:', error);
    }
  };

  // Get all transactions on initial load
  useEffect(() => {
    fetchTransactions();
  }, []);

  const handleAddTransaction = async (transactionData) => {
    try {
      await transactionsAPI.create(transactionData);
      await fetchTransactions(); // refresh table
    } catch (error) {
      console.error('Error adding transaction:', error);
      throw new Error()
    }
  };

  const handleDeleteTransaction = async (id) => {
    try {
      await transactionsAPI.delete(id);
      await fetchTransactions(); // refresh table
    } catch (error) {
      console.error(error);
      alert('Failed to delete transaction');
    }
  };

  const handleDeleteMultiple = async (ids) => {
    try {
      await transactionsAPI.deleteMultiple(ids);
      await fetchTransactions(); // refresh table
    } catch (error) {
      console.error(error);
      alert('Failed to delete transactions');
    }
  };

  const handleUploadSuccess = async () => {
    try {
      await fetchTransactions(); // refresh table
    } catch (error) {
      console.error(error);
      alert('Failed to retrieve new transactions');
    }
  };

  const handleFilterChange = (e) => {
    const { name, value } = e.target;
    setFilters(prev => ({
      ...prev,
      [name]: value,
    }));
  };

  const clearFilters = () => {
    setFilters({
      startDate: '',
      endDate: '',
      category: '',
      search: '',
    });
  };

  // Get categories for filter dropdown
  const categories = [...new Set(transactions.map(t => t.category))].sort();

  return (
    <div className="transactions-page">
      <div className="page-header">
        <h1>Transaction Management</h1>
        <p className="page-subtitle">
          Upload bank statements, manage transactions, and prepare data for AI analysis.
        </p>
      </div>

      <div className="content-grid">
        <div className="left-column">
          <CsvUploader onUploadSuccess={handleUploadSuccess} />
          <TransactionForm onSubmit={handleAddTransaction} categories={categories} />
        </div>

        <div className="right-column">
          <div className="stats-card">
            <h3>Transaction Statistics</h3>
            <div className="stats-grid">
              <div className="stat">
                <div className="stat-value">{transactions.length}</div>
                <div className="stat-label">Total Transactions</div>
              </div>
              <div className="stat">
                <div className="stat-value">
                  £{transactions
                    .filter(t => parseFloat(t.amount) > 0)
                    .reduce((sum, t) => sum + parseFloat(t.amount), 0)
                    .toFixed(2)}
                </div>
                <div className="stat-label">Total Income</div>
              </div>
              <div className="stat">
                <div className="stat-value">
                  £{Math.abs(transactions
                    .filter(t => parseFloat(t.amount) < 0)
                    .reduce((sum, t) => sum + parseFloat(t.amount), 0))
                    .toFixed(2)}
                </div>
                <div className="stat-label">Total Expenses</div>
              </div>
              <div className="stat">
                <div className="stat-value">
                  £{transactions
                    .reduce((sum, t) => sum + parseFloat(t.amount), 0)
                    .toFixed(2)}
                </div>
                <div className="stat-label">Net Balance</div>
              </div>
            </div>
          </div>

          <div className="filters-container">
            <h3>Filter Transactions</h3>
            <div className="filters-grid">
              <div className="filter-group">
                <label>Start Date</label>
                <input
                  type="date"
                  name="startDate"
                  value={filters.startDate}
                  onChange={handleFilterChange}
                />
              </div>
              
              <div className="filter-group">
                <label>End Date</label>
                <input
                  type="date"
                  name="endDate"
                  value={filters.endDate}
                  onChange={handleFilterChange}
                />
              </div>
              
              <div className="filter-group">
                <label>Category</label>
                <select
                  name="category"
                  value={filters.category}
                  onChange={handleFilterChange}
                >
                  <option value="">All Categories</option>
                  {categories.map(category => (
                    <option key={category} value={category}>{category}</option>
                  ))}
                </select>
              </div>
              
              <div className="filter-group">
                <label>Search</label>
                <input
                  type="text"
                  name="search"
                  value={filters.search}
                  onChange={handleFilterChange}
                  placeholder="Search descriptions..."
                />
              </div>
              
              <button onClick={clearFilters} className="clear-filters-btn">
                Clear Filters
              </button>
            </div>
          </div>

          <TransactionTable
            transactions={transactions.filter(t => {
              // Apply filters
              if (filters.startDate && new Date(t.date) < new Date(filters.startDate)) return false;
              if (filters.endDate && new Date(t.date) > new Date(filters.endDate)) return false;
              if (filters.category && t.category !== filters.category) return false;
              if (filters.search && !t.description.toLowerCase().includes(filters.search.toLowerCase())) return false;
              return true;
            })}
            onDelete={handleDeleteTransaction}
            onDeleteMultiple={handleDeleteMultiple}
            onSelectionChange={setSelectedRows}
          />
        </div>
      </div>
    </div>
  );
};

export default Transactions;