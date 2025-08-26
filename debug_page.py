import requests
from bs4 import BeautifulSoup
import json

def debug_page():
    """Отладка структуры страницы divan.ru"""
    url = "https://www.divan.ru/blagoveshchensk/category/divany"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        print("🔍 Получаем страницу для анализа...")
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        print(f"✅ Страница получена. Статус: {response.status_code}")
        print(f"📏 Размер страницы: {len(response.text)} символов")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Ищем различные возможные селекторы для товаров
        print("\n🔍 Анализируем структуру страницы...")
        
        # Проверяем наличие основных элементов
        print("\n📋 Основные элементы страницы:")
        
        # Ищем заголовок страницы
        title = soup.find('title')
        if title:
            print(f"   Заголовок: {title.get_text().strip()}")
        
        # Ищем мета-теги
        meta_description = soup.find('meta', attrs={'name': 'description'})
        if meta_description:
            print(f"   Описание: {meta_description.get('content', '')}")
        
        # Ищем различные возможные контейнеры товаров
        print("\n🔍 Поиск контейнеров товаров:")
        
        # Попробуем найти товары по различным селекторам
        selectors_to_try = [
            '.product-item',
            '.catalog-item',
            '.item',
            '.product',
            '.divan-item',
            '[data-product]',
            '.catalog__item',
            '.product-card',
            '.item-card'
        ]
        
        for selector in selectors_to_try:
            items = soup.select(selector)
            if items:
                print(f"   ✅ Найдено {len(items)} элементов по селектору '{selector}'")
                # Показываем первый элемент для анализа
                if len(items) > 0:
                    first_item = items[0]
                    print(f"      Первый элемент: {first_item.name} с классами: {first_item.get('class', [])}")
                    # Ищем название
                    name_elem = first_item.find(['h1', 'h2', 'h3', 'h4', '.name', '.title', '.product-name'])
                    if name_elem:
                        print(f"      Название: {name_elem.get_text().strip()[:100]}...")
                    # Ищем цену
                    price_elem = first_item.find(['.price', '.cost', '.product-price', '[data-price]'])
                    if price_elem:
                        print(f"      Цена: {price_elem.get_text().strip()[:50]}...")
            else:
                print(f"   ❌ Селектор '{selector}' не найден")
        
        # Ищем по атрибутам data-*
        print("\n🔍 Поиск по data-атрибутам:")
        data_elements = soup.find_all(attrs={'data-product': True})
        if data_elements:
            print(f"   ✅ Найдено {len(data_elements)} элементов с data-product")
        
        # Ищем по классам, содержащим определенные слова
        print("\n🔍 Поиск по классам с ключевыми словами:")
        keywords = ['product', 'item', 'card', 'divan', 'catalog']
        for keyword in keywords:
            elements = soup.find_all(class_=lambda x: x and keyword in x.lower())
            if elements:
                print(f"   ✅ Найдено {len(elements)} элементов с классом, содержащим '{keyword}'")
        
        # Сохраняем HTML для анализа
        with open('page_debug.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
        print(f"\n💾 HTML страницы сохранен в файл 'page_debug.html'")
        
        # Ищем скрипты с данными
        print("\n🔍 Поиск скриптов с данными:")
        scripts = soup.find_all('script')
        for i, script in enumerate(scripts):
            if script.string and ('product' in script.string.lower() or 'catalog' in script.string.lower()):
                print(f"   ✅ Скрипт {i+1} содержит данные о товарах")
                script_content = script.string[:200] + "..." if len(script.string) > 200 else script.string
                print(f"      Содержимое: {script_content}")
        
    except Exception as e:
        print(f"❌ Ошибка при анализе страницы: {e}")

if __name__ == "__main__":
    debug_page()
