import pandas as pd
import random
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
import holidays

class FinancialForecaster:
    def __init__(self, forecast_days=90):
        self.forecast_days = forecast_days
        self.uk_holidays = holidays.UnitedKingdom()
        self.payday_cycle = 30 
        # Only these categories will use the Hurdle logic
        self.spiky_categories = ['Shopping & Retail', 'Entertainment', 'Dining']

    def _check_maturity(self, df):
        duration = (df['ds'].max() - df['ds'].min()).days
        if duration < 30:
            raise ValueError(f"Insufficient data: Need 30 days, found {duration}.")
        return True

    def _get_features(self, df, last_income_date):
        df = df.copy()
        df['day_of_week'] = df['ds'].dt.dayofweek
        df['day_of_month'] = df['ds'].dt.day
        df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
        df['is_holiday'] = df['ds'].apply(lambda x: 1 if x in self.uk_holidays else 0)
        df['days_since_income'] = (df['ds'] - last_income_date).dt.days
        df['days_since_income'] = df['days_since_income'].clip(lower=0, upper=45)
        return df[['day_of_week', 'day_of_month', 'is_weekend', 'is_holiday', 'days_since_income']]

    def prepare_daily_series(self, df, category):
        cat_df = df[df['category'] == category].copy()
        daily = cat_df.groupby('ds')['amount'].sum().reset_index()
        full_range = pd.date_range(start=df['ds'].min(), end=df['ds'].max(), freq='D')
        daily = daily.set_index('ds').reindex(full_range).fillna(0.0).reset_index()
        daily.columns = ['ds', 'y']
        return daily

    def run_forecast(self, transactions_df, include_zero_output=False):
        transactions_df['ds'] = pd.to_datetime(transactions_df['transaction_date'])
        self._check_maturity(transactions_df)

        # Identify Payday Pattern
        income_df = transactions_df[transactions_df['category'] == 'Income'].sort_values('ds')
        if not income_df.empty:
            gaps = income_df['ds'].diff().dt.days.dropna()
            self.payday_cycle = int(gaps.median()) if not gaps.empty else 30
            last_income_date = income_df['ds'].max()
        else:
            last_income_date = transactions_df['ds'].min()

        categories = transactions_df['category'].unique()
        all_future_preds = []

        for cat in categories:
            daily_data = self.prepare_daily_series(transactions_df, cat)
            X_train = self._get_features(daily_data, last_income_date)
            y_train = daily_data['y']

            # Standard model
            model_std = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42)
            model_std.fit(X_train, y_train)

            # Hurdle models
            clf_hurdle = None
            reg_hurdle = None
            if cat in self.spiky_categories:
                y_binary = (y_train != 0).astype(int)
                clf_hurdle = RandomForestClassifier(n_estimators=100, random_state=42)
                clf_hurdle.fit(X_train, y_binary)
                
                non_zero_mask = y_train != 0
                if non_zero_mask.sum() > 0:
                    reg_hurdle = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42)
                    reg_hurdle.fit(X_train[non_zero_mask], y_train[non_zero_mask])

            # 2. Recursive Forecast Loop
            current_last_income = last_income_date
            current_date = transactions_df['ds'].max()

            for _ in range(self.forecast_days):
                current_date += timedelta(days=1)
                
                days_since = (current_date - current_last_income).days
                if days_since >= self.payday_cycle:
                    current_last_income = current_date
                
                features = self._get_features(pd.DataFrame({'ds': [current_date]}), current_last_income)

                if cat in self.spiky_categories and clf_hurdle:
                    # Only predict if probability > 50%
                    prob = clf_hurdle.predict_proba(features)[0][1]
                    if prob > 0.5 and reg_hurdle:
                        pred = reg_hurdle.predict(features)[0]
                    else:
                        pred = 0.0
                else:
                    # Use standard model for stable trends
                    pred = model_std.predict(features)[0]

                # Clamping Logic
                hist_mean = y_train.mean()
                if hist_mean < 0: pred = min(0, pred)
                if hist_mean > 0: pred = max(0, pred)
                
                if include_zero_output == False and pred == 0.0:
                    pass
                else:
                    all_future_preds.append({'ds': current_date, 'amount': round(pred, 2), 'category': cat})
            
        return pd.DataFrame(all_future_preds)



# # Configuration
# base_date = datetime(2024, 1, 1)
# num_days = 180  # Roughly 6 months
# data = {'transaction_date': [], 'amount': [], 'category': []}

# for i in range(num_days):
#     current_date = base_date + timedelta(days=i)
#     date_str = current_date.strftime('%Y-%m-%d')
#     day_of_month = current_date.day
#     is_weekend = current_date.weekday() >= 5

#     # 1. INCOME: Bi-monthly paycheck
#     if day_of_month in [1, 15]:
#         data['transaction_date'].append(date_str)
#         data['amount'].append(2500.00)
#         data['category'].append("Income")
    
#     if random.random() > 0.95:
#         data['transaction_date'].append(date_str)
#         data['amount'].append(round(random.uniform(50, 5), 2))
#         data['category'].append("Income")

#     # 2. BILLS: Fixed monthly expenses (Rent/Utilities) on the 1st
#     if day_of_month == 1:
#         data['transaction_date'].append(date_str)
#         data['amount'].append(random.uniform(-1300, -1100))
#         data['category'].append("Bills")

#     # 3. TRANSPORT: Daily commute (weekdays)
#     if not is_weekend:
#         data['transaction_date'].append(date_str)
#         data['amount'].append(round(random.uniform(-10, -5), 2))
#         data['category'].append("Transport")

#     # 4. GROCERIES: Weekly big trip
#     if current_date.weekday() == 6: # Sunday
#         data['transaction_date'].append(date_str)
#         data['amount'].append(round(random.uniform(-80, -150), 2))
#         data['category'].append("Groceries")

#     # 5. DINING & ENTERTAINMENT: On weekends
#     if is_weekend:
#         if random.random() > 0.3: # 70% chance to go out on weekend
#             data['transaction_date'].append(date_str)
#             data['amount'].append(round(random.uniform(-30, -100), 2))
#             data['category'].append("Dining")
        
#         if random.random() > 0.6: # 40% chance for movies/events
#             data['transaction_date'].append(date_str)
#             data['amount'].append(round(random.uniform(-20, -60), 2))
#             data['category'].append("Entertainment")

#     # 6. SHOPPING & RETAIL: Random impulses
#     if random.random() > 0.9: # 10% daily chance
#         data['transaction_date'].append(date_str)
#         data['amount'].append(round(random.uniform(-15, -200), 2))
#         data['category'].append("Shopping & Retail")

# # OVERALL TRENDS EXPLANATION:
# # - Income: High-volume, low-frequency spikes appearing strictly on the 1st and 15th.
# # - Bills: Large negative outflow at the start of every month; very low variance.
# # - Transport: Consistent, small daily outflows with gaps on weekends.
# # - Groceries: Periodic weekly spikes (Sundays) representing bulk shopping.
# # - Dining/Entertainment: Clustered activity on weekends with high variance in cost.
# # - Shopping: Highly stochastic (random) with no specific temporal pattern.



# mock_df = pd.DataFrame(data)
# print("-"*100)
# print("INPUT DATA")
# print(mock_df.to_string())
# forecaster = FinancialForecaster(forecast_days=90) # Forecast next week

# results = forecaster.run_forecast(mock_df)

# # # print("--- Forecast Results (Sample) ---")
# # print("-"*100)
# # print("Forecast Results (Sample)")
# # print(results[['ds', 'category', 'yhat']].tail(10))

# print("-"*100)
# print("ALL RESULTS")
# print(results.to_string())