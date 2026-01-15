// src/components/Header.jsx
import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import './Header.css';

const Header = () => {
  const location = useLocation();
  
  const isActive = (path) => {
    return location.pathname === path ? 'active' : '';
  };

  return (
    <header className="header">
      <div className="logo">
        <Link to="/" style={{ textDecoration: 'none', color: 'white' }}>
          <h1>FinDash AI</h1>
        </Link>
        <p className="tagline">AI-Powered Personal Finance Dashboard</p>
      </div>
      <nav className="nav">
        <Link to="/" className={`nav-btn ${isActive('/')}`}>
          Dashboard
        </Link>
        <Link to="/transactions" className={`nav-btn ${isActive('/transactions')}`}>
          Transactions
        </Link>
        <button className="nav-btn">Analytics</button>
        <button className="nav-btn">Forecast</button>
      </nav>
    </header>
  );
};

export default Header;