import logging
from typing import List, Dict, Any

import numpy as np

from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import LabelEncoder

import joblib  # For saving and loading trained models
import os
import time

# from nlp import NLPDataProcessor
# from reader import CSVReader

class FinancialTransactionClassifier:
    """
    A machine learning classifier for categorising financial transactions based on their NLP embeddings or TF-IDF features.
    
    This class handles the entire ML pipeline of training, evaluation, prediction, and model persistence. It supports multiple classifier types and provides comprehensive evaluation metrics.
    """
    
    def __init__(self, model_type: str = 'random_forest', random_state: int = 42):
        """
        Initialise the financial transaction classifier.
        
        The constructor sets up the classifier with default parameters and prepares it for training.
        
        Args:
            model_type (str): Type of classifier to use. Options:
                - 'svm': Support Vector Machine (good for high-dimensional text data)
                - 'random_forest': Random Forest Classifier (robust, handles non-linearity)
                - 'logistic_regression': Logistic Regression (fast, good baseline)
            random_state (int): Random seed for reproducibility. This ensures that every time you run the code, you get the same results, which is crucial for debugging and reproducibility.
        """
        # Set up logging to track what's happening during execution
        self.logger = logging.getLogger(__name__)

        # self.reader = CSVReader()
        
        # Store configuration parameters
        self.random_state = random_state  # For reproducible results
        self.model_type = model_type.lower()  # Convert the model name to lowercase
        self.model = None  # Will hold the actual scikit-learn model object
        self.label_encoder = LabelEncoder()  # Converts string labels to numbers
        self.feature_type = None  # Tracks whether we're using 'tfidf' or 'embeddings'
        self.is_trained = False  # Flag to check if model is ready for prediction
        
        self.logger.info(f"Initialized FinancialTransactionClassifier with model_type: {model_type}")
    
    def _initialize_model(self) -> None:
        """
        Initialise the appropriate ML model based on model_type.
        
        This method creates the actual scikit-learn model instance for text classification.
        """
        if self.model_type == 'svm':
            self.model = SVC(
                kernel='linear',  # Linear kernel works well with text features
                probability=True,  # Enable probability predictions (slower but useful)
                random_state=self.random_state,  # For reproducibility
                class_weight='balanced'  # Adjusts for imbalanced class distributions
            )
            self.logger.info("Initialized SVM classifier with linear kernel")
            
        elif self.model_type == 'random_forest':
            self.model = RandomForestClassifier(
                n_estimators=100,  # Number of decision trees in the forest
                random_state=self.random_state,  # For reproducibility
                class_weight='balanced',  # Handle class imbalance
                n_jobs=-1  # Use all available CPU cores
            )
            self.logger.info("Initialized Random Forest classifier with 100 trees")
            
        elif self.model_type == 'logistic_regression':
            self.model = LogisticRegression(
                random_state=self.random_state,  # For reproducibility
                class_weight='balanced',  # Handle class imbalance
                max_iter=1000,  # Increase iterations for convergence
                n_jobs=-1  # Use all available CPU cores
            )
            self.logger.info("Initialized Logistic Regression classifier")
            
        else:
            # Handle invalid model types
            raise ValueError(f"Unsupported model_type: {self.model_type}. Choose from 'svm', 'random_forest', 'logistic_regression'")
    
    def _prepare_training_data(self, 
                            features: np.ndarray, 
                            labels: List[str],
                            test_size: float = 0.2,
                            feature_type: str = 'embeddings') -> tuple:
        """
        Prepare training data by encoding labels and splitting the data into train and test sets.
        
        Args:
            features (np.ndarray): Feature matrix from NLP processor (2D array)
            labels (List[str]): Corresponding category labels (e.g., ['Transport', 'Groceries', ...])
            test_size (float): Proportion of data to use for testing (0.2 = 20%)
            feature_type (str): Type of features ('tfidf' or 'embeddings') - for tracking purposes
            
        Returns:
            tuple: (X_train, X_test, y_train, y_test, y_encoded) where:
                - X_train: Training features
                - X_test: Testing features
                - y_train: Training labels (encoded as numbers)
                - y_test: Testing labels (encoded as numbers)
                - y_encoded: All labels encoded as numbers
        """
        self.logger.info("Preparing training data...")
        
        # Encode category labels to numerical values (0, 1, 2, ...)
        y_encoded = self.label_encoder.fit_transform(labels)
        self.feature_type = feature_type  # Store for reference
        
        # Log the mapping between string labels and numerical codes
        self.logger.info(f"Encoded {len(self.label_encoder.classes_)} classes: {list(self.label_encoder.classes_)}")
        for i, class_name in enumerate(self.label_encoder.classes_):
            self.logger.debug(f"  {class_name} -> {i}")
        
        # Split the data into training and testing sets to evaluate model performance on unseen data
        X_train, X_test, y_train, y_test = train_test_split(
            features, 
            y_encoded, 
            test_size=test_size,  # 20% for testing, 80% for training
            random_state=self.random_state,  # reproducible split
            stratify=y_encoded  # Maintain same class distribution in both sets
        )
        
        self.logger.info(f"Data split: {X_train.shape[0]} training, {X_test.shape[0]} test samples")
        
        return X_train, X_test, y_train, y_test, y_encoded
    
    def train(self, 
             features: np.ndarray, 
             labels: List[str],
             feature_type: str = 'embeddings',
             test_size: float = 0.2,
             cross_validate: bool = True) -> Dict[str, Any]:
        """
        This is the main training method that carries out data preparation, model initialisation, training, and evaluation.

        Args:
            features (np.ndarray): Feature matrix from NLP processing (TF-IDF vectors or Transformer embeddings)
            labels (List[str]): Corresponding category labels for each transaction
            feature_type (str): Type of features used ('tfidf' or 'embeddings')
            test_size (float): Proportion of data to reserve for the test set (default 0.2)
            cross_validate (bool): Whether to perform cross-validation for more robust evaluation
            
        Returns:
            Dict[str, Any]: A results dictionary including:
                - accuracy (float): Global accuracy on the test set
                - balanced_accuracy (float): Accuracy adjusted for class imbalance
                - macro_f1 (float): F1-score treating all classes equally (key for rare categories)
                - latency_ms_per_sample (float): Avg time taken to classify a single transaction
                - avg_confidence (float): The mean probability score for all predictions
                - confidence_correct (float): Mean confidence when the model is right
                - confidence_incorrect (float): Mean confidence when the model is wrong
                - classification_report (dict): Per-class precision, recall, and F1-score
                - confusion_matrix (list): Raw matrix of actual vs. predicted counts
                - cross_val_scores (list): Individual fold scores if cross_validate is True
                - classes (list): The list of category names (label mapping)
                - feature_type (str): The extraction method used (tfidf/embeddings)
                - model_type (str): The classifier used (random_forest/svm/etc)
        """
        self.logger.info(f"Starting training with {self.model_type} classifier using {feature_type}...")
        
        # Prepare the data (encode labels, split into train/test)
        X_train, X_test, y_train, y_test, y_encoded = self._prepare_training_data(
            features, labels, test_size, feature_type
        )
        
        # Initialise the appropriate ML model
        self._initialize_model()
        
        # Train the model on the training data
        self.logger.info("Training the model...")
        self.model.fit(X_train, y_train)
        self.is_trained = True  # Mark model as trained
        
        # Evaluate model performance on the test set (unseen data)
        eval_results = self.evaluate(X_test, y_test)
        
        # Optional cross-validation for more robust evaluation
        # Cross-validation trains on different subsets of data to get a better performance estimate
        cv_scores = None
        if cross_validate:
            self.logger.info("Performing cross-validation...")
            cv_scores = cross_val_score(
                self.model, 
                features, 
                y_encoded,
                cv=5,  # 5-fold cross-validation (train on 4/5, test on 1/5, repeat 5 times)
                n_jobs=-1,  # Use all CPU cores
                scoring='accuracy'  # Use accuracy as the evaluation metric
            )
        
        # Compile all results into a comprehensive dictionary
        results = eval_results.copy()
        results.update({
            'cross_val_scores': cv_scores.tolist() if cv_scores is not None else None,
            'cross_val_mean': np.mean(cv_scores) if cv_scores is not None else None,
            'classes': self.label_encoder.classes_.tolist(),
            'feature_type': feature_type,
            'model_type': self.model_type
        })
        
        self.logger.info(f"Training completed. Accuracy: {results['accuracy']:.3f}, Macro F1: {results['macro_f1']:.3f}")
        if cv_scores is not None:
            self.logger.info(f"Cross-validation accuracy: {np.mean(cv_scores):.3f} ± {np.std(cv_scores):.3f}")
        
        return results

    def evaluate(self, X_test: np.ndarray, y_test: np.ndarray) -> Dict[str, Any]:
        """
        Evaluation to compare TF-IDF vs Transformer models.

        Args:
            X_test (np.ndarray): Feature matrix for the test set.
            y_test (np.ndarray): Ground truth labels (encoded numerically).

        Returns:
            Dict[str, Any]: A dictionary containing evaluation results:
                - accuracy (float): Overall proportion of correct predictions.
                - balanced_accuracy (float): Mean of recall on each class.
                - macro_f1 (float): Unweighted mean of F1 scores.
                - latency_ms_per_sample (float): Inference speed in milliseconds.
                - avg_confidence (float): Mean probability score of all predictions.
                - confidence_correct (float): Average confidence when predictions are accurate (measures model decisiveness).
                - confidence_incorrect (float): Average confidence when predictions are wrong (measures model overconfidence).
                - confusion_matrix (list): 2D array of actual vs. predicted labels for error analysis.
                - classification_report (dict): Per-class precision, recall, and F1 metrics.
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before evaluation")
        
        # Measure latency
        start_time = time.time()
        y_pred = self.model.predict(X_test)
        y_probs = self.model.predict_proba(X_test)
        end_time = time.time()
        
        total_time = end_time - start_time
        latency_per_sample = total_time / len(X_test)

        # Basic accuracy and F1
        from sklearn.metrics import f1_score, balanced_accuracy_score
        accuracy = accuracy_score(y_test, y_pred)
        balanced_acc = balanced_accuracy_score(y_test, y_pred)
        macro_f1 = f1_score(y_test, y_pred, average='macro')

        # Confidence analysis
        # Get the probability of the chosen class for each prediction
        confidences = np.max(y_probs, axis=1)
        avg_confidence = np.mean(confidences)
        
        # Separate confidence for correct vs incorrect (Is the model overconfident?)
        correct_mask = (y_pred == y_test)
        conf_correct = np.mean(confidences[correct_mask]) if any(correct_mask) else 0
        conf_incorrect = np.mean(confidences[~correct_mask]) if any(~correct_mask) else 0

        # Standard classification report and confusion matrix
        classification_rep = classification_report(
            y_test, y_pred, 
            target_names=self.label_encoder.classes_, 
            output_dict=True
        )
        conf_matrix = confusion_matrix(y_test, y_pred)

        return {
            'accuracy': accuracy,
            'balanced_accuracy': balanced_acc,
            'macro_f1': macro_f1,
            'latency_ms_per_sample': latency_per_sample * 1000,
            'avg_confidence': avg_confidence,
            'confidence_correct': conf_correct,
            'confidence_incorrect': conf_incorrect,
            'confusion_matrix': conf_matrix.tolist(),
            'classification_report': classification_rep
        }
    
    def predict(self, features: np.ndarray) -> List[Dict[str, Any]]:
        """
        This is the main prediction method that takes new transaction features and returns categorised predictions with confidence scores.
        
        Args:
            features (np.ndarray): Feature matrix for new transactions
            
        Returns:
            List[Dict[str, Any]]: List of prediction dictionaries, each containing:
                - predicted_category: The most likely category (string)
                - confidence: Probability score for the prediction (0-1)
                - all_probabilities: Probabilities for all possible categories
                - is_high_confidence: Boolean flag for high-confidence predictions
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before making predictions")
        
        # Get probability estimates for all classes
        predicted_probs = self.model.predict_proba(features)
        
        # Process each prediction and format the results
        predictions = []
        for probs in predicted_probs:
            # Create a dictionary of probabilities for all possible classes
            confidence = 0
            class_probabilities = {}
            for class_idx, class_name in enumerate(self.label_encoder.classes_):
                probability = probs[class_idx]
                class_probabilities[class_name] = probability

                # Find the most likely class and it's probability
                if probability > confidence:
                    predicted_class = class_name
                    confidence = probability
            
            # Compile all prediction information into a structured dictionary
            predictions.append({
                'predicted_category': predicted_class,  # The most likely category
                'confidence': confidence,  # How confident the model is (0-1)
                'all_probabilities': class_probabilities,  # Probabilities for each class
                'is_high_confidence': bool(confidence > 0.7)  # Flag for high confidence predictions
            })
        
        return predictions
    
    def predict_single(self, feature_vector: np.ndarray) -> Dict[str, Any]:
        """
        Predict category for a single transaction feature vector.
        
        Args:
            feature_vector (np.ndarray): Single feature vector for one transaction
            
        Returns:
            Dict[str, Any]: Prediction dictionary (same structure as predict())
        """
        # Reshape for single sample prediction (models expect 2D arrays)
        if len(feature_vector.shape) == 1:
            feature_vector = feature_vector.reshape(1, -1)  # Convert from 1D to 2D
        
        predictions = self.predict(feature_vector)
        return predictions[0] if predictions else None
    
    def save_model(self, filepath: str) -> None:
        """
        Save the trained model and associated artifacts to disk.
        
        This allows you to train once and reuse the model later without retraining.
        Essential for deployment and avoiding the computational cost of retraining.
        
        Args:
            filepath (str): Path to save the model (without extension)
                Example: "models/transaction_classifier"
        """
        if not self.is_trained:
            raise ValueError("No trained model to save")
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else '.', exist_ok=True)
        
        # Prepare all components needed to recreate the classifier later
        model_data = {
            'model': self.model,  # The trained scikit-learn model
            'label_encoder': self.label_encoder,  # The label encoding mapping
            'feature_type': self.feature_type,  # Type of features used
            'model_type': self.model_type,  # Type of model used
            'is_trained': self.is_trained  # Training status flag
        }
        
        # Save using joblib (efficient for scikit-learn models)
        joblib.dump(model_data, f"{filepath}.joblib")
        self.logger.info(f"Model saved to {filepath}.joblib")
    
    def load_model(self, filepath: str) -> None:
        """
        Load a trained model and associated artifacts from disk.
        
        This allows you to use a previously trained model without going through the training process again.
        
        Args:
            filepath (str): Path to the saved model file (with .joblib extension)
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Model file not found: {filepath}")
        
        # Load the saved model data
        model_data = joblib.load(filepath)
        
        # Restore all components
        self.model = model_data['model']
        self.label_encoder = model_data['label_encoder']
        self.feature_type = model_data['feature_type']
        self.model_type = model_data['model_type']
        self.is_trained = model_data['is_trained']
        
        self.logger.info(f"Model loaded from {filepath}. Model type: {self.model_type}")
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the current model state.
        
        Useful for debugging, logging, or displaying model information in the UI.
        
        Returns:
            Dict[str, Any]: Model information including:
                - is_trained: Whether the model is trained
                - model_type: Type of classifier
                - feature_type: Type of features used
                - num_classes: Number of categories
                - classes: List of category names
        """
        return {
            'is_trained': self.is_trained,
            'model_type': self.model_type,
            'feature_type': self.feature_type,
            'num_classes': len(self.label_encoder.classes_) if hasattr(self.label_encoder, 'classes_') else 0,
            'classes': self.label_encoder.classes_.tolist() if hasattr(self.label_encoder, 'classes_') else []
        }

# Load a model

# model = FinancialTransactionClassifier()
# model.load_model("/Users/umarali/Library/CloudStorage/OneDrive-UniversityCollegeLondon/Third Year/Final Year Project/Personal-Finance-Dashboard/transaction_classifier.joblib")
# nlp = NLPDataProcessor()
# reader = CSVReader()

# Save a Model

# model = FinancialTransactionClassifier(model_type='random_forest')
# nlp = NLPDataProcessor()
# reader = CSVReader()
# transactions, categories = reader.read_dataset("data/dataset.csv")
# features = nlp.transform_embeddings(transactions)
# model.train(features, categories)
# model.save_model("/Users/umarali/Library/CloudStorage/OneDrive-UniversityCollegeLondon/Third Year/Final Year Project/Personal-Finance-Dashboard/transformer_transaction_classifier")

# Train a Model

# model = FinancialTransactionClassifier(random_state=109)
# nlp = NLPDataProcessor()
# reader = CSVReader()
# transactions, categories = reader.read_dataset("data/dataset.csv")
# features = nlp.transform_tfidf(transactions)
# results = model.train(features, categories)
# print(f"Model: {results['model_type']} with {results['feature_type']}")
# print(f"Accuracy: {results['accuracy']:.4f}")
# print(f"Latency: {results['latency_ms_per_sample']:.4f} ms/sample")
# print(f"Confidence Gap: {results['confidence_correct'] - results['confidence_incorrect']:.4f}")

# print(model.predict_single(nlp.transform_embeddings(["Costa Coffee Credit"])[0]))
# print(model.predict_single(nlp.transform_embeddings(["Cineworld Superman Viewing"])[0]))
# print(model.predict_single(nlp.transform_embeddings(["TFL TRAVEL CHRG"])[0]))
# print(model.predict_single(nlp.transform_embeddings(["Paxta Local Supermarket"])[0]))