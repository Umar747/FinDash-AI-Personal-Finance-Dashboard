// src/components/TransactionForm.jsx
import React, { useEffect, useState } from 'react';
import './TransactionForm.css';

// Maybe use the categories stuff commented out in a future version, so user can enter category themselves if they want
// const TransactionForm = ({ onSubmit, categories = [] }) => {
const TransactionForm = ({ onSubmit, accounts, userId = 1 }) => {
  const [formData, setFormData] = useState({
    date: new Date().toISOString().split('T')[0],
    description: '',
    amount: '',
    // category: '',
    account_id: '',
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleClear = () => {
    setFormData({
      date: new Date().toISOString().split('T')[0],
      description: '',
      amount: '',
      account_id: '',
    });
    setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    
    // Check if accounts array exists and has data
    if (!accounts || accounts.length === 0) {
      setError('Please add a bank account in the Bank Account Management section above before adding transactions.');
      return;
    }

    // Check if an account was actually selected
    if (!formData.account_id) {
      setError('Please select an account from the dropdown.');
      return;
    }

    setLoading(true);

    try {
      if (onSubmit) {
        const selectedAccount = accounts.find(acc => acc.id.toString() === formData.account_id);

        const transactionData = {
          ...formData,
          account: selectedAccount ? selectedAccount.account : '',
        };

        await onSubmit(transactionData);
      }

      // Reset form
      handleClear();

      // Show success message
      setSuccess('Transaction added successfully!');
      setTimeout(() => setSuccess(''), 5000);
    } catch (err) {
      console.error(err);

      // Show error message
      setError(err.message || 'Failed to create transaction');
    } finally {
      // Remove success message after 5 seconds
      setLoading(false);
    }
  };

  // const defaultCategories = ['Income', 'Shopping', 'Groceries', 'Transport', 'Entertainment', 'Food & Dining', 'Health & Fitness', 'Bills', 'Education', 'Other'];
  // const allCategories = Array.from(new Set([...categories, ...defaultCategories]));

  return (
    <div className="transaction-form-container">
      <h3>Add New Transaction</h3>
      <form onSubmit={handleSubmit} className="transaction-form">
        <div className="form-row">
          <div className="form-group">
            <label>Date</label>
            <input
              type="date"
              name="date"
              value={formData.date}
              onChange={handleChange}
              required
            />
          </div>
        </div>

        <div className="form-group">
          <label>Description</label>
          <input
            type="text"
            name="description"
            value={formData.description}
            onChange={handleChange}
            placeholder="e.g. Tesco Supermarket, Salary Deposit"
            required
          />
        </div>

        <div className="form-row">
          <div className="form-group">
            <label>Amount (£)</label>
            <input
              type="number"
              name="amount"
              value={formData.amount}
              onChange={handleChange}
              step="0.01"
              placeholder="0.00"
              required
            />
          </div>

          {/* <div className="form-group">
            <label>Category</label>
            <select
              name="category"
              value={formData.category}
              onChange={handleChange}
              required
            >
              <option value="">Select a category</option>
              {allCategories.map(category => (
                <option key={category} value={category}>{category}</option>
              ))}
            </select>
          </div> */}
        </div>

        <div className="form-group">
          <label>Account</label>
          {!accounts || accounts.length === 0 ? (
            <div className="no-accounts">
              <span className="warning-text">No accounts available.</span>
              <p className="account-hint">
                Please add bank accounts in the Account Manager above.
              </p>
            </div>
          ) : (
            <select
              name="account_id"
              value={formData.account_id}
              onChange={handleChange}
              required
            >
              <option value="">Select an account</option>
              {accounts.map(account => (
                <option key={account.id} value={account.id}>
                  {account.account} (ID: {account.id})
                </option>
              ))}
            </select>
          )}
        </div>

        <div style={{ 
          marginTop: '1.5rem', 
          display: 'flex', 
          flexDirection: 'row-reverse', 
          gap: '12px' 
        }}>
          <button type="submit" className="submit-btn" disabled={loading} style={{ margin: 0, flex: 1 }}>
            {loading ? 'Adding...' : '+ Add Transaction'}
          </button>

          <button 
            type="button" 
            onClick={handleClear}
            className="clear-btn"
          >
            Clear
          </button>
        </div>

        {success && <p className="success-text" >{success}</p>}
        {error && <p className="error-text" >{error}</p>}
      </form>
    </div>
  );
};

export default TransactionForm;