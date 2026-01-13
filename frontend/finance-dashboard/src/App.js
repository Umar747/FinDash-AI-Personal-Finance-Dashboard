// src/App.js
import React from 'react';
import Header from './components/Header';
import HomePage from './pages/HomePage';
import './App.css';

function App() {
  return (
    <div className="App">
      <Header />
      <HomePage />
      <footer className="footer">
        <p>Final Year Project - UCL Computer Science | AI-Powered Personal Finance Dashboard</p>
        <p className="footer-note">Created by Umar Ali</p>
      </footer>
    </div>
  );
}

export default App;