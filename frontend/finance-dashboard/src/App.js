// src/App.js
import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import Header from './components/Header';
import HomePage from './pages/HomePage';
import Transactions from './pages/Transactions';
import './App.css';
import Insights from './pages/Insights';
import Chat from './pages/Chat';

function App() {
  return (
    <div className="App">
    <Header />
    <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/transactions" element={<Transactions />} />
        <Route path="/insights" element={<Insights />} />
        <Route path="/chat" element={<Chat />} />
    </Routes>
    <footer className="footer">
        <p>Final Year Project - UCL Computer Science | AI-Powered Personal Finance Dashboard</p>
        <p className="footer-note">Created by Umar Ali</p>
    </footer>
    </div>
  );
}

export default App;