import psycopg2
import os
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database connection function
def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST'),
            port=os.getenv('DB_PORT'),
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD')
        )
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None

def create_transactions(user_id, account_id):
    conn = get_db_connection()
    if not conn:
        return
    
    cur = conn.cursor()
    
    # Configuration
    base_date = datetime(2024, 1, 1)
    num_days = 180  # Roughly 6 months
    
    print(f"Generating and inserting data for User {user_id}...")

    try:
        for i in range(num_days):
            current_date = base_date + timedelta(days=i)
            date_str = current_date.strftime('%Y-%m-%d')
            day_of_month = current_date.day
            is_weekend = current_date.weekday() >= 5
            
            # Temporary list to hold today's generated transactions
            daily_transactions = []

            # 1. INCOME: Bi-monthly paycheck
            if day_of_month in [1, 15]:
                daily_transactions.append(("Paycheck", 3500.00, "Income"))
            
            if random.random() > 0.95:
                daily_transactions.append(("Extra Income", round(random.uniform(5, 50), 2), "Income"))

            # 2. BILLS: Fixed monthly expenses
            if day_of_month == 1:
                daily_transactions.append(("Monthly Rent/Bills", round(random.uniform(-1300, -1100), 2), "Bills"))

            # 3. TRANSPORT: Daily commute
            if not is_weekend:
                daily_transactions.append(("Commute", round(random.uniform(-10, -5), 2), "Travel"))

            # 4. GROCERIES: Weekly trip
            if current_date.weekday() == 6: # Sunday
                daily_transactions.append(("Grocery Store", round(random.uniform(-150, -80), 2), "Groceries"))

            # 5. DINING & ENTERTAINMENT
            if is_weekend:
                if random.random() > 0.3:
                    daily_transactions.append(("Restaurant/Dining", round(random.uniform(-100, -30), 2), "Dining"))
                if random.random() > 0.6:
                    daily_transactions.append(("Cinema/Event", round(random.uniform(-60, -20), 2), "Entertainment"))

            # 6. SHOPPING & RETAIL
            if random.random() > 0.9:
                daily_transactions.append(("Retail Purchase", round(random.uniform(-200, -15), 2), "Shopping & Retail"))

            # Execute inserts for the day
            for name, amt, cat in daily_transactions:
                cur.execute(
                    """
                    INSERT INTO transactions (user_id, account_id, transaction_name, amount, transaction_date, category)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (user_id, account_id, name, amt, date_str, cat)
                )

        conn.commit()
        print("Database sync complete.")

    except Exception as e:
        conn.rollback()
        print(f"An error occurred: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    TARGET_USER_ID = 1 
    TARGET_ACCOUNT_ID = 1
    
    create_transactions(TARGET_USER_ID, TARGET_ACCOUNT_ID)