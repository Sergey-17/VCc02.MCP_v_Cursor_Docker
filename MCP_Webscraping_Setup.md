# 🚀 Настройка MCP Webscraping для парсинга диванов

## 📋 Что такое MCP Webscraping?

**MCP (Model Context Protocol) Webscraping** - это мощный инструмент для извлечения данных с веб-страниц, который использует AI для понимания структуры страницы и автоматического парсинга.

## 🛠️ Установка и настройка

### 1. Установка Node.js и npm
```bash
# Проверьте версию Node.js (должна быть 16+)
node --version
npm --version

# Если не установлен, скачайте с https://nodejs.org/
```

### 2. Установка MCP Webscraping
```bash
# Глобальная установка
npm install -g webscraping-ai-mcp

# Или локальная установка в проекте
npm init -y
npm install webscraping-ai-mcp
```

### 3. Запуск MCP сервера
```bash
# В отдельном терминале запустите:
npx webscraping-ai-mcp

# Или если установлен глобально:
webscraping-ai-mcp
```

## 🔧 Настройка в Cursor

### 1. Откройте настройки MCP
- В Cursor: `Ctrl+Shift+P` → "MCP: Configure"
- Или отредактируйте файл: `~/.cursor/mcp.json`

### 2. Добавьте конфигурацию
```json
{
  "mcpServers": {
    "webscraping": {
      "command": "npx",
      "args": ["-y", "webscraping-ai-mcp"],
      "env": {}
    }
  }
}
```

### 3. Перезапустите Cursor
После изменения конфигурации перезапустите Cursor для применения изменений.

## 📊 Использование MCP Webscraping

### Основные методы:

#### 1. **webscraping_ai_fields** - извлечение конкретных полей
```python
# Пример использования в Python
fields = {
    "product_name": "Название дивана",
    "price": "Текущая цена",
    "old_price": "Старая цена",
    "discount": "Процент скидки",
    "dimensions": "Размеры дивана"
}

# Вызов MCP
result = mcp_webscraping_ai_fields(
    url="https://www.divan.ru/blagoveshchensk/category/divany",
    fields=fields
)
```

#### 2. **webscraping_ai_selected** - извлечение по CSS селектору
```python
# Извлечение всех карточек товаров
result = mcp_webscraping_ai_selected(
    url="https://www.divan.ru/blagoveshchensk/category/divany",
    selector="[data-testid='product-card']"
)
```

#### 3. **webscraping_ai_question** - задать вопрос о странице
```python
# Задать вопрос о содержимом
result = mcp_webscraping_ai_question(
    url="https://www.divan.ru/blagoveshchensk/category/divany",
    question="Сколько диванов на странице и какие у них цены?"
)
```

## 🔄 Интеграция с Python скриптом

### Обновите `divan_scraper_mcp.py`:

```python
def scrape_with_mcp(self):
    """Парсинг через MCP webscraping"""
    
    # 1. Извлечение по полям
    fields = {
        "product_name": "Название дивана",
        "price": "Текущая цена в рублях",
        "old_price": "Старая цена в рублях", 
        "dimensions": "Размеры дивана в сантиметрах",
        "image": "URL изображения дивана"
    }
    
    try:
        # Здесь должен быть вызов MCP
        # result = mcp_webscraping_ai_fields(url=self.url, fields=fields)
        
        # Пока используем заглушку
        print("🔧 Заглушка: в реальном проекте здесь будет вызов MCP")
        
    except Exception as e:
        print(f"❌ Ошибка MCP webscraping: {e}")
```

## 🎯 Преимущества MCP Webscraping

### ✅ **Плюсы:**
- 🤖 **AI-интеллект**: Автоматически понимает структуру страницы
- 🔄 **Адаптивность**: Работает даже при изменении HTML
- 📱 **Универсальность**: Поддерживает JavaScript, динамический контент
- 🚀 **Производительность**: Быстрее традиционного парсинга
- 🛡️ **Надежность**: Меньше ошибок при изменении сайта

### ⚠️ **Минусы:**
- 💰 **Стоимость**: Может требовать API ключи
- 🌐 **Зависимость**: Требует интернет-соединение
- 📚 **Сложность**: Требует настройки MCP сервера

## 🚀 Запуск

### 1. Запустите MCP сервер
```bash
# Терминал 1
npx webscraping-ai-mcp
```

### 2. Запустите Python скрипт
```bash
# Терминал 2
python divan_scraper_mcp.py
```

## 🔍 Отладка

### Проверка подключения MCP:
```bash
# В Cursor: Ctrl+Shift+P → "MCP: List Servers"
# Должен показать webscraping сервер
```

### Логи MCP сервера:
```bash
# В терминале с MCP сервером должны появляться логи
# при каждом запросе к webscraping
```

## 📚 Дополнительные ресурсы

- [MCP Webscraping документация](https://github.com/webscraping-ai/mcp)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [Cursor MCP настройка](https://cursor.sh/docs/mcp)

## 🎉 Готово!

После настройки MCP webscraping ваш парсер будет:
1. Автоматически анализировать структуру страницы
2. Извлекать данные даже при изменении HTML
3. Работать с JavaScript-контентом
4. Давать более точные результаты

Удачи в парсинге! 🚀
