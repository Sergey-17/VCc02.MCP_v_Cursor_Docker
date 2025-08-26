import psycopg2
import pandas as pd
import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

def connect_to_db():
    """Подключение к базе данных"""
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST'),
            port=int(os.getenv('DB_PORT', 5432)),
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD')
        )
        print("✅ Успешно подключились к базе данных PostgreSQL!")
        return conn
    except Exception as e:
        print(f"❌ Ошибка подключения к базе данных: {e}")
        return None

def view_divans_data():
    """Просмотр данных о диванах из базы"""
    conn = connect_to_db()
    if not conn:
        return
    
    try:
        cursor = conn.cursor()
        
        # Получаем общее количество записей
        cursor.execute("SELECT COUNT(*) FROM divans")
        total_count = cursor.fetchone()[0]
        print(f"\n📊 Всего диванов в базе: {total_count}")
        
        if total_count == 0:
            print("❌ В базе нет данных о диванах")
            return
        
        # Получаем последние 10 записей с актуальными названиями колонок
        cursor.execute("""
            SELECT name, price, old_price, discount_percent, 
                   dimensions, sleeping_dimensions, scraped_at
            FROM divans 
            ORDER BY scraped_at DESC 
            LIMIT 10
        """)
        
        rows = cursor.fetchall()
        
        print(f"\n🔄 Последние {len(rows)} добавленных диванов:")
        print("=" * 120)
        print(f"{'Название':<50} {'Цена':<12} {'Старая цена':<15} {'Скидка':<8} {'Размеры':<20} {'Спальное место':<20}")
        print("=" * 120)
        
        for row in rows:
            name, price, old_price, discount, dims, sleep_dims, scraped_at = row
            
            # Обрезаем длинное название
            name_short = name[:47] + "..." if len(name) > 50 else name
            
            # Форматируем цены
            price_str = f"{price:,.0f}₽" if price else "N/A"
            old_price_str = f"{old_price:,.0f}₽" if old_price else "N/A"
            discount_str = f"{discount}%" if discount else "N/A"
            
            print(f"{name_short:<50} {price_str:<12} {old_price_str:<15} {discount_str:<8} {dims:<20} {sleep_dims:<20}")
        
        # Статистика по ценам
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                AVG(price) as avg_price,
                MIN(price) as min_price,
                MAX(price) as max_price,
                AVG(discount_percent) as avg_discount
            FROM divans 
            WHERE price IS NOT NULL
        """)
        
        stats = cursor.fetchone()
        if stats and stats[0] > 0:
            total, avg_price, min_price, max_price, avg_discount = stats
            
            print(f"\n📈 Статистика по ценам:")
            print(f"Средняя цена: {avg_price:,.0f}₽")
            print(f"Минимальная цена: {min_price:,.0f}₽")
            print(f"Максимальная цена: {max_price:,.0f}₽")
            print(f"Средняя скидка: {avg_discount:.1f}%" if avg_discount else "Средняя скидка: N/A")
        
        # Статистика по скидкам
        cursor.execute("""
            SELECT 
                CASE 
                    WHEN discount_percent >= 50 THEN '50%+'
                    WHEN discount_percent >= 30 THEN '30-49%'
                    WHEN discount_percent >= 20 THEN '20-29%'
                    WHEN discount_percent >= 10 THEN '10-19%'
                    WHEN discount_percent > 0 THEN '1-9%'
                    ELSE 'Без скидки'
                END as discount_range,
                COUNT(*) as count
            FROM divans 
            GROUP BY discount_range
            ORDER BY 
                CASE discount_range
                    WHEN '50%+' THEN 1
                    WHEN '30-49%' THEN 2
                    WHEN '20-29%' THEN 3
                    WHEN '10-19%' THEN 4
                    WHEN '1-9%' THEN 5
                    ELSE 6
                END
        """)
        
        discount_stats = cursor.fetchall()
        if discount_stats:
            print(f"\n🏷️ Статистика по скидкам:")
            for discount_range, count in discount_stats:
                print(f"{discount_range}: {count} диванов")
        
        cursor.close()
        
    except Exception as e:
        print(f"❌ Ошибка получения данных: {e}")
    
    finally:
        if conn:
            conn.close()

def export_to_csv():
    """Экспорт данных в CSV файл"""
    conn = connect_to_db()
    if not conn:
        return
    
    try:
        # Читаем все данные в DataFrame
        query = "SELECT * FROM divans ORDER BY scraped_at DESC"
        df = pd.read_sql_query(query, conn)
        
        if df.empty:
            print("❌ Нет данных для экспорта")
            return
        
        # Сохраняем в CSV
        filename = f"divans_export_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        
        print(f"✅ Данные экспортированы в файл: {filename}")
        print(f"📊 Экспортировано записей: {len(df)}")
        
    except Exception as e:
        print(f"❌ Ошибка экспорта: {e}")
    
    finally:
        if conn:
            conn.close()

def main():
    """Основная функция"""
    print("🔍 Просмотр данных о диванах из базы данных")
    print("=" * 60)
    
    while True:
        print("\n📋 ВЫБЕРИТЕ ДЕЙСТВИЕ:")
        print("1️⃣  Просмотреть данные о диванах (статистика + последние 10)")
        print("2️⃣  Экспортировать все данные в CSV файл")
        print("3️⃣  Выход из программы")
        
        choice = input("\n💬 Введите номер (1, 2 или 3): ").strip()
        
        if choice == "1":
            print("\n" + "="*60)
            view_divans_data()
            print("="*60)
        elif choice == "2":
            print("\n" + "="*60)
            export_to_csv()
            print("="*60)
        elif choice == "3":
            print("\n👋 До свидания! Программа завершена.")
            break
        else:
            print("❌ Неверный выбор! Введите 1, 2 или 3.")

if __name__ == "__main__":
    main()
