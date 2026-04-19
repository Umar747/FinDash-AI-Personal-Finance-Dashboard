// src/pages/Transactions.jsx
import React, { useState, useEffect } from 'react';
import TransactionForm from '../components/TransactionForm';
import TransactionTable from '../components/TransactionTable';
import CsvUploader from '../components/CsvUploader';
import AccountManager from '../components/AccountManager';
import EditTransactionBox from '../components/EditTransactionBox';
import { transactionsAPI, accountsAPI } from '../services/api';
import './Transactions.css';

const Transactions = () => {
  const [transactions, setTransactions] = useState([]);
  const [accounts, setAccounts] = useState([]);
  const [editingTransaction, setEditingTransaction] = useState(null);
  const [filters, setFilters] = useState({
    startDate: '',
    endDate: '',
    category: '',
    search: '',
  });

  const CATEGORIES = [
    "Income", "Transport", "Groceries", "Dining", 
    "Shopping & Retail", "Entertainment", "Bills"
  ]; // Hardcoded categories

  const fetchTransactions = async () => {
    try {
      const response = await transactionsAPI.getAll();
      setTransactions(response.data.transactions);
    } catch (error) {
      console.error('Error fetching transactions:', error);
    }
  };

  const fetchAccounts = async () => {
      try {
        const response = await accountsAPI.getAll();
        setAccounts(response.data.accounts || []);
      } catch (err) {
        console.error('Error fetching accounts:', err);
      }
    };

  // Initial load of transactions and accounts
  useEffect(() => {
    fetchTransactions();
    fetchAccounts();
  }, []);

  const handleAccountChange = () => {
    fetchAccounts(); // Refresh accounts list when added/deleted
  };

  const handleAddTransaction = async (transactionData) => {
    try {
      await transactionsAPI.create(transactionData);
      await fetchTransactions(); // refresh table
    } catch (error) {
      console.error('Error adding transaction:', error);
      throw new Error();
    }
  };

  const handleUpdateTransaction = async (id, updatedData) => {
      try {
        await transactionsAPI.update(id, updatedData);
        setEditingTransaction(null); // Close the popup
        await fetchTransactions(); // Refresh the table
      } catch (error) {
        console.error('Error updating transaction:', error);
        alert('Failed to update transaction');
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
    setTransactions(prev =>
      prev.filter(t => !ids.includes(t.id))
    );

    try {
      await transactionsAPI.deleteMultiple(ids);
      await fetchTransactions(); // refresh table
    } catch (error) {
      console.error(error);
      alert('Failed to delete transactions');
      fetchTransactions(); // rollback if needed
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
  // const categories = [...new Set(transactions.map(t => t.category))].sort();

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
          <AccountManager 
            accounts={accounts} // Pass down lifted state
            onAccountChange={handleAccountChange}
          />
          
          <CsvUploader onUploadSuccess={handleUploadSuccess} accounts={accounts} />
          <TransactionForm onSubmit={handleAddTransaction} accounts={accounts} categories={CATEGORIES} />
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
                  {CATEGORIES.map(category => (
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
            onEdit={(transaction) => setEditingTransaction(transaction)} // Handle edit click
          />
        </div>
      </div>

      {editingTransaction && (
        <EditTransactionBox 
          transaction={editingTransaction}
          accounts={accounts}
          onClose={() => setEditingTransaction(null)}
          onSave={handleUpdateTransaction}
        />
      )}
    </div>
  );
};

export default Transactions;