// src/components/TransactionTable.jsx
import React, { useState } from 'react';
import { formatCurrency, formatDate, getCategoryColor } from '../utils/format';
import { FaTrash, FaPencilAlt } from "react-icons/fa";
import './TransactionTable.css';

const TransactionTable = ({ 
  transactions, 
  onDelete, 
  onDeleteMultiple,
  onEdit,
}) => {
  const [selectedRows, setSelectedRows] = useState(new Set());
  const [sortConfig, setSortConfig] = useState({ key: 'date', direction: 'desc' });

  const handleSelectRow = (id) => {
    const newSelected = new Set(selectedRows);
    if (newSelected.has(id)) {
      newSelected.delete(id);
    } else {
      newSelected.add(id);
    }
    setSelectedRows(newSelected);
  };

  const handleSelectAll = (e) => {
    if (e.target.checked) {
      const allIds = transactions.map(t => t.id);
      setSelectedRows(new Set(allIds));
    } else {
      setSelectedRows(new Set());
    }
  };

  const handleSort = (key) => {
    setSortConfig(prev => ({
      key,
      direction: prev.key === key && prev.direction === 'asc' ? 'desc' : 'asc'
    }));
  };

  const sortedTransactions = [...transactions].sort((a, b) => {
    let aValue = a[sortConfig.key];
    let bValue = b[sortConfig.key];

    // Convert to float if sorting by amount
    if (sortConfig.key === 'amount') {
        aValue = parseFloat(aValue);
        bValue = parseFloat(bValue);
    }

    if (aValue < bValue) {
        return sortConfig.direction === 'asc' ? -1 : 1;
    }
    if (aValue > bValue) {
        return sortConfig.direction === 'asc' ? 1 : -1;
    }
    return 0;
  });

  const handleDeleteSelected = async () => {
    if (selectedRows.size === 0) return;
    
    if (window.confirm(`Are you sure you want to delete ${selectedRows.size} selected transaction(s)?`)) {
      await onDeleteMultiple(Array.from(selectedRows));
      setSelectedRows(new Set());
    }
  };

  return (
    <div className="transaction-table-container">
      <div className="table-header">
        <h3>Transaction History</h3>
        {selectedRows.size > 0 && (
          <button 
            onClick={handleDeleteSelected}
            className="delete-selected-btn"
          >
            <FaTrash className="btn-icon" /> Delete Selected ({selectedRows.size})
          </button>
        )}
      </div>
      
      <div className="table-wrapper">
        <table className="transaction-table">
          <thead>
            <tr>
              <th style={{ width: '50px' }}>
                <input
                  type="checkbox"
                  onChange={handleSelectAll}
                  checked={selectedRows.size === transactions.length && transactions.length > 0}
                />
              </th>
              <th onClick={() => handleSort('id')} className="sortable">
                ID {sortConfig.key === 'id' && (sortConfig.direction === 'asc' ? '↑' : '↓')}
              </th>
              <th onClick={() => handleSort('date')} className="sortable">
                Date {sortConfig.key === 'date' && (sortConfig.direction === 'asc' ? '↑' : '↓')}
              </th>
              <th onClick={() => handleSort('description')} className="sortable">
                Description {sortConfig.key === 'description' && (sortConfig.direction === 'asc' ? '↑' : '↓')}
              </th>
              <th onClick={() => handleSort('amount')} className="sortable">
                Amount {sortConfig.key === 'amount' && (sortConfig.direction === 'asc' ? '↑' : '↓')}
              </th>
              <th onClick={() => handleSort('category')} className="sortable">
                Category {sortConfig.key === 'category' && (sortConfig.direction === 'asc' ? '↑' : '↓')}
              </th>
              <th>Account</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {sortedTransactions.map((transaction) => (
              <tr 
                key={transaction.id}
                className={selectedRows.has(transaction.id) ? 'selected' : ''}
              >
                <td>
                  <input
                    type="checkbox"
                    checked={selectedRows.has(transaction.id)}
                    onChange={() => handleSelectRow(transaction.id)}
                  />
                </td>
                <td>{transaction.id}</td>
                <td>{formatDate(transaction.date)}</td>
                <td className="description">{transaction.description}</td>
                <td className={`amount ${transaction.amount >= 0 ? 'credit' : 'debit'}`}>
                  {formatCurrency(transaction.amount)}
                </td>
                <td>
                  <span 
                    className="category-badge"
                    style={{ backgroundColor: getCategoryColor(transaction.category) }}
                  >
                    {transaction.category}
                  </span>
                </td>
                <td>{transaction.account}</td>
                <td>
                  <div className="action-buttons" style={{ display: 'flex', gap: '10px' }}>
                    <button
                      onClick={() => onEdit(transaction)}
                      className="edit-btn"
                      title="Edit transaction"
                      style={{ 
                        background: 'none', 
                        border: 'none', 
                        color: '#4a90e2', 
                        cursor: 'pointer',
                        fontSize: '1rem' 
                      }}
                    >
                      <FaPencilAlt />
                    </button>
                    <button
                      onClick={async () => {
                        if (window.confirm('Are you sure you want to delete this transaction?')) {
                          onDelete(transaction.id);
                        }
                      }}
                      className="delete-btn"
                      title="Delete transaction"
                    >
                      <FaTrash />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      
      {transactions.length === 0 && (
        <div className="empty-state">
          <p>No transactions found. Upload a CSV file or add a transaction manually.</p>
        </div>
      )}
    </div>
  );
};

export default TransactionTable;