// src/pages/HomePage.jsx
import React from 'react';
import { useNavigate } from 'react-router-dom';
import { FaUpload } from 'react-icons/fa';
import './HomePage.css';

const HomePage = () => {
  const navigate = useNavigate();
  return (
    <div className="homepage">
      <div className="hero">
        <h2>Transform Your Financial Data Into Actionable Insights</h2>
        <p className="subtitle">
          Upload bank statements, get AI-powered categorisation, 
          and predict future spending with machine learning.
        </p>
        
        <div className="cta-section">
          <button className="primary-btn" onClick={() => navigate('/transactions')}>
            <FaUpload /> Upload Statement
          </button>
          <button className="secondary-btn" onClick={() => navigate('/insights')}>
            Go to Analytics (Next Step)
          </button>
        </div>
      </div>

      <div className="features">
        <div className="feature-card">
          <div className="feature-icon">🤖</div>
          <h3>AI Categorisation</h3>
          <p>Machine learning automatically categorises your transactions using NLP.</p>
        </div>
        
        <div className="feature-card">
          <div className="feature-icon">📈</div>
          <h3>Predictive Analytics</h3>
          <p>Our tailored models forecast your future spending patterns.</p>
        </div>
        
        <div className="feature-card">
          <div className="feature-icon">🎯</div>
          <h3>Smart Insights</h3>
          <p>Get personalised recommendations to optimise your finances.</p>
        </div>
      </div>

      <div className="tech-stack">
        <h3>Technical Stack</h3>
        <div className="tech-icons">
          <span className="tech-icon">⚛️ React</span>
          <span className="tech-icon">🐍 Flask</span>
          <span className="tech-icon">🧠 Scikit-Learn</span>
          <span className="tech-icon">📊 PostgreSQL</span>
          <span className="tech-icon">🤗 Transformers</span>
        </div>
      </div>

    </div>
  );
};

export default HomePage;