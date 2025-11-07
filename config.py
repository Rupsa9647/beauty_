import os
from dotenv import load_dotenv

load_dotenv()

# Groq API Configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Database Configuration
DB_CONFIG = {
    'dbname': 'personal_care_chatbot',
    'user': 'postgres',
    'password': os.getenv('DB_PASSWORD', 'password'),
    'host': 'localhost',
    'port': '5432'
}

# ChromaDB Configuration
CHROMA_PERSIST_DIR = "./chroma_db"
COLLECTION_NAME = "personal_care_products"

# Contact Information
CUSTOMER_SERVICE_CONTACT = "+1-800-123-4567"
HUMAN_REPRESENTATIVE_CONTACT = "+1-800-987-6543"

# File paths - Now supports multiple CSV files in data folder
DATA_FOLDER = "./data"


## Step 2: PostgreSQL Database (Conversations Only)
