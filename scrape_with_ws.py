import requests
from bs4 import BeautifulSoup
import json
import csv
import os
import asyncio
import websockets
from datetime import datetime
import time

class WebSocketScraper:
    def __init__(self, ws_url="ws://localhost:8765"):
        self.ws_url = ws_url
        self.websocket = None
        self.data_collected = []
        
    async def connect_websocket(self):
        """Connect to WebSocket server"""
        try:
            self.websocket = await websockets.connect(self.ws_url)
            print("✅ Connected to WebSocket server")
            
            # Kirim pesan selamat datang
            await self.send_data({
                'type': 'info',
                'message': 'Scraper connected',
                'timestamp': str(datetime.now())
            })
            return True
        except Exception as e:
            print(f"⚠️ WebSocket connection failed: {e}")
            print("📝 Running in offline mode (data will be saved locally)")
            return False
    
    async def send_data(self, data):
        """Send data via WebSocket"""
        if self.websocket:
            try:
                await self.websocket.send(json.dumps(data))
                print(f"📡 Data sent via WebSocket: {data.get('type', 'data')}")
            except Exception as e:
                print(f"❌ Failed to send via WebSocket: {e}")
    
    async def scrape_books(self):
        """Scrape books and send via WebSocket"""
        url = "https://books.toscrape.com/"
        print(f"\n📚 Scraping: {url}")
        
        try:
            response = requests.get(url)
            
            if response.status_code != 200:
                print(f"❌ Error: {response.status_code}")
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            books = soup.find_all('article', class_='product_pod')
            
            print(f"📊 Found {len(books)} books\n")
            
            for idx, book in enumerate(books[:20], 1):
                # Extract data
                title = book.h3.a['title']
                price = book.find('p', class_='price_color').text
                
                rating_class = book.find('p', class_='star-rating')['class'][1]
                rating_map = {'One': 1, 'Two': 2, 'Three': 3, 'Four': 4, 'Five': 5}
                rating = rating_map.get(rating_class, 0)
                
                book_data = {
                    'type': 'book',
                    'no': idx,
                    'judul': title,
                    'harga': price,
                    'rating': rating,
                    'timestamp': str(datetime.now())
                }
                
                # Store locally
                self.data_collected.append(book_data)
                
                # Send via WebSocket
                await self.send_data(book_data)
                
                print(f"✓ [{idx}] {title[:50]} - {price} (⭐{rating})")
                await asyncio.sleep(0.5)  # Delay to avoid overwhelming
            
        except Exception as e:
            print(f"❌ Error scraping books: {e}")
        
        return self.data_collected
    
    async def scrape_quotes(self):
        """Scrape quotes and send via WebSocket"""
        url = "http://quotes.toscrape.com/"
        print(f"\n💬 Scraping: {url}")
        
        try:
            response = requests.get(url)
            
            if response.status_code != 200:
                print(f"❌ Error: {response.status_code}")
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            quotes = soup.find_all('div', class_='quote')
            
            print(f"📊 Found {len(quotes)} quotes\n")
            
            for idx, quote in enumerate(quotes[:15], 1):
                text = quote.find('span', class_='text').text
                author = quote.find('small', class_='author').text
                tags = [tag.text for tag in quote.find_all('a', class_='tag')]
                
                quote_data = {
                    'type': 'quote',
                    'no': idx,
                    'kutipan': text,
                    'penulis': author,
                    'tags': ', '.join(tags[:3]),  # Limit tags
                    'timestamp': str(datetime.now())
                }
                
                self.data_collected.append(quote_data)
                await self.send_data(quote_data)
                
                print(f"✓ [{idx}] {text[:60]}... - {author}")
                await asyncio.sleep(0.5)
                
        except Exception as e:
            print(f"❌ Error scraping quotes: {e}")
        
        return self.data_collected
    
    async def scrape_wikipedia(self):
        """Scrape countries from Wikipedia and send via WebSocket"""
        url = "https://id.wikipedia.org/wiki/Daftar_negara_di_dunia"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        
        print(f"\n🌏 Scraping: {url}")
        
        try:
            response = requests.get(url, headers=headers)
            
            if response.status_code != 200:
                print(f"❌ Error: {response.status_code}")
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            table = soup.find('table', class_='wikitable')
            
            if not table:
                print("❌ Table not found")
                return []
            
            rows = table.find_all('tr')[1:31]  # 30 countries
            
            print(f"📊 Found {len(rows)} countries\n")
            
            for idx, row in enumerate(rows, 1):
                cols = row.find_all('td')
                
                if len(cols) >= 2:
                    country = cols[0].get_text(strip=True)
                    capital = cols[1].get_text(strip=True)
                    
                    # Clean up text
                    import re
                    country = re.sub(r'\[.*?\]', '', country)
                    capital = re.sub(r'\[.*?\]', '', capital)
                    
                    country_data = {
                        'type': 'country',
                        'no': idx,
                        'negara': country,
                        'ibu_kota': capital,
                        'timestamp': str(datetime.now())
                    }
                    
                    self.data_collected.append(country_data)
                    await self.send_data(country_data)
                    
                    print(f"✓ [{idx}] {country} - {capital}")
                    await asyncio.sleep(0.3)
                    
        except Exception as e:
            print(f"❌ Error scraping Wikipedia: {e}")
        
        return self.data_collected
    
    def save_to_files(self, filename_prefix="scraping_result"):
        """Save collected data to JSON and CSV files"""
        if not self.data_collected:
            print("⚠️ No data to save")
            return
        
        # Create folder
        os.makedirs('hasil_websocket', exist_ok=True)
        
        # Save JSON
        json_file = f'hasil_websocket/{filename_prefix}.json'
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(self.data_collected, f, indent=2, ensure_ascii=False)
        print(f"💾 Saved to {json_file}")
        
        # Save CSV (flatten the data)
        if self.data_collected:
            csv_file = f'hasil_websocket/{filename_prefix}.csv'
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=self.data_collected[0].keys())
                writer.writeheader()
                writer.writerows(self.data_collected)
            print(f"💾 Saved to {csv_file}")
    
    async def run_scraping(self, choice="all"):
        """Main scraping function"""
        print("\n" + "="*50)
        print("🚀 WEB SCRAPING WITH WEBSOCKET")
        print("="*50)
        
        # Connect to WebSocket
        await self.connect_websocket()
        
        # Send start notification
        await self.send_data({
            'type': 'start',
            'message': 'Scraping started',
            'timestamp': str(datetime.now())
        })
        
        # Run selected scraper
        start_time = time.time()
        
        if choice == "books":
            await self.scrape_books()
        elif choice == "quotes":
            await self.scrape_quotes()
        elif choice == "countries":
            await self.scrape_wikipedia()
        else:  # all
            await self.scrape_books()
            await self.scrape_quotes()
            await self.scrape_wikipedia()
        
        # Send completion notification
        elapsed = time.time() - start_time
        await self.send_data({
            'type': 'complete',
            'message': f'Scraping completed in {elapsed:.2f} seconds',
            'total_data': len(self.data_collected),
            'timestamp': str(datetime.now())
        })
        
        # Save to files
        self.save_to_files()
        
        # Close WebSocket connection
        if self.websocket:
            await self.websocket.close()
            print("\n🔌 WebSocket connection closed")
        
        print(f"\n✨ Scraping completed! Total data: {len(self.data_collected)}")
        print(f"⏱️ Time elapsed: {elapsed:.2f} seconds")

async def main():
    scraper = WebSocketScraper()
    
    print("\n📋 Pilih data yang ingin di-scrape:")
    print("1. Buku (Books to Scrape)")
    print("2. Kutipan (Quotes to Scrape)")
    print("3. Negara (Wikipedia)")
    print("4. SEMUA DATA")
    
    choice_map = {
        '1': 'books',
        '2': 'quotes',
        '3': 'countries',
        '4': 'all'
    }
    
    pilihan = input("\nPilihan Anda (1-4): ").strip()
    choice = choice_map.get(pilihan, 'all')
    
    await scraper.run_scraping(choice)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Scraper stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")