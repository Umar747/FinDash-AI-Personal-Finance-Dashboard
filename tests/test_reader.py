import pytest
import tempfile
import shutil
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from reader import CSVReader

# Create a CSVReader object for tests to read CSV files
@pytest.fixture
def reader():
    reader = CSVReader()
    return reader

# Create a temporary directory for test files
@pytest.fixture
def temp_dir():
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

# Create valid CSV data for tests
@pytest.fixture
def valid_csv_data():
    return """transaction,category
Uber ride,Transport
Supermarket,Food
Netflix,Entertainment
Gas station,Transport
Restaurant,Food"""

# Create CSV file with missing columns
@pytest.fixture
def missing_columns_csv_data():
    return """transaction,amount
Uber ride,15.50
Supermarket,45.75"""

# Create empty CSV file
@pytest.fixture
def empty_csv_data():
    return ""

# Basic Functionality - Does the function read a valid CSV correctly?
def test_read_valid_csv(reader, temp_dir, valid_csv_data):
    # Create a temporary CSV file
    filepath = os.path.join(temp_dir, "valid_dataset.csv")
    with open(filepath, 'w') as f:
        f.write(valid_csv_data)
    
    # Test the function
    transactions, categories = reader.read_dataset(filepath)
    
    # Check results
    assert isinstance(transactions, list)
    assert isinstance(categories, list)
    assert len(transactions) == 5
    assert len(categories) == 5
    assert transactions == ["Uber ride", "Supermarket", "Netflix", "Gas station", "Restaurant"]
    assert categories == ["Transport", "Food", "Entertainment", "Transport", "Food"]

# Error Handling - Does it raise FileNotFoundError for non-existent files?
def test_file_not_found(reader):
    non_existent_file = "non_existent_directory/non_existent_file.csv"
    
    with pytest.raises(FileNotFoundError, match=f"Training data file not found: {non_existent_file}"):
        reader.read_dataset(non_existent_file)

# Error Handling - Does it raise ValueError for missing 'transaction' column?
def test_missing_transaction_column(reader, temp_dir, missing_columns_csv_data):
    filepath = os.path.join(temp_dir, "missing_transaction.csv")
    with open(filepath, 'w') as f:
        f.write(missing_columns_csv_data)
    
    with pytest.raises(ValueError, match="CSV file must contain 'transaction' and 'category' columns"):
        reader.read_dataset(filepath)

# Error Handling - Does it raise ValueError for missing 'category' column?
def test_missing_category_column(reader, temp_dir):
    # Create CSV with only transaction column
    csv_data = """transaction
Uber ride
Supermarket"""
    
    filepath = os.path.join(temp_dir, "missing_category.csv")
    with open(filepath, 'w') as f:
        f.write(csv_data)
    
    with pytest.raises(ValueError, match="CSV file must contain 'transaction' and 'category' columns"):
        reader.read_dataset(filepath)

# Error Handling - Does it handle empty CSV files?
def test_empty_csv_file(reader, temp_dir, empty_csv_data):
    filepath = os.path.join(temp_dir, "empty_dataset.csv")
    with open(filepath, 'w') as f:
        f.write(empty_csv_data)
    
    with pytest.raises(ValueError, match="CSV file cannot be empty and must contain 'transaction' and 'category' columns"):
        reader.read_dataset(filepath)

# Data Types - Does it return correct data types?
def test_return_data_types(reader, temp_dir, valid_csv_data):
    filepath = os.path.join(temp_dir, "test_types.csv")
    with open(filepath, 'w') as f:
        f.write(valid_csv_data)
    
    transactions, categories = reader.read_dataset(filepath)
    
    assert isinstance(transactions, list)
    assert isinstance(categories, list)
    assert all(isinstance(item, str) for item in transactions)
    assert all(isinstance(item, str) for item in categories)

# Column Order - Does it work regardless of column order?
def test_different_column_order(reader, temp_dir):
    # CSV with columns in different order
    csv_data = """category,transaction
Transport,Uber ride
Food,Supermarket
Entertainment,Netflix"""
    
    filepath = os.path.join(temp_dir, "different_order.csv")
    with open(filepath, 'w') as f:
        f.write(csv_data)
    
    transactions, categories = reader.read_dataset(filepath)
    
    assert transactions == ["Uber ride", "Supermarket", "Netflix"]
    assert categories == ["Transport", "Food", "Entertainment"]

# Large Dataset - Does it handle larger datasets correctly?
def test_large_dataset(reader, temp_dir):
    # Create a larger dataset
    transactions_data = []
    categories_data = []
    
    for i in range(100):
        transactions_data.append(f"Transaction {i}")
        categories_data.append(f"Category {i % 5}")
    
    csv_content = "transaction,category\n" + "\n".join(
        f"{trans},{cat}" for trans, cat in zip(transactions_data, categories_data)
    )
    
    filepath = os.path.join(temp_dir, "large_dataset.csv")
    with open(filepath, 'w') as f:
        f.write(csv_content)
    
    transactions, categories = reader.read_dataset(filepath)
    
    assert len(transactions) == 100
    assert len(categories) == 100
    assert transactions[0] == "Transaction 0"
    assert categories[0] == "Category 0"

# Special Characters - Does it handle special characters in data?
def test_special_characters(reader, temp_dir):
    csv_data = '''transaction,category
"McDonald's, Inc.",Food
"Café & Restaurant",Food
"Movie: "Avengers"",Entertainment
Gas $ Station,Transport'''
    
    filepath = os.path.join(temp_dir, "special_chars.csv")
    with open(filepath, 'w') as f:
        f.write(csv_data)
    
    transactions, categories = reader.read_dataset(filepath)
    
    assert len(transactions) == 4
    assert len(categories) == 4
    assert "McDonald's, Inc." in transactions
    assert "Café & Restaurant" in transactions

# Whitespace Handling - Does it handle leading/trailing whitespace?
def test_whitespace_handling(reader, temp_dir):
    csv_data = """transaction,category
  Uber ride  ,  Transport  
Supermarket  ,Food
  Netflix,Entertainment  """
    
    filepath = os.path.join(temp_dir, "whitespace.csv")
    with open(filepath, 'w') as f:
        f.write(csv_data)
    
    transactions, categories = reader.read_dataset(filepath)
    
    assert transactions == ["  Uber ride  ", "Supermarket  ", "  Netflix"]
    assert categories == ["  Transport  ", "Food", "Entertainment  "]

# Empty Values - Does it handle empty values in the data?
def test_empty_values(reader, temp_dir):
    csv_data = """transaction,category
Uber ride,Transport
,Food
Netflix,"""
    
    filepath = os.path.join(temp_dir, "empty_values.csv")
    with open(filepath, 'w') as f:
        f.write(csv_data)
    
    transactions, categories = reader.read_dataset(filepath)
    
    assert len(transactions) == 3
    assert len(categories) == 3
    # Empty values will be read as empty strings by pandas
    assert transactions[1] == ""  # Empty transaction
    assert categories[2] == ""  # Empty category

# Case Sensitivity - Is the column name check case-sensitive?
def test_case_sensitive_columns(reader, temp_dir):
    # CSV with uppercase columns
    csv_data = """Transaction,Category
Uber ride,Transport
Supermarket,Food"""
    
    filepath = os.path.join(temp_dir, "uppercase_columns.csv")
    with open(filepath, 'w') as f:
        f.write(csv_data)
    
    with pytest.raises(ValueError, match="CSV file must contain 'transaction' and 'category' columns"):
        reader.read_dataset(filepath)

# Return Value Structure - Does it return exactly two lists?
def test_return_structure(reader, temp_dir, valid_csv_data):
    filepath = os.path.join(temp_dir, "structure_test.csv")
    with open(filepath, 'w') as f:
        f.write(valid_csv_data)
    
    result = reader.read_dataset(filepath)
    
    assert isinstance(result, tuple)
    assert len(result) == 2
    assert isinstance(result[0], list)
    assert isinstance(result[1], list)