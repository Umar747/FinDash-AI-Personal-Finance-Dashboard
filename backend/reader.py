import pandas as pd
import os

class CSVReader:
    """
    A class to handle reading all CSV files.
    It's job is to take filepaths for CSV files, and retrieve the data in the required format.
    """
    def __init__(self):
        """
        The constructor.
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
    
    def read_statement(self, filepath: str, encoding: str = 'utf-8') -> str:
        # Raise an error if the file does not exist
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Bank statement file not found: {filepath}")
        
        try:
            df = pd.read_csv(filepath, usecols=["Date", "Name", "Amount"], encoding=encoding)
        # Raise an error if the CSV file is empty
        except pd.errors.EmptyDataError:
            raise ValueError("CSV file cannot be empty and must contain 'Date', 'Name' and 'Amount' columns")
        # Raise an error if the CSV file is not in the correct format
        except ValueError as e:
            if "Usecols do not match columns" in str(e):
                raise ValueError("CSV file must contain 'Date', 'Name' and 'Amount' columns")
            
        try:
            df["Date"] = (pd.to_datetime(df["Date"].str.strip(), format="mixed", dayfirst=True, errors="raise").dt.strftime("%Y-%m-%d"))
        except Exception:
            raise ValueError("Date column must be in DD/MM/YYYY format or YYYY-MM-DD format")
        
        data = {}

        for column in df.columns:
            data.update({
                column: df[column].tolist()
            })

        return data
