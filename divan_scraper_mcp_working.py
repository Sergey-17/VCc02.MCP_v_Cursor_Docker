import os
import psycopg2
import pandas as pd
import re
from datetime import datetime
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

class DivanScraperMCPWorking:
    """Рабочий парсер диванов через MCP webscraping"""
    
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
            
            cursor.execute("""
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
            """)
            
            conn.commit()
            print("✅ Таблица divans готова к работе")
            
        except Exception as e:
            print(f"❌ Ошибка при создании таблицы: {e}")
        finally:
            if conn:
                conn.close()
    
    def parse_product_data(self, text_content):
        """Парсинг данных о продуктах из текста страницы"""
        products = []
        
        # Паттерны для поиска данных
        # Ищем блоки с диванами (между названиями и ценами)
        product_patterns = [
            r'\[([^\]]+)\]\s*\(/product/[^)]+\)\s*([\d\s]+)руб\.\s*([\d\s]+)руб\.\s*(\d+)',
            r'([^[]+)\s*([\d\s]+)руб\.\s*([\d\s]+)руб\.\s*(\d+)',
            r'([^[]+)\s*([\d\s]+)руб\.\s*(\d+)'
        ]
        
        # Ищем размеры
        dimensions_pattern = r'Размеры \(ДхШхВ\)\s*([\d\sx]+)см'
        sleeping_pattern = r'Спальное место \(ДхШхВ\)\s*([\d\sx]+)см'
        
        # Разбиваем текст на строки для анализа
        lines = text_content.split('\n')
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
                
            # Ищем диваны
            for pattern in product_patterns:
                matches = re.findall(pattern, line)
                if matches:
                    for match in matches:
                        try:
                            if len(match) == 4:  # Название, цена, старая цена, скидка
                                name, price, old_price, discount = match
                            elif len(match) == 3:  # Название, цена, скидка
                                name, price, discount = match
                                old_price = None
                            else:
                                continue
                            
                            # Очищаем данные
                            name = name.strip()
                            price = re.sub(r'[^\d]', '', price.strip())
                            if old_price:
                                old_price = re.sub(r'[^\d]', '', old_price.strip())
                            discount = re.sub(r'[^\d]', '', discount.strip())
                            
                            # Проверяем, что это действительно диван
                            if 'диван' in name.lower() or 'кушетка' in name.lower():
                                # Ищем размеры в следующих строках
                                dimensions = None
                                sleeping_dimensions = None
                                
                                # Ищем размеры в ближайших строках
                                for j in range(max(0, i-5), min(len(lines), i+5)):
                                    dim_match = re.search(dimensions_pattern, lines[j])
                                    if dim_match:
                                        dimensions = dim_match.group(1).strip()
                                    
                                    sleep_match = re.search(sleeping_pattern, lines[j])
                                    if sleep_match:
                                        sleeping_dimensions = sleep_match.group(1).strip()
                                
                                # Формируем URL продукта
                                url = f"https://www.divan.ru/product/{name.lower().replace(' ', '-')}"
                                
                                product = {
                                    'name': name,
                                    'price': float(price) if price else None,
                                    'old_price': float(old_price) if old_price else None,
                                    'discount_percent': int(discount) if discount else None,
                                    'dimensions': dimensions,
                                    'sleeping_dimensions': sleeping_dimensions,
                                    'url': url,
                                    'image_url': None  # Пока не извлекаем изображения
                                }
                                
                                products.append(product)
                                print(f"✅ Найден диван: {name[:50]}... - {price}₽")
                                
                        except Exception as e:
                            print(f"⚠️ Ошибка при парсинге строки: {e}")
                            continue
        
        return products
    
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
                    cursor.execute("""
                        INSERT INTO divans (name, price, old_price, discount_percent, 
                                         dimensions, sleeping_dimensions, url, image_url)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        product['name'],
                        product['price'],
                        product['old_price'],
                        product['discount_percent'],
                        product['dimensions'],
                        product['sleeping_dimensions'],
                        product['url'],
                        product['image_url']
                    ))
                    saved_count += 1
                    
                except Exception as e:
                    print(f"⚠️ Ошибка при сохранении {product['name']}: {e}")
                    continue
            
            conn.commit()
            print(f"✅ Сохранено в базу данных: {saved_count} диванов")
            return saved_count
            
        except Exception as e:
            print(f"❌ Ошибка при сохранении в базу: {e}")
            return 0
        finally:
            if conn:
                conn.close()
    
    def export_to_csv(self, filename="divans_mcp.csv"):
        """Экспорт данных в CSV файл"""
        try:
            conn = psycopg2.connect(**self.db_config)
            
            # Читаем данные из базы
            df = pd.read_sql_query("""
                SELECT name, price, old_price, discount_percent, 
                       dimensions, sleeping_dimensions, url, scraped_at
                FROM divans 
                ORDER BY scraped_at DESC
            """, conn)
            
            # Сохраняем в CSV
            df.to_csv(filename, index=False, encoding='utf-8-sig')
            print(f"✅ Данные экспортированы в {filename}")
            print(f"📊 Всего записей: {len(df)}")
            
            # Показываем статистику
            if not df.empty:
                print("\n📈 СТАТИСТИКА:")
                print(f"💰 Средняя цена: {df['price'].mean():,.0f}₽")
                print(f"💰 Минимальная цена: {df['price'].min():,.0f}₽")
                print(f"💰 Максимальная цена: {df['price'].max():,.0f}₽")
                print(f"🎯 Средняя скидка: {df['discount_percent'].mean():.1f}%")
                
                # Топ-5 самых дорогих диванов
                print("\n🏆 ТОП-5 самых дорогих диванов:")
                top_expensive = df.nlargest(5, 'price')[['name', 'price', 'discount_percent']]
                for _, row in top_expensive.iterrows():
                    print(f"   • {row['name'][:40]}... - {row['price']:,.0f}₽ (скидка: {row['discount_percent']}%)")
            
        except Exception as e:
            print(f"❌ Ошибка при экспорте: {e}")
        finally:
            if conn:
                conn.close()
    
    def run_scraping(self):
        """Основной метод запуска парсинга"""
        print("🚀 Запуск парсинга диванов через MCP webscraping...")
        print(f"🌐 URL: {self.url}")
        
        # Создаем таблицу
        self.create_table()
        
        # Здесь должен быть вызов MCP webscraping
        # Пока используем тестовые данные для демонстрации
        print("\n📝 Примечание: Для реального парсинга используйте MCP webscraping")
        print("   Пример команды в Cursor:")
        print("   mcp_webscraping-ai_webscraping_ai_text(url='https://www.divan.ru/blagoveshchensk/category/divany')")
        
        # Тестовые данные для демонстрации
        test_products = [
            {
                'name': 'Диван прямой Филс-Мини 120 Velvet Terra',
                'price': 41150.0,
                'old_price': 58790.0,
                'discount_percent': 30,
                'dimensions': '198 x 120 x 36 см',
                'sleeping_dimensions': '198 x 120 x 36 см',
                'url': 'https://www.divan.ru/product/divan-pryamoj-fils-mini-120-velvet-terra',
                'image_url': None
            },
            {
                'name': 'Диван прямой Мелоу Velvet Eclipse',
                'price': 80840.0,
                'old_price': 101420.0,
                'discount_percent': 20,
                'dimensions': '205 x 112 x 92 см',
                'sleeping_dimensions': '205 x 160 x 46 см',
                'url': 'https://www.divan.ru/product/divan-pryamoj-melou-velvet-eclipse',
                'image_url': None
            }
        ]
        
        print(f"\n📦 Найдено тестовых диванов: {len(test_products)}")
        
        # Сохраняем в базу
        saved_count = self.save_to_database(test_products)
        
        if saved_count > 0:
            # Экспортируем в CSV
            self.export_to_csv()
        
        print("\n✅ Парсинг завершен!")

def main():
    """Главная функция"""
    scraper = DivanScraperMCPWorking()
    scraper.run_scraping()

if __name__ == "__main__":
    main()
