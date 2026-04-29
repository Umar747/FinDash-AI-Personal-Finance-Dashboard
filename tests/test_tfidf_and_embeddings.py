import pytest
import numpy as np
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.nlp import NLPDataProcessor

# Create an instance of NLPDataProcessor for each test
@pytest.fixture
def processor():
    return NLPDataProcessor()

# TF-IDF Fitting - Does _fit_tfidf learn vocabulary correctly?
def test_fit_tfidf_basic(processor):
    test_cases = [
        (["TFL TRAVEL CHRG", "UBER TRIP LONDON"], ["tfl", "travel", "uber", "trip"]),
        (["TESCO GROCERY", "SAINSBURYS SHOPPING"], ["tesco", "grocery", "sainsburys", "shopping"]),
        (["NETFLIX SUBSCRIPTION", "SPOTIFY PREMIUM"], ["netflix", "subscription", "spotify", "premium"])
    ]
    
    for transactions, expected_words in test_cases:
        processor._fit_tfidf(transactions)
        vocab = processor.tfidf_vectorizer.get_feature_names_out()
        for word in expected_words:
            assert word in vocab, f"Word '{word}' not found in vocabulary for transactions: {transactions}"

# TF-IDF Transformation - Does transform_tfidf produce correct features?
def test_transform_tfidf_basic(processor):
    training_data = ["UBER TRIP", "TESCO SHOPPING", "NETFLIX SUB"]
    test_data = ["UBER RIDE", "AMAZON SHOPPING"]
    
    processor._fit_tfidf(training_data)
    features = processor.transform_tfidf(test_data)
    
    assert isinstance(features, np.ndarray)
    assert features.shape[0] == len(test_data)
    assert features.shape[1] > 0
    assert np.any(features != 0)

# TF-IDF Auto-Fit - Does transform_tfidf auto-fit when needed?
def test_transform_tfidf_auto_fit(processor):
    processor.transaction_set = ["UBER TRIP", "TESCO SHOPPING", "NETFLIX SUB"]
    test_data = ["UBER RIDE"]
    
    features = processor.transform_tfidf(test_data)
    
    assert processor.tfidf_vectorizer is not None
    assert isinstance(features, np.ndarray)
    assert features.shape[0] == len(test_data)

# TF-IDF Different Outputs - Do different inputs produce different features?
def test_transform_tfidf_different_outputs(processor):
    training_data = ["UBER TRIP LONDON", "TESCO GROCERY SHOP", "NETFLIX SUBSCRIPTION", "COSTA COFFEE DEAL"]
    test_cases = [
        ("UBER RIDE TO AIRPORT", "TESCO FOOD SHOPPING"),
        ("NETFLIX MOVIE NIGHT", "AMAZON ONLINE SHOPPING"),
        ("STARBUCKS COFFEE", "PRET SANDWICH LUNCH")
    ]
    
    processor._fit_tfidf(training_data)
    
    for text1, text2 in test_cases:
        features1 = processor.transform_tfidf([text1])
        features2 = processor.transform_tfidf([text2])
        assert not np.array_equal(features1, features2), f"Features should differ for '{text1}' vs '{text2}'"

# Embedding Model Loading - Does load_embedding_model work correctly?
def test_load_embedding_model_default(processor):
    processor.load_embedding_model()
    
    assert processor.embedding_model is not None
    assert hasattr(processor.embedding_model, 'encode')

# Embedding Transformation - Does transform_embeddings produce correct embeddings?
def test_transform_embeddings_basic(processor):
    test_data = ["UBER TRIP LONDON", "TESCO GROCERY SHOP"]
    
    processor.load_embedding_model()
    embeddings = processor.transform_embeddings(test_data)
    
    assert isinstance(embeddings, np.ndarray)
    assert embeddings.shape[0] == len(test_data)
    assert embeddings.shape[1] == 384
    assert not np.any(np.isnan(embeddings))
    assert np.any(embeddings != 0)

# Embedding Auto-Load - Does transform_embeddings auto-load model when needed?
def test_transform_embeddings_auto_load(processor):
    test_data = ["TEST TRANSACTION"]
    
    embeddings = processor.transform_embeddings(test_data)
    
    assert processor.embedding_model is not None
    assert embeddings.shape[0] == len(test_data)

# Embedding Different Outputs - Do different inputs produce different embeddings?
def test_transform_embeddings_different_outputs(processor):
    test_cases = [
        ("UBER TRIP TO AIRPORT", "TESCO GROCERY SHOPPING"),
        ("NETFLIX MOVIE NIGHT", "STARBUCKS COFFEE BREAK"),
        ("AMAZON ONLINE ORDER", "SPOTIFY MUSIC STREAMING")
    ]
    
    processor.load_embedding_model()
    
    for text1, text2 in test_cases:
        embeddings = processor.transform_embeddings([text1, text2])
        assert not np.array_equal(embeddings[0], embeddings[1]), f"Embeddings should differ for '{text1}' vs '{text2}'"

# TF-IDF vs Embeddings - Do both methods produce meaningful but different representations?
def test_tfidf_vs_embeddings_differences(processor):
    test_data = ["UBER TRIP LONDON", "TESCO GROCERY SHOP"]
    
    processor._fit_tfidf(test_data)
    tfidf_features = processor.transform_tfidf(test_data)
    embeddings = processor.transform_embeddings(test_data)
    
    assert tfidf_features.shape != embeddings.shape
    assert tfidf_features.shape[1] != embeddings.shape[1]

# Error Handling - Does transform_tfidf handle missing transaction_set correctly?
def test_transform_tfidf_no_fit_data(processor):
    processor.transaction_set = None
    
    with pytest.raises(TypeError):
        processor.transform_tfidf(["SOME TEXT"])