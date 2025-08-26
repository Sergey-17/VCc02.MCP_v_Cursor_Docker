import requests
from bs4 import BeautifulSoup
import asyncio
import asyncpg
import pandas as pd
import time
import re
from datetime import datetime
import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

class DivanScraperAsync:
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
        
    async def create_table(self):
        """Создание таблицы divans в PostgreSQL"""
        try:
            conn = await asyncpg.connect(**self.db_config)
            
            create_table_query = """
            CREATE TABLE IF NOT EXISTS divans (
                id SERIAL PRIMARY KEY,
                name VARCHAR(500),
                price_original DECIMAL(10, 2),
                price_discount DECIMAL(10, 2),
                discount_percent INTEGER,
                dimensions VARCHAR(100),
                sleeping_dimensions VARCHAR(100),
                material VARCHAR(200),
                color VARCHAR(100),
                style VARCHAR(100),
                features TEXT[],
                url VARCHAR(500),
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
            
            await conn.execute(create_table_query)
            print("✅ Таблица divans создана/проверена")
            await conn.close()
            
        except Exception as e:
            print(f"❌ Ошибка создания таблицы: {e}")
    
    def get_page_content(self, url):
        """Получение содержимого страницы"""
        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"❌ Ошибка получения страницы {url}: {e}")
            return None
    
    def parse_divan_item(self, item_div):
        """Парсинг отдельного товара дивана"""
        try:
            # Название дивана
            name_elem = item_div.find('h3', class_='product-card__title')
            name = name_elem.get_text(strip=True) if name_elem else "Название не найдено"
            
            # Цены
            price_original = None
            price_discount = None
            discount_percent = None
            
            price_elem = item_div.find('span', class_='price__current')
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                price_discount = self.extract_price(price_text)
            
            old_price_elem = item_div.find('span', class_='price__old')
            if old_price_elem:
                old_price_text = old_price_elem.get_text(strip=True)
                price_original = self.extract_price(old_price_text)
                
                if price_original and price_discount:
                    discount_percent = int(((price_original - price_discount) / price_original) * 100)
            
            # Размеры
            dimensions = "Не указано"
            sleeping_dimensions = "Не указано"
            
            dimensions_elem = item_div.find('div', class_='product-card__dimensions')
            if dimensions_elem:
                dim_text = dimensions_elem.get_text(strip=True)
                if 'Спальное место' in dim_text:
                    # Извлекаем размеры спального места
                    sleeping_match = re.search(r'Спальное место.*?(\d+\s*x\s*\d+\s*x\s*\d+)', dim_text)
                    if sleeping_match:
                        sleeping_dimensions = sleeping_match.group(1)
                    
                    # Извлекаем общие размеры
                    general_match = re.search(r'Размеры.*?(\d+\s*x\s*\d+\s*x\s*\d+)', dim_text)
                    if general_match:
                        dimensions = general_match.group(1)
            
            # Материал и цвет (если доступно)
            material = "Не указано"
            color = "Не указано"
            
            # Стиль и особенности
            style = "Не указано"
            features = []
            
            # URL товара
            url = ""
            link_elem = item_div.find('a', class_='product-card__link')
            if link_elem and link_elem.get('href'):
                url = "https://www.divan.ru" + link_elem.get('href')
            
            return {
                'name': name,
                'price_original': price_original,
                'price_discount': price_discount,
                'discount_percent': discount_percent,
                'dimensions': dimensions,
                'sleeping_dimensions': sleeping_dimensions,
                'material': material,
                'color': color,
                'style': style,
                'features': features,
                'url': url
            }
            
        except Exception as e:
            print(f"❌ Ошибка парсинга товара: {e}")
            return None
    
    def extract_price(self, price_text):
        """Извлечение цены из текста"""
        try:
            # Убираем все символы кроме цифр
            price_clean = re.sub(r'[^\d]', '', price_text)
            if price_clean:
                return float(price_clean)
        except:
            pass
        return None
    
    def scrape_divans(self):
        """Основной метод парсинга диванов"""
        print("🚀 Начинаем парсинг диванов с divan.ru...")
        
        # Получаем содержимое страницы
        content = self.get_page_content(self.base_url)
        if not content:
            return []
        
        soup = BeautifulSoup(content, 'html.parser')
        
        # Ищем все товары диванов
        divan_items = soup.find_all('div', class_='product-card')
        
        if not divan_items:
            print("❌ Товары диванов не найдены на странице")
            return []
        
        print(f"📋 Найдено товаров: {len(divan_items)}")
        
        scraped_data = []
        
        for i, item in enumerate(divan_items, 1):
            print(f"🔄 Обрабатываем товар {i}/{len(divan_items)}")
            
            divan_data = self.parse_divan_item(item)
            if divan_data:
                scraped_data.append(divan_data)
            
            # Небольшая задержка между запросами
            time.sleep(0.5)
        
        print(f"✅ Успешно обработано товаров: {len(scraped_data)}")
        return scraped_data
    
    async def save_to_database(self, divans_data):
        """Сохранение данных в PostgreSQL"""
        if not divans_data:
            print("❌ Нет данных для сохранения")
            return
        
        try:
            conn = await asyncpg.connect(**self.db_config)
            
            # Подготавливаем данные для вставки
            insert_query = """
            INSERT INTO divans (
                name, price_original, price_discount, discount_percent,
                dimensions, sleeping_dimensions, material, color, style, features, url
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            """
            
            for divan in divans_data:
                await conn.execute(insert_query, 
                    divan['name'],
                    divan['price_original'],
                    divan['price_discount'],
                    divan['discount_percent'],
                    divan['dimensions'],
                    divan['sleeping_dimensions'],
                    divan['material'],
                    divan['color'],
                    divan['style'],
                    divan['features'],
                    divan['url']
                )
            
            print(f"✅ Успешно сохранено {len(divans_data)} записей в базу данных")
            await conn.close()
            
        except Exception as e:
            print(f"❌ Ошибка сохранения в базу данных: {e}")
    
    async def run(self):
        """Запуск всего процесса"""
        print("🎯 Запуск скрипта парсинга диванов (асинхронная версия)")
        print("=" * 50)
        
        # Создаем таблицу
        await self.create_table()
        
        # Парсим данные
        divans_data = self.scrape_divans()
        
        if divans_data:
            # Сохраняем в базу данных
            await self.save_to_database(divans_data)
            
            # Показываем статистику
            print("\n📊 Статистика парсинга:")
            print(f"Всего товаров: {len(divans_data)}")
            
            prices = [d['price_discount'] for d in divans_data if d['price_discount']]
            if prices:
                print(f"Средняя цена: {sum(prices) / len(prices):.2f} руб.")
                print(f"Минимальная цена: {min(prices)} руб.")
                print(f"Максимальная цена: {max(prices)} руб.")
            
            print("\n✅ Парсинг завершен успешно!")
        else:
            print("❌ Не удалось получить данные для парсинга")

async def main():
    """Основная функция"""
    scraper = DivanScraperAsync()
    await scraper.run()

if __name__ == "__main__":
    asyncio.run(main())
