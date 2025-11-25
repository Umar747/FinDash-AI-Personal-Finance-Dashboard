import pandas as pd
import os

class CSVReader:
    """
    A class to handle reading all CSV files.
    It's job is to take filepaths for CSV files, and retrieve the data in the required format.
    """
    def __init__(self):
        """
        The constructor. This method initializes all the necessary tools and empty placeholders for models.
        """

    def read_dataset(self, filepath: str) -> str:
        # Raise an error if the file does not exist
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Training data file not found: {filepath}")
        
        try:
            df = pd.read_csv(filepath, keep_default_na=False)
        # Raise an error if the CSV file is empty
        except pd.errors.EmptyDataError:
            raise ValueError("CSV file cannot be empty and must contain 'transaction' and 'category' columns")
        
        # Raise an error if the CSV file is not in the correct format
        if "transaction" not in df.columns or "category" not in df.columns:
            raise ValueError("CSV file must contain 'transaction' and 'category' columns")

        transactions = df["transaction"].tolist()
        category = df["category"].tolist()

        return transactions, category
    
    def read_statement(self, filepath: str) -> str:
        # Raise an error if the file does not exist
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Bank statement file not found: {filepath}")
        
        try:
            df = pd.read_csv(filepath, usecols=["Date", "Name", "Amount"])
        # Raise an error if the CSV file is empty
        except pd.errors.EmptyDataError:
            raise ValueError("CSV file cannot be empty and must contain 'Date', 'Name' and 'Amount' columns")
        # Raise an error if the CSV file is not in the correct format
        except ValueError as e:
            if "Usecols do not match columns" in str(e):
                raise ValueError("CSV file must contain 'Date', 'Name' and 'Amount' columns")

        return df








# EVENTUALLY CHANGE CODE TO USE CSV READER!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

def read_csv(filepath: str) -> str:
        # Raise an error if the file does not exist
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Training data file not found: {filepath}")
        
        try:
            df = pd.read_csv(filepath, keep_default_na=False)
        except pd.errors.EmptyDataError:
            raise ValueError("CSV file must contain 'transaction' and 'category' columns")
        
        # Raise an error if the CSV file is not in the correct format
        if "transaction" not in df.columns or "category" not in df.columns:
            raise ValueError("CSV file must contain 'transaction' and 'category' columns")

        transactions = df["transaction"].tolist()
        category = df["category"].tolist()

        return transactions, category

reader = CSVReader()
filepath = "data/dataset.csv"

# transactions, categories = reader.read_dataset(filepath)
# print(transactions)
# print(categories)

# data = reader.read_statement("data/Sample_Statement.csv")
# data = reader.read_statement("data/statement.csv")
# data = reader.read_statement("data/statement.csv")
# print(data)
# print(len(data))
# for record in data["Name"]:
#     print(record)

# for i in range(len(data)):
#     print(f"The transaction called {data['Name'][i]} was made on {data['Date'][i]} with an amount of {data['Amount'][i]}")
# print(type(data["Date"][0]))