# 🚀 Быстрый запуск MCP парсера диванов

## ⚡ **3 шага для запуска:**

### **1️⃣ Получите данные через MCP webscraping**
В Cursor выполните:
```python
mcp_webscraping-ai_webscraping_ai_text(
    url='https://www.divan.ru/blagoveshchensk/category/divany',
    text_format='plain',
    return_links=True
)
```

### **2️⃣ Вставьте данные в парсер**
Откройте `divan_scraper_mcp_final.py` и замените содержимое переменной `text_data` на полученный текст.

### **3️⃣ Запустите парсер**
```bash
python divan_scraper_mcp_final.py
```

## 📁 **Файлы проекта:**
- `divan_scraper_mcp_final.py` - Основной парсер
- `divan_scraper_mcp_working.py` - Тестовая версия
- `MCP_Usage_Guide.md` - Подробная инструкция
- `requirements_mcp.txt` - Зависимости

## 🎯 **Результат:**
- ✅ Данные сохранятся в PostgreSQL
- ✅ Экспорт в CSV файл
- ✅ Статистика по ценам и скидкам

---
**⏱️ Время выполнения: ~2-3 минуты**
