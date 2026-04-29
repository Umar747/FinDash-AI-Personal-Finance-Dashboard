import pandas as pd
import re
import logging
from typing import List

import numpy as np

import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

import spacy

from sklearn.feature_extraction.text import TfidfVectorizer

from sentence_transformers import SentenceTransformer

# Try to find NLTK data, and if it's not found, download it
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('punkt')
    nltk.download('stopwords')

class NLPDataProcessor:
    """
    A class to handle all NLP processing for financial transaction data.
    It's job is to turn raw, messy transaction strings into clean numerical embeddings.
    """
    def __init__(self):
        """
        The constructor. This method initialises all the necessary tools and empty placeholders for models.
        """
        # Configure logging messages formatting
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

        # Load the CSV file and extract only the transaction column
        try:
            self.logger.info("Loading transaction dataset from dataset.csv...")
            df = pd.read_csv('data/dataset.csv')
            # Extract the transaction column as a list of strings
            self.transaction_set = df['transaction'].astype(str).tolist()
            self.logger.info(f"Loaded {len(self.transaction_set)} transactions from file.")
        except Exception as e:
            self.logger.error(f"Failed to load dataset.csv: {e}")
            self.transaction_set = []

        # Combine English stopwords and finance-related stopwords into one set
        self.stop_words = set(stopwords.words('english'))
        self.finance_stop_words = {'pos', 'debit', 'credit', 'chq', 'chrg', 'ref', 'pmt', 'sq', '*', 'card', 'payment', 'direct', 'fund', 'transfer', 'online', 'purchase'}
        self.stop_words.update(self.finance_stop_words)
        self.logger.info(f"Loaded {len(self.stop_words)} stopwords.")

        # Load the spaCy model
        self.logger.info("Loading spaCy language model...")
        try:
            # Try to load the model as if it's already installed
            self.nlp = spacy.load("en_core_web_sm", disable=['parser', 'ner'])
            self.logger.info("spaCy model 'en_core_web_sm' loaded successfully.")
        except OSError:
            # If the model is not found, download it
            self.logger.info("spaCy model 'en_core_web_sm' not found. Downloading...")
            import subprocess
            import sys
            subprocess.run([sys.executable, "-m", "spacy", "download", "en_core_web_sm"], check=True)

            # Try to load the model again
            self.nlp = spacy.load("en_core_web_sm", disable=['parser', 'ner'])
            self.logger.info("spaCy model 'en_core_web_sm' loaded successfully.")

        # Initialise placeholders for the models that will be trained or loaded later
        self.tfidf_vectorizer = None
        self.embedding_model = None
    
    # Cleans and preprocesses a single transaction string
    def _preprocess_text(self, text: str) -> str:
        """
        Cleans and preprocesses a single transaction string.
        Returns a cleaned string of tokens.
        """
        # Convert to lowercase
        text_original = text
        text = text.lower()
        
        # Remove punctuation/special chars
        text = re.sub(r'[^a-zA-Z\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Tokenise
        tokens = word_tokenize(text)
        
        # Remove stopwords
        filtered_tokens = [word for word in tokens if word not in self.stop_words]
        
        # Make a set of all capitalised words
        original_words = word_tokenize(text_original)
        capitalised = set()
        for i, original_word in enumerate(original_words):
            if original_word[0].isupper():
                capitalised.add(original_words[i].lower())
        
        # Lemmatisation but preserve capitalised words
        final_tokens = []
        doc = self.nlp(" ".join(filtered_tokens))
        for token in doc:
            if token.text in capitalised:
                # Keep the original form for capitalised words
                final_tokens.append(token.text)
            else:
                # Lemmatise everything else
                final_tokens.append(token.lemma_.lower())
        
        return " ".join(final_tokens)
    
    def _fit_tfidf(self, transactions: List[str]):
        """
        Learn the vocabulary and IDF (Inverse Document Frequency) from the list of transactions.
        This must be called by `transform_tfidf()` at least once.
        """
        self.logger.info("Fitting TF-IDF vectorizer...")
        
        # Preprocess the entire list of transactions
        transactions = [self._preprocess_text(text) for text in transactions]

        # Initialise the TFIDFVectorizer object with the parameters
        self.tfidf_vectorizer = TfidfVectorizer(
            min_df=1, # Ignore words that appear in fewer than 2 documents. Prunes rare typos
            max_features=1000, # Keep only the top 1000 most important words by term frequency
            ngram_range=(1, 2) # Consider both single words (unigrams) and pairs of words (bigrams) e.g., "blue" and "bottle" and also "blue_bottle"
        )
        # The .fit() method learns the vocabulary and the IDF from the transactions
        self.tfidf_vectorizer.fit(transactions)
        self.logger.info(f"TF-IDF Vectorizer fitted. Vocabulary size: {len(self.tfidf_vectorizer.get_feature_names_out())}")

    def transform_tfidf(self, texts: List[str]) -> np.ndarray:
        """
        Transform a list of raw transaction strings into a TF-IDF feature matrix.
        """
        # Check if the vectorizer has been fitted first
        if self.tfidf_vectorizer is None:
            # If the vectorizer has not been fitted, fit it
            self._fit_tfidf(self.transaction_set)

        # Preprocess the new texts using the same cleaning function
        processed_texts = [self._preprocess_text(text) for text in texts]
        
        # transform() converts the new text data into the TF-IDF matrix based on the vocabulary learned during .fit()
        return self.tfidf_vectorizer.transform(processed_texts).toarray()
    
    def load_embedding_model(self, model_name: str = 'all-MiniLM-L6-v2'):
        """
        Load a pre-trained sentence embedding model.
        """
        self.logger.info(f"Loading sentence embedding model: {model_name}...")
        # Downloads the model and sets it up
        self.embedding_model = SentenceTransformer(model_name)
        self.logger.info("Embedding model loaded.")

    def transform_embeddings(self, texts: List[str]) -> np.ndarray:
        """
        Transform a list of raw transaction strings into sentence embeddings.
        """
        # If no model is loaded, load it
        if self.embedding_model is None:
            self.load_embedding_model()

        self.logger.info("Generating sentence embeddings...")
        # Tokenizes and creates embeddings for each input text, then converts the results into a numpy array
        embeddings = self.embedding_model.encode(texts, convert_to_numpy=True)
        self.logger.info(f"Generated {embeddings.shape[0]} embeddings. Dimension: {embeddings.shape[1]}")
        return embeddings
