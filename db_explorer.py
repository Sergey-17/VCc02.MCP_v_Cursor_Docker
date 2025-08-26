import psycopg2
import pandas as pd
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Параметры подключения к базе данных
DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'database': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD')
}

def connect_to_db():
    """Подключение к базе данных"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print("✅ Успешно подключились к базе данных PostgreSQL!")
        return conn
    except Exception as e:
        print(f"❌ Ошибка подключения к базе данных: {e}")
        return None

def get_tables(conn):
    """Получение списка всех таблиц"""
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT table_name, table_type 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        tables = cursor.fetchall()
        cursor.close()
        
        print(f"\n📋 Найдено таблиц: {len(tables)}")
        print("=" * 50)
        
        for table_name, table_type in tables:
            print(f"📊 {table_name} ({table_type})")
        
        return [table[0] for table in tables]
    except Exception as e:
        print(f"❌ Ошибка получения списка таблиц: {e}")
        return []

def get_table_info(conn, table_name):
    """Получение информации о структуре таблицы"""
    try:
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = '{table_name}'
            ORDER BY ordinal_position;
        """)
        columns = cursor.fetchall()
        cursor.close()
        
        print(f"\n🔍 Структура таблицы '{table_name}':")
        print("-" * 60)
        print(f"{'Колонка':<20} {'Тип':<15} {'NULL':<8} {'По умолчанию'}")
        print("-" * 60)
        
        for col_name, data_type, is_nullable, col_default in columns:
            nullable = "YES" if is_nullable == "YES" else "NO"
            default = str(col_default) if col_default else "NULL"
            print(f"{col_name:<20} {data_type:<15} {nullable:<8} {default}")
        
        return columns
    except Exception as e:
        print(f"❌ Ошибка получения информации о таблице {table_name}: {e}")
        return []

def get_table_data(conn, table_name, limit=10):
    """Получение данных из таблицы (первые N строк)"""
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(f"SELECT * FROM {table_name} LIMIT {limit}")
        rows = cursor.fetchall()
        cursor.close()
        
        if rows:
            print(f"\n📄 Первые {len(rows)} строк таблицы '{table_name}':")
            print("-" * 80)
            
            # Конвертируем в DataFrame для красивого вывода
            df = pd.DataFrame(rows)
            print(df.to_string(index=False))
            
            return rows
        else:
            print(f"\n📄 Таблица '{table_name}' пуста")
            return []
            
    except Exception as e:
        print(f"❌ Ошибка получения данных из таблицы {table_name}: {e}")
        return []

def main():
    """Основная функция"""
    print("🚀 Подключение к базе данных PostgreSQL...")
    
    # Подключаемся к базе данных
    conn = connect_to_db()
    if not conn:
        return
    
    try:
        # Получаем список таблиц
        tables = get_tables(conn)
        
        if not tables:
            print("❌ Таблицы не найдены")
            return
        
        # Показываем информацию о каждой таблице
        for table_name in tables:
            print(f"\n{'='*80}")
            print(f"📊 АНАЛИЗ ТАБЛИЦЫ: {table_name}")
            print(f"{'='*80}")
            
            # Структура таблицы
            get_table_info(conn, table_name)
            
            # Данные таблицы
            get_table_data(conn, table_name)
            
            print(f"\n{'='*80}")
        
        print("\n✅ Анализ базы данных завершен!")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    finally:
        if conn:
            conn.close()
            print("🔌 Соединение с базой данных закрыто")

if __name__ == "__main__":
    main()
