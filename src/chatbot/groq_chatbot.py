from langchain_groq import ChatGroq
#from langchain.schema import HumanMessage, SystemMessage
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_groq import ChatGroq
#from langchain.schema import HumanMessage, SystemMessage
from src.vector_store.chroma_manager import ChromaDBManager
from src.database.postgres_setup import PostgreSQLManager
import config

class PersonalCareChatbot:
    def __init__(self):
        try:
            self.llm = ChatGroq(
                groq_api_key=config.GROQ_API_KEY,
                model_name="llama-3.1-8b-instant"
            )
            self.vector_store = ChromaDBManager()
            self.db_manager = PostgreSQLManager()
            print("✅ Chatbot initialized successfully!")
        except Exception as e:
            print(f"❌ Error initializing chatbot: {e}")
            raise
    
    def classify_intent(self, user_message):
        """Classify user intent to determine if human assistance is needed"""
        user_message_lower = user_message.lower()
        
        # Keywords that require human assistance
        human_assistance_keywords = [
            'offer', 'discount', 'promotion', 'sale', 'deal', 'coupon', 'voucher',
            'return', 'refund', 'exchange', 'shipping', 'delivery', 'track',
            'payment', 'order status', 'track order', 'account', 'billing',
            'complaint', 'issue', 'problem', 'cancel', 'warranty', 'guarantee',
            'complaint', 'support', 'help desk'
        ]
        
        for keyword in human_assistance_keywords:
            if keyword in user_message_lower:
                return 'human_assistance', True
        
        # Product inquiry keywords
        product_keywords = [
            'product', 'item', 'benefit', 'use', 'how to', 'what is',
            'recommend', 'suggest', 'find', 'search', 'look for',
            'price', 'brand', 'review', 'rating', 'feature', 'ingredient',
            'lipstick', 'skincare', 'makeup', 'cream', 'lotion', 'serum',
            'shampoo', 'conditioner', 'perfume', 'cosmetic', 'fragrance',
            'moisturizer', 'cleanser', 'toner', 'mask', 'scrub', 'oil',
            'sunscreen', 'protection', 'anti-aging', 'hydrating', 'natural'
        ]
        
        for keyword in product_keywords:
            if keyword in user_message_lower:
                return 'product_inquiry', False
        
        return 'general_inquiry', False
    
    def generate_response(self, user_message, user_id="default_user"):
        """Generate response based on user message"""
        # Classify intent
        intent, requires_human = self.classify_intent(user_message)
        
        # If human assistance required, provide contact information
        if requires_human:
            response = f"""I understand you're asking about a topic that requires specialized assistance. 

For inquiries about offers, returns, shipping, payments, or account issues, please contact our dedicated team:

📞 Customer Service: {config.CUSTOMER_SERVICE_CONTACT}
👨‍💼 Human Representative: {config.HUMAN_REPRESENTATIVE_CONTACT}

They'll provide you with the most accurate and up-to-date information!"""
            
            # Store conversation
            self.db_manager.store_conversation(
                user_id, user_message, response, intent, 
                requires_human=True, contact=config.CUSTOMER_SERVICE_CONTACT
            )
            
            return response
        
        # For product inquiries, search vector store
        product_results = []
        if intent == 'product_inquiry':
            product_results = self.vector_store.search_products(user_message, n_results=3)
        
        # Generate response using LLM
        try:
            enhanced_prompt = self.create_enhanced_prompt(user_message, intent, product_results)
            
            messages = [
                SystemMessage(content=enhanced_prompt),
                HumanMessage(content=user_message)
            ]
            
            response = self.llm.invoke(messages)
            bot_response = response.content
            
            # Store conversation
            self.db_manager.store_conversation(
                user_id, user_message, bot_response, intent,
                requires_human=False, contact=None
            )
            
            return bot_response
            
        except Exception as e:
            error_msg = "I apologize, but I'm experiencing technical difficulties. Please try again later."
            self.db_manager.store_conversation(
                user_id, user_message, error_msg, "error",
                requires_human=False, contact=None
            )
            return error_msg
    
    def create_enhanced_prompt(self, user_message, intent, product_results):
        """Create enhanced prompt based on intent and available products"""
        base_prompt = f"""
        You are a helpful personal care product assistant. Your responsibilities include:

        1. Providing information about available personal care products
        2. Answering questions about product benefits, usage, and features
        3. Helping users find suitable products based on their needs
        4. Being honest when you don't have specific information

        Contact Information for specialized inquiries:
        - Customer Service: {config.CUSTOMER_SERVICE_CONTACT}
        - Human Representative: {config.HUMAN_REPRESENTATIVE_CONTACT}

        User Question: {user_message}
        """
        
        if intent == 'product_inquiry' and product_results:
            product_context = "Based on our product database, here are relevant products:\n"
            for result in product_results:
                metadata = result['metadata']
                product_context += f"""
                🛍️ Product: {metadata['product_name']}
                🏷️ Brand: {metadata['brand']}
                💰 Price: ${metadata['price']}
                ⭐ Rating: {metadata['rating']}
                📁 Category: {metadata['breadcrumbs']}
                ---
                """
            
            return base_prompt + f"""
            Available Product Information:
            {product_context}

            Please provide helpful information about these products. Be specific about their features and benefits.
            If the user asks for recommendations, suggest the most relevant products from the list above.
            """
        else:
            return base_prompt + """
            Please provide helpful information about personal care products in general.
            If you cannot find specific products in our database, be honest and offer general advice.
            """
    
    def get_conversation_history(self, user_id="default_user", limit=10):
        """Get conversation history for a user"""
        return self.db_manager.get_conversation_history(user_id, limit)
