import logging
from typing import List, Dict, Any

import numpy as np

from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import LabelEncoder

import joblib  # For saving/loading trained models
import os

from main import NLPDataProcessor
from reader import CSVReader

class FinancialTransactionClassifier:
    """
    A machine learning classifier for categorising financial transactions based on their NLP embeddings or TF-IDF features.
    
    This class handles the entire ML pipeline of training, evaluation, prediction, and model persistence. It supports multiple classifier types and provides comprehensive evaluation metrics.
    """
    
    def __init__(self, model_type: str = 'svm', random_state: int = 42):
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
            features (np.ndarray): Feature matrix from NLP processing
            labels (List[str]): Category labels for each feature
            feature_type (str): Type of features ('tfidf' or 'embeddings')
            test_size (float): Proportion of data to reserve for testing
            cross_validate (bool): Whether to perform cross-validation for more robust evaluation
            
        Returns:
            Dict[str, Any]: Comprehensive training results including:
                - test_accuracy: Accuracy on the test set
                - classification_report: Detailed per-class metrics
                - confusion_matrix: Matrix of prediction vs actual counts
                - cross_val_scores: Scores from cross-validation
                - classes: List of class names
                - feature_type: Type of features used
                - model_type: Type of model used
        """
        self.logger.info(f"Starting training with {self.model_type} classifier...")
        
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
        test_accuracy, classification_rep, conf_matrix = self.evaluate(X_test, y_test)
        
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
        results = {
            'test_accuracy': test_accuracy,  # Accuracy on the test set
            'classification_report': classification_rep,  # Precision, recall, F1 per class
            'confusion_matrix': conf_matrix,  # Matrix of actual vs predicted counts
            'cross_val_scores': cv_scores,  # List of accuracy scores from CV
            # 'cross_val_mean_accuracy': np.mean(cv_scores) if cv_scores is not None else None,  # Average CV accuracy
            # 'cross_val_std_accuracy': np.std(cv_scores) if cv_scores is not None else None,  # Standard deviation of CV accuracy
            'classes': self.label_encoder.classes_.tolist(),  # List of class names
            'feature_type': feature_type,  # Type of features used
            'model_type': self.model_type  # Type of model used
        }
        
        self.logger.info(f"Training completed. Test accuracy: {test_accuracy:.3f}")
        if cv_scores is not None:
            self.logger.info(f"Cross-validation accuracy: {np.mean(cv_scores):.3f} ± {np.std(cv_scores):.3f}")
        
        return results
    
    def evaluate(self, X_test: np.ndarray, y_test: np.ndarray) -> tuple:
        """
        This method calculates various performance metrics to understand how well the model generalises on unseen data.
        
        Args:
            X_test (np.ndarray): Test features (from the test set)
            y_test (np.ndarray): True test labels (encoded as numbers)
            
        Returns:
            tuple: (accuracy, classification_report, confusion_matrix)
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before evaluation")
        
        # Make predictions on the test data
        y_pred = self.model.predict(X_test)
        
        # Overall accuracy (percentage of correct predictions)
        accuracy = accuracy_score(y_test, y_pred)
        
        # Detailed classification report with per class metrics
        classification_rep = classification_report(
            y_test, 
            y_pred, 
            target_names=self.label_encoder.classes_,  # Use original class names
            output_dict=True  # Return as dictionary for easier processing
        )
        
        # 3. Confusion matrix (shows what types of mistakes the model makes)
        conf_matrix = confusion_matrix(y_test, y_pred)
        
        return accuracy, classification_rep, conf_matrix
    
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

# model = FinancialTransactionClassifier()
# model.load_model("/Users/umarali/Library/CloudStorage/OneDrive-UniversityCollegeLondon/Third Year/Final Year Project/Personal-Finance-Dashboard/transaction_classifier.joblib")
# nlp = NLPDataProcessor()
# reader = CSVReader()
# # print(type(nlp.transform_embeddings(["Cafe Nero Coffee Chrg"])[0]))
# transactions, categories = reader.read_dataset("data/dataset.csv")
# features = nlp.transform_embeddings(transactions)
# model.train(features, categories)
# # model.save_model("/Users/umarali/Library/CloudStorage/OneDrive-UniversityCollegeLondon/Third Year/Final Year Project/Personal-Finance-Dashboard/transaction_classifier")

# print(model.predict_single(nlp.transform_embeddings(["Costa Coffee Credit"])[0]))
# print(model.predict_single(nlp.transform_embeddings(["Cineworld Superman Viewing"])[0]))
# print(model.predict_single(nlp.transform_embeddings(["TFL TRAVEL CHRG"])[0]))
# print(model.predict_single(nlp.transform_embeddings(["Paxta Local Supermarket"])[0]))