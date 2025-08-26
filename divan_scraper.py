import requests
from bs4 import BeautifulSoup
import psycopg2
import pandas as pd
import time
import re
from datetime import datetime
import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

class DivanScraper:
    def __init__(self):
        self.base_url = "https://www.divan.ru/blagoveshchensk/category/divany"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.db_config = {
            'host': os.getenv('DB_HOST'),
            'port': int(os.getenv('DB_PORT', 5432)),
            'database': os.getenv('DB_NAME'),
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD')
        }
        
    def create_table(self):
        """Создание таблицы для диванов"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            
            create_table_query = """
            CREATE TABLE IF NOT EXISTS divans (
                id SERIAL PRIMARY KEY,
                name VARCHAR(500),
                price DECIMAL(10,2),
                old_price DECIMAL(10,2),
                discount_percent INTEGER,
                dimensions VARCHAR(100),
                sleeping_dimensions VARCHAR(100),
                url VARCHAR(500),
                image_url VARCHAR(500),
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
            
            cursor.execute(create_table_query)
            conn.commit()
            print("✅ Таблица divans создана/проверена")
            
        except Exception as e:
            print(f"❌ Ошибка создания таблицы: {e}")
        finally:
            if conn:
                conn.close()
    
    def extract_price(self, price_text):
        """Извлечение цены из текста"""
        if not price_text:
            return None
        
        # Убираем все символы кроме цифр
        price_match = re.search(r'[\d\s]+', price_text.replace('руб.', '').strip())
        if price_match:
            price_str = price_match.group().replace(' ', '')
            try:
                return float(price_str)
            except ValueError:
                return None
        return None
    
    def extract_dimensions(self, specs_list):
        """Извлечение размеров из списка характеристик"""
        dimensions = {}
        if specs_list:
            for spec in specs_list.find_all('li', class_='aoJQe'):
                spec_name = spec.find('span', class_='u0pek')
                spec_value = spec.find('span', class_='vdukP')
                
                if spec_name and spec_value:
                    name = spec_name.get_text().strip()
                    value = spec_value.get_text().strip()
                    
                    if 'Размеры (ДхШхВ)' in name:
                        dimensions['dimensions'] = value
                    elif 'Спальное место (ДхШхВ)' in name:
                        dimensions['sleeping_dimensions'] = value
        
        return dimensions
    
    def parse_products(self, soup):
        """Парсинг товаров со страницы"""
        products = []
        
        # Ищем все карточки товаров по data-testid
        product_cards = soup.find_all('div', attrs={'data-testid': 'product-card'})
        
        if not product_cards:
            print("❌ Карточки товаров не найдены по data-testid='product-card'")
            # Попробуем альтернативный способ
            product_cards = soup.find_all('div', class_='_Ud0k')
            if product_cards:
                print(f"✅ Найдено {len(product_cards)} товаров по классу '_Ud0k'")
            else:
                print("❌ Товары не найдены ни одним способом")
                return products
        
        print(f"🔍 Найдено {len(product_cards)} товаров для парсинга")
        
        for i, card in enumerate(product_cards):
            try:
                # Название товара
                name_elem = card.find('span', attrs={'itemprop': 'name'})
                name = name_elem.get_text().strip() if name_elem else f"Диван {i+1}"
                
                # URL товара
                url_elem = card.find('a', class_='qUioe')
                url = "https://www.divan.ru" + url_elem.get('href') if url_elem else None
                
                # Изображение
                img_elem = card.find('img', attrs={'itemprop': 'image'})
                image_url = img_elem.get('src') if img_elem else None
                
                # Цены
                price_elem = card.find('span', attrs={'data-testid': 'price'})
                price = self.extract_price(price_elem.get_text()) if price_elem else None
                
                # Старая цена (если есть скидка)
                old_price_elem = card.find('span', class_='ui-SVNym')
                old_price = self.extract_price(old_price_elem.get_text()) if old_price_elem else None
                
                # Процент скидки
                discount_elem = card.find('div', class_='ui-OQy8X')
                discount_percent = int(discount_elem.get_text()) if discount_elem else None
                
                # Размеры
                dimensions = {}
                specs_container = card.find('div', class_='nfZ4w')
                if specs_container:
                    dimensions = self.extract_dimensions(specs_container)
                
                # Создаем объект товара
                product = {
                    'name': name,
                    'price': price,
                    'old_price': old_price,
                    'discount_percent': discount_percent,
                    'dimensions': dimensions.get('dimensions', ''),
                    'sleeping_dimensions': dimensions.get('sleeping_dimensions', ''),
                    'url': url,
                    'image_url': image_url
                }
                
                products.append(product)
                print(f"   ✅ {name[:50]}... - {price} руб.")
                
            except Exception as e:
                print(f"   ❌ Ошибка парсинга товара {i+1}: {e}")
                continue
        
        return products
    
    def save_to_database(self, products):
        """Сохранение товаров в базу данных"""
        if not products:
            print("❌ Нет товаров для сохранения")
            return
        
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            
            # Подготавливаем данные для вставки
            insert_query = """
            INSERT INTO divans (name, price, old_price, discount_percent, dimensions, sleeping_dimensions, url, image_url)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            for product in products:
                cursor.execute(insert_query, (
                    product['name'],
                    product['price'],
                    product['old_price'],
                    product['discount_percent'],
                    product['dimensions'],
                    product['sleeping_dimensions'],
                    product['url'],
                    product['image_url']
                ))
            
            conn.commit()
            print(f"✅ Сохранено {len(products)} товаров в базу данных")
            
        except Exception as e:
            print(f"❌ Ошибка сохранения в базу данных: {e}")
        finally:
            if conn:
                conn.close()
    
    def scrape(self):
        """Основной метод парсинга"""
        print("🎯 Запуск скрипта парсинга диванов")
        print("=" * 50)
        
        try:
            # Создаем таблицу
            self.create_table()
            
            print("🚀 Начинаем парсинг диванов с divan.ru...")
            
            # Получаем страницу
            response = requests.get(self.base_url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            # Парсим HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Парсим товары
            products = self.parse_products(soup)
            
            if products:
                print(f"\n📊 Найдено {len(products)} товаров")
                
                # Сохраняем в базу данных
                self.save_to_database(products)
                
                # Создаем DataFrame для анализа
                df = pd.DataFrame(products)
                print(f"\n📈 Статистика по ценам:")
                print(f"   Средняя цена: {df['price'].mean():.0f} руб.")
                print(f"   Минимальная цена: {df['price'].min():.0f} руб.")
                print(f"   Максимальная цена: {df['price'].max():.0f} руб.")
                
                # Сохраняем в CSV для проверки
                csv_filename = f"divans_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
                print(f"💾 Данные сохранены в {csv_filename}")
                
            else:
                print("❌ Товары диванов не найдены на странице")
                
        except Exception as e:
            print(f"❌ Ошибка при парсинге: {e}")

if __name__ == "__main__":
    scraper = DivanScraper()
    scraper.scrape()
