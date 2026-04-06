// src/components/EditTransactionBox.jsx
import React, { useState } from 'react';
import './TransactionForm.css'; // Reusing existing form styles

const EditTransactionBox = ({ transaction, accounts, onClose, onSave }) => {
  const [formData, setFormData] = useState({
    date: transaction.date,
    description: transaction.description,
    amount: transaction.amount,
    category: transaction.category,
    account_id: accounts.find(a => a.account === transaction.account)?.id || ""
  });

  const categories = ["Income", "Transport", "Groceries", "Dining", "Shopping & Retail", "Entertainment", "Bills"];

  const handleSubmit = (e) => {
    e.preventDefault();
    onSave(transaction.id, formData);
  };

  return (
    <div className="modal-overlay" style={{
      position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, 
      backgroundColor: 'rgba(0, 0, 0, 0.6)',
      display: 'flex', justifyContent: 'center', alignItems: 'center', 
      zIndex: 1000, backdropFilter: 'blur(2px)'
    }}>
      <div className="modal-content" style={{ 
        backgroundColor: 'white', 
        padding: '2rem', 
        borderRadius: '12px',
        width: '100%',
        maxWidth: '450px', 
        boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)' 
      }}>
        <h3 style={{ marginBottom: '1.5rem', fontSize: '1.25rem', color: '#1a202c' }}>Edit Transaction</h3>
        
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Date</label>
            <input type="date" value={formData.date} onChange={e => setFormData({...formData, date: e.target.value})} required />
          </div>
          
          <div className="form-group">
            <label>Description</label>
            <input type="text" value={formData.description} onChange={e => setFormData({...formData, description: e.target.value})} required />
          </div>
          
          <div className="form-group">
            <label>Amount</label>
            <input type="number" step="0.01" value={formData.amount} onChange={e => setFormData({...formData, amount: e.target.value})} required />
          </div>
          
          <div className="form-group">
            <label>Category</label>
            <select value={formData.category} onChange={e => setFormData({...formData, category: e.target.value})} required>
              {categories.map(cat => <option key={cat} value={cat}>{cat}</option>)}
            </select>
          </div>
          
          <div className="form-group">
            <label>Account</label>
            <select value={formData.account_id} onChange={e => setFormData({...formData, account_id: e.target.value})} required>
              <option value="">Select Account</option>
              {accounts.map(acc => (
                <option key={acc.id} value={acc.id}>ID: {acc.id} - {acc.account}</option>
              ))}
            </select>
          </div>

          <div style={{ 
            marginTop: '2rem', 
            display: 'flex', 
            flexDirection: 'row-reverse',
            gap: '12px' 
          }}>
            <button type="submit" className="submit-btn" style={{ margin: 0, flex: 1 }}>
              Save Changes
            </button>
            
            <button 
              type="button" 
              onClick={onClose} 
              style={{
                flex: 1,
                padding: '0.75rem 1rem',
                borderRadius: '6px',
                border: '1px solid #e2e8f0',
                backgroundColor: 'white',
                color: '#4a5568',
                fontWeight: '500',
                cursor: 'pointer',
                transition: 'all 0.2s'
              }}
              onMouseOver={(e) => {
                e.target.style.backgroundColor = '#f7fafc';
                e.target.style.borderColor = '#cbd5e0';
              }}
              onMouseOut={(e) => {
                e.target.style.backgroundColor = 'white';
                e.target.style.borderColor = '#e2e8f0';
              }}
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default EditTransactionBox;