import os
import psycopg2
import pandas as pd
import re
import logging
import time
from datetime import datetime
from dotenv import load_dotenv

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('divan_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Загружаем переменные окружения
load_dotenv()

class DivanScraperMCPFinal:
    """Улучшенный парсер диванов через MCP webscraping"""
    
    def __init__(self):
        """Инициализация парсера"""
        self.base_url = "https://www.divan.ru/blagoveshchensk/category/divany"
        self.max_pages = 3  # Для тестирования используем только 3 страницы
        self.delay_between_requests = 1.0  # Задержка между запросами
        self.db_config = {
            'host': os.getenv('DB_HOST'),
            'port': int(os.getenv('DB_PORT', 5432)),
            'database': os.getenv('DB_NAME'),
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD')
        }
        
        # Проверяем конфигурацию
        self.validate_config()
        
    def validate_config(self):
        """Проверка конфигурации"""
        required_vars = ['DB_HOST', 'DB_NAME', 'DB_USER', 'DB_PASSWORD']
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            logger.error(f"Отсутствуют переменные окружения: {missing_vars}")
            raise ValueError(f"Необходимо настроить: {missing_vars}")
        
        logger.info("Конфигурация проверена")
        
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
                    page_number INTEGER,
                    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            conn.commit()
            logger.info("Таблица divans готова к работе")
            
        except Exception as e:
            logger.error(f"Ошибка при создании таблицы: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def get_mcp_data(self, url):
        """
        Получение данных через MCP webscraping
        В реальной реализации здесь будет прямой вызов MCP API
        """
        try:
            logger.info(f"Получение данных с: {url}")
            
            # Импортируем реальные данные MCP
            from mcp_real_data import get_mcp_data_by_page
            
            # Определяем номер страницы из URL
            if "page-" in url:
                page_number = int(url.split("page-")[-1])
            else:
                page_number = 1
                
            # Получаем данные для страницы
            return get_mcp_data_by_page(page_number)
                
        except Exception as e:
            logger.error(f"Ошибка при получении данных MCP: {e}")
            return None
    
    def validate_mcp_response(self, response):
        """Проверка корректности ответа MCP"""
        if not response:
            return False
        
        # Проверяем наличие ключевых элементов
        required_elements = ['диван', 'руб.']
        response_lower = response.lower()
        
        has_required = all(element in response_lower for element in required_elements)
        
        if not has_required:
            logger.warning("Ответ MCP не содержит ожидаемые элементы")
            
        return has_required
    
    def parse_mcp_text_data(self, text_content, page_number=1):
        """Улучшенный парсинг данных о продуктах из текста MCP webscraping"""
        products = []
        
        if not self.validate_mcp_response(text_content):
            logger.error(f"Неверный ответ MCP для страницы {page_number}")
            return products
        
        # Разбиваем текст на строки для анализа
        lines = text_content.split('\n')
        
        # Отладочная информация
        logger.info(f"Анализируем {len(lines)} строк для страницы {page_number}")
        logger.info(f"Первые 5 строк: {lines[:5]}")
        
        # Показываем строки с диванами
        divan_lines = [line for line in lines if 'диван' in line.lower()]
        logger.info(f"Строки с диванами: {divan_lines}")
        
        # Улучшенные паттерны для поиска диванов
        product_patterns = [
            # Паттерн: [Название] (/product/...) цена руб. старая_цена руб. скидка
            r'\[([^\]]+)\]\s*\(/product/[^)]+\)\s*([\d\s]+)руб\.([\d\s]+)руб\.\s*(\d+)',
            # Паттерн: [Название] (/product/...) цена руб. скидка (без старой цены)
            r'\[([^\]]+)\]\s*\(/product/[^)]+\)\s*([\d\s]+)руб\.\s*(\d+)',
            # Паттерн: Название цена руб. старая_цена руб. скидка
            r'([^[]+)\s*([\d\s]+)руб\.([\d\s]+)руб\.\s*(\d+)',
            # Паттерн: Название цена руб. скидка (без старой цены)
            r'([^[]+)\s*([\d\s]+)руб\.\s*(\d+)'
        ]
        
        # Улучшенные паттерны для размеров
        dimensions_patterns = [
            r'Размеры \(ДхШхВ\)\s*:\s*([\d\sx]+)см',
            r'Размеры \(ДхШхВ\)\s*([\d\sx]+)см',
            r'Размеры:\s*([\d\sx]+)см'
        ]
        
        sleeping_patterns = [
            r'Спальное место \(ДхШхВ\)\s*:\s*([\d\sx]+)см',
            r'Спальное место \(ДхШхВ\)\s*([\d\sx]+)см',
            r'Спальное место:\s*([\d\sx]+)см'
        ]
        
        # Ищем диваны по структуре: название -> цены -> скидка
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            # Проверяем, что это строка с названием дивана
            if line.startswith('[Диван') and '](/product/' in line:
                try:
                    # Извлекаем название дивана
                    name_match = re.search(r'\[([^\]]+)\]', line)
                    if not name_match:
                        continue
                    
                    name = name_match.group(1).strip()
                    logger.info(f"Найден диван: {name}")
                    
                    # Ищем цены в следующей строке
                    if i + 1 < len(lines):
                        price_line = lines[i + 1].strip()
                        logger.info(f"Строка с ценами: {price_line}")
                        
                        # Извлекаем цены
                        price_match = re.search(r'([\d\s]+)руб\.([\d\s]+)руб\.', price_line)
                        if price_match:
                            price = price_match.group(1).strip()
                            old_price = price_match.group(2).strip()
                            
                            # Ищем скидку в следующей строке
                            discount = None
                            if i + 2 < len(lines):
                                discount_line = lines[i + 2].strip()
                                if discount_line.isdigit():
                                    discount = discount_line
                                    logger.info(f"Скидка: {discount}%")
                            
                            # Очищаем цены от пробелов
                            price = re.sub(r'[^\d]', '', price)
                            old_price = re.sub(r'[^\d]', '', old_price)
                            
                            # Ищем размеры в ближайших строках
                            dimensions = self.find_dimensions(lines, i, dimensions_patterns)
                            sleeping_dimensions = self.find_dimensions(lines, i, sleeping_patterns)
                            
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
                                'image_url': None,
                                'page_number': page_number
                            }
                            
                            products.append(product)
                            logger.info(f"Обработан диван: {name[:50]}... - {price} руб. (стр. {page_number})")
                            
                except Exception as e:
                    logger.warning(f"Ошибка при парсинге дивана: {e}")
                    continue
        
        return products
    
    def find_dimensions(self, lines, current_index, patterns):
        """Поиск размеров в ближайших строках"""
        # Ищем размеры в диапазоне ±5 строк
        for j in range(max(0, current_index-5), min(len(lines), current_index+5)):
            for pattern in patterns:
                match = re.search(pattern, lines[j])
                if match:
                    return match.group(1).strip()
        return None
    
    def save_to_database(self, products):
        """Сохранение продуктов в базу данных"""
        if not products:
            logger.warning("Нет данных для сохранения")
            return 0
        
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            
            saved_count = 0
            for product in products:
                try:
                    cursor.execute("""
                        INSERT INTO divans (name, price, old_price, discount_percent, 
                                         dimensions, sleeping_dimensions, url, image_url, page_number)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        product['name'],
                        product['price'],
                        product['old_price'],
                        product['discount_percent'],
                        product['dimensions'],
                        product['sleeping_dimensions'],
                        product['url'],
                        product['image_url'],
                        product['page_number']
                    ))
                    saved_count += 1
                    
                except Exception as e:
                    logger.warning(f"Ошибка при сохранении {product['name']}: {e}")
                    continue
            
            conn.commit()
            logger.info(f"Сохранено в базу данных: {saved_count} диванов")
            return saved_count
            
        except Exception as e:
            logger.error(f"Ошибка при сохранении в базу: {e}")
            return 0
        finally:
            if conn:
                conn.close()
    
    def scrape_all_pages(self):
        """Парсинг всех страниц каталога"""
        all_products = []
        
        logger.info(f"Начинаем парсинг {self.max_pages} страниц...")
        
        for page in range(1, self.max_pages + 1):
            try:
                # Формируем URL страницы
                if page == 1:
                    url = self.base_url
                else:
                    url = f"{self.base_url}/page-{page}"
                
                logger.info(f"Обработка страницы {page}/{self.max_pages}: {url}")
                
                # Получаем данные через MCP
                page_data = self.get_mcp_data(url)
                
                if page_data:
                    # Парсим данные страницы
                    products = self.parse_mcp_text_data(page_data, page)
                    all_products.extend(products)
                    
                    logger.info(f"Страница {page}: найдено {len(products)} диванов")
                else:
                    logger.warning(f"Страница {page}: данные не получены")
                
                # Задержка между запросами
                if page < self.max_pages:
                    time.sleep(self.delay_between_requests)
                    
            except Exception as e:
                logger.error(f"Ошибка при обработке страницы {page}: {e}")
                continue
        
        logger.info(f"Всего найдено диванов: {len(all_products)}")
        return all_products
    
    def export_to_csv(self, filename="divans_mcp_final.csv"):
        """Экспорт данных в CSV файл"""
        try:
            conn = psycopg2.connect(**self.db_config)
            
            # Читаем данные из базы
            df = pd.read_sql_query("""
                SELECT name, price, old_price, discount_percent, 
                       dimensions, sleeping_dimensions, url, page_number, scraped_at
                FROM divans 
                ORDER BY scraped_at DESC
            """, conn)
            
            # Сохраняем в CSV
            df.to_csv(filename, index=False, encoding='utf-8-sig')
            logger.info(f"Данные экспортированы в {filename}")
            logger.info(f"Всего записей: {len(df)}")
            
            # Показываем статистику
            if not df.empty:
                self.show_statistics(df)
            
        except Exception as e:
            logger.error(f"Ошибка при экспорте: {e}")
        finally:
            if conn:
                conn.close()
    
    def show_statistics(self, df):
        """Показ статистики по данным"""
        print("\nСТАТИСТИКА:")
        print(f"Средняя цена: {df['price'].mean():,.0f} руб.")
        print(f"Минимальная цена: {df['price'].min():,.0f} руб.")
        print(f"Максимальная цена: {df['price'].max():,.0f} руб.")
        
        # Фильтруем скидки (убираем NaN)
        valid_discounts = df['discount_percent'].dropna()
        if len(valid_discounts) > 0:
            print(f"Средняя скидка: {valid_discounts.mean():.1f}%")
        
        # Статистика по страницам
        print(f"Обработано страниц: {df['page_number'].nunique()}")
        
        # Топ-5 самых дорогих диванов
        print("\nТОП-5 самых дорогих диванов:")
        top_expensive = df.nlargest(5, 'price')[['name', 'price', 'discount_percent', 'page_number']]
        for _, row in top_expensive.iterrows():
            discount_str = f"{row['discount_percent']}%" if pd.notna(row['discount_percent']) else "N/A"
            print(f"   • {row['name'][:40]}... - {row['price']:,.0f} руб. (скидка: {discount_str}, стр. {row['page_number']})")
    
    def run_scraping(self):
        """Основной метод запуска парсинга"""
        logger.info("Запуск улучшенного парсера диванов через MCP webscraping...")
        logger.info(f"Базовый URL: {self.base_url}")
        logger.info(f"Максимум страниц: {self.max_pages}")
        
        try:
            # Создаем таблицу
            self.create_table()
            
            # Парсим все страницы
            all_products = self.scrape_all_pages()
            
            if all_products:
                logger.info(f"Всего найдено диванов: {len(all_products)}")
                
                # Сохраняем в базу
                saved_count = self.save_to_database(all_products)
                
                if saved_count > 0:
                    # Экспортируем в CSV
                    self.export_to_csv()
                    
                    logger.info(f"Парсинг завершен успешно! Сохранено {saved_count} диванов")
                else:
                    logger.error("Не удалось сохранить данные в базу")
            else:
                logger.warning("Диваны не найдены на всех страницах")
                
        except Exception as e:
            logger.error(f"Критическая ошибка при парсинге: {e}")
            raise
        
        logger.info("Парсинг завершен!")

def main():
    """Главная функция"""
    try:
        scraper = DivanScraperMCPFinal()
        scraper.run_scraping()
    except Exception as e:
        logger.error(f"Ошибка в главной функции: {e}")
        print(f"\nКритическая ошибка: {e}")
        print("Проверьте логи в файле divan_scraper.log")

if __name__ == "__main__":
    main()
