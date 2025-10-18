from flask import Flask, request, jsonify
from flask_cors import CORS  # ✅ ДОБАВЛЕНО
import random
import json
import os

app = Flask(__name__)
CORS(app)  # ✅ ДОБАВЛЕНО

# Множители из Excel
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

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

@app.route('/')
def home():
    return "Бэкенд запущен! Используй /start_game и /open_cell"

@app.route('/start_game', methods=['POST'])
def start_game():
    data = request.json
    user_id = str(data.get('user_id'))
    bombs = int(data.get('bombs'))
    bet = int(data.get('bet'))

    users = load_users()

    if user_id not in users:
        users[user_id] = {"balance": 50, "games_played": 0, "wins": 0, "losses": 0}

    user = users[user_id]

    if user['balance'] < bet:
        return jsonify({"error": "Недостаточно средств"}), 400

    user['balance'] -= bet
    user['games_played'] += 1

    field = [[0 for _ in range(5)] for _ in range(5)]
    positions = [(i, j) for i in range(5) for j in range(5)]
    bomb_positions = random.sample(positions, bombs)

    for x, y in bomb_positions:
        field[x][y] = -1  # мина

    save_users(users)

    return jsonify({
        'field': field,
        'bombs': bombs,
        'bet': bet,
        'multipliers': multipliers[bombs],
        'balance': user['balance']
    })

@app.route('/open_cell', methods=['POST'])
def open_cell():
    data = request.json
    x = int(data.get('x'))
    y = int(data.get('y'))
    field = data.get('field')
    step = data.get('step', 0)
    bombs = data.get('bombs')
    user_id = str(data.get('user_id'))
    bet = data.get('bet') # ✅ ИЗВЛЕКАЕМ СТАВКУ

    # ✅ ПРОВЕРЯЕМ, ЧТО СТАВКА НЕ None
    if bet is None:
        return jsonify({"error": "Ставка не указана"}), 400

    users = load_users()
    user = users.get(user_id, {"balance": 0})

    if field[x][y] == -1:
        user['losses'] += 1
        save_users(users)
        return jsonify({'result': 'lose', 'multiplier': 0})

    step += 1
    # ✅ ИСПРАВЛЕНАЯ ЛОГИКА: ПРОВЕРЯЕМ ГРАНИЦЫ СПИСКА
    if step <= len(multipliers[bombs]):
        multiplier = multipliers[bombs][step - 1]
    else:
        multiplier = multipliers[bombs][-1] # последний множитель

    win_amount = round(bet * multiplier, 2) # ✅ ИСПОЛЬЗУЕМ СТАВКУ
    user['balance'] += win_amount
    user['wins'] += 1

    save_users(users)

    return jsonify({
        'result': 'win',
        'step': step,
        'multiplier': multiplier,
        'field': field,
        'balance': user['balance']
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
