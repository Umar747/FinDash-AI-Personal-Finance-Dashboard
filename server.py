from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import psycopg2
import pandas as pd
import os
import tempfile
import traceback
import jwt
import bcrypt
import re
from datetime import datetime, timedelta
from functools import wraps
from dotenv import load_dotenv

from database import get_db_connection
from ml_classifier import FinancialTransactionClassifier
from main import NLPDataProcessor
from reader import CSVReader
from forecast import FinancialForecaster

from finance_agent import ask_finance_agent

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')

# Configuration
UPLOAD_FOLDER = tempfile.gettempdir()
ALLOWED_EXTENSIONS = {'csv'}
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

def allowed_file(filename):
    """Check if file has allowed extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

model = FinancialTransactionClassifier()
nlp = NLPDataProcessor()
reader = CSVReader()
model.load_model("/Users/umarali/Library/CloudStorage/OneDrive-UniversityCollegeLondon/Third Year/Final Year Project/Personal-Finance-Dashboard/transaction_classifier.joblib")

# transactions, categories = reader.read_dataset("data/dataset.csv")
# features = nlp.transform_embeddings(transactions)
# model.train(features, categories)

def password_check(password):
    """
    Verify the strength of the password given
    Criteria: 5 or more characters, 1 uppercase, 1 number, 1 special character.
    """
    if len(password) < 5:
        return False, "Password must be at least 5 characters long."
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r"[0-9]", password):
        return False, "Password must contain at least one number."
    if not re.search(r"[!@#£$%^&*(),.?\":{}|<>]", password):
        return False, "Password must contain at least one special character."
    return True, "Strong password."

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        try:
            # Token usually comes as "Bearer <token>"
            token = token.split(" ")[1]
            data = jwt.decode(token, app.config['JWT_SECRET_KEY'], algorithms=["HS256"])
            current_user_id = data['user_id']
        except Exception as e:
            return jsonify({'message': 'Token is invalid or expired!'}), 401
        
        return f(current_user_id, *args, **kwargs)
    return decorated



@app.route('/')
def index():
    """Serve the HTML upload page"""
    return render_template('test.html')  # If using templates folder



@app.route('/transactions', methods=['GET'])
@token_required
def get_all_transactions(current_user_id):
    """Handle retrieving transactions database and return them"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT t.id, t.transaction_date, t.transaction_name, t.amount, t.category, a.account_name FROM transactions t INNER JOIN accounts a ON t.account_id = a.id WHERE t.user_id = %s;", (current_user_id,))
        transactions = cur.fetchall()

        if not transactions:
            return jsonify({'error': 'Transactions not found'}), 404
        
        res_transactions = []
        for transaction in transactions:
            res_transactions.append({
                "id": transaction[0],
                "date": str(transaction[1]),
                "description": transaction[2],
                "amount": transaction[3],
                "category": transaction[4],
                "account": transaction[5]
            })
        
        return jsonify({
            'transactions': res_transactions
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()



@app.route('/transactions/<int:transaction_id>', methods=['GET'])
@token_required
def get_transaction(current_user_id, transaction_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT t.id, t.transaction_date, t.transaction_name, t.amount, t.category, a.account_name FROM transactions t JOIN accounts a ON t.account_id = a.id WHERE t.id = %s AND t.user_id = %s", (transaction_id, current_user_id))
        transaction = cur.fetchone()

        if not transaction:
            return jsonify({'error': 'Transaction not found'}), 404

        return jsonify({
            "id": transaction[0],
            "date": str(transaction[1]),
            "description": transaction[2],
            "amount": (transaction[3]),
            "category": transaction[4],
            "account": transaction[5]
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()



@app.route('/transactions', methods=['POST'])
@token_required
def create_transaction(current_user_id):
    data = request.get_json()

    required_fields = [
        'date',
        'description',
        'amount',
        'account_id',
    ]

    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("INSERT INTO transactions (user_id, account_id, transaction_name, amount, transaction_date, category) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id", (current_user_id, data['account_id'], data['description'], data['amount'], data['date'], model.predict_single(nlp.transform_embeddings([data['description']])[0]).get("predicted_category")))

        transaction_id = cur.fetchone()[0]
        conn.commit()

        return jsonify({
            'message': 'Transaction created',
            'transaction_id': transaction_id
        }), 201

    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()



@app.route('/transactions/upload', methods=['POST'])
@token_required
def upload_csv(current_user_id):
    """Handle CSV file upload and return column names"""
    # Check if file was uploaded
    if 'csvFile' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['csvFile']
    
    # Check if file was selected
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Check file extension
    if not allowed_file(file.filename):
        return jsonify({'error': 'Only CSV files are allowed'}), 400
    
    account_id = request.form.get('account_id')
    if not account_id:
        return jsonify({'message': 'Account ID is required'}), 400
    
    try:
        account_id = int(account_id)
    except ValueError:
        return jsonify({'message': 'Invalid account ID'}), 400
    
    try:
        # Save file temporarily
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(temp_path)
        
        # Read CSV with pandas
        try:
            # Try different encodings if needed
            try:
                data = reader.read_statement(temp_path)
            except UnicodeDecodeError:
                data = reader.read_statement(temp_path, encoding='latin-1')
            except ValueError as e:
                if str(e) == "Date column must be in DD/MM/YYYY format or YYYY-MM-DD format":
                    print("I WAS HERE")
                    return jsonify({'error': str(e)}), 400

            num_rows = len(data["Date"])

            # Clean up: remove temp file
            try:
                os.remove(temp_path)
            except:
                pass  # Ignore cleanup errors            
            
        except pd.errors.EmptyDataError:
            return jsonify({'error': 'The CSV file is empty'}), 400
        except Exception as e:
            return jsonify({'error': f'Error reading CSV: {str(e)}'}), 400
            
    except Exception as e:
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # # Get account_id
        # cur.execute("SELECT id FROM accounts WHERE user_id = %s AND account_name = %s", (1, data['account']))

        # account = cur.fetchone()
        # if not account:
        #     return jsonify({'error': 'Account not found'}), 404

        # account_id = account[0]

        for row_num in range(num_rows):
            print(f'{data["Name"][row_num]} has an amount of {data["Amount"][row_num]} and a date of {data["Date"][row_num]}')
            category = model.predict_single(nlp.transform_embeddings([data['Name'][row_num]])[0]).get("predicted_category")
            cur.execute("INSERT INTO transactions (user_id, account_id, transaction_name, amount, transaction_date, category) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id", (current_user_id, account_id, data['Name'][row_num], data['Amount'][row_num], data['Date'][row_num], category))

        conn.commit()

        return jsonify({
            'message': 'File uploaded successfully',
            'transactions': num_rows
        }), 201

    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()



@app.route('/transactions/<int:transaction_id>', methods=['PUT'])
@token_required
def update_transaction(current_user_id, transaction_id):
    data = request.get_json()
    
    required_fields = ['date', 'description', 'amount', 'category', 'account_id']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Update the transaction making sure it belongs to the correct user
        query = """
            UPDATE transactions 
            SET transaction_date = %s, 
                transaction_name = %s, 
                amount = %s, 
                category = %s, 
                account_id = %s 
            WHERE id = %s AND user_id = %s
        """
        cur.execute(query, (
            data['date'], 
            data['description'], 
            data['amount'], 
            data['category'], 
            data['account_id'], 
            transaction_id, 
            current_user_id
        ))

        if cur.rowcount == 0:
            return jsonify({'error': 'Transaction not found or unauthorized'}), 404

        conn.commit()
        return jsonify({'message': 'Transaction updated successfully'}), 200

    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()



@app.route('/transactions/<int:transaction_id>', methods=['DELETE'])
@token_required
def delete_transaction(current_user_id, transaction_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("DELETE FROM transactions WHERE id = %s AND user_id = %s", (transaction_id, current_user_id))

        if cur.rowcount == 0:
            return jsonify({'error': 'Transaction not found'}), 404

        conn.commit()

        return jsonify({'message': 'Transaction deleted'})

    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()



@app.route('/transactions/delete-multiple', methods=['POST'])
@token_required
def delete_transactions_multiple(current_user_id):
    data = request.get_json()
    ids = data.get('ids')

    if not ids or not isinstance(ids, list):
        return jsonify({'error': 'ids must be a non-empty list'}), 400

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("DELETE FROM transactions WHERE user_id = %s AND id = ANY(%s)", (current_user_id, ids))

        deleted_count = cur.rowcount
        conn.commit()

        return jsonify({
            'message': 'Transactions deleted successfully',
            'deleted_count': deleted_count,
            'deleted_ids': ids
        })

    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()



@app.route('/accounts', methods=['GET'])
@token_required
def get_all_accounts(current_user_id):
    """Handle retrieving accounts database and return them"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, account_name FROM accounts WHERE user_id = (%s);", (current_user_id, ))
        accounts = cur.fetchall()
        
        res_accounts = []
        for account in accounts:
            res_accounts.append({
                "id": account[0],
                "account": account[1]
            })
        
        return jsonify({
            'accounts': res_accounts
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()



@app.route('/accounts/<int:account_id>', methods=['GET'])
@token_required
def get_account(current_user_id, account_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, account_name FROM accounts WHERE user_id = (%s) AND id = (%s);", (current_user_id, account_id))
        account = cur.fetchone()

        if not account:
            return jsonify({'error': 'Account not found'}), 404

        return jsonify({
            "id": account[0],
            "account": account[1]
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()



@app.route('/accounts', methods=['POST'])
@token_required
def create_account(current_user_id):
    data = request.get_json()

    required_fields = ['account_name']

    if not data or not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields: Account Name'}), 400

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("INSERT INTO accounts (user_id, account_name) VALUES (%s, %s) RETURNING id, account_name", (current_user_id, data['account_name']))

        account = cur.fetchone()
        conn.commit()

        return jsonify({
            'message': 'Account created',
            'account_id': account[0],
            'account_name': account[1]
        }), 201

    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        return jsonify({
            'error': 'Bank account with this name already exists for this user'
        }), 409
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()



@app.route('/accounts/<int:account_id>', methods=['DELETE'])
@token_required
def delete_account(current_user_id, account_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("DELETE FROM accounts WHERE id = %s AND user_id = %s", (account_id, current_user_id))

        if cur.rowcount == 0:
            return jsonify({'error': 'Account not found'}), 404

        conn.commit()

        return jsonify({
            'message': 'Account deleted'
        })

    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()





@app.route('/transactions/forecast', methods=['GET'])
@token_required
def generate_forecast(current_user_id):
    """Trigger forecasting logic, save to database, and return results"""
    
    try:
        # Fetch transaction data
        conn = get_db_connection()
        cur = conn.cursor()
        
        query = """
            SELECT transaction_date, amount, category 
            FROM transactions 
            WHERE user_id = %s;
        """
        cur.execute(query, (current_user_id,))
        rows = cur.fetchall()
        
        if not rows:
            return jsonify({'error': f'No transactions found for this user'}), 404

        # Prepare DataFrame for run_forecast()
        df = pd.DataFrame(rows, columns=['transaction_date', 'amount', 'category'])
        df['amount'] = df['amount'].astype(float)
        df['transaction_date'] = pd.to_datetime(df['transaction_date'])

        # Run Forecast
        forecaster = FinancialForecaster(forecast_days=90)
        results = forecaster.run_forecast(df)

        # Delete existing forecasts and update database
        cur.execute("DELETE FROM forecasts WHERE user_id = %s;", (current_user_id,))
        
        insert_query = """
            INSERT INTO forecasts (user_id, category, forecast_date, predicted_amount)
            VALUES (%s, %s, %s, %s);
        """
        
        # Format data for executemany
        forecast_data = [
            (current_user_id, row['category'], row['ds'].date(), row['amount']) 
            for _, row in results.iterrows()
        ]
        
        cur.executemany(insert_query, forecast_data)
        conn.commit()

        # Prepare JSON response
        res_forecasts = []
        for _, row in results.iterrows():
            res_forecasts.append({
                "category": row['category'],
                "date": str(row['ds'].date()),
                "predicted_amount": str(row['amount'])
            })

        return jsonify({
            'message': f'Successfully created {len(forecast_data)} forecast rows',
            'forecasts': res_forecasts
        }), 200

    except ValueError as e:
        if "Insufficient data" in str(e):
            return jsonify({'error': 'Not enough transaction history to generate a forecast'}), 400
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()





@app.route('/api/chat', methods=['POST'])
@token_required
def chat_with_agent(current_user_id):
    data = request.get_json()
    user_message = data.get('message')
    
    try:
        agent_response = ask_finance_agent(user_message, current_user_id)
        return jsonify({"response": agent_response})
    except Exception as e:
        print("--- AGENT ERROR ---")
        traceback.print_exc() 
        return jsonify({"error": "Internal Agent Error", "details": str(e)}), 500





@app.route('/auth/signup', methods=['POST'])
def signup():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400

    is_strong, msg = password_check(password)
    if not is_strong:
        return jsonify({'error': msg}), 400

    hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO users (username, password_hash) VALUES (%s, %s) RETURNING id", (username, hashed_pw))
        user_id = cur.fetchone()[0]
        conn.commit()
        return jsonify({'message': 'User created successfully', 'user_id': user_id}), 201
    except psycopg2.errors.UniqueViolation:
        return jsonify({'error': 'Username already exists'}), 409
    finally:
        cur.close()
        conn.close()

@app.route('/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, password_hash FROM users WHERE username = %s", (username,))
    user = cur.fetchone()
    cur.close()
    conn.close()

    if user and bcrypt.checkpw(password.encode('utf-8'), user[1].encode('utf-8')):
        token = jwt.encode({
            'user_id': user[0],
            'exp': datetime.utcnow() + timedelta(hours=24)
        }, app.config['JWT_SECRET_KEY'], algorithm="HS256")
        
        return jsonify({'token': token, 'user_id': user[0]})
    
    return jsonify({'error': 'Incorrect username or password'}), 401



# if __name__ == '__main__':
#     # Create upload folder if it doesn't exist
#     if not os.path.exists(UPLOAD_FOLDER):
#         os.makedirs(UPLOAD_FOLDER)
    
#     print(f"Upload folder: {UPLOAD_FOLDER}")
#     print("Starting Flask server on http://localhost:5000")
#     print("Upload HTML page available at http://localhost:5000/")
    
#     app.run(debug=True, host='0.0.0.0', port=5000)