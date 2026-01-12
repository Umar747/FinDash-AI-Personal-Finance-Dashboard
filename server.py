from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import psycopg2
import pandas as pd
import os
from dotenv import load_dotenv
import tempfile

from ml_classifier import FinancialTransactionClassifier
from main import NLPDataProcessor
from reader import CSVReader

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Database connection function
def get_db_connection():
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT'),
        database=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD')
    )
    return conn

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

@app.route('/')
def index():
    """Serve the HTML upload page"""
    return render_template('test.html')  # If using templates folder

@app.route('/upload', methods=['POST'])
def upload_csv():
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
    
    try:
        # Save file temporarily
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(temp_path)
        
        # Read CSV with pandas
        try:
            # Try different encodings if needed
            try:
                df = pd.read_csv(temp_path)
            except UnicodeDecodeError:
                df = pd.read_csv(temp_path, encoding='latin-1')
            
            print(df["Name"])
            for name in df['Name']:
                print(f'The category for the shop {name} is {model.predict_single(nlp.transform_embeddings([name])[0]).get("predicted_category")}')
            
            # Get column names
            columns = df.columns.tolist()
            
            # Get basic info
            num_rows = len(df)
            num_columns = len(columns)
            
            # Clean up: remove temp file
            try:
                os.remove(temp_path)
            except:
                pass  # Ignore cleanup errors
            
            # Return success response with column information
            return jsonify({
                'message': f'File uploaded successfully! Found {num_rows} rows and {num_columns} columns.',
                'filename': file.filename,
                'columns': columns,
                'num_rows': num_rows,
                'num_columns': num_columns,
                'sample_data': df.head(3).to_dict(orient='records') if num_rows > 0 else []
            })
            
        except pd.errors.EmptyDataError:
            return jsonify({'error': 'The CSV file is empty'}), 400
        except Exception as e:
            return jsonify({'error': f'Error reading CSV: {str(e)}'}), 400
            
    except Exception as e:
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500

# @app.route('/api/info', methods=['GET'])
# def get_csv_info():
#     """Example API endpoint to demonstrate pandas usage"""
#     # You can modify this to read from a specific file
#     try:
#         # Example: reading from a sample file
#         df = pd.DataFrame({
#             'Name': ['Alice', 'Bob', 'Charlie'],
#             'Age': [25, 30, 35],
#             'City': ['New York', 'London', 'Tokyo']
#         })
        
#         return jsonify({
#             'columns': df.columns.tolist(),
#             'data': df.to_dict(orient='records'),
#             'shape': df.shape
#         })
#     except Exception as e:
#         return jsonify({'error': str(e)}), 500

# if __name__ == '__main__':
#     # Create upload folder if it doesn't exist
#     if not os.path.exists(UPLOAD_FOLDER):
#         os.makedirs(UPLOAD_FOLDER)
    
#     print(f"Upload folder: {UPLOAD_FOLDER}")
#     print("Starting Flask server on http://localhost:5000")
#     print("Upload HTML page available at http://localhost:5000/")
    
#     app.run(debug=True, host='0.0.0.0', port=5000)