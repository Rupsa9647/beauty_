import pandas as pd
import os
import glob
from typing import List, Dict
import config

class CSVDataLoader:
    def __init__(self):
        self.data_folder = config.DATA_FOLDER
    
    def find_csv_files(self):
        """Find all CSV files in the data folder"""
        csv_pattern = os.path.join(self.data_folder, "*.csv")
        csv_files = glob.glob(csv_pattern)
        return csv_files
    
    def load_all_products(self):
        """Load products from all CSV files in data folder"""
        csv_files = self.find_csv_files()
        
        if not csv_files:
            print("❌ No CSV files found in the data folder!")
            return []
        
        all_products = []
        
        for csv_file in csv_files:
            print(f"📁 Loading data from: {os.path.basename(csv_file)}")
            products = self.load_products_from_csv(csv_file)
            all_products.extend(products)
        
        print(f"✅ Loaded {len(all_products)} products from {len(csv_files)} CSV file(s)")
        return all_products
    
    def load_products_from_csv(self, csv_path):
        """Load products from a specific CSV file"""
        try:
            df = pd.read_csv(csv_path)
            print(f"   📊 Found {len(df)} products in {os.path.basename(csv_path)}")
            
            # Convert DataFrame to list of dictionaries
            products = df.to_dict('records')
            
            # Clean and standardize the data
            cleaned_products = self.clean_product_data(products)
            
            return cleaned_products
            
        except Exception as e:
            print(f"❌ Error loading CSV {csv_path}: {e}")
            return []
    
    def clean_product_data(self, products: List[Dict]):
        """Clean and standardize product data"""
        cleaned_products = []
        
        for product in products:
            cleaned_product = {}
            
            # Handle product name
            cleaned_product['product_name'] = self.get_value(product, ['product_name', 'name', 'title', 'product'])
            
            # Handle brand
            cleaned_product['brand'] = self.get_value(product, ['brand', 'company', 'manufacturer']) or "Unknown Brand"
            
            # Handle price
            price = self.get_value(product, ['price', 'cost', 'amount'])
            cleaned_product['price'] = self.clean_price(price)
            
            # Handle rating
            cleaned_product['rating'] = self.get_value(product, ['rating', 'review', 'score']) or "No rating"
            
            # Handle product URL
            cleaned_product['product_url'] = self.get_value(product, ['product_url', 'url', 'link']) or ""
            
            # Handle breadcrumbs
            cleaned_product['breadcrumbs'] = self.get_value(product, ['breadcrumbs', 'category', 'categories']) or "Home / Personal Care"
            
            # Handle description
            cleaned_product['description'] = self.get_value(product, ['description', 'desc', 'details']) or f"{cleaned_product['brand']} {cleaned_product['product_name']}"
            
            # Only add if we have at least a product name
            if cleaned_product['product_name']:
                cleaned_products.append(cleaned_product)
            else:
                print(f"⚠️  Skipping product without name: {product}")
        
        return cleaned_products
    
    def get_value(self, product_dict, possible_keys):
        """Get value from dictionary using multiple possible keys"""
        for key in possible_keys:
            if key in product_dict and pd.notna(product_dict[key]) and product_dict[key] != '':
                return str(product_dict[key])
        return None
    
    def clean_price(self, price_value):
        """Clean and convert price to float"""
        if not price_value:
            return 0.0
        
        try:
            # Remove currency symbols and commas
            price_str = str(price_value).replace('$', '').replace('₹', '').replace(',', '').strip()
            
            # Extract numbers
            import re
            numbers = re.findall(r'\d+\.?\d*', price_str)
            if numbers:
                return float(numbers[0])
            return 0.0
        except:
            return 0.0
    
    def validate_data_quality(self, products):
        """Validate the quality of loaded data"""
        if not products:
            return False
        
        total_products = len(products)
        products_with_name = len([p for p in products if p.get('product_name')])
        products_with_brand = len([p for p in products if p.get('brand') and p['brand'] != "Unknown Brand"])
        products_with_price = len([p for p in products if p.get('price', 0) > 0])
        
        print(f"\n📈 Data Quality Report:")
        print(f"   Total products: {total_products}")
        print(f"   Products with name: {products_with_name} ({products_with_name/total_products*100:.1f}%)")
        print(f"   Products with brand: {products_with_brand} ({products_with_brand/total_products*100:.1f}%)")
        print(f"   Products with price: {products_with_price} ({products_with_price/total_products*100:.1f}%)")
        
        return products_with_name > 0
