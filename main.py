from src.utils.data_loader import CSVDataLoader
from src.vector_store.chroma_manager import ChromaDBManager
from src.chatbot.groq_chatbot import PersonalCareChatbot
import os

def setup_system():
    """Set up the system with CSV data from data folder"""
    print("🚀 Setting up Personal Care Chatbot System...")
    
    # Create data folder if it doesn't exist
    os.makedirs("./data", exist_ok=True)
    
    # Load data from CSV files
    csv_loader = CSVDataLoader()
    products = csv_loader.load_all_products()
    
    if not products:
        print("❌ No products loaded. Please ensure you have CSV files in the 'data' folder.")
        print("💡 The CSV files should have columns like: product_name, brand, price, etc.")
        return None
    
    # Validate data quality
    if not csv_loader.validate_data_quality(products):
        print("⚠️  Data quality issues detected, but continuing...")
    
    # Add products to ChromaDB
    vector_store = ChromaDBManager()
    vector_store.add_products(products)
    
    product_count = vector_store.get_product_count()
    print(f"✅ System setup complete! Vector store contains {product_count} products.")
    
    return products

def interactive_chatbot():
    """Run interactive chatbot session"""
    print("\n" + "="*60)
    print("💄 Personal Care Product Chatbot - Interactive Mode")
    print("="*60)
    print("💬 Type your questions about personal care products")
    print("📋 Type 'history' to see your conversation history")
    print("❌ Type 'quit' to exit")
    print("="*60)
    
    chatbot = PersonalCareChatbot()
    user_id = "interactive_user"
    
    while True:
        try:
            user_input = input("\n👤 You: ").strip()
            
            if user_input.lower() == 'quit':
                break
            elif user_input.lower() == 'history':
                history = chatbot.get_conversation_history(user_id)
                print("\n📜 Conversation History:")
                if not history:
                    print("   No conversation history yet.")
                else:
                    for i, (user_msg, bot_resp, timestamp) in enumerate(history, 1):
                        print(f"   {i}. You: {user_msg}")
                        print(f"      Bot: {bot_resp[:80]}..." if len(bot_resp) > 80 else f"      Bot: {bot_resp}")
                        print(f"      Time: {timestamp}")
                continue
            elif not user_input:
                continue
            
            print("🤖 Bot: Thinking...")
            response = chatbot.generate_response(user_input, user_id)
            print(f"🤖 Bot: {response}")
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

def demo_chatbot():
    """Run demo conversations to test the system"""
    print("\n" + "="*50)
    print("🧪 Personal Care Product Chatbot - Demo Mode")
    print("="*50)
    
    chatbot = PersonalCareChatbot()
    
    # Test conversations covering different scenarios
    test_queries = [
        # Product inquiries
        "What personal care products do you have?",
        "Can you recommend skincare products?",
        "What are the benefits of using moisturizer?",
        "Do you have any anti-aging creams?",
        "What brands of shampoo do you carry?",
        
        # Human assistance scenarios
        "I want to know about current offers and discounts",
        "How can I return a product I purchased?",
        "What's your shipping policy?",
        "Can you help me track my order?",
        "Do you have any coupon codes?",
        
        # General inquiries
        "What's the price range for your products?",
        "Tell me about your brand products",
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{i}. 👤 You: {query}")
        response = chatbot.generate_response(query)
        print(f"   🤖 Bot: {response}")
        print("   " + "-" * 50)

if __name__ == "__main__":
    # Setup system with CSV data
    products = setup_system()
    
    if products:
        print("\n🎯 Choose mode:")
        print("1. Interactive Chatbot (Live conversation)")
        print("2. Demo Mode (Pre-defined test queries)")
        
        try:
            choice = input("Enter your choice (1 or 2): ").strip()
            
            if choice == "1":
                interactive_chatbot()
            else:
                demo_chatbot()
            
            print("\n✨ Thank you for using the Personal Care Chatbot!")
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
    else:
        print("\n❌ System setup failed.")
        print("💡 Please check:")
        print("   - Your CSV files are in the 'data' folder")
        print("   - CSV files have required columns (product_name, brand, price)")
        print("   - PostgreSQL database is running")
        print("   - GROQ_API_KEY is set in .env file")
