import os
import psycopg2
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

def fix_table_structure():
    """Исправление структуры таблицы divans для MCP парсера"""
    
    # Конфигурация базы данных
    db_config = {
        'host': os.getenv('DB_HOST'),
        'port': int(os.getenv('DB_PORT', 5432)),
        'database': os.getenv('DB_NAME'),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD')
    }
    
    try:
        # Подключаемся к базе
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        
        print("🔧 Проверяем структуру таблицы divans...")
        
        # Проверяем существующие колонки
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'divans' 
            ORDER BY ordinal_position
        """)
        
        columns = cursor.fetchall()
        print(f"📋 Текущие колонки: {[col[0] for col in columns]}")
        
        # Проверяем, есть ли колонка page_number
        has_page_number = any(col[0] == 'page_number' for col in columns)
        
        if not has_page_number:
            print("➕ Добавляем колонку page_number...")
            
            # Добавляем колонку page_number
            cursor.execute("""
                ALTER TABLE divans 
                ADD COLUMN page_number INTEGER DEFAULT 1
            """)
            
            # Обновляем существующие записи
            cursor.execute("""
                UPDATE divans 
                SET page_number = 1 
                WHERE page_number IS NULL
            """)
            
            print("✅ Колонка page_number добавлена и заполнена")
        else:
            print("✅ Колонка page_number уже существует")
        
        # Проверяем финальную структуру
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'divans' 
            ORDER BY ordinal_position
        """)
        
        final_columns = cursor.fetchall()
        print("\n📊 Финальная структура таблицы divans:")
        print("=" * 80)
        print(f"{'Колонка':<20} {'Тип':<15} {'NULL':<8} {'По умолчанию':<20}")
        print("=" * 80)
        
        for col in final_columns:
            name, data_type, nullable, default = col
            default_str = str(default) if default else 'NULL'
            print(f"{name:<20} {data_type:<15} {nullable:<8} {default_str:<20}")
        
        # Показываем количество записей
        cursor.execute("SELECT COUNT(*) FROM divans")
        count = cursor.fetchone()[0]
        print(f"\n📈 Всего записей в таблице: {count}")
        
        # Фиксируем изменения
        conn.commit()
        print("\n✅ Структура таблицы исправлена успешно!")
        
    except Exception as e:
        print(f"❌ Ошибка при исправлении таблицы: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()

def main():
    """Главная функция"""
    try:
        print("🚀 Исправление структуры таблицы divans для MCP парсера...")
        fix_table_structure()
        print("\n🎉 Готово! Теперь можно запускать MCP парсер")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        print("📋 Проверьте подключение к базе данных и переменные окружения")

if __name__ == "__main__":
    main()
