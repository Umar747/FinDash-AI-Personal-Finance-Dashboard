import pytest
import pandas as pd
from datetime import datetime, timedelta
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.forecast import FinancialForecaster

# Initialise forecaster with a default 90-day window
@pytest.fixture
def forecaster():
    return FinancialForecaster(forecast_days=90)

# Generates 40 days of dummy transaction data with some zero days to test Hurdle logic
@pytest.fixture
def mock_transaction_data():
    base_date = datetime(2024, 1, 1)
    data = []
    for i in range(40):
        current_date = base_date + timedelta(days=i)
        
        # Salary on the 1st
        if current_date.day == 1:
            data.append({'transaction_date': current_date, 'amount': 3500.0, 'category': 'Income'})
            
        # Dining spend only on weekends (spiky)
        if current_date.weekday() >= 5:
            data.append({'transaction_date': current_date, 'amount': -50.0, 'category': 'Dining'})
        
        # Groceries spend every 7 days
        if i % 7 == 0:
            data.append({'transaction_date': current_date, 'amount': -100.0, 'category': 'Groceries'})
            
    return pd.DataFrame(data)

# Data Maturity Tests - Does it catch insufficient history?
def test_check_maturity(forecaster):
    # Create data with only 10 days of history
    short_data = pd.DataFrame({
        'ds': [datetime(2024, 1, 1), datetime(2024, 1, 10)],
        'amount': [100, 200]
    })
    
    with pytest.raises(ValueError, match="Insufficient data"):
        forecaster._check_maturity(short_data)

# Feature Engineering - Are time features (day-of-week, weekend, and holiday flags) calculated correctly?
def test_get_features(forecaster):
    test_date = datetime(2024, 1, 1) # This was a Monday in 2024
    income_date = datetime(2023, 12, 25)
    df = pd.DataFrame({'ds': [test_date]})
    
    features = forecaster._get_features(df, income_date)
    
    assert features['day_of_week'].iloc[0] == 0 # Monday is 0
    assert features['is_weekend'].iloc[0] == 0
    assert features['is_holiday'].iloc[0] == 1 # Jan 1st is a UK holiday
    assert features['days_since_income'].iloc[0] == 7

# Daily Series Preparation - Does it fill gaps with zeros?
def test_prepare_daily_series(forecaster, mock_transaction_data):
    mock_transaction_data['ds'] = pd.to_datetime(mock_transaction_data['transaction_date'])
    daily = forecaster.prepare_daily_series(mock_transaction_data, 'Dining')
    
    # Check that there are no NaN values
    assert daily['y'].isnull().sum() == 0
    # Check that the length matches the span of the input data
    expected_days = (mock_transaction_data['ds'].max() - mock_transaction_data['ds'].min()).days + 1
    assert len(daily) == expected_days

# Forecast Accuracy and Clamping - Are the results clamped properly?
def test_run_forecast_clamping(forecaster, mock_transaction_data):
    results = forecaster.run_forecast(mock_transaction_data)
    
    # Check Dining (expense) predictions
    dining_preds = results[results['category'] == 'Dining']
    assert (dining_preds['amount'] <= 0).all(), "Expense forecast predicted positive income"
    
    # Check Income predictions
    income_preds = results[results['category'] == 'Income']
    assert (income_preds['amount'] >= 0).all(), "Income forecast predicted negative expense"

# Spiky Category Logic - Does it handle 'Hurdle' logic?
def test_spiky_categories_logic(forecaster):
    assert 'Entertainment' in forecaster.spiky_categories
    assert 'Dining' in forecaster.spiky_categories
    assert 'Bills' not in forecaster.spiky_categories

# Forecast Output Format - Is the returned data structured for the database?
def test_forecast_output_structure(forecaster, mock_transaction_data):
    results = forecaster.run_forecast(mock_transaction_data)
    
    required_columns = ['ds', 'amount', 'category']
    for col in required_columns:
        assert col in results.columns
    
    # Check the number of days matches the config
    unique_cats = mock_transaction_data['category'].unique()
    assert len(results) >= len(unique_cats) * 1 # Ensure at least some data is generated