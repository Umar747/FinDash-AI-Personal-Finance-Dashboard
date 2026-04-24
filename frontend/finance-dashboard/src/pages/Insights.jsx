import React, { useState, useEffect, useMemo } from 'react';
import { 
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, 
  AreaChart, Area, ReferenceLine, Line, ComposedChart, Legend, 
  PieChart, Pie, Cell, Bar, BarChart 
} from 'recharts';
import { analyticsAPI, transactionsAPI } from '../services/api';
import { formatCurrency, getCategoryColor } from '../utils/format';
import './Insights.css';

const Insights = () => {
  const [data, setData] = useState([]);
  const [rawHistoryData, setRawHistoryData] = useState([]);
  const [forecastPieData, setForecastPieData] = useState([]);
  const [monthlyStats, setMonthlyStats] = useState([]);
  const [pivotDate, setPivotDate] = useState(null);
  const [dateRange, setDateRange] = useState(90);
  const [pieDateRange, setPieDateRange] = useState(90);
  const [savingsDateRange, setSavingsDateRange] = useState(180);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        const [historyRes, forecastRes] = await Promise.all([
          transactionsAPI.getAll(),
          analyticsAPI.getForecast()
        ]);

        const rawHistory = historyRes.data.transactions || [];
        const rawForecasts = forecastRes.data.forecasts || [];
        setRawHistoryData(rawHistory);
        
        // Process monthly savings data
        const monthlyMap = rawHistory.reduce((acc, t) => {
          const date = new Date(t.date);
          const monthKey = date.toLocaleDateString('en-GB', { month: 'short', year: '2-digit' });
          const sortKey = date.toISOString().substring(0, 7); // yyyy-mm for sorting

          if (!acc[monthKey]) {
            acc[monthKey] = { name: monthKey, income: 0, expenses: 0, sortKey };
          }
          
          const amt = parseFloat(t.amount);
          if (amt > 0) {
            acc[monthKey].income += amt;
          } else {
            acc[monthKey].expenses += Math.abs(amt);
          }
          
          return acc;
        }, {});

        const processedMonthly = Object.values(monthlyMap)
          .sort((a, b) => a.sortKey.localeCompare(b.sortKey))
          .map(m => ({
            ...m,
            savings: Math.round((m.income - m.expenses) * 100) / 100,
            savingsRate: m.income > 0 ? Math.round(((m.income - m.expenses) / m.income) * 100) : 0
          }));
        setMonthlyStats(processedMonthly);

        // Filter out Income and aggregate by category
        const forecastCategoryMap = rawForecasts
          .filter(f => f.category !== 'Income')
          .reduce((acc, f) => {
            const amount = Math.abs(parseFloat(f.predicted_amount));
            acc[f.category] = (acc[f.category] || 0) + amount;
            return acc;
          }, {});

        const fPieData = Object.entries(forecastCategoryMap).map(([name, value]) => ({
          name,
          value: Math.round(value * 100) / 100
        })).sort((a, b) => b.value - a.value); // Sort by highest spending

        setForecastPieData(fPieData);

        const historyMap = rawHistory.reduce((acc, t) => {
          const date = t.date.split(' ')[0];
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

        // Process sorted history
        const sortedHistoryDates = Object.keys(historyMap).sort((a, b) => new Date(a) - new Date(b));
        sortedHistoryDates.forEach(date => {
          runningBalance += historyMap[date];
          processed.push({
            date: date,
            balance: Math.round(runningBalance * 100) / 100,
            type: 'historical'
          });
        });

        // Identify the pivot (the current day overlap)
        if (processed.length > 0) {
          const lastPoint = processed[processed.length - 1];
          setPivotDate(lastPoint.date); // Save this for filtering

          // Create the bridge point for the chart
          processed.push({
            date: lastPoint.date,
            balance: lastPoint.balance,
            type: 'forecast'
          });
        }

        // Process sorted forecasts
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
  }, []);

  // Get burn rate data (current month spent vs AI forecast)
    const burnRateData = useMemo(() => {
      if (!pivotDate || !rawHistoryData.length) return [];
      
      const now = new Date(pivotDate);
      const startOfMonth = new Date(now.getFullYear(), now.getMonth(), 1);
      
      // Aggregate spending this month
      const actualMap = rawHistoryData
        .filter(t => new Date(t.date) >= startOfMonth && t.category !== 'Income' && parseFloat(t.amount) < 0)
        .reduce((acc, t) => {
          acc[t.category] = (acc[t.category] || 0) + Math.abs(parseFloat(t.amount));
          return acc;
        }, {});
  
      // Comparison against predicted
      return forecastPieData.slice(0, 6).map(item => ({
        name: item.name,
        spent: Math.round((actualMap[item.name] || 0) * 100) / 100,
        forecast: Math.round((item.value / 3) * 100) / 100 // Average per month
      }));
    }, [rawHistoryData, pivotDate, forecastPieData]);
  
    // Filters for savings chart
    const filteredSavingsData = useMemo(() => {
      if (savingsDateRange === 0) return monthlyStats;
      const monthsToShow = Math.floor(savingsDateRange / 30);
      return monthlyStats.slice(-monthsToShow);
    }, [monthlyStats, savingsDateRange]);

  // Derive historical pie data based on selected pieDateRange
  const historicalPieData = useMemo(() => {
    if (!rawHistoryData.length || !pivotDate) return [];

    const anchor = new Date(pivotDate);
    const cutoff = new Date(pivotDate);
    if (pieDateRange !== 0) {
        cutoff.setDate(anchor.getDate() - pieDateRange);
    }

    const categoryMap = rawHistoryData
      .filter(t => {
        const tDate = new Date(t.date);
        const isWithinRange = pieDateRange === 0 || tDate >= cutoff;
        return t.category !== 'Income' && parseFloat(t.amount) < 0 && isWithinRange;
      })
      .reduce((acc, t) => {
        const amount = Math.abs(parseFloat(t.amount));
        acc[t.category] = (acc[t.category] || 0) + amount;
        return acc;
      }, {});

    return Object.entries(categoryMap)
      .map(([name, value]) => ({ name, value: Math.round(value * 100) / 100 }))
      .sort((a, b) => b.value - a.value);
  }, [rawHistoryData, pieDateRange, pivotDate]);

  const filteredChartData = useMemo(() => {
    if (data.length === 0 || !pivotDate || dateRange === 0) return data;
    const cutoff = new Date(pivotDate);
    cutoff.setDate(new Date(pivotDate).getDate() - dateRange);
    return data.filter(d => d.type === 'forecast' || new Date(d.date) >= cutoff);
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
          <button className={dateRange === 30 ? 'active' : ''} onClick={() => setDateRange(30)}>1 Month</button>
          <button className={dateRange === 90 ? 'active' : ''} onClick={() => setDateRange(90)}>3 Months</button>
          <button className={dateRange === 180 ? 'active' : ''} onClick={() => setDateRange(180)}>6 Months</button>
          <button className={dateRange === 365 ? 'active' : ''} onClick={() => setDateRange(365)}>12 Months</button>
          <button className={dateRange === 0 ? 'active' : ''} onClick={() => setDateRange(0)}>All Time</button>
        </div>
        <div className="chart-container">
          <ResponsiveContainer width="100%" height={400}>
            <ComposedChart data={filteredChartData}>
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

      <div className="chart-card pie-comparison-section">
        <div className="pie-column">
          <h3>Historical Spending Distribution</h3>
          <div className="insights-controls">
            <button className={pieDateRange === 30 ? 'active' : ''} onClick={() => setPieDateRange(30)}>1 Month</button>
            <button className={pieDateRange === 90 ? 'active' : ''} onClick={() => setPieDateRange(90)}>3 Months</button>
            <button className={pieDateRange === 180 ? 'active' : ''} onClick={() => setPieDateRange(180)}>6 Months</button>
            <button className={pieDateRange === 365 ? 'active' : ''} onClick={() => setPieDateRange(365)}>12 Months</button>
            <button className={pieDateRange === 0 ? 'active' : ''} onClick={() => setPieDateRange(0)}>All Time</button>
          </div>
          <ResponsiveContainer width="100%" height={350}>
            <PieChart>
              <Pie
                data={historicalPieData}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={100}
                paddingAngle={5}
                dataKey="value"
                label={({ name, percent }) => `${name} (${(percent * 100).toFixed(0)}%)`}
              >
                {historicalPieData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={getCategoryColor(entry.name)} />
                ))}
              </Pie>
              <Tooltip formatter={(value) => formatCurrency(value)} />
              <Legend verticalAlign="bottom" height={36}/>
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div className="arrow-column">
          <div className="trajectory-arrow">➔</div>
          <span className="arrow-label">Forecast</span>
        </div>

        <div className="pie-column">
          <h3>Predicted Spending Distribution (Next 90 Days)</h3>
          <div className="placeholder-spacer"></div> {/* Matches the height of the control buttons for alignment */}
            <ResponsiveContainer width="100%" height={350}>
              <PieChart>
                <Pie
                  data={forecastPieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={100}
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

      <div className="insights-grid">
        <div className="chart-card">
          <h3>Monthly Savings & Savings Rate</h3>
          <div className="insights-controls">
            <button className={savingsDateRange === 30 ? 'active' : ''} onClick={() => setSavingsDateRange(30)}>1 Month</button>
            <button className={savingsDateRange === 90 ? 'active' : ''} onClick={() => setSavingsDateRange(90)}>3 Months</button>
            <button className={savingsDateRange === 180 ? 'active' : ''} onClick={() => setSavingsDateRange(180)}>6 Months</button>
            <button className={savingsDateRange === 365 ? 'active' : ''} onClick={() => setSavingsDateRange(365)}>12 Months</button>
            <button className={savingsDateRange === 0 ? 'active' : ''} onClick={() => setSavingsDateRange(0)}>All Time</button>
          </div>
          <div className="chart-container">
            <ResponsiveContainer width="100%" height={300}>
              <ComposedChart data={filteredSavingsData}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e7eb" />
                <XAxis dataKey="name" tick={{fontSize: 12, fill: '#6B7280'}} />
                <YAxis yAxisId="left" tick={{fontSize: 12, fill: '#6B7280'}} tickFormatter={(val) => `£${val}`} />
                <YAxis yAxisId="right" orientation="right" tick={{fontSize: 12, fill: '#10B981'}} tickFormatter={(val) => `${val}%`} />
                <Tooltip formatter={(value, name) => name === 'Savings Rate' ? [`${value}%`, name] : [formatCurrency(value), name]} />
                <Legend />
                <Bar yAxisId="left" name="Savings" dataKey="savings" fill="#667eea" radius={[4, 4, 0, 0]} />
                <Line yAxisId="right" name="Savings Rate" type="monotone" dataKey="savingsRate" stroke="#10B981" strokeWidth={3} dot={{ r: 4 }} />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="chart-card">
          <h3>Category Burn Rate vs. AI Budget</h3>
          <p className="card-desc">Actual spending this month vs. predicted monthly average.</p>
          <div className="chart-container">
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={burnRateData} layout="vertical" margin={{ left: 30, right: 30 }}>
                <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} stroke="#e5e7eb" />
                <XAxis type="number" hide />
                <YAxis dataKey="name" type="category" tick={{fontSize: 12, fill: '#6B7280'}} width={80} />
                <Tooltip formatter={(value) => formatCurrency(value)} />
                <Legend />
                <Bar name="AI Predicted" dataKey="forecast" fill="#94A3B8" radius={[0, 4, 4, 0]} barSize={20} />
                <Bar name="Actual Spent" dataKey="spent" fill="#DC2626" radius={[0, 4, 4, 0]} barSize={20} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

    </div>
  );
};

export default Insights;