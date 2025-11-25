import pytest

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from main import NLPDataProcessor

# Create an instance of NLPDataProcessor for each test
@pytest.fixture
def processor():
    return NLPDataProcessor()

# Basic Functionality - Does the preprocessing work?
def test_preprocess_text(processor):
    test_cases = [("TFL TRAVEL CHRG", "tfl travel"),
        ("SQ *BLUE BOTTLE", "blue bottle"),
        ("POS AMZNMktp LON", "amznmktp lon"),
        ("UBER *TRIP", "uber trip"),
        ("NETFLIX.COM", "netflix com")]
    
    for input_text, expected_output in test_cases:
        result = processor._preprocess_text(input_text)
        assert result == expected_output, f"Failed for input: {input_text}. Got: {result}, Expected: {expected_output}"

# Edge Cases - How does it handle weird input?
def test_preprocess_text_edge_cases(processor):
    # Test preprocessing with edge cases like empty strings, numbers and special characters
    assert processor._preprocess_text("") == ""
    assert processor._preprocess_text("   ") == ""
    assert processor._preprocess_text("12345") == ""
    assert processor._preprocess_text("Café") == "caf"
    assert processor._preprocess_text("A & B * C") == "b c"

# Stopword Removal - Are financial stopwords being removed?
def test_finance_stopwords_removal(processor):
    # Test that financial stopwords are properly removed
    test_cases = [
        ("POS DEBIT CHRG", ""),
        ("CARD PAYMENT REF", ""),
        ("CARD Starbucks", "starbucks"),
        ("Credit Amazon", "amazon"),
        ("NATWEST", "natwest"),
    ]
    
    for input_text, expected_output in test_cases:
        result = processor._preprocess_text(input_text)
        assert result == expected_output, f"Failed for input: {input_text}. Got: {result}, Expected: {expected_output}"

# Capitalisation Lemmatization Exception - Are capitalised words not being lemmatized?
def test_capitalised_lemmatization(processor):
    # Test that capitalised words are not lemmatized, while other words are
    test_cases = [
        ("POS", ""),
        ("Visa", "visa"),
        ("Hermes", "hermes"),
        ("guess", "guess"),
        ("chrg sketchers", "sketcher"),
        ("philips", "philip"),
        ("TRANSFER BARCLAYS", "barclays"),
        ("Ref UPS", "ups"),
    ]
    
    for input_text, expected_output in test_cases:
        result = processor._preprocess_text(input_text)
        assert result == expected_output, f"Failed for input: {input_text}. Got: {result}, Expected: {expected_output}"