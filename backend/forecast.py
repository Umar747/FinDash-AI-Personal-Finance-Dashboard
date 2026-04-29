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

            # Recursive Forecast Loop
            current_last_income = last_income_date
            current_date = transactions_df['ds'].max()

            for _ in range(self.forecast_days):
                current_date += timedelta(days=1)
                
                days_since = (current_date - current_last_income).days
                if days_since >= self.payday_cycle:
                    current_last_income = current_date
                
                features = self._get_features(pd.DataFrame({'ds': [current_date]}), current_last_income)
                
                if cat in self.spiky_categories and clf_hurdle:
                    # Check if the classifier actually knows about both zero and non-zero classes
                    if len(clf_hurdle.classes_) == 2:
                        prob = clf_hurdle.predict_proba(features)[0][1]
                    else:
                        prob = 1.0 if clf_hurdle.classes_[0] == 1 else 0.0
                    
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
