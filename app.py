from flask import Flask, request, jsonify, make_response
import random
import json
import os

app = Flask(__name__)

multipliers = {
    3: [1.07, 1.22, 1.4, 1.62, 1.89, 2.22, 2.63, 3.15, 3.82, 4.7, 5.87, 7.47, 9.71, 12.94, 17.79, 25.41, 38.11, 60.97, 106.69, 213.38, 533.45, 2133.8],
    6: [1.25, 1.66, 2.24, 3.08, 4.31, 6.15, 8.98, 13.47, 20.81, 33.29, 55.48, 97.09, 180.31, 360.62, 793.36, 1983.4, 5950.2, 23800.8, 166605.6],
    9: [1.48, 2.36, 3.87, 6.54, 11.44, 20.8, 39.52, 79.04, 167.96, 383.9, 959.75, 2687.3, 8733.72, 34934.88, 192141.84, 1921418.4],
    12: [1.82, 3.64, 7.61, 16.74, 39.06, 97.65, 265.05, 795.15, 2703.51, 10814.04, 54070.2, 378491.4, 4920388.2],
    15: [2.37, 6.32, 18.17, 57.1, 199.85, 799.4, 3797.15, 22782.9, 193654.65, 3098474.4],
    16: [2.63, 7.89, 25.92, 95.04, 399.16, 1995.8, 12640.06, 113760.54, 1933929.18],
    17: [2.96, 10.14, 38.37, 171.02, 897.85, 5985.66, 56863.77, 1023547.86],
    18: [3.39, 13.56, 62.37, 343.03, 2401.21, 24012.1, 456229.9],
    19: [3.95, 18.96, 109.02, 799.48, 8394.54, 167890.8],
    20: [4.75, 28.5, 218.5, 2403.5, 50473.5],
    21: [5.94, 47.44, 545.56, 12002.32],
    22: [7.91, 94.92, 2183.16],
    23: [11.87, 284.88],
    24: [23.75]
}

USERS_FILE = 'users.json'

# Бонусы магазина
SHOP_BONUSES = {
    'bonus_100': {'coins': 100, 'games_required': 10},
    'bonus_200': {'coins': 200, 'games_required': 15},
    'bonus_500': {'coins': 500, 'games_required': 30}
}

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

def add_cors_headers(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', '*')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

@app.route('/')
def home():
    response = make_response("✅ Бэкенд Miner запущен! API: /start_game, /open_cell, /cashout, /balance, /shop_bonus")
    return add_cors_headers(response)

@app.route('/balance', methods=['POST', 'OPTIONS'])
def get_balance():
    if request.method == 'OPTIONS':
        return add_cors_headers(make_response())

    data = request.json
    user_id = str(data.get('user_id'))
    
    users = load_users()
    
    if user_id not in users:
        users[user_id] = {
            "balance": 100,  # Начальный баланс 100
            "games_played": 0, 
            "wins": 0, 
            "losses": 0,
            "claimed_bonuses": []  # Список полученных бонусов
        }
        save_users(users)
    
    user = users[user_id]
    
    # Проверяем доступные бонусы
    available_bonuses = []
    for bonus_id, bonus_data in SHOP_BONUSES.items():
        if bonus_id not in user.get('claimed_bonuses', []):
            if user['games_played'] >= bonus_data['games_required']:
                available_bonuses.append({
                    'id': bonus_id,
                    'coins': bonus_data['coins'],
                    'games_required': bonus_data['games_required']
                })
    
    response = make_response(jsonify({
        'balance': user['balance'],
        'games_played': user['games_played'],
        'wins': user['wins'],
        'losses': user['losses'],
        'available_bonuses': available_bonuses
    }))
    
    return add_cors_headers(response)

@app.route('/start_game', methods=['POST', 'OPTIONS'])
def start_game():
    if request.method == 'OPTIONS':
        return add_cors_headers(make_response())

    data = request.json
    user_id = str(data.get('user_id'))
    bombs = int(data.get('bombs'))
    bet = int(data.get('bet'))

    users = load_users()

    if user_id not in users:
        users[user_id] = {
            "balance": 100, 
            "games_played": 0, 
            "wins": 0, 
            "losses": 0,
            "claimed_bonuses": []
        }

    user = users[user_id]

    if user['balance'] < bet:
        response = make_response(jsonify({"error": "Недостаточно средств"}), 400)
    else:
        user['balance'] -= bet
        user['games_played'] += 1

        field = [[0 for _ in range(5)] for _ in range(5)]
        positions = [(i, j) for i in range(5) for j in range(5)]
        bomb_positions = random.sample(positions, bombs)

        for x, y in bomb_positions:
            field[x][y] = -1

        save_users(users)

        response = make_response(jsonify({
            'field': field,
            'bombs': bombs,
            'bet': bet,
            'multipliers': multipliers[bombs],
            'balance': user['balance'],
            'games_played': user['games_played']
        }))

    return add_cors_headers(response)

@app.route('/open_cell', methods=['POST', 'OPTIONS'])
def open_cell():
    if request.method == 'OPTIONS':
        return add_cors_headers(make_response())

    data = request.json
    x = int(data.get('x'))
    y = int(data.get('y'))
    field = data.get('field')
    step = data.get('step', 0)
    bombs = data.get('bombs')
    user_id = str(data.get('user_id'))

    users = load_users()
    user = users.get(user_id, {
        "balance": 100, 
        "games_played": 0, 
        "wins": 0, 
        "losses": 0,
        "claimed_bonuses": []
    })

    if field[x][y] == -1:
        user['losses'] += 1
        save_users(users)
        
        response = make_response(jsonify({
            'result': 'lose', 
            'multiplier': 0,
            'balance': user['balance']
        }))
    else:
        step += 1
        multiplier = multipliers[bombs][step - 1] if step <= len(multipliers[bombs]) else multipliers[bombs][-1]
        
        save_users(users)

        response = make_response(jsonify({
            'result': 'win',
            'step': step,
            'multiplier': multiplier,
            'balance': user['balance']
        }))

    return add_cors_headers(response)

@app.route('/cashout', methods=['POST', 'OPTIONS'])
def cashout():
    if request.method == 'OPTIONS':
        return add_cors_headers(make_response())

    data = request.json
    user_id = str(data.get('user_id'))
    bet = float(data.get('bet'))
    multiplier = float(data.get('multiplier'))

    users = load_users()
    user = users.get(user_id, {
        "balance": 100, 
        "games_played": 0, 
        "wins": 0, 
        "losses": 0,
        "claimed_bonuses": []
    })

    win_amount = round(bet * multiplier, 2)
    user['balance'] += win_amount
    user['wins'] += 1

    save_users(users)

    response = make_response(jsonify({
        'balance': user['balance'],
        'win_amount': win_amount
    }))

    return add_cors_headers(response)

@app.route('/shop_bonus', methods=['POST', 'OPTIONS'])
def shop_bonus():
    if request.method == 'OPTIONS':
        return add_cors_headers(make_response())

    data = request.json
    user_id = str(data.get('user_id'))
    bonus_id = data.get('bonus_id')

    users = load_users()
    user = users.get(user_id, {
        "balance": 100, 
        "games_played": 0, 
        "wins": 0, 
        "losses": 0,
        "claimed_bonuses": []
    })

    # Проверяем существование бонуса
    if bonus_id not in SHOP_BONUSES:
        response = make_response(jsonify({"error": "Неизвестный бонус"}), 400)
        return add_cors_headers(response)

    bonus_data = SHOP_BONUSES[bonus_id]

    # Проверяем, не был ли бонус уже получен
    if bonus_id in user.get('claimed_bonuses', []):
        response = make_response(jsonify({"error": "Бонус уже получен"}), 400)
        return add_cors_headers(response)

    # Проверяем количество игр
    if user['games_played'] < bonus_data['games_required']:
        response = make_response(jsonify({
            "error": f"Нужно сыграть ещё {bonus_data['games_required'] - user['games_played']} игр"
        }), 400)
        return add_cors_headers(response)

    # Начисляем бонус
    user['balance'] += bonus_data['coins']
    if 'claimed_bonuses' not in user:
        user['claimed_bonuses'] = []
    user['claimed_bonuses'].append(bonus_id)

    save_users(users)

    response = make_response(jsonify({
        'balance': user['balance'],
        'bonus_coins': bonus_data['coins'],
        'message': f'Получено {bonus_data["coins"]} монет!'
    }))

    return add_cors_headers(response)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
