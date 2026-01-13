// src/components/Header.jsx
import React from 'react';
import './Header.css';

const Header = () => {
  return (
    <header className="header">
      <div className="logo">
        <h1>FinDash AI</h1>
        <p className="tagline">AI-Powered Personal Finance Dashboard</p>
      </div>
      <nav className="nav">
        <button className="nav-btn active">Dashboard</button>
        <button className="nav-btn">Transactions</button>
        <button className="nav-btn">Analytics</button>
        <button className="nav-btn">Forecast</button>
      </nav>
    </header>
  );
};

export default Header;