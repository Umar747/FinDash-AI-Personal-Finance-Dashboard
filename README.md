# FinDash AI — Personal Finance Dashboard with Predictive Analytics

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![React](https://img.shields.io/badge/React-18.x-61DAFB.svg)](https://reactjs.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0+-000000.svg)](https://flask.palletsprojects.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-336791.svg)](https://www.postgresql.org/)
[![Ollama](https://img.shields.io/badge/Ollama-Llama%203.1%208B-orange.svg)](https://ollama.com/)

**FinDash AI** is an intelligent, full-stack personal finance management platform designed to bridge the "interpretation gap" between raw banking records and actionable financial intelligence. Moving beyond passive, rule-based tracking apps, FinDash leverages **Transformer-based Natural Language Processing (NLP)**, **Hurdle-model supervised forecasting**, and a local **Agentic AI assistant** to automate transaction categorisation, predict future cash flow, and manage financial records via natural language.

---

## Key Features

* **Multi-Account CSV Aggregation:** Seamlessly import, clean, and unify bank statements across multiple accounts (e.g., Current, Savings) with automated validation and ACID-compliant bulk database insertion.
* **AI-Powered Transaction Categorisation:** Overcomes semantic sparsity in cryptic merchant strings (e.g., `SQ *MORN-BRW` or `AMZN MKTP`) using `all-MiniLM-L6-v2` Sentence Transformer embeddings paired with a Random Forest classifier—achieving **97.8% accuracy** and outperforming traditional TF-IDF baselines.
* **90-Day Predictive Spending Forecasting:** Uses feature-based supervised learning (accounting for payday cycles, weekends, and UK public holidays) alongside a **two-stage Hurdle Model** to accurately forecast both steady expenses and "spiky" discretionary categories (e.g., Dining, Entertainment).
* **Conversational Agentic AI (Local & Private):** Powered by **LangChain (ReAct framework)** and **Llama 3.1 (8B)** running locally via **Ollama**. Users can query spending habits, add/delete transactions, and reclassify entries in plain English without sensitive financial data ever leaving their machine.
* **Interactive Financial Visualisations:** Dynamic Recharts dashboards displaying combined cash flow trajectories, historical vs. predicted spending distributions, monthly savings rates, and category burn-rate comparisons.
* **Enterprise-Grade Security:** JWT-based session authentication, parameterised SQL queries to prevent SQL injection, and strict server-side `user_id` parameter injection ensuring the AI agent cannot access or modify unauthorised user data.

---

## System Architecture

FinDash follows a decoupled three-tier client-server architecture:

```text
┌─────────────────────┐      REST API (JSON/JWT)      ┌──────────────────────────────────────┐
│                     │ ◄───────────────────────────► │          Flask API Backend           │
│   React Frontend    │                               │  • NLP Categoriser (Transformers)    │
│  (SPA + Recharts)   │                               │  • Forecaster (Hurdle + RF Models)   │
│                     │                               │  • ReAct AI Agent (LangChain/Ollama) │
└─────────────────────┘                               └──────────────────┬───────────────────┘
                                                                         │ psycopg2
                                                                         ▼
                                                      ┌──────────────────────────────────────┐
                                                      │         PostgreSQL Database          │
                                                      │   (Users, Accounts, Transactions,    │
                                                      │              Forecasts)              │
                                                      └──────────────────────────────────────┘
```

### Comparative ML Research Highlights
As part of this project, a quantitative evaluation was conducted comparing traditional Bag-of-Words (**TF-IDF**) against **Sentence Transformer embeddings (`all-MiniLM-L6-v2`)** on noisy financial merchant descriptions:

| Metric | TF-IDF Baseline | Sentence Transformer |
| :--- | :---: | :---: |
| **Accuracy** | 76.1% | **97.8%** |
| **Macro F1-Score** | 0.785 | **0.978** |
| **Inference Latency / Sample** | 0.0125 ms | **0.0110 ms** |

---

## Project Structure

```text
Personal-Finance-Dashboard/
├── backend/
│   ├── data/
│   │   └── dataset.csv                # Training dataset for transaction categorisation
│   ├── agent_tools.py                 # LangChain tools (CRUD operations + Calculator tool)
│   ├── database.py                    # PostgreSQL connection and query utilities
│   ├── finance_agent.py               # ReAct AI Agent setup & Ollama integration
│   ├── forecast.py                    # 90-day Hurdle & Random Forest forecasting engine
│   ├── ml_classifier.py               # Classifier training, evaluation, and Joblib persistence
│   ├── nlp.py                         # Text preprocessing, spaCy lemmatisation & embeddings
│   ├── reader.py                      # CSV statement parser and validator
│   ├── requirements.txt               # Python dependencies
│   ├── server.py                      # Main Flask REST API entry point
│   └── transaction.sql                # PostgreSQL relational schema & indexes
├── frontend/
│   └── finance-dashboard/
│       ├── public/
│       │   └── sample-statement.csv   # Sample bank CSV for testing uploads
│       └── src/
│           ├── components/            # Reusable UI components (CsvUploader, TransactionTable, etc.)
│           ├── context/               # JWT AuthContext state management
│           ├── pages/                 # Main views (HomePage, Transactions, Insights, Chat, Auth)
│           └── services/              # Axios API service layer
├── tests/                             # Pytest unit & integration test suite
├── pytest.ini                         # Pytest configuration
└── README.md
```

---

## Prerequisites

Before setting up the project locally, ensure you have the following installed:

* **Python** `v3.11+` (Conda recommended)
* **Node.js** `v18+` and **npm**
* **PostgreSQL** `v14+`
* **Ollama** ([Download here](https://ollama.com/)) for running the local LLM

---

## Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/Personal-Finance-Dashboard.git
cd Personal-Finance-Dashboard
```

### 2. Configure the Local AI Agent (Ollama)
Install Ollama, start the Ollama background service, and pull the **Llama 3.1 (8B)** model:
```bash
ollama pull llama3.1:8b
```
> **Note:** Ensure the Ollama application/daemon is actively running before starting the backend server so the AI Chat interface can connect.

### 3. Database Configuration (PostgreSQL)
1. Open your PostgreSQL terminal (`psql`) or GUI (e.g., pgAdmin) and create a new database:
   ```sql
   CREATE DATABASE finance;
   ```
2. Initialise the database schema and indexes using the provided SQL script:
   ```bash
   psql -d finance -f backend/transaction.sql
   ```
3. Create or update the `.env` file in the root directory with your database credentials and secret keys:
   ```env
   DB_NAME=finance
   DB_USER=your_postgres_username
   DB_PASSWORD=your_postgres_password
   DB_HOST=localhost
   DB_PORT=5432
   SECRET_KEY=your_jwt_secret_key
   ```

### 4. Backend Setup
Create a dedicated virtual environment, install dependencies, and install the local `spaCy` model wheel:
```bash
# Create and activate Conda environment
conda create --name findash python=3.11 -y
conda activate findash

# Install Python packages
cd backend
pip install -r requirements.txt

# Install the included spaCy English model
pip install en_core_web_sm-3.8.0-py3-none-any.whl
```

### 5. Frontend Setup
Open a new terminal window and install the React dependencies:
```bash
cd frontend/finance-dashboard
npm install
```

---

## Running the Application

To run the full-stack application, keep two terminal sessions running simultaneously:

**Terminal 1 — Start the Flask Backend:**
```bash
conda activate findash
cd backend
python server.py
```
*The API server will start on `http://127.0.0.1:5000`.*

**Terminal 2 — Start the React Frontend:**
```bash
cd frontend/finance-dashboard
npm start
```
*The dashboard will launch automatically in your browser at `http://localhost:3000`.*

---

## Usage Guide

1. **Create an Account:** Sign up on the landing screen (passwords require at least 5 characters, 1 uppercase letter, 1 number, and 1 special character).
2. **Add a Bank Account:** Navigate to the **Transactions** tab and create an account (e.g., *HSBC Current Account*).
3. **Import Transactions:** Drag and drop a CSV bank statement (you can test with `frontend/finance-dashboard/public/sample-statement.csv`) or add entries manually. Each transaction is automatically categorised by the Transformer model.
4. **Explore Insights & Forecasts:** Once you have at least **30 days of transaction history**, visit the **Insights** page to view interactive cash-flow projections, 90-day category forecasts, and burn-rate analytics.
5. **Chat with the AI Agent:** Open the **Chat** tab to interact with your data naturally—try prompts like:
   * *"Show my last 5 transactions."*
   * *"How much did I spend on Groceries in total?"*
   * *"Add a £4.50 transaction for Starbucks today."*
   * *"Change the category of transaction ID 235 to Dining."*

---

## Running Tests

FinDash includes a comprehensive unit and integration test suite built with `pytest` (using mocked database and model dependencies for rapid execution). From the project root directory, run:

```bash
conda activate findash
pytest
```

---

## Future Roadmap

* **Direct Open Banking Integration:** Replace manual CSV uploads with automated real-time bank synchronisation via Open Banking APIs.
* **Domain-Specific Fine-Tuned LLM:** Fine-tune a compact financial LLM for complex multi-step tax and compound interest reasoning.
* **Proactive Financial Advisory:** Add automated bill-splitting detection and personalised savings/investment allocation recommendations.