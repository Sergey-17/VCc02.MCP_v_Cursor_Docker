#!/usr/bin/env python3
"""
Тестовый скрипт для проверки API подбрасывания монетки
"""

import requests
import json
import time

BASE_URL = "http://localhost:5000"

def test_endpoint(endpoint, description):
    """Тестирует указанный эндпоинт"""
    try:
        print(f"\n🔍 Тестирую: {description}")
        print(f"URL: {BASE_URL}{endpoint}")
        
        response = requests.get(f"{BASE_URL}{endpoint}", timeout=10)
        
        print(f"Статус: {response.status_code}")
        print(f"Ответ: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        
        return response.status_code == 200
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка запроса: {e}")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ Ошибка парсинга JSON: {e}")
        return False

def main():
    """Основная функция тестирования"""
    print("🚀 Начинаю тестирование API подбрасывания монетки")
    print("=" * 60)
    
    # Тестируем все эндпоинты
    tests = [
        ("/", "Главная страница"),
        ("/flip", "Подбросить монетку один раз"),
        ("/flip/5", "Подбросить монетку 5 раз"),
        ("/flip/10", "Подбросить монетку 10 раз"),
        ("/stats", "Статистика"),
    ]
    
    success_count = 0
    total_tests = len(tests)
    
    for endpoint, description in tests:
        if test_endpoint(endpoint, description):
            success_count += 1
            print("✅ Успешно")
        else:
            print("❌ Неудачно")
        
        # Небольшая пауза между запросами
        time.sleep(0.5)
    
    print("\n" + "=" * 60)
    print(f"📊 Результаты тестирования: {success_count}/{total_tests} успешно")
    
    if success_count == total_tests:
        print("🎉 Все тесты прошли успешно! API работает корректно.")
    else:
        print("⚠️  Некоторые тесты не прошли. Проверьте логи контейнера.")

if __name__ == "__main__":
    main()
