import requests
from bs4 import BeautifulSoup
import csv
import json
import time
import re
from datetime import datetime
from typing import List, Dict, Optional
import os
import logging
from urllib.parse import urljoin, urlparse
import random

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class Product:
    """Class to represent a product"""
    
    def __init__(self):
        self.name = ""
        self.price = 0.0
        self.rating = 0
        self.description = ""
        self.availability = ""
        self.category = ""
        self.product_url = ""
        self.image_url = ""
        self.upc = ""
        self.reviews_count = 0
        self.tax = 0.0
        self.price_excluding_tax = 0.0
        self.price_including_tax = 0.0
    
    def to_dict(self) -> Dict:
        """Convert product to dictionary"""
        return {
            'name': self.name,
            'price': self.price,
            'rating': self.rating,
            'description': self.description,
            'availability': self.availability,
            'category': self.category,
            'product_url': self.product_url,
            'image_url': self.image_url,
            'upc': self.upc,
            'reviews_count': self.reviews_count,
            'tax': self.tax,
            'price_excluding_tax': self.price_excluding_tax,
            'price_including_tax': self.price_including_tax
        }
    
    def __str__(self):
        return f"{self.name} - ${self.price} - {self.rating}★"

class ECommerceScraper:
    """Main scraper class for e-commerce websites"""
    
    def __init__(self, base_url: str, delay: float = 1.0, max_pages: int = 50):
        """
        Initialize the scraper
        
        Args:
            base_url: Base URL of the website
            delay: Delay between requests in seconds
            max_pages: Maximum number of pages to scrape
        """
        self.base_url = base_url
        self.delay = delay
        self.max_pages = max_pages
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
        self.products = []
        self.categories = {}
        self.scraped_urls = set()
    
    def get_soup(self, url: str) -> Optional[BeautifulSoup]:
        """
        Fetch URL and return BeautifulSoup object
        
        Args:
            url: URL to fetch
            
        Returns:
            BeautifulSoup object or None if failed
        """
        if url in self.scraped_urls:
            logger.warning(f"Already scraped: {url}")
            return None
        
        try:
            logger.info(f"Fetching: {url}")
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            # Check if response is HTML
            if 'text/html' not in response.headers.get('Content-Type', ''):
                logger.warning(f"Skipping non-HTML content: {url}")
                return None
            
            self.scraped_urls.add(url)
            return BeautifulSoup(response.content, 'html.parser')
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching {url}: {e}")
            return None
    
    def extract_rating(self, rating_class: str) -> int:
        """
        Extract numeric rating from CSS class
        
        Args:
            rating_class: CSS class containing rating
            
        Returns:
            Numeric rating (1-5)
        """
        rating_map = {
            'One': 1,
            'Two': 2,
            'Three': 3,
            'Four': 4,
            'Five': 5
        }
        
        for key, value in rating_map.items():
            if key.lower() in rating_class.lower():
                return value
        return 0
    
    def parse_product_page(self, soup: BeautifulSoup, url: str) -> Optional[Product]:
        """
        Parse product details from individual product page
        
        Args:
            soup: BeautifulSoup object of product page
            url: Product URL
            
        Returns:
            Product object or None if parsing fails
        """
        try:
            product = Product()
            product.product_url = url
            
            # Product name
            title_elem = soup.find('h1')
            if title_elem:
                product.name = title_elem.text.strip()
            
            # Price
            price_elem = soup.find('p', class_='price_color')
            if price_elem:
                price_text = price_elem.text.strip()
                product.price = float(re.sub(r'[£$€]', '', price_text))
            
            # Rating
            rating_elem = soup.find('p', class_='star-rating')
            if rating_elem:
                rating_classes = rating_elem.get('class', [])
                for cls in rating_classes:
                    rating = self.extract_rating(cls)
                    if rating > 0:
                        product.rating = rating
                        break
            
            # Description
            desc_elem = soup.find('div', id='product_description')
            if desc_elem:
                desc_text = desc_elem.find_next('p')
                if desc_text:
                    product.description = desc_text.text.strip()
            
            # Availability
            avail_elem = soup.find('p', class_='instock availability')
            if avail_elem:
                product.availability = avail_elem.text.strip()
            
            # Product details table
            table = soup.find('table', class_='table-striped')
            if table:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 2:
                        key = cells[0].text.strip()
                        value = cells[1].text.strip()
                        
                        if 'UPC' in key:
                            product.upc = value
                        elif 'Tax' in key:
                            product.tax = float(re.sub(r'[£$€]', '', value))
                        elif 'Reviews' in key:
                            product.reviews_count = int(value)
            
            # Image URL
            image_elem = soup.find('img')
            if image_elem and image_elem.get('src'):
                image_src = image_elem.get('src')
                product.image_url = urljoin(self.base_url, image_src)
            
            return product
            
        except Exception as e:
            logger.error(f"Error parsing product page {url}: {e}")
            return None
    
    def parse_category_page(self, soup: BeautifulSoup, category: str) -> List[str]:
        """
        Parse product URLs from category page
        
        Args:
            soup: BeautifulSoup object of category page
            category: Category name
            
        Returns:
            List of product URLs
        """
        product_urls = []
        
        # Find all product links
        articles = soup.find_all('article', class_='product_pod')
        for article in articles:
            link_elem = article.find('h3').find('a') if article.find('h3') else None
            if link_elem and link_elem.get('href'):
                product_url = urljoin(self.base_url, link_elem.get('href'))
                product_urls.append(product_url)
        
        logger.info(f"Found {len(product_urls)} products in category: {category}")
        return product_urls
    
    def extract_categories(self, soup: BeautifulSoup) -> Dict[str, str]:
        """
        Extract all categories and their URLs from sidebar
        
        Args:
            soup: BeautifulSoup object of homepage
            
        Returns:
            Dictionary of category names to URLs
        """
        categories = {}
        
        # Find category sidebar
        sidebar = soup.find('div', class_='side_categories')
        if sidebar:
            # Find all category links (skip the first "Books" category)
            category_links = sidebar.find_all('a')[1:]  # Skip "Books"
            
            for link in category_links:
                name = link.text.strip()
                href = link.get('href')
                if href:
                    url = urljoin(self.base_url, href)
                    categories[name] = url
        
        return categories
    
    def scrape_category(self, category_name: str, category_url: str) -> int:
        """
        Scrape all products from a category
        
        Args:
            category_name: Name of the category
            category_url: URL of the category
            
        Returns:
            Number of products scraped
        """
        logger.info(f"Scraping category: {category_name}")
        page = 1
        total_products = 0
        
        while True:
            # Construct page URL (if pagination exists)
            if page == 1:
                page_url = category_url
            else:
                # Handle pagination for books.toscrape.com
                if 'index.html' in category_url:
                    page_url = category_url.replace('index.html', f'page-{page}.html')
                else:
                    page_url = category_url.rstrip('/') + f'/page-{page}.html'
            
            soup = self.get_soup(page_url)
            if not soup:
                break
            
            # Check if this is a valid page (not an error page)
            if soup.find('title') and '404' in soup.find('title').text:
                logger.info(f"No more pages in category: {category_name}")
                break
            
            # Parse product URLs from category page
            product_urls = self.parse_category_page(soup, category_name)
            
            if not product_urls:
                logger.info(f"No products found on page {page} for {category_name}")
                break
            
            # Scrape each product
            for product_url in product_urls:
                product_soup = self.get_soup(product_url)
                if product_soup:
                    product = self.parse_product_page(product_soup, product_url)
                    if product:
                        product.category = category_name
                        self.products.append(product)
                        total_products += 1
                        logger.info(f"Scraped: {product.name[:50]}... (${product.price})")
                
                # Be polite - delay between requests
                time.sleep(self.delay + random.uniform(0, 0.5))
            
            page += 1
            
            # Check if we've reached max pages
            if page > self.max_pages:
                logger.warning(f"Reached maximum pages ({self.max_pages}) for category: {category_name}")
                break
        
        logger.info(f"Scraped {total_products} products from category: {category_name}")
        return total_products
    
    def scrape_site(self, categories: Optional[List[str]] = None) -> int:
        """
        Scrape the entire site or specific categories
        
        Args:
            categories: List of category names to scrape (None for all categories)
            
        Returns:
            Total number of products scraped
        """
        # Start with homepage
        soup = self.get_soup(self.base_url)
        if not soup:
            logger.error("Failed to fetch homepage")
            return 0
        
        # Extract all categories
        all_categories = self.extract_categories(soup)
        self.categories = all_categories
        
        logger.info(f"Found {len(all_categories)} categories")
        
        # Determine which categories to scrape
        if categories:
            target_categories = {k: v for k, v in all_categories.items() 
                                if any(cat.lower() in k.lower() for cat in categories)}
        else:
            target_categories = all_categories
        
        total_products = 0
        
        # Scrape each category
        for category_name, category_url in target_categories.items():
            logger.info(f"Processing category: {category_name}")
            count = self.scrape_category(category_name, category_url)
            total_products += count
            
            # Add delay between categories
            time.sleep(self.delay * 2)
        
        logger.info(f"Total products scraped: {total_products}")
        return total_products
    
    def export_to_csv(self, filename: str = 'products.csv'):
        """Export scraped products to CSV file"""
        if not self.products:
            logger.warning("No products to export")
            return
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['name', 'price', 'rating', 'description', 'availability', 
                            'category', 'product_url', 'image_url', 'upc', 'reviews_count',
                            'tax', 'price_excluding_tax', 'price_including_tax']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for product in self.products:
                    writer.writerow(product.to_dict())
            
            logger.info(f"Exported {len(self.products)} products to {filename}")
            
        except Exception as e:
            logger.error(f"Error exporting to CSV: {e}")
    
    def export_to_json(self, filename: str = 'products.json'):
        """Export scraped products to JSON file"""
        if not self.products:
            logger.warning("No products to export")
            return
        
        try:
            data = {
                'scrape_date': datetime.now().isoformat(),
                'base_url': self.base_url,
                'total_products': len(self.products),
                'categories': list(self.categories.keys()),
                'products': [product.to_dict() for product in self.products]
            }
            
            with open(filename, 'w', encoding='utf-8') as jsonfile:
                json.dump(data, jsonfile, indent=2, ensure_ascii=False)
            
            logger.info(f"Exported {len(self.products)} products to {filename}")
            
        except Exception as e:
            logger.error(f"Error exporting to JSON: {e}")
    
    def get_statistics(self) -> Dict:
        """Get scraping statistics"""
        if not self.products:
            return {'total_products': 0}
        
        # Price statistics
        prices = [p.price for p in self.products]
        avg_price = sum(prices) / len(prices) if prices else 0
        
        # Rating statistics
        ratings = [p.rating for p in self.products if p.rating > 0]
        avg_rating = sum(ratings) / len(ratings) if ratings else 0
        
        # Category distribution
        category_dist = {}
        for product in self.products:
            category_dist[product.category] = category_dist.get(product.category, 0) + 1
        
        return {
            'total_products': len(self.products),
            'average_price': avg_price,
            'min_price': min(prices) if prices else 0,
            'max_price': max(prices) if prices else 0,
            'average_rating': avg_rating,
            'rating_distribution': {
                '1': len([p for p in self.products if p.rating == 1]),
                '2': len([p for p in self.products if p.rating == 2]),
                '3': len([p for p in self.products if p.rating == 3]),
                '4': len([p for p in self.products if p.rating == 4]),
                '5': len([p for p in self.products if p.rating == 5]),
                'unrated': len([p for p in self.products if p.rating == 0])
            },
            'category_distribution': category_dist,
            'categories_scraped': len(self.categories),
            'urls_scraped': len(self.scraped_urls)
        }

class ShoppingScraper:
    """Alternative scraper for shopping websites (example with Amazon-like structure)"""
    
    def __init__(self, search_query: str, max_products: int = 50):
        """
        Initialize shopping scraper
        
        Args:
            search_query: Product search query
            max_products: Maximum products to scrape
        """
        self.search_query = search_query
        self.max_products = max_products
        self.products = []
        
        # For demonstration, we'll use a mock implementation
        # In production, you would implement actual scraping logic
        self.mock_data = [
            {'name': 'Wireless Bluetooth Headphones', 'price': 49.99, 'rating': 4.5},
            {'name': 'Smart LED TV 55" 4K', 'price': 599.99, 'rating': 4.7},
            {'name': 'Portable Power Bank 20000mAh', 'price': 29.99, 'rating': 4.3},
            {'name': 'Wireless Charging Pad', 'price': 19.99, 'rating': 4.1},
            {'name': 'Bluetooth Speaker Portable', 'price': 39.99, 'rating': 4.6},
        ]
    
    def scrape(self) -> List[Dict]:
        """
        Scrape product information
        
        Returns:
            List of product dictionaries
        """
        logger.info(f"Searching for: {self.search_query}")
        logger.info("Using mock data (in production, this would scrape actual website)")
        
        # In production, you would implement:
        # 1. Send request to search URL
        # 2. Parse HTML response
        # 3. Extract product information
        # 4. Handle pagination
        
        # Return mock data for demonstration
        return self.mock_data
    
    def export_to_csv(self, filename: str = 'shopping_products.csv'):
        """Export scraped products to CSV"""
        products = self.scrape()
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            if products:
                fieldnames = products[0].keys()
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(products)
        
        logger.info(f"Exported {len(products)} products to {filename}")

def display_menu():
    """Display main menu"""
    print("\n" + "="*60)
    print("🛒 E-COMMERCE PRODUCT SCRAPER")
    print("="*60)
    print("1. Scrape Books to Scrape (Demo Site)")
    print("2. Scrape Shopping Site (Mock Data)")
    print("3. View Scraped Data")
    print("4. Export Data")
    print("5. Show Statistics")
    print("6. Exit")
    print("="*60)

def main():
    """Main program entry point"""
    scraper = None
    products_file = None
    
    while True:
        display_menu()
        choice = input("\nEnter your choice (1-6): ").strip()
        
        if choice == '1':
            # Scrape Books to Scrape
            print("\n--- SCRAPING BOOKS TO SCRAPE ---")
            base_url = input("Enter base URL (default: http://books.toscrape.com/): ").strip()
            if not base_url:
                base_url = "http://books.toscrape.com/"
            
            max_pages = input("Enter max pages per category (default: 20): ").strip()
            max_pages = int(max_pages) if max_pages else 20
            
            delay = input("Enter delay between requests in seconds (default: 1.0): ").strip()
            delay = float(delay) if delay else 1.0
            
            # Optional: Scrape specific categories
            categories_input = input("Enter specific categories (comma-separated) or press Enter for all: ").strip()
            categories = [c.strip() for c in categories_input.split(',')] if categories_input else None
            
            print("\n🚀 Starting scraper...")
            scraper = ECommerceScraper(base_url, delay=delay, max_pages=max_pages)
            
            try:
                total = scraper.scrape_site(categories=categories)
                products_file = 'products.csv'
                scraper.export_to_csv(products_file)
                print(f"\n✅ Scraped {total} products successfully!")
            except Exception as e:
                print(f"\n❌ Error: {e}")
                
        elif choice == '2':
            # Scrape Shopping Site (Mock)
            print("\n--- SHOPPING SITE SCRAPER (MOCK DATA) ---")
            query = input("Enter search query: ").strip()
            if not query:
                query = "electronics"
            
            max_products = input("Enter max products (default: 10): ").strip()
            max_products = int(max_products) if max_products else 10
            
            print(f"\n🔍 Searching for: {query}")
            shopper = ShoppingScraper(query, max_products)
            products = shopper.scrape()
            
            print(f"\n✅ Found {len(products)} products:")
            for i, product in enumerate(products, 1):
                print(f"  {i}. {product['name']} - ${product['price']} ({product['rating']}★)")
            
            shopper.export_to_csv('shopping_products.csv')
            products_file = 'shopping_products.csv'
            
        elif choice == '3':
            # View scraped data
            if not scraper or not scraper.products:
                print("\n📭 No data available. Please scrape first.")
                continue
            
            print("\n📊 SCRAPED PRODUCTS (First 10):")
            print("-"*80)
            for i, product in enumerate(scraper.products[:10], 1):
                print(f"{i}. {product.name[:50]:50} ${product.price:8.2f} {product.rating}★")
                print(f"   Category: {product.category}")
                print(f"   URL: {product.product_url[:60]}...")
                print()
            
            if len(scraper.products) > 10:
                print(f"... and {len(scraper.products) - 10} more products")
        
        elif choice == '4':
            # Export data
            if not scraper or not scraper.products:
                print("\n📭 No data available. Please scrape first.")
                continue
            
            print("\n💾 EXPORT OPTIONS:")
            print("1. Export to CSV")
            print("2. Export to JSON")
            print("3. Export both formats")
            
            export_choice = input("\nEnter choice (1-3): ").strip()
            
            if export_choice in ['1', '3']:
                filename = input("Enter CSV filename (default: products.csv): ").strip()
                if not filename:
                    filename = 'products.csv'
                scraper.export_to_csv(filename)
                print(f"✅ Exported to {filename}")
            
            if export_choice in ['2', '3']:
                filename = input("Enter JSON filename (default: products.json): ").strip()
                if not filename:
                    filename = 'products.json'
                scraper.export_to_json(filename)
                print(f"✅ Exported to {filename}")
        
        elif choice == '5':
            # Show statistics
            if not scraper or not scraper.products:
                print("\n📭 No data available. Please scrape first.")
                continue
            
            stats = scraper.get_statistics()
            print("\n📈 SCRAPING STATISTICS:")
            print("-"*50)
            print(f"Total Products: {stats['total_products']}")
            print(f"Categories Scraped: {stats['categories_scraped']}")
            print(f"URLs Scraped: {stats['urls_scraped']}")
            print(f"Average Price: ${stats['average_price']:.2f}")
            print(f"Price Range: ${stats['min_price']:.2f} - ${stats['max_price']:.2f}")
            print(f"Average Rating: {stats['average_rating']:.2f}★")
            
            print("\nRating Distribution:")
            for rating, count in stats['rating_distribution'].items():
                if count > 0:
                    print(f"  {rating} stars: {count}")
            
            print("\nTop Categories:")
            sorted_categories = sorted(stats['category_distribution'].items(), 
                                     key=lambda x: x[1], reverse=True)
            for category, count in sorted_categories[:5]:
                print(f"  {category}: {count} products")
        
        elif choice == '6':
            print("\n👋 Goodbye!")
            break
        
        else:
            print("❌ Invalid choice. Please enter 1-6.")
        
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Program interrupted. Goodbye!")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        logger.error(f"Unexpected error: {e}", exc_info=True)