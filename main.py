from flask import Flask, jsonify, request
import random
import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

app = Flask(__name__)

@app.route('/')
def home():
    """Главная страница с информацией об API"""
    return jsonify({
        'message': 'API для подбрасывания монетки',
        'endpoints': {
            '/': 'Информация об API',
            '/flip': 'Подбросить монетку один раз',
            '/flip/<int:count>': 'Подбросить монетку указанное количество раз',
            '/stats': 'Статистика подбрасываний'
        }
    })

@app.route('/flip')
def flip_coin():
    """Подбросить монетку один раз"""
    result = random.choice(['Орёл', 'Решка'])
    return jsonify({
        'result': result,
        'timestamp': __import__('datetime').datetime.now().isoformat()
    })

@app.route('/flip/<int:count>')
def flip_multiple(count):
    """Подбросить монетку указанное количество раз"""
    if count <= 0:
        return jsonify({'error': 'Количество должно быть положительным числом'}), 400
    
    if count > 1000:
        return jsonify({'error': 'Максимальное количество подбрасываний: 1000'}), 400
    
    results = [random.choice(['Орёл', 'Решка']) for _ in range(count)]
    heads = results.count('Орёл')
    tails = results.count('Решка')
    
    return jsonify({
        'results': results,
        'summary': {
            'total': count,
            'heads': heads,
            'tails': tails,
            'heads_percentage': round((heads / count) * 100, 2),
            'tails_percentage': round((tails / count) * 100, 2)
        },
        'timestamp': __import__('datetime').datetime.now().isoformat()
    })

@app.route('/stats')
def get_stats():
    """Получить статистику подбрасываний"""
    return jsonify({
        'message': 'Статистика подбрасываний',
        'note': 'Это демо API, статистика не сохраняется между запросами',
        'possible_results': ['Орёл', 'Решка'],
        'timestamp': __import__('datetime').datetime.now().isoformat()
    })

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Эндпоинт не найден'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Внутренняя ошибка сервера'}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('DEBUG', 'False').lower() == 'true'
    
    app.run(host='0.0.0.0', port=port, debug=debug)
