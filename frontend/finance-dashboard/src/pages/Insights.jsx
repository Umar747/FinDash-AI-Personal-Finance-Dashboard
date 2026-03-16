import React, { useState, useEffect, useMemo } from 'react';
import { 
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, 
  AreaChart, Area, ReferenceLine, Line, ComposedChart, Legend, 
  PieChart, Pie, Cell 
} from 'recharts';
import { analyticsAPI, transactionsAPI } from '../services/api';
import { formatCurrency, getCategoryColor } from '../utils/format';
import './Insights.css';

const Insights = ({ userId = 1 }) => {
  const [data, setData] = useState([]);
  const [forecastPieData, setForecastPieData] = useState([]);
  const [pivotDate, setPivotDate] = useState(null);
  const [dateRange, setDateRange] = useState(90);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        const [historyRes, forecastRes] = await Promise.all([
          transactionsAPI.getAll(),
          analyticsAPI.getForecast(userId)
        ]);

        const rawHistory = historyRes.data.transactions || [];
        const rawForecasts = forecastRes.data.forecasts || [];

        // Filter out "Income" and aggregate by category
        const categoryMap = rawForecasts
          .filter(f => f.category !== 'Income')
          .reduce((acc, f) => {
            const amount = Math.abs(parseFloat(f.predicted_amount));
            acc[f.category] = (acc[f.category] || 0) + amount;
            return acc;
          }, {});

        const pieData = Object.entries(categoryMap).map(([name, value]) => ({
          name,
          value: Math.round(value * 100) / 100
        })).sort((a, b) => b.value - a.value); // Sort by highest spending

        setForecastPieData(pieData);

        console.log(pieData)

        const historyMap = rawHistory.reduce((acc, t) => {
          const date = t.date.split('T')[0];
          acc[date] = (acc[date] || 0) + parseFloat(t.amount);
          return acc;
        }, {});

        const forecastMap = rawForecasts.reduce((acc, f) => {
          const date = f.date; 
          acc[date] = (acc[date] || 0) + parseFloat(f.predicted_amount);
          return acc;
        }, {});

        let runningBalance = 0;
        const processed = [];

        // 3. Process Sorted History
        const sortedHistoryDates = Object.keys(historyMap).sort((a, b) => new Date(a) - new Date(b));
        sortedHistoryDates.forEach(date => {
          runningBalance += historyMap[date];
          processed.push({
            date: date,
            balance: Math.round(runningBalance * 100) / 100,
            type: 'historical'
          });
        });

        // Identify the pivot (The "Today" overlap)
        if (processed.length > 0) {
          const lastPoint = processed[processed.length - 1];
          setPivotDate(lastPoint.date); // Save this for filtering and the red line

          // 4. Create the Bridge Point for the chart
          processed.push({
            date: lastPoint.date,
            balance: lastPoint.balance,
            type: 'forecast'
          });
        }

        // 5. Process Sorted Forecasts
        const sortedForecastDates = Object.keys(forecastMap).sort((a, b) => new Date(a) - new Date(b));
        sortedForecastDates.forEach(date => {
          runningBalance += forecastMap[date];
          processed.push({
            date: date,
            balance: Math.round(runningBalance * 100) / 100,
            type: 'forecast'
          });
        });

        setData(processed);
      } catch (err) {
        setError(err.response?.data?.error || "Failed to load insights");
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [userId]);

  const filteredData = useMemo(() => {
    if (data.length === 0 || !pivotDate) return [];
    
    // If dateRange is 0 (All Time), skip the filtering logic and return everything
    if (dateRange === 0) return data;

    const anchor = new Date(pivotDate);
    const cutoff = new Date(pivotDate);
    cutoff.setDate(anchor.getDate() - dateRange);
    
    return data.filter(d => new Date(d.date) >= cutoff);
  }, [data, dateRange, pivotDate]);

  if (loading) return <div className="insights-state">Generating AI Insights...</div>;
  if (error) return <div className="insights-state error">⚠️ {error}</div>;

  return (
    <div className="insights-page">
      <div className="page-header">
        <h1>Financial Insights</h1>
        <p className="page-subtitle">Your financial trajectory - grounded in data, powered by AI.</p>
      </div>

      <div className="chart-card">
        <h3>Combined Cash Flow</h3>
        <div className="insights-controls">
          <button className={dateRange === 30 ? 'active' : ''} onClick={() => setDateRange(30)}>1 Month History</button>
          <button className={dateRange === 90 ? 'active' : ''} onClick={() => setDateRange(90)}>3 Months History</button>
          <button className={dateRange === 180 ? 'active' : ''} onClick={() => setDateRange(180)}>6 Months History</button>
          <button className={dateRange === 365 ? 'active' : ''} onClick={() => setDateRange(365)}>12 Months History</button>
          <button className={dateRange === 0 ? 'active' : ''} onClick={() => setDateRange(0)}>All Time</button>
        </div>
        <div className="chart-container">
          <ResponsiveContainer width="100%" height={450}>
            <ComposedChart data={filteredData}>
              <defs>
                <linearGradient id="historyGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#667eea" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#667eea" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e7eb" />
              <XAxis 
                dataKey="date" 
                minTickGap={60} 
                tick={{fontSize: 12, fill: '#6B7280'}}
                tickFormatter={(str) => new Date(str).toLocaleDateString('en-GB', { month: 'short', day: 'numeric' })}
              />
              <YAxis 
                tick={{fontSize: 12, fill: '#6B7280'}}
                tickFormatter={(val) => `£${val.toLocaleString()}`}
              />

              <Legend 
                verticalAlign="top" 
                align="right" 
                height={36}
                iconType="circle"
              />

              <Tooltip 
                formatter={(value) => [formatCurrency(value), 'Cumulative Balance']}
                contentStyle={{ borderRadius: '10px', border: 'none', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}
              />
              
              <ReferenceLine 
                x={pivotDate} 
                stroke="#EF4444" 
                strokeDasharray="3 3" 
                label={{ value: 'Current Date', position: 'insideTopLeft', fill: '#EF4444', fontSize: 12 }} 
              />

              <Area
                name="Historical Balance"
                type="monotone"
                dataKey={(d) => d.type === 'historical' ? d.balance : null}
                stroke="#667eea"
                strokeWidth={3}
                fillOpacity={1}
                fill="url(#historyGradient)"
                connectNulls={false}
              />

              <Line
                name="AI Forecast"
                type="monotone"
                dataKey={(d) => d.type === 'forecast' ? d.balance : null}
                stroke="#9CA3AF"
                strokeWidth={2}
                strokeDasharray="5 5"
                dot={false}
                connectNulls={true}
              />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="chart-card pie-section">
        <h3>Predicted Spending Distribution (Next 90 Days)</h3>
        <div className="chart-container pie-container">
          <ResponsiveContainer width="100%" height={400}>
            <PieChart>
              <Pie
                data={forecastPieData}
                cx="50%"
                cy="50%"
                innerRadius={80}
                outerRadius={120}
                paddingAngle={5}
                dataKey="value"
                label={({ name, percent }) => `${name} (${(percent * 100).toFixed(0)}%)`}
              >
                {forecastPieData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={getCategoryColor(entry.name)} />
                ))}
              </Pie>
              <Tooltip formatter={(value) => formatCurrency(value)} />
              <Legend verticalAlign="bottom" height={36}/>
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

    </div>
  );
};

export default Insights;