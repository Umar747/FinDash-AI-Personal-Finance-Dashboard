// src/components/Header.jsx
import React from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import './Header.css';

const Header = () => {
  const { isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };
  
  const isActive = (path) => {
    return location.pathname === path ? 'active' : '';
  };

  return (
    <header className="header">
      <div className="header-container">
        <div className="logo">
          <Link to="/" style={{ textDecoration: 'none', color: 'white' }}>
            <h1>FinDash AI</h1>
          </Link>
          <p className="tagline">AI-Powered Personal Finance Dashboard</p>
        </div>

        {/* Only show navigation if authenticated */}
        {isAuthenticated && (
          <nav className="nav-links">
            <Link to="/" className={`nav-btn ${isActive('/')}`}>
              Home
            </Link>
            <Link to="/transactions" className={`nav-btn ${isActive('/transactions')}`}>
              Transactions
            </Link>
            <Link to="/insights" className={`nav-btn ${isActive('/insights')}`}>
              Insights
            </Link>
            <Link to="/chat" className={`nav-btn ${isActive('/chat')}`}>
              Chat
            </Link>
            <button onClick={handleLogout} className="logout-button">
              Logout
            </button>
          </nav>
        )}

        {!isAuthenticated && (
          <div className="nav-links">
            <Link to="/login" className={`nav-btn ${isActive('/login')}`}>Login</Link>
          </div>
        )}
      </div>
    </header>
  );
};

export default Header;