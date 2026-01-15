// src/components/TransactionForm.jsx
import React, { useState } from 'react';
import './TransactionForm.css';

const TransactionForm = ({ onSubmit, categories = [] }) => {
  const [formData, setFormData] = useState({
    date: new Date().toISOString().split('T')[0],
    description: '',
    amount: '',
    category: '',
    account: 'HSBC Current',
    type: 'debit',
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    
    const transaction = {
      ...formData,
      amount: formData.type === 'debit' ? -Math.abs(parseFloat(formData.amount)) : Math.abs(parseFloat(formData.amount)),
    };
    
    onSubmit(transaction);
    
    // Reset form
    setFormData({
      date: new Date().toISOString().split('T')[0],
      description: '',
      amount: '',
      category: '',
      account: 'HSBC Current',
      type: 'debit',
    });
  };

  const defaultCategories = [
    'Income', 'Shopping', 'Groceries', 'Transport', 
    'Entertainment', 'Food & Dining', 'Health & Fitness', 
    'Bills', 'Education', 'Other'
  ];

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
          
          <div className="form-group">
            <label>Type</label>
            <select
              name="type"
              value={formData.type}
              onChange={handleChange}
              className="type-select"
            >
              <option value="debit">Expense (-)</option>
              <option value="credit">Income (+)</option>
            </select>
          </div>
        </div>

        <div className="form-group">
          <label>Description</label>
          <input
            type="text"
            name="description"
            value={formData.description}
            onChange={handleChange}
            placeholder="e.g., Tesco Supermarket, Salary Deposit"
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
              min="0"
              step="0.01"
              placeholder="0.00"
              required
            />
          </div>

          <div className="form-group">
            <label>Category</label>
            <select
              name="category"
              value={formData.category}
              onChange={handleChange}
              required
            >
              <option value="">Select a category</option>
              {(categories.length > 0 ? categories : defaultCategories).map(category => (
                <option key={category} value={category}>{category}</option>
              ))}
            </select>
          </div>
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

        <button type="submit" className="submit-btn">
          + Add Transaction
        </button>
      </form>
    </div>
  );
};

export default TransactionForm;