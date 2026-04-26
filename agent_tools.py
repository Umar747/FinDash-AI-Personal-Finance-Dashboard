from langchain.tools import tool
import psycopg2
import os
import re
from datetime import datetime
from database import get_db_connection

from ml_classifier import FinancialTransactionClassifier
from main import NLPDataProcessor

# Initialise components
model = FinancialTransactionClassifier()
nlp = NLPDataProcessor()
model.load_model("/Users/umarali/Library/CloudStorage/OneDrive-UniversityCollegeLondon/Third Year/Final Year Project/Personal-Finance-Dashboard/transformer_transaction_classifier.joblib")

@tool
def get_recent_transactions(input_str: str = "5", user_id: int = None):
    """
    Retrieves the most recent transactions from the database. 
    Input format: num_transactions=limit (e.g., 'num_transactions=5')
    """

    conn = None
    cur = None

    # Parsing using regex to find digits in the input string
    try:
        # Extracts only the digits from the input
        numbers = re.findall(r'\d+', str(input_str))
        limit = int(numbers[0]) if numbers else 5
    except Exception:
        limit = 5

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # Database query using the extracted limit
        query = """
            SELECT t.transaction_date, t.transaction_name, t.amount, t.category 
            FROM transactions t 
            WHERE t.user_id = %s 
            ORDER BY t.transaction_date DESC 
            LIMIT %s
        """
        cur.execute(query, (user_id, limit,))
        rows = cur.fetchall()
        
        if not rows:
            return "Observation: No transactions found in the database."
            
        # Formatting the data for the LLM's context
        # Converts tuples into a readable string format
        data = "\n".join([f"{r[0]}: {r[1]} - £{r[2]} ({r[3]})" for r in rows])
        
        # Explicitly prefix with Observation to help the ReAct agent stop looping
        return f"\nObservation: {data}" 
        
    except Exception as e:
        return f"Observation: Error retrieving transactions - {str(e)}"
    finally:
        if cur is not None:
            cur.close()
        if conn is not None:
            conn.close()



@tool
def create_new_transaction(input_str: str, user_id: int = None):
    """
    Creates a new transaction. 
    All parameters (description, amount, account_id, date) MUST be present.
    Input format: description="name", date="YYYY-MM-DD", amount=value, account_id=id (e.g., 'description="Coffee", date="2026-01-01", amount=1.50, account_id=1')
    """

    conn = None
    cur = None

    try:
        print("Input string is " + input_str)
        # Extracts value for description and date

        desc_match = re.search(r'description=(?:["\'](.*?)["\']|(\S+))', input_str)
        date_match = re.search(r'date=(?:["\'](.*?)["\']|(\S+))', input_str)
        
        # Extracts numeric values for amount and account_id
        amount_match = re.search(r'amount=(-?\d+(?:\.\d+)?)', input_str)
        account_match = re.search(r'account_id=(\d+)', input_str)

        print("Date match is " + str(date_match))

        # Check if all matches exist
        if not all([desc_match, date_match, amount_match, account_match]):
            missing = []
            if not desc_match: missing.append("description")
            if not amount_match: missing.append("amount")
            if not account_match: missing.append("account_id")
            if not date_match: missing.append("date")
            return f"Observation: Error - Missing required fields: {', '.join(missing)}."

        # Assign values
        description = desc_match.group(1)
        amount = float(amount_match.group(1))
        account_id = int(account_match.group(1))
        date = date_match.group(1)

        conn = get_db_connection()
        cur = conn.cursor()

        # Security check to verify the account belongs to the user
        cur.execute("SELECT id FROM accounts WHERE id = %s AND user_id = %s", (account_id, user_id))
        if not cur.fetchone():
            return f"Observation: Error - Account ID {account_id} does not exist or does not belong to you."
        
        # Use the ML model for category prediction
        from server import model, nlp 
        category = model.predict_single(nlp.transform_embeddings([description])[0]).get("predicted_category")

        cur.execute("""
            INSERT INTO transactions (user_id, account_id, transaction_name, amount, transaction_date, category)
            VALUES (%s, %s, %s, %s, %s, %s) RETURNING id
        """, (user_id, account_id, description, amount, date, category))
        
        new_id = cur.fetchone()[0]
        conn.commit()
        
        return f"Observation: Success! Added transaction {new_id}: {description} (£{amount}) on {date}."
    
    except Exception as e:
        return f"Observation: Failed to parse or insert transaction. Error: {str(e)}"
    finally:
        if cur is not None:
            cur.close()
        if conn is not None:
            conn.close()



@tool
def update_transaction_category(input_str: str, user_id: int = None):
    """
    Updates the category of an existing transaction given its ID.
    Input format: category="New Category", transaction_id=ID (e.g., "category="Groceries", transaction_id=12")
    """

    conn = None
    cur = None

    try:
        # Extract ID and Category using regex
        id_match = re.search(r'transaction_id=(\d+)', input_str)
        cat_match = re.search(r'category=["\'](.*?)["\']', input_str)

        if not id_match or not cat_match:
            return "Observation: Error - Please provide both transaction_id and category."

        transaction_id = int(id_match.group(1))
        new_category = cat_match.group(1).strip()

        conn = get_db_connection()
        cur = conn.cursor()

        # Fetch the transaction to check if it exists, who owns it, and the amount
        cur.execute(
            "SELECT amount FROM transactions WHERE id = %s AND user_id = %s", 
            (transaction_id, user_id)
        )
        row = cur.fetchone()

        if not row:
            return f"Observation: Error - Transaction ID {transaction_id} not found or access denied."

        amount = float(row[0])
        valid_expense_categories = ["Travel", "Groceries", "Dining", "Shopping & Retail", "Entertainment", "Bills"]

        # Validation Logic
        if amount > 0:
            if new_category != "Income":
                return f"Observation: Error - Positive transactions (Income) can only be categorised as 'Income'. Received: {new_category}."
        else:
            if new_category not in valid_expense_categories:
                return f"Observation: Error - Negative transactions must be one of: {', '.join(valid_expense_categories)}. Received: {new_category}."

        cur.execute("UPDATE transactions SET category = %s WHERE id = %s", (new_category, transaction_id))
        conn.commit()

        return f"Observation: Success! Transaction {transaction_id} category updated to {new_category}."

    except Exception as e:
        return f"Observation: Error updating category - {str(e)}"
    finally:
        if cur is not None:
            cur.close()
        if conn is not None:
            conn.close()



@tool
def delete_transaction(input_str: str, user_id: int = None):
    """
    Deletes a transaction from the database given its ID.
    Input format: transaction_id=ID (e.g., 'transaction_id=42')
    """

    conn = None
    cur = None

    try:
        # Extract the ID using regex
        match = re.search(r'transaction_id=(\d+)', input_str)
        if not match:
            # Try to find any digits if the agent didn't follow the format perfectly
            numbers = re.findall(r'\d+', input_str)
            if not numbers:
                return "Observation: Error - No transaction ID found in input."
            transaction_id = int(numbers[0])
        else:
            transaction_id = int(match.group(1))

        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("DELETE FROM transactions WHERE id = %s AND user_id = %s", (transaction_id, user_id))
        
        if cur.rowcount == 0:
            return f"Observation: Error - Transaction with ID {transaction_id} not found."

        conn.commit()
        return f"Observation: Success! Transaction {transaction_id} has been deleted."

    except Exception as e:
        return f"Observation: Error deleting transaction - {str(e)}"
    finally:
        if cur is not None:
            cur.close()
        if conn is not None:
            conn.close()



@tool
def search_transactions(input_str: str, user_id: int = None):
    """
    Searches transactions based on user criteria. 
    All parameters are optional.
    Input format: category="Search Category", start_date="YYYY-MM-DD", end_date="YYYY-MM-DD", name="Search Name", min_amount=minimum_search_amount, max_amount=maximum_search_amount (e.g., "category="Groceries", start_date="2024-01-01", end_date="2024-01-31", name="Tesco", min_amount=10, max_amount=100")
    """

    conn = None
    cur = None

    try:
        # Extraction using Regex (all optional)
        cat_match = re.search(r"category=['\"](.*?)['\"]", input_str)
        name_match = re.search(r"name=['\"](.*?)['\"]", input_str)
        start_match = re.search(r"start_date=['\"](\d{4}-\d{2}-\d{2})['\"]", input_str)
        end_match = re.search(r"end_date=['\"](\d{4}-\d{2}-\d{2})['\"]", input_str)
        min_match = re.search(r"min_amount=(-?\d+(?:\.\d+)?)", input_str)
        max_match = re.search(r"max_amount=(-?\d+(?:\.\d+)?)", input_str)

        # Build dynamic SQL query
        query_parts = ["SELECT transaction_date, transaction_name, amount, category FROM transactions WHERE user_id = %s"]
        params = [user_id]

        # Check if match exists AND group(1) is not an empty string
        if cat_match and cat_match.group(1).strip():
            query_parts.append("AND category ILIKE %s")
            params.append(cat_match.group(1).strip())
        
        if name_match and name_match.group(1).strip():
            query_parts.append("AND transaction_name ILIKE %s")
            params.append(f"%{name_match.group(1).strip()}%")

        if start_match and start_match.group(1).strip():
            query_parts.append("AND transaction_date >= %s")
            params.append(start_match.group(1).strip())

        if end_match and end_match.group(1).strip():
            query_parts.append("AND transaction_date <= %s")
            params.append(end_match.group(1).strip())

        if min_match and min_match.group(1).strip():
            query_parts.append("AND amount >= %s")
            params.append(float(min_match.group(1)))

        if max_match and max_match.group(1).strip():
            query_parts.append("AND amount <= %s")
            params.append(float(max_match.group(1)))

        final_query = " ".join(query_parts) + " ORDER BY transaction_date DESC"
        print(final_query)

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(final_query, tuple(params))
        rows = cur.fetchall()
        
        if not rows:
            return "Observation: No transactions found matching those specific criteria."

        results = "\n".join([f"{r[0]}: {r[1]} - £{r[2]} ({r[3]})" for r in rows])
        return f"Observation: Found the following transactions:\n{results}"

    except Exception as e:
        return f"Observation: Error during filtered search: {str(e)}"
    finally:
        if cur is not None:
            cur.close()
        if conn is not None:
            conn.close()

# Export list of tools
tools = [get_recent_transactions, create_new_transaction, update_transaction_category, delete_transaction, search_transactions]