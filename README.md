
# Personal Care Product Chatbot & Myntra Scraper

## 📘 Project Overview
This project demonstrates two integrated modules:
1. **Myntra Product Scraper** – A Playwright-based web scraper designed to extract product data from the Myntra website (Lipstick category).
2. **Personal Care Product Chatbot** – An AI-powered chatbot that answers product-related queries, stores conversations, and can recommend products using vector-based retrieval.

---

## 🧩 Components

### 1. Myntra Product Scraper
- Built with **Playwright** to handle dynamic web pages.
- Designed to scrape up to 5 pages of product listings from Myntra.
- Extracts key product details such as name, brand, price, rating, and product URL.
- Saves data to `scraped_products.csv` for downstream use.
- Includes checks for **robots.txt** to comply with ethical scraping standards.

⚠️ **Note:**  
Myntra’s website does not permit automated scraping. The scraper may run indefinitely or fail to retrieve results due to JavaScript-based content loading and anti-bot measures.  
Use manually exported or sample data for testing.

### 2. Personal Care Product Chatbot
- Built using **LangChain Groq** with the **LLaMA 3.1-8B-Instant** model.
- Uses **ChromaDB** for semantic product search and **PostgreSQL** for chat history storage.
- Accessible via a **Streamlit interface** for real-time user interaction.
- Redirects queries about offers or returns to a human representative.

#### Core Features
- Intent recognition (product inquiry, general query, or human assistance).
- Retrieval-augmented responses using ChromaDB embeddings.
- PostgreSQL logging for all user and bot messages.
- Streamlit chat UI with live conversation tracking.

---

## ⚙️ Setup Instructions

### Prerequisites
Ensure you have the following installed:
- Python 3.9+
- PostgreSQL
- Playwright and Chromium browser
- Dependencies listed in `requirements.txt`

### Installation
```bash
# Create a virtual environment
python -m venv venv
source venv/bin/activate   # (use venv\Scripts\activate on Windows)

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
python -m playwright install chromium
```

### Configuration
Create a file named `config.py` in the project root directory with the following content:

```python
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'dbname': 'chatbot_db',
    'user': 'postgres',
    'password': 'yourpassword'
}

CHROMA_PERSIST_DIR = './chroma_data'
COLLECTION_NAME = 'myntra_personal_care'
DATA_FOLDER = './data'
GROQ_API_KEY = 'your_groq_api_key'
CUSTOMER_SERVICE_CONTACT = '+91-XXXXXXXXXX'
HUMAN_REPRESENTATIVE_CONTACT = '+91-YYYYYYYYYY'
CURRENCY_SYMBOL = '₹'
```

---

## 🚀 Running the Project

### Step 1: Run the Scraper
```bash
python myntra_scraper_playwright.py
```
This will attempt to scrape up to 5 pages of lipstick products and save the results to `scraped_products.csv`.

### Step 2: Load Data into ChromaDB
```python
from src.utils.data_loader import CSVDataLoader
from src.vector_store.chroma_manager import ChromaDBManager

loader = CSVDataLoader()
products = loader.load_all_products()
vector_store = ChromaDBManager()
vector_store.add_products(products)
```

### Step 3: Launch the Chatbot Interface
```bash
streamlit run app.py
```

Once the interface loads, type your query (e.g., “Recommend a good matte lipstick”) and interact with the chatbot.

---

## 🗄️ Database Schema
**Table:** `user_conversations`
| Column | Type | Description |
|---|---|---|
| id | SERIAL | Primary key |
| user_id | VARCHAR(100) | Unique user identifier |
| user_message | TEXT | Message from user |
| bot_response | TEXT | Chatbot’s reply |
| intent | VARCHAR(50) | Intent classification |
| requires_human_assistance | BOOLEAN | Whether escalation required |
| contact_provided | VARCHAR(20) | Contact number for human help |
| created_at | TIMESTAMP | Timestamp of interaction |

---

## 🧠 Project Workflow
1. Scraper collects or loads CSV data.
2. CSV data is processed using `CSVDataLoader` and indexed in `ChromaDB`.
3. User interacts via Streamlit chat UI.
4. Chatbot uses Groq LLM to generate intelligent responses.
5. All messages are logged into PostgreSQL for review.

---

## 📊 Ethical and Practical Considerations
- Respect Myntra’s `robots.txt` and terms of service — scraping is restricted.  
- Use open or sample datasets for demonstration purposes.  
- Protect API keys and credentials — never commit secrets in source code.

---

## 👩‍💻 Author
**Name:** Rupsa Jana  
**Date:** November 2025  
**Project:** Personal Care Chatbot & Myntra Scraper  
**Institution:** Academic Submission Project

---

## 🏁 Conclusion
This project integrates data extraction, machine learning, and conversational AI in one system.  
While Myntra’s anti-bot policy restricts real scraping, the implemented modules demonstrate the full workflow of data collection, processing, and interactive product recommendations.
