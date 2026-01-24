// src/components/CsvUploader.jsx
import React, { useState, useRef } from 'react';
import { transactionsAPI } from '../services/api';
import { FaDownload, FaUpload, FaFolderOpen } from "react-icons/fa";
import './CsvUploader.css';

const CsvUploader = ({ onUploadSuccess }) => {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const fileInputRef = useRef(null);

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleFile(files[0]);
    }
  };

  const handleFileInput = (e) => {
    const file = e.target.files[0];
    if (file) {
      handleFile(file);
    }
  };

  const handleFile = async (file) => {
    // Check file type
    if (!file.name.toLowerCase().endsWith('.csv')) {
      setError('Please upload a CSV file');
      return;
    }

    // Check file size (max 10MB)
    if (file.size > 10 * 1024 * 1024) {
      setError('File size must be less than 10MB');
      return;
    }

    setIsUploading(true);
    setError('');
    setSuccess('');

    const formData = new FormData();
    formData.append('csvFile', file);

    try {
      const response = await transactionsAPI.uploadCSV(formData);

      setSuccess(`Successfully uploaded ${response.data.transactions} transactions`);
      onUploadSuccess();
      
      // Remove success message after 5 seconds
      setTimeout(() => {
        setSuccess('');
      }, 5000);

    } catch (err) {
      setError(err.response?.data?.message || 'Upload failed. Please try again.');
      console.log(err.message)
    } finally {
      setIsUploading(false);

      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  return (
    <div className="csv-uploader-container">
      <h3>Upload Bank Statement (CSV)</h3>
      <p className="upload-description">
        Upload your bank statement in CSV format. The system will automatically categorise transactions using AI and add them to your dashboard.
      </p>

      <div
        className={`upload-area ${isDragging ? 'dragging' : ''} ${isUploading ? 'uploading' : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => !isUploading && document.getElementById('file-input').click()}
      >
        <input
          ref={fileInputRef}
          id="file-input"
          type="file"
          accept=".csv"
          onChange={handleFileInput}
          disabled={isUploading}
          style={{ display: 'none' }}
        />
        
        <div className="upload-content">
          {isUploading ? (
            <>
              <div className="upload-icon"><FaUpload /></div>
              <p>Uploading your CSV…</p>
              <div className="spinner" />
            </>
          ) : (
            <>
              <div className="upload-icon"><FaFolderOpen /></div>
              <p className="upload-text">
                <strong>Drag & drop your CSV file here</strong>
                <span className="upload-subtext">or click to browse</span>
              </p>
              <p className="file-requirements">
                CSV files only • Max 10MB • Supported banks: HSBC, Barclays, Santander, Monzo
              </p>
            </>
          )}
        </div>
      </div>

      {error && (
        <div className="error-message">
          ⚠️ {error}
        </div>
      )}

      {success && (
        <div className="success-message">
          {success}
        </div>
      )}

      <div className="csv-guide">
        <h4>CSV Format Guide:</h4>
        <ul>
          <li>Required columns: <code>Date</code>, <code>Description</code>, <code>Amount</code></li>
          <li>Date format: <code>YYYY-MM-DD</code> or <code>DD/MM/YYYY</code></li>
          <li>Amount format: Positive for credits, negative for debits</li>
          <li><a href="sample-statement.csv" download><FaDownload /> Download sample CSV</a></li>
        </ul>
      </div>
    </div>
  );
};

export default CsvUploader;