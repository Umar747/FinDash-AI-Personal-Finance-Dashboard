// src/components/CsvUploader.jsx
import React, { useState } from 'react';
import { transactionsAPI } from '../services/api';
import { FaDownload, FaUpload, FaFolderOpen } from "react-icons/fa";
import './CsvUploader.css';

const CsvUploader = ({ onUploadSuccess }) => {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

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
    setUploadProgress(0);

    const formData = new FormData();
    formData.append('file', file);

    try {
      // Simulate progress for demonstration
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return 90;
          }
          return prev + 10;
        });
      }, 200);

      // For now, simulate API call (replace with actual when backend is ready)
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      clearInterval(progressInterval);
      setUploadProgress(100);

      // Uncomment when backend is ready:
      // const response = await transactionsAPI.uploadCSV(formData);
      
      // For now, use mock response
      const mockResponse = {
        data: {
          message: 'File uploaded successfully',
          transactions: 45,
          processed: true,
        }
      };

      setSuccess(`Successfully uploaded ${mockResponse.data.transactions} transactions`);
    //   onUploadSuccess(mockResponse.data.transactions);
      
      // Reset after 5 seconds
      setTimeout(() => {
        setSuccess('');
        setUploadProgress(0);
      }, 5000);

    } catch (err) {
      setError(err.response?.data?.message || 'Upload failed. Please try again.');
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="csv-uploader-container">
      <h3>Upload Bank Statement (CSV)</h3>
      <p className="upload-description">
        Upload your bank statement in CSV format. The system will automatically 
        categorize transactions using AI and add them to your dashboard.
      </p>

      <div
        className={`upload-area ${isDragging ? 'dragging' : ''} ${isUploading ? 'uploading' : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => !isUploading && document.getElementById('file-input').click()}
      >
        <input
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
              <p>Uploading... {uploadProgress}%</p>
              <div className="progress-bar">
                <div 
                  className="progress-fill" 
                  style={{ width: `${uploadProgress}%` }}
                ></div>
              </div>
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
          <li><a href="/sample.csv" download="sample-statement.csv"><FaDownload /> Download sample CSV</a></li>
        </ul>
      </div>
    </div>
  );
};

export default CsvUploader;