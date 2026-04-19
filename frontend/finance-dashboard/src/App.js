// src/App.js
import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './context/AuthContext';
import Header from './components/Header';
import HomePage from './pages/HomePage';
import Transactions from './pages/Transactions';
import './App.css';
import Insights from './pages/Insights';
import Chat from './pages/Chat';
import Auth from './pages/Auth'; // New Import
import './App.css';

// Component to protect routes
const ProtectedRoute = ({ children }) => {
  const { isAuthenticated } = useAuth();
  return isAuthenticated ? children : <Navigate to="/login" />;
};

function App() {
  return (
    <div className="App">
    <Header />
    <Routes>
      {/* Public Route */}
      <Route path="/login" element={<Auth />} />

      {/* Protected Routes */}
      <Route path="/" element={<ProtectedRoute><HomePage /></ProtectedRoute>} />
      <Route path="/transactions" element={<ProtectedRoute><Transactions /></ProtectedRoute>} />
      <Route path="/insights" element={<ProtectedRoute><Insights /></ProtectedRoute>} />
      <Route path="/chat" element={<ProtectedRoute><Chat /></ProtectedRoute>} />
    </Routes>
    <footer className="footer">
        <p>Final Year Project - UCL Computer Science | AI-Powered Personal Finance Dashboard</p>
        <p className="footer-note">Created by Umar Ali</p>
    </footer>
    </div>
  );
}

export default App;