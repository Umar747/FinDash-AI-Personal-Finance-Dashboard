import pytest
import numpy as np
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from ml_classifier import FinancialTransactionClassifier

# Create an instance of FinancialTransactionClassifier for each test
@pytest.fixture
def classifier():
    return FinancialTransactionClassifier()

# Create sample training data for tests
@pytest.fixture
def sample_training_data():
    # Sample features (embeddings) - 20 samples, 5 features each
    features = np.random.rand(20, 5)
    # Sample labels for 3 categories
    # labels = ['Transport', 'Groceries', 'Entertainment', 'Transport', 'Groceries', 'Entertainment', 'Transport', 'Groceries', 'Entertainment', 'Transport', 'Groceries', 'Entertainment', 'Transport', 'Groceries', 'Entertainment', 'Transport', 'Groceries', 'Entertainment', 'Transport', 'Groceries']
    labels = ['Entertainment', 'Groceries', 'Transport', 'Entertainment', 'Groceries', 'Transport', 'Entertainment', 'Groceries', 'Transport', 'Entertainment', 'Groceries', 'Transport', 'Entertainment', 'Groceries', 'Transport', 'Entertainment', 'Groceries', 'Transport', 'Entertainment', 'Groceries']
    return features, labels

# Model Initialisation - Does the classifier initialise correctly?
def test_classifier_initialisation():
    test_cases = [
        ('svm', 'svm'),
        ('random_forest', 'random_forest'),
        ('logistic_regression', 'logistic_regression'),
        ('SVM', 'svm'),  # Test case insensitivity
        ('RaNdoM_fOreST', 'random_forest')
    ]
    
    for input_type, expected_type in test_cases:
        classifier = FinancialTransactionClassifier(model_type=input_type)
        assert classifier.model_type == expected_type
        assert classifier.model is None
        assert not classifier.is_trained

# Model Initialisation - Does it handle invalid model types?
def test_invalid_model_type(sample_training_data):
    model_type = "invalid_model"
    features, labels = sample_training_data
    with pytest.raises(ValueError, match=f"Unsupported model_type: {model_type}. Choose from 'svm', 'random_forest', 'logistic_regression'"):
        FinancialTransactionClassifier(model_type=model_type).train(features, labels, test_size=0.3)

# Model Training - Does training work with different model types?
def test_training_different_models(sample_training_data):
    features, labels = sample_training_data
    test_cases = [
        ('svm', 'embeddings'),
        ('random_forest', 'tfidf'),
        ('logistic_regression', 'embeddings')
    ]
    
    for model_type, feature_type in test_cases:
        classifier = FinancialTransactionClassifier(model_type=model_type)
        results = classifier.train(features, labels, feature_type=feature_type)
        
        assert classifier.is_trained
        assert classifier.model is not None
        assert results['model_type'] == model_type
        assert results['feature_type'] == feature_type
        assert 'Transport' in results['classes']
        assert 'Groceries' in results['classes']
        assert 'Entertainment' in results['classes']

# Model Training - Does it return proper evaluation metrics?
def test_training_metrics(sample_training_data):
    features, labels = sample_training_data
    classifier = FinancialTransactionClassifier(model_type='random_forest')
    results = classifier.train(features, labels, cross_validate=True)
    
    # Check that all expected metrics are present
    expected_keys = ['accuracy', 'balanced_accuracy', 'macro_f1', 'latency_ms_per_sample', 'avg_confidence', 'confidence_correct', 'confidence_incorrect', 'classification_report', 'confusion_matrix', 'cross_val_scores', 'cross_val_mean', 'classes', 'feature_type', 'model_type']
    for key in expected_keys:
        assert key in results, f"Metric '{key}' missing from training results"
    
    # Check metric types and logic
    assert 0 <= results['accuracy'] <= 1
    assert isinstance(results['classification_report'], dict)
    
    assert isinstance(results['confusion_matrix'], list)
    
    # Check cross-validation logic
    assert len(results['cross_val_scores']) == 5
    assert isinstance(results['cross_val_mean'], float)

    # Check confidence logic
    assert 'avg_confidence' in results
    assert 0 <= results['avg_confidence'] <= 1
    
    # Check metadata
    assert results['model_type'] == 'random_forest'
    assert len(results['classes']) == 3  # Based on sample data

# Data Preparation - Does _prepare_training_data work correctly?
def test_prepare_training_data(classifier, sample_training_data):
    features, labels = sample_training_data
    
    X_train, X_test, y_train, y_test, y_encoded = classifier._prepare_training_data(
        features, labels, test_size=0.3
    )
    
    # Check shapes and sizes
    assert X_train.shape[0] == 14  # 70% of 10 samples
    assert X_test.shape[0] == 6   # 30% of 10 samples
    assert len(y_train) == 14
    assert len(y_test) == 6
    assert len(y_encoded) == 20
    
    # Check that labels are properly encoded
    assert set(y_encoded) == {0, 1, 2}  # Should be 3 unique classes encoded as 0,1,2

# Prediction - Do predictions return correct structure?
def test_prediction_structure(classifier, sample_training_data):
    features, labels = sample_training_data
    
    # Train the classifier first
    classifier.train(features, labels)
    
    # Create test features
    test_features = np.random.rand(3, 5)
    predictions = classifier.predict(test_features)
    
    # Check prediction structure
    assert len(predictions) == 3
    for prediction in predictions:
        print(prediction)
        assert 'predicted_category' in prediction
        assert 'confidence' in prediction
        assert 'all_probabilities' in prediction
        assert 'is_high_confidence' in prediction
        
        # Check data types
        assert isinstance(prediction['predicted_category'], str)
        assert isinstance(prediction['confidence'], float)
        assert isinstance(prediction['all_probabilities'], dict)
        assert isinstance(prediction['is_high_confidence'], bool)
        
        # Check probability ranges
        assert 0 <= prediction['confidence'] <= 1
        for prob in prediction['all_probabilities'].values():
            assert 0 <= prob <= 1

# Single Prediction - Does predict_single work for individual transactions?
def test_single_prediction(classifier, sample_training_data):
    features, labels = sample_training_data
    classifier.train(features, labels)
    
    # Test with 1D array (single sample)
    single_feature = np.random.rand(5)
    prediction = classifier.predict_single(single_feature)
    
    assert prediction is not None
    assert 'predicted_category' in prediction
    assert 'confidence' in prediction
    assert 'all_probabilities' in prediction
    assert 'is_high_confidence' in prediction
    
    # Test with 2D array (single sample in 2D)
    single_feature_2d = np.random.rand(1, 5)
    prediction_2d = classifier.predict_single(single_feature_2d)
    assert prediction_2d is not None
    assert 'predicted_category' in prediction_2d
    assert 'confidence' in prediction_2d
    assert 'all_probabilities' in prediction_2d
    assert 'is_high_confidence' in prediction_2d

# Error Handling - Does it handle untrained model correctly?
def test_prediction_without_training(classifier):
    test_features = np.random.rand(2, 5)
    
    with pytest.raises(ValueError, match="Model must be trained before making predictions"):
        classifier.predict(test_features)

# Error Handling - Does evaluation fail without training?
def test_evaluation_without_training(classifier):
    test_features = np.random.rand(2, 5)
    test_labels = np.array([0, 1])
    
    with pytest.raises(ValueError, match="Model must be trained before evaluation"):
        classifier.evaluate(test_features, test_labels)

# Different Feature Types - Does it handle both TF-IDF and embeddings?
def test_different_feature_types(sample_training_data):
    features, labels = sample_training_data
    size = len(labels)
    test_cases = [
        ('embeddings', 384),  # Embeddings typically have 384 dimensions
        ('tfidf', 1000)       # TF-IDF typically has up to 1000 features
    ]
    
    for feature_type, expected_dimension in test_cases:
        classifier = FinancialTransactionClassifier()
        
        # Mock features with appropriate dimensions
        if feature_type == 'embeddings':
            mock_features = np.random.rand(size, 384)
        else:
            mock_features = np.random.rand(size, 1000)
            
        results = classifier.train(mock_features, labels, feature_type=feature_type)
        assert results['feature_type'] == feature_type

# Model Information - Does get_model_info return correct information?
def test_get_model_info(classifier, sample_training_data):
    features, labels = sample_training_data
    
    # Test before training
    info_before = classifier.get_model_info()
    assert not info_before['is_trained']
    assert info_before['model_type'] == 'random_forest'
    assert info_before['num_classes'] == 0
    assert info_before['classes'] == []
    
    # Test after training
    classifier.train(features, labels)
    info_after = classifier.get_model_info()
    
    assert info_after['is_trained']
    assert info_after['model_type'] == 'random_forest'
    assert info_after['num_classes'] == 3
    assert set(info_after['classes']) == {'Transport', 'Groceries', 'Entertainment'}

# Cross-Validation - Does cross-validation work when enabled?
def test_cross_validation(classifier, sample_training_data):
    features, labels = sample_training_data
    
    # classifier = FinancialTransactionClassifier()
    results_with_cv = classifier.train(features, labels, cross_validate=True)
    results_without_cv = classifier.train(features, labels, cross_validate=False)
    
    # Check that cross-validation scores are present when enabled
    assert results_with_cv['cross_val_scores'] is not None
    assert len(results_with_cv['cross_val_scores']) == 5
    # assert len(results_with_cv['cross_val_scores']) == 6
    
    # Check that cross-validation scores are absent when disabled
    assert results_without_cv['cross_val_scores'] is None

# Prediction Confidence - Are confidence scores reasonable?
def test_prediction_confidence(classifier, sample_training_data):
    features, labels = sample_training_data
    classifier.train(features, labels)
    
    test_features = np.random.rand(2, 5)
    predictions = classifier.predict(test_features)
    
    for prediction in predictions:
        print(prediction)
        # Confidence should be the highest probability
        max_prob = max(prediction['all_probabilities'].values())
        assert prediction['confidence'] == max_prob
        
        # High confidence flag should match threshold
        assert prediction['is_high_confidence'] == (prediction['confidence'] > 0.7)

# Different Test Sizes - Does it handle different train/test splits?
def test_different_test_sizes(sample_training_data):
    features, labels = sample_training_data
    test_cases = [0.2, 0.3, 0.4]
    
    for test_size in test_cases:
        classifier = FinancialTransactionClassifier()
        X_train, X_test, y_train, y_test, y_encoded = classifier._prepare_training_data(
            features, labels, test_size=test_size
        )
        
        expected_train_size = int(len(features) * (1 - test_size))
        expected_test_size = len(features) - expected_train_size
        
        assert X_train.shape[0] == expected_train_size
        assert X_test.shape[0] == expected_test_size

# Label Encoding - Are labels properly encoded and decoded?
def test_label_encoding(classifier, sample_training_data):
    features, labels = sample_training_data
    classifier.train(features, labels)
    
    # Test encoding
    test_labels = ['Entertainment', 'Groceries', 'Transport']
    encoded = classifier.label_encoder.fit_transform(test_labels)
    print(f"Encoded is {encoded}")
    decoded = classifier.label_encoder.inverse_transform(encoded)
    print(f"Decoded is {decoded}")
    
    assert list(encoded) == [0, 1, 2]  # Should match the encoding order
    assert list(decoded) == test_labels  # Should decode back to original

# Empty Input Handling - Does it handle edge cases gracefully?
def test_empty_input_handling(classifier):
    # Test with empty features and labels
    empty_features = np.array([]).reshape(0, 5)
    empty_labels = []
    
    with pytest.raises(ValueError):
        classifier._prepare_training_data(empty_features, empty_labels)