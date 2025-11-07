import psycopg2
import config

class PostgreSQLManager:
    def __init__(self):
        self.connection = None
        self.connect()
        self.setup_tables()
    
    def connect(self):
        try:
            self.connection = psycopg2.connect(**config.DB_CONFIG)
            print("✅ Connected to PostgreSQL database successfully!")
        except Exception as e:
            print(f"❌ Error connecting to database: {e}")
    
    def setup_tables(self):
        """Create only conversation table"""
        try:
            cursor = self.connection.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_conversations (
                    id SERIAL PRIMARY KEY,
                    user_id VARCHAR(100) NOT NULL,
                    user_message TEXT NOT NULL,
                    bot_response TEXT NOT NULL,
                    intent VARCHAR(50),
                    requires_human_assistance BOOLEAN DEFAULT FALSE,
                    contact_provided VARCHAR(20),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            self.connection.commit()
            cursor.close()
            print("✅ Conversation table created successfully!")
        except Exception as e:
            print(f"❌ Error setting up tables: {e}")
    
    def store_conversation(self, user_id, user_message, bot_response, intent=None, requires_human=False, contact=None):
        """Store user-AI conversation only"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                INSERT INTO user_conversations 
                (user_id, user_message, bot_response, intent, requires_human_assistance, contact_provided)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (user_id, user_message, bot_response, intent, requires_human, contact))
            self.connection.commit()
            cursor.close()
            return True
        except Exception as e:
            print(f"❌ Error storing conversation: {e}")
            return False
    
    def get_conversation_history(self, user_id="default_user", limit=10):
        """Get conversation history for a user"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT user_message, bot_response, created_at 
                FROM user_conversations 
                WHERE user_id = %s 
                ORDER BY created_at DESC 
                LIMIT %s
            """, (user_id, limit))
            results = cursor.fetchall()
            cursor.close()
            return results
        except Exception as e:
            print(f"❌ Error fetching conversation history: {e}")
            return []
