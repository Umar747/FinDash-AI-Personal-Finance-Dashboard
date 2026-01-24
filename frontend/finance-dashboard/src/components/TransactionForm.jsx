// src/components/TransactionForm.jsx
import React, { useState } from 'react';
import './TransactionForm.css';

// Maybe use the categories stuff commented out in a future version, so user can enter category themselves if they want
// const TransactionForm = ({ onSubmit, categories = [] }) => {
const TransactionForm = ({ onSubmit }) => {
  const [formData, setFormData] = useState({
    date: new Date().toISOString().split('T')[0],
    description: '',
    amount: '',
    // category: '',
    account: 'HSBC Current Account',
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

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      if (onSubmit) {
        await onSubmit(formData);
      }

      // Reset form
      setFormData({
        date: new Date().toISOString().split('T')[0],
        description: '',
        amount: '',
        // category: '',
        account: 'HSBC Current Account',
      });

      // Show success message
      setSuccess('Transaction added successfully!');
      setTimeout(() => setSuccess(''), 5000);
    } catch (err) {
      console.error(err);
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
          <input
            type="text"
            name="account"
            value={formData.account}
            onChange={handleChange}
            placeholder="e.g., HSBC Current Account"
            required
          />
        </div>

        <button type="submit" className="submit-btn" disabled={loading}>
          {loading ? 'Adding...' : '+ Add Transaction'}
        </button>

        {success && <p className="success-text">{success}</p>}
        {error && <p className="error-text">{error}</p>}
      </form>
    </div>
  );
};

export default TransactionForm;
