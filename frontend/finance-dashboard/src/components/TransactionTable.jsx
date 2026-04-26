// src/components/TransactionTable.jsx
import React, { useState, useMemo } from 'react';
import { formatCurrency, formatDate, getCategoryColor } from '../utils/format';
import { FaTrash, FaPencilAlt, FaChevronLeft, FaChevronRight } from "react-icons/fa";
import './TransactionTable.css';

const TransactionTable = ({ 
  transactions, 
  onDelete, 
  onDeleteMultiple,
  onEdit,
}) => {
  const [selectedRows, setSelectedRows] = useState(new Set());
  const [sortConfig, setSortConfig] = useState({ key: 'date', direction: 'desc' });

  // Pagination State
  const [currentPage, setCurrentPage] = useState(1);
  const [rowsPerPage, setRowsPerPage] = useState(10);

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

  // Sorting Logic
  const sortedTransactions = useMemo(() => {
    const sortableItems = [...transactions];
    sortableItems.sort((a, b) => {
      let aValue = a[sortConfig.key];
      let bValue = b[sortConfig.key];

      if (sortConfig.key === 'amount' || sortConfig.key === 'id') {
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

    return sortableItems;
  }, [transactions, sortConfig]);

  // Pagination Logic
  const totalPages = Math.ceil(sortedTransactions.length / rowsPerPage);
  const indexOfLastRow = currentPage * rowsPerPage;
  const indexOfFirstRow = indexOfLastRow - rowsPerPage;
  const currentRows = sortedTransactions.slice(indexOfFirstRow, indexOfLastRow);

  const getPaginationGroup = () => {
    const pageLimit = 5; // How many numbers to show around current page
    let pages = [];
    
    if (totalPages <= 7) {
      // If total pages is small, show all
      for (let i = 1; i <= totalPages; i++) pages.push(i);
    } else {
      // Always include the first page
      pages.push(1);

      if (currentPage > 4) pages.push('...');

      const start = Math.max(2, currentPage - 3);
      const end = Math.min(totalPages - 1, currentPage + 3);

      for (let i = start; i <= end; i++) {
        pages.push(i);
      }

      if (currentPage < totalPages - 3) pages.push('...');

      // Always include the last page
      pages.push(totalPages);
    }
    return pages;
  };

  const paginate = (pageNumber) => {
    if (pageNumber >= 1 && pageNumber <= totalPages) {
      setCurrentPage(pageNumber);
    }
  };

  const handleDeleteSelected = async () => {
    if (selectedRows.size === 0) return;
    
    if (window.confirm(`Are you sure you want to delete ${selectedRows.size} selected transaction(s)?`)) {
      await onDeleteMultiple(Array.from(selectedRows));
      setSelectedRows(new Set());
    }
  };

  const PaginationControls = () => (
    <div className="pagination-controls">
      <div className="page-size-selector">
        <label>Rows per page:</label>
        <select value={rowsPerPage} onChange={(e) => { setRowsPerPage(parseInt(e.target.value)); setCurrentPage(1); }}>
          <option value={5}>5</option>
          <option value={10}>10</option>
          <option value={25}>25</option>
          <option value={50}>50</option>
        </select>
      </div>

      <div className="pagination-navigation">
        <button 
          onClick={() => paginate(currentPage - 1)} 
          disabled={currentPage === 1}
          className="page-btn"
        >
          <FaChevronLeft />
        </button>
        
        <div className="page-numbers">
          {getPaginationGroup().map((item, index) => (
            item === '...' ? (
              <span key={`ellipses-${index}`} className="pagination-ellipsis">...</span>
            ) : (
              <button 
                key={item} 
                onClick={() => paginate(item)}
                className={`page-num-btn ${currentPage === item ? 'active' : ''}`}
              >
                {item}
              </button>
            )
          ))}
        </div>

        <button 
          onClick={() => paginate(currentPage + 1)} 
          disabled={currentPage === totalPages || totalPages === 0}
          className="page-btn"
        >
          <FaChevronRight />
        </button>
      </div>
      
      <div className="page-info">
        Page {currentPage} of {totalPages || 1}
      </div>
    </div>
  );

  return (
    <div className="transaction-table-container">
      <div className="table-header">
        <div className="header-left">
          <h3>Transaction History</h3>
          <span className="total-count">({transactions.length} total)</span>
        </div>
        <div className="header-right">
          {selectedRows.size > 0 && (
            <button 
              onClick={handleDeleteSelected}
              className="delete-selected-btn"
            >
              <FaTrash className="btn-icon" /> Delete Selected ({selectedRows.size})
            </button>
          )}
        </div>
      </div>

    <PaginationControls />
      
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
            {currentRows.map((transaction) => (
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
                  <div className="action-buttons">
                    <button
                      onClick={() => onEdit(transaction)}
                      className="edit-btn-icon"
                      title="Edit transaction"
                    >
                      <FaPencilAlt />
                    </button>
                    <button
                      onClick={async () => {
                        if (window.confirm('Are you sure you want to delete this transaction?')) {
                          onDelete(transaction.id);
                          
                          // Clear from selectedRows if it was checked
                          const newSelected = new Set(selectedRows);
                          newSelected.delete(transaction.id);
                          setSelectedRows(newSelected);
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
      
      {transactions.length > 0 && <PaginationControls />}
      
      {transactions.length === 0 && (
        <div className="empty-state">
          <p>No transactions found. Upload a CSV file or add a transaction manually.</p>
        </div>
      )}
    </div>
  );
};

export default TransactionTable;