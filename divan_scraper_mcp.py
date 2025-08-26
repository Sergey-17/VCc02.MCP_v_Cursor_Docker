import asyncio
import json
import os
import psycopg2
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

class DivanScraperMCP:
    """Парсер диванов через MCP webscraping"""
    
    def __init__(self):
        """Инициализация парсера"""
        self.url = "https://www.divan.ru/blagoveshchensk/category/divany"
        self.db_config = {
            'host': os.getenv('DB_HOST'),
            'port': int(os.getenv('DB_PORT', 5432)),
            'database': os.getenv('DB_NAME'),
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD')
        }
        
    def create_table(self):
        """Создание таблицы divans если её нет"""
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
            print("✅ Таблица divans готова к работе")
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            print(f"❌ Ошибка создания таблицы: {e}")
    
    def save_to_database(self, products):
        """Сохранение продуктов в базу данных"""
        if not products:
            print("❌ Нет данных для сохранения")
            return 0
        
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            
            saved_count = 0
            for product in products:
                try:
                    insert_query = """
                    INSERT INTO divans (name, price, old_price, discount_percent, 
                                      dimensions, sleeping_dimensions, url, image_url)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    
                    cursor.execute(insert_query, (
                        product.get('name'),
                        product.get('price'),
                        product.get('old_price'),
                        product.get('discount_percent'),
                        product.get('dimensions'),
                        product.get('sleeping_dimensions'),
                        product.get('url'),
                        product.get('image_url')
                    ))
                    saved_count += 1
                    
                except Exception as e:
                    print(f"⚠️ Ошибка сохранения продукта '{product.get('name', 'Unknown')}': {e}")
                    continue
            
            conn.commit()
            print(f"✅ Сохранено в базу данных: {saved_count} диванов")
            
            cursor.close()
            conn.close()
            
            return saved_count
            
        except Exception as e:
            print(f"❌ Ошибка подключения к базе данных: {e}")
            return 0
    
    def extract_price(self, price_text):
        """Извлечение цены из текста"""
        if not price_text:
            return None
        
        import re
        # Ищем числа в тексте цены
        price_match = re.search(r'(\d[\d\s]*)', price_text.replace(' ', ''))
        if price_match:
            try:
                price = int(price_match.group(1).replace(' ', ''))
                return price
            except ValueError:
                return None
        return None
    
    def calculate_discount(self, old_price, current_price):
        """Расчет процента скидки"""
        if old_price and current_price and old_price > current_price:
            discount = int(((old_price - current_price) / old_price) * 100)
            return discount
        return None
    
    def parse_products_from_mcp(self, mcp_response):
        """Парсинг продуктов из ответа MCP webscraping"""
        products = []
        
        try:
            # Пытаемся распарсить JSON ответ
            if isinstance(mcp_response, str):
                data = json.loads(mcp_response)
            else:
                data = mcp_response
            
            # Анализируем структуру ответа
            print(f"🔍 Анализируем структуру ответа MCP...")
            print(f"Тип ответа: {type(data)}")
            print(f"Ключи верхнего уровня: {list(data.keys()) if isinstance(data, dict) else 'Не словарь'}")
            
            # Ищем данные о продуктах в разных возможных местах
            product_data = None
            
            if isinstance(data, dict):
                # Проверяем различные возможные ключи
                possible_keys = ['products', 'items', 'data', 'result', 'content', 'products_data']
                for key in possible_keys:
                    if key in data:
                        product_data = data[key]
                        print(f"✅ Найдены данные в ключе: {key}")
                        break
                
                # Если не нашли по ключам, ищем в тексте
                if not product_data:
                    text_content = data.get('text', '')
                    if text_content:
                        print("🔍 Анализируем текстовое содержимое...")
                        # Здесь можно добавить логику парсинга текста
                        product_data = self.parse_text_content(text_content)
            
            if not product_data:
                print("❌ Не удалось найти данные о продуктах в ответе MCP")
                return products
            
            # Обрабатываем найденные данные
            if isinstance(product_data, list):
                for item in product_data:
                    if isinstance(item, dict):
                        product = self.parse_single_product(item)
                        if product:
                            products.append(product)
            elif isinstance(product_data, dict):
                # Если это один продукт
                product = self.parse_single_product(product_data)
                if product:
                    products.append(product)
            
            print(f"✅ Найдено продуктов: {len(products)}")
            
        except Exception as e:
            print(f"❌ Ошибка парсинга ответа MCP: {e}")
            print(f"Ответ MCP: {mcp_response[:500]}...")
        
        return products
    
    def parse_text_content(self, text_content):
        """Парсинг текстового содержимого для поиска продуктов"""
        # Простая логика поиска продуктов в тексте
        # В реальном проекте здесь можно использовать более сложные алгоритмы
        products = []
        
        # Разбиваем текст на строки
        lines = text_content.split('\n')
        current_product = {}
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Ищем названия диванов (обычно содержат слова "диван", "угловой", "прямой")
            if any(keyword in line.lower() for keyword in ['диван', 'угловой', 'прямой', 'мягкая мебель']):
                if current_product:
                    products.append(current_product)
                current_product = {'name': line}
            
            # Ищем цены
            elif '₽' in line or 'руб' in line.lower():
                price = self.extract_price(line)
                if price:
                    if 'old_price' not in current_product:
                        current_product['old_price'] = price
                    else:
                        current_product['price'] = price
            
            # Ищем размеры
            elif 'см' in line or 'x' in line:
                if 'dimensions' not in current_product:
                    current_product['dimensions'] = line
        
        # Добавляем последний продукт
        if current_product:
            products.append(current_product)
        
        return products
    
    def parse_single_product(self, item):
        """Парсинг одного продукта"""
        try:
            product = {}
            
            # Название
            product['name'] = item.get('name') or item.get('title') or item.get('product_name') or 'Неизвестный диван'
            
            # URL
            product['url'] = item.get('url') or item.get('link') or item.get('href') or ''
            
            # Изображение
            product['image_url'] = item.get('image_url') or item.get('image') or item.get('img') or ''
            
            # Цены
            price_text = item.get('price') or item.get('current_price') or ''
            old_price_text = item.get('old_price') or item.get('original_price') or ''
            
            product['price'] = self.extract_price(price_text)
            product['old_price'] = self.extract_price(old_price_text)
            
            # Скидка
            if product['old_price'] and product['price']:
                product['discount_percent'] = self.calculate_discount(product['old_price'], product['price'])
            else:
                product['discount_percent'] = None
            
            # Размеры
            product['dimensions'] = item.get('dimensions') or item.get('size') or ''
            product['sleeping_dimensions'] = item.get('sleeping_dimensions') or item.get('sleeping_size') or ''
            
            # Проверяем, что у продукта есть хотя бы название
            if product['name'] and product['name'] != 'Неизвестный диван':
                return product
            
        except Exception as e:
            print(f"⚠️ Ошибка парсинга продукта: {e}")
        
        return None
    
    def export_to_csv(self, products):
        """Экспорт данных в CSV файл"""
        if not products:
            print("❌ Нет данных для экспорта")
            return
        
        try:
            df = pd.DataFrame(products)
            filename = f"divans_mcp_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            df.to_csv(filename, index=False, encoding='utf-8-sig')
            print(f"✅ Данные экспортированы в CSV: {filename}")
            print(f"📊 Экспортировано записей: {len(df)}")
            
        except Exception as e:
            print(f"❌ Ошибка экспорта в CSV: {e}")
    
    def scrape(self):
        """Основной метод парсинга"""
        print("🚀 Запуск парсинга диванов через MCP webscraping")
        print("=" * 60)
        
        # Создаем таблицу
        self.create_table()
        
        print(f"🌐 Анализируем страницу: {self.url}")
        print("⚠️ ВНИМАНИЕ: Для работы этого скрипта нужен MCP webscraping сервер!")
        print("📋 Инструкция по настройке MCP webscraping:")
        print("1. Установите MCP webscraping: npm install -g webscraping-ai-mcp")
        print("2. Запустите MCP сервер в отдельном терминале")
        print("3. Настройте подключение в вашем MCP клиенте")
        print("=" * 60)
        
        # Здесь должен быть код для вызова MCP webscraping
        # Поскольку у нас нет прямого доступа к MCP, создаем заглушку
        
        print("🔧 Создаю тестовые данные для демонстрации...")
        
        # Создаем тестовые данные
        test_products = [
            {
                'name': 'Диван "Комфорт" угловой с подлокотниками',
                'price': 45000,
                'old_price': 60000,
                'discount_percent': 25,
                'dimensions': '200x80x85 см',
                'sleeping_dimensions': '160x200 см',
                'url': 'https://www.divan.ru/product/test1',
                'image_url': 'https://example.com/image1.jpg'
            },
            {
                'name': 'Диван "Уют" прямой с механизмом еврокнижка',
                'price': 35000,
                'old_price': 45000,
                'discount_percent': 22,
                'dimensions': '180x75x80 см',
                'sleeping_dimensions': '180x200 см',
                'url': 'https://www.divan.ru/product/test2',
                'image_url': 'https://example.com/image2.jpg'
            }
        ]
        
        print(f"✅ Создано тестовых продуктов: {len(test_products)}")
        
        # Сохраняем в базу
        saved_count = self.save_to_database(test_products)
        
        # Экспортируем в CSV
        self.export_to_csv(test_products)
        
        print("\n📊 ИТОГИ ПАРСИНГА:")
        print(f"📦 Всего продуктов: {len(test_products)}")
        print(f"💾 Сохранено в БД: {saved_count}")
        print(f"📁 Экспорт в CSV: ✅")
        
        print("\n🔧 Для реального парсинга через MCP webscraping:")
        print("1. Настройте MCP webscraping сервер")
        print("2. Замените тестовые данные на реальные вызовы MCP")
        print("3. Используйте методы: webscraping_ai_fields, webscraping_ai_selected")
        
        return test_products

def main():
    """Главная функция"""
    scraper = DivanScraperMCP()
    scraper.scrape()

if __name__ == "__main__":
    main()
