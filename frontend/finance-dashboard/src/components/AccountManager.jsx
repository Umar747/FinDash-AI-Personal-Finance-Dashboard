import React, { useState, useEffect } from 'react';
import { FaChevronDown, FaChevronUp, FaPlus, FaTrash, FaCreditCard, FaBuilding } from 'react-icons/fa';
import { accountsAPI } from '../services/api';
import './AccountManager.css';

const AccountManager = ({ accounts, onAccountChange }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [newAccountName, setNewAccountName] = useState('');
  const [isCreating, setIsCreating] = useState(false);
  const [toast, setToast] = useState(null);

  const showToast = (type, message) => {
    setToast({ type, message });
    setTimeout(() => {
      setToast(null);
    }, 5000);
  };

  const handleCreateAccount = async (e) => {
    e.preventDefault();
    if (!newAccountName.trim()) {
      setError('Account name is required');
      return;
    }

    setIsCreating(true);
    try {
      await accountsAPI.create({
        account_name: newAccountName.trim()
      });
      
      // Notify parent component to refresh the accounts state
      if (onAccountChange) {
        onAccountChange();
      }
      
      // Clear form
      setNewAccountName('');
      setError('');
      
      showToast('success', 'Account created successfully!');
    } catch (err) {
      console.error('Error creating account:', err);
      setError(err.response?.data?.error || 'Failed to create account');
    } finally {
      setIsCreating(false);
    }
  };

  const handleDeleteAccount = async (accountId, accountName) => {
    if (!window.confirm(`Are you sure you want to delete "${accountName}"? This action cannot be undone.`)) {
      return;
    }

    try {
      await accountsAPI.delete(accountId);
      
      // Notify parent component to refresh the accounts state
      if (onAccountChange) {
        onAccountChange();
      }
      
      showToast('success', 'Account deleted successfully!');
    } catch (err) {
      console.error('Error deleting account:', err);
      showToast('error', err.response?.data?.error || 'Failed to delete account');
    }
  };

  return (
    <div className={`account-manager-container ${isExpanded ? 'expanded' : 'collapsed'}`}>
      <div 
        className="account-manager-header"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="header-content">
          <FaBuilding className="header-icon" />
          <div className="header-text">
            <h3>Bank Account Management</h3>
            {!isExpanded && (
              <p className="collapsed-subtitle">
                Manage your connected bank accounts
                {accounts && accounts.length > 0 && (
                    <>
                    <br />
                    ({accounts.length} accounts)
                    </>
                )}
              </p>
            )}
          </div>
        </div>
        <div className="header-toggle">
          {isExpanded ? <FaChevronUp /> : <FaChevronDown />}
        </div>
      </div>

      {isExpanded && (
        <div className="account-manager-content">
          <div className="create-account-section">
            <h4>Add New Bank Account</h4>
            <form onSubmit={handleCreateAccount} className="account-form">
              <div className="form-group">
                <label htmlFor="accountName">
                  <FaCreditCard className="input-icon" /> Account Name
                </label>
                <input
                  id="accountName"
                  type="text"
                  value={newAccountName}
                  onChange={(e) => setNewAccountName(e.target.value)}
                  placeholder="e.g., HSBC Current Account, Monzo Max"
                  disabled={isCreating}
                  required
                />
                <p className="input-hint">
                  This is the display name for your bank account
                </p>
              </div>
              
              <button 
                type="submit" 
                className="create-account-btn"
                disabled={isCreating || !newAccountName.trim()}
              >
                <FaPlus className="btn-icon" />
                {isCreating ? 'Creating...' : 'Add Account'}
              </button>
            </form>
          </div>

          {toast && (
            <div className={`toast-message ${toast.type}`}>
              {toast.message}
            </div>
          )}

          <div className="accounts-list-section">
            <div className="section-header">
              <h4>Your Bank Accounts</h4>
              <span className="account-count">{accounts?.length || 0} account(s)</span>
            </div>
            
            {error && (
              <div className="error-state">
                <p>{error}</p>
                <button 
                  onClick={() => setError('')}
                  className="retry-btn"
                >
                  Dismiss
                </button>
              </div>
            )}
            
            {!accounts || accounts.length === 0 ? (
              <div className="empty-state">
                <p>No bank accounts added yet. Add your first account above.</p>
              </div>
            ) : (
              <div className="accounts-grid">
                {accounts.map((account) => (
                  <div key={account.id} className="account-card">
                    <div className="account-info">
                      <div className="account-details">
                        <span className="account-name">{account.account}</span>
                        <span className="account-id">ID: {account.id}</span>
                      </div>
                    </div>
                    <button
                      onClick={() => handleDeleteAccount(account.id, account.account)}
                      className="delete-account-btn"
                      title="Delete account"
                    >
                      <FaTrash />
                    </button>
                  </div>
                ))}
              </div>
            )}
            
            <div className="account-notes">
              <p className="note">
                💡 <strong>Note:</strong> Adding accounts here helps organise your transactions. 
                You'll be able to select which account a transaction belongs to when adding manually.
              </p>
              <p className="note">
                🔒 <strong>Security:</strong> We don't store your actual bank login credentials. 
                You'll need to upload statements manually for each account.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AccountManager;