import psycopg2
import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

def fix_table():
    """Исправление структуры таблицы divans"""
    db_config = {
        'host': os.getenv('DB_HOST'),
        'port': int(os.getenv('DB_PORT', 5432)),
        'database': os.getenv('DB_NAME'),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD')
    }
    
    try:
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        
        print("🔧 Исправляем структуру таблицы divans...")
        
        # Удаляем старую таблицу
        cursor.execute("DROP TABLE IF EXISTS divans;")
        print("   ✅ Старая таблица удалена")
        
        # Создаем новую таблицу с правильной структурой
        create_table_query = """
        CREATE TABLE divans (
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
        print("   ✅ Новая таблица создана с правильной структурой")
        
        # Проверяем структуру
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'divans' 
            ORDER BY ordinal_position;
        """)
        
        columns = cursor.fetchall()
        print("\n📋 Структура таблицы divans:")
        for col in columns:
            print(f"   {col[0]}: {col[1]}")
        
        print("\n✅ Таблица исправлена успешно!")
        
    except Exception as e:
        print(f"❌ Ошибка исправления таблицы: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    fix_table()
