import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from typing import List, Dict
import config

class ChromaDBManager:
    def __init__(self):
        self.client = chromadb.PersistentClient(path=config.CHROMA_PERSIST_DIR)
        self.collection = self.client.get_or_create_collection(name=config.COLLECTION_NAME)
        self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
    
    def add_products(self, products: List[Dict]):
        """Add products to ChromaDB vector store"""
        if not products:
            print("❌ No products to add to ChromaDB")
            return
        
        documents = []
        metadatas = []
        ids = []
        
        for idx, product in enumerate(products):
            if not product.get('product_name'):
                continue
                
            # Create document text for embedding
            doc_text = self.create_product_document(product)
            
            documents.append(doc_text)
            metadatas.append({
                'product_name': product.get('product_name', ''),
                'brand': product.get('brand', 'Unknown Brand'),
                'price': str(product.get('price', 0)),
                'rating': product.get('rating', 'No rating'),
                'product_url': product.get('product_url', ''),
                'breadcrumbs': product.get('breadcrumbs', 'Home / Personal Care'),
                'description': product.get('description', ''),
                'type': 'product'
            })
            ids.append(f"product_{idx}")
        
        if documents:
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            print(f"✅ Added {len(products)} products to ChromaDB vector store")
        else:
            print("❌ No valid products to add to ChromaDB")
    
    def create_product_document(self, product):
        """Create a comprehensive document for vector embedding"""
        return f"""
        Product: {product.get('product_name', '')}
        Brand: {product.get('brand', 'Unknown Brand')}
        Price: {product.get('price', 'N/A')}
        Rating: {product.get('rating', 'No rating')}
        Description: {product.get('description', '')}
        Category: {product.get('breadcrumbs', 'Home / Personal Care')}
        Type: Personal Care Product
        """
    
    def search_products(self, query: str, n_results: int = 5):
        """Search for products similar to the query"""
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results
            )
            
            products = []
            if results['documents'] and results['documents'][0]:
                for i in range(len(results['documents'][0])):
                    product_info = {
                        'document': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i],
                        'distance': results['distances'][0][i] if results['distances'] else 0
                    }
                    products.append(product_info)
            
            return products
        except Exception as e:
            print(f"❌ Error searching products: {e}")
            return []
    
    def get_product_count(self):
        """Get number of products in collection"""
        try:
            results = self.collection.get()
            return len(results['ids']) if results and 'ids' in results else 0
        except Exception as e:
            print(f"❌ Error getting product count: {e}")
            return 0
    
    def get_all_products(self):
        """Get all products from collection (for debugging)"""
        try:
            return self.collection.get()
        except Exception as e:
            print(f"❌ Error getting all products: {e}")
            return None

## Step 5: Chatbot
