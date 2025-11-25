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
        The constructor. This method initializes all the necessary tools and empty placeholders for models.
        """
        # Configure logging INFO messages formatting
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

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
        
        self.transaction_set = [
            # Transport Category
            "TFL TRAVEL CHRG",
            "UBER TRIP LONDON",
            "UBER EATS DELIVERY",
            "LONDON BUS FARE",
            "TUBE JOURNEY FARE",
            "TAXI CHARGE CENTRAL",
            "NATIONAL RAIL TICKET",
            "GATWICK EXPRESS FARE",
            "CITY AIRPORT TRANSFER",
            "PARKING CHARGE NCP",
            "PETROL STATION SHELL",
            "BP PETROL STATION",
            "TESCO PETROL STATION",
            "SHELL SERVICE STATION",
            "TFL CONTACTLESS FARE",

            # Groceries Category
            "TESCO SUPERSTORE",
            "SAINSBURYS LOCAL",
            "WAITROSE SUPERMARKET",
            "MORRISONS GROCERIES",
            "ASDA SUPERSTORE LTD",
            "LIDL SUPERMARKET UK",
            "ALDI FOOD STORE",
            "CO-OP FOOD STORE",
            "MARKS SPENCER FOOD",
            "WHOLE FOODS MARKET",
            "ICELAND SUPERMARKET",
            "OCCADO DELIVERY",
            "TESCO EXPRESS STORE",
            "SAINSBURYS SUPERMARKET",
            "M&S SIMPLY FOOD",

            # Dining & Coffee Category
            "STARBUCKS COFFEE",
            "PRET A MANGER",
            "COSTA COFFEE SHOP",
            "CAFE NERO LONDON",
            "MCDONALDS RESTAURANT",
            "BURGER KING MEAL",
            "KFC FRIED CHICKEN",
            "SUBWAY SANDWICHES",
            "DOMINOS PIZZA DELIV",
            "PIZZA EXPRESS MEAL",
            "NANDOS RESTAURANT",
            "WAGAMAMA NOODLES",
            "GREGGS BAKERY SHOP",
            "ITSUSUSHI LUNCH",
            "LEON RESTAURANT",

            # Shopping & Retail Category
            "AMAZON MARKETPLACE",
            "AMAZON PRIME VIDEO",
            "EBAY ONLINE SHOPPING",
            "ASOS FASHION ONLINE",
            "NEXT RETAIL STORE",
            "JOHN LEWIS PARTNERS",
            "ARGOS CATALOGUE STORE",
            "PRIMARK CLOTHING STORE",
            "BOOTS CHEMIST STORE",
            "SUPERDRUG PHARMACY",
            "IKEA FURNITURE STORE",
            "CURRYS PC WORLD",
            "APPLE STORE ONLINE",
            "H&M CLOTHING STORE",
            "ZARA FASHION RETAIL",

            # Entertainment & Subscription Category
            "NETFLIX SUBSCRIPTION",
            "SPOTIFY PREMIUM SUB",
            "AMAZON PRIME SUB",
            "DISNEY PLUS SUB",
            "APPLE MUSIC SUB",
            "YOUTUBE PREMIUM SUB",
            "PLAYSTATION NETWORK",
            "XBOX LIVE SUBSCRIPTION",
            "CINEMA TICKET ODEON",
            "VUE CINEMA TICKETS",
            "THEATRE ROYAL TICKET",
            "LONDON MUSEUM ENTRY",
            "GYM MEMBERSHIP PAY",
            "SWIMMING POOL ENTRY",
            "GOLF CLUB MEMBERSHIP",

            # Utilities & Bills Category
            "THAMES WATER BILL",
            "BRITISH GAS BILL",
            "EDF ENERGY BILL",
            "EE MOBILE BILL",
            "VODAFONE BILL PAY",
            "O2 MOBILE PAYMENT",
            "THREE MOBILE BILL",
            "SKY TV SUBSCRIPTION",
            "VIRGIN MEDIA BILL",
            "BT BROADBAND BILL",
            "COUNCIL TAX PAYMENT",
            "TV LICENCE PAYMENT",
            "HOME INSURANCE PAY",
            "CAR INSURANCE PREM",
            "CAR TAX PAYMENT DVLA",

            # Travel & Accommodation Category
            "BRITISH AIRWAYS FLIGHT",
            "EASYJET FLIGHT TICKET",
            "RYANAIR FLIGHT BOOKING",
            "HOTEL BOOKING PREMIER",
            "HOLIDAY INN HOTEL",
            "TRAVELODGE ACCOMMODATION",
            "AIRBNB BOOKING FEE",
            "BOOKING COM RESERVATION",
            "EXPEDIA TRAVEL BOOKING",
            "EUROSTAR TICKET BOOKING",
            "HERTZ CAR RENTAL",
            "EUPCAR RENTAL SERVICE",
            "HOSTELWORLD BOOKING",
            "TRAVELSUPERMARKET DEAL",
            "LASTMINUTE COM BOOKING",

            # Financial Services Category
            "BARCLAYS BANK CHARGES",
            "HSBC BANK FEE",
            "LLOYDS BANK CHARGES",
            "NATWEST BANK FEE",
            "SANTANDER BANK CHARGE",
            "CASH WITHDRAWAL ATM",
            "BANK TRANSFER FEE",
            "PAYPAL PAYMENT SENT",
            "WISE TRANSFER FEE",
            "REVOLUT CARD PAYMENT",
            "MONZO BANK PAYMENT",
            "STARLING BANK PAYMENT",
            "CURRENCY EXCHANGE FEE",
            "WESTERN UNION TRANSFER",
            "MONEYGRAM TRANSFER FEE"
        ]

        # Initialise placeholders for the models that will be trained or loaded later
        self.tfidf_vectorizer = None
        self.embedding_model = None
    
    # Cleans and preprocesses a single transaction string
    def _preprocess_text(self, text: str) -> str:
        """
        Cleans and preprocesses a single transaction string.
        Returns a cleaned string of tokens.

        Args:
            text (str): The raw transaction string (e.g., "TFL TRAVEL CHRG").

        Returns:
            str: The cleaned and processed string of tokens (e.g., "tfl travel").
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
        
        # Lemmatization but preserve capitalised words
        final_tokens = []
        doc = self.nlp(" ".join(filtered_tokens))
        for token in doc:
            if token.text in capitalised:
                # Keep the original form for capitalised words
                final_tokens.append(token.text)
            else:
                # Lemmatize everything else
                final_tokens.append(token.lemma_.lower())
        
        return " ".join(final_tokens)
    
    def _fit_tfidf(self, transactions: List[str]):
        """
        Learn the vocabulary and IDF (Inverse Document Frequency) from the list of transactions.
        This must be called by `transform_tfidf()` at least once.

        Args:
            transactions (List[str]): A list of raw transaction strings.
        """
        self.logger.info("Fitting TF-IDF vectorizer...")
        
        # Preprocess the entire list of transactions
        transactions = [self._preprocess_text(text) for text in transactions]

        # Initialise the TFIDFVectorizer object with the desired parameters
        self.tfidf_vectorizer = TfidfVectorizer(
            min_df=1,          # Ignore words that appear in fewer than 2 documents. Prunes rare typos
            max_features=1000,  # Keep only the top 1000 most important words by term frequency
            ngram_range=(1, 2) # Consider both single words (unigrams) and pairs of words (bigrams)
                                # e.g., "blue" and "bottle" and also "blue_bottle"
        )
        # The .fit() method learns the vocabulary and the IDF from the transactions
        self.tfidf_vectorizer.fit(transactions)
        self.logger.info(f"TF-IDF Vectorizer fitted. Vocabulary size: {len(self.tfidf_vectorizer.get_feature_names_out())}")

    def transform_tfidf(self, texts: List[str]) -> np.ndarray:
        """
        Transform a list of raw transaction strings into a TF-IDF feature matrix.

        Args:
            texts (List[str]): List of raw transaction strings.

        Returns:
            np.ndarray: A numerical matrix of TF-IDF features.
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

        Args:
            model_name (str): The name of the model to load - 'all-MiniLM-L6-v2'
        """
        self.logger.info(f"Loading sentence embedding model: {model_name}...")
        # Downloads the model and sets it up
        self.embedding_model = SentenceTransformer(model_name)
        self.logger.info("Embedding model loaded.")

    def transform_embeddings(self, texts: List[str]) -> np.ndarray:
        """
        Transform a list of raw transaction strings into sentence embeddings.

        Args:
            texts (List[str]): List of raw transaction strings.

        Returns:
            np.ndarray: A matrix of sentence embeddings.
        """
        # If no model is loaded, load it
        if self.embedding_model is None:
            self.load_embedding_model()

        self.logger.info("Generating sentence embeddings...")
        # Tokenizes and creates embeddings for each input text, then converts the results into a NumPy array
        embeddings = self.embedding_model.encode(texts, convert_to_numpy=True)
        self.logger.info(f"Generated {embeddings.shape[0]} embeddings. Dimension: {embeddings.shape[1]}")
        return embeddings

# processor = NLPDataProcessor()
# print(processor._preprocess_text("SHOPPING"))
# print(processor.transform_tfidf(["CARD Starbucks", "TRANSFER BARCLAYS", "Ref UPS"]))
# print(processor.tfidf_vectorizer.get_feature_names_out())
# check = processor.transform_tfidf(["CARD Starbucks Coffee", "TRANSFER BARCLAYS", "Ref UPS"])
# print(check[0])
# print(processor.transform_embeddings(["CARD Starbucks", "TRANSFER BARCLAYS", "Ref UPS"]))