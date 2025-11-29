from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import random
import json
import os
from datetime import datetime

app = FastAPI(title="Miner Game API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
TRANSACTIONS_FILE = 'transactions.json'
WITHDRAWAL_PERCENT = 0.40
MIN_ROUNDS_FOR_WITHDRAWAL = 20
DAILY_WITHDRAWAL_LIMIT = 500
MIN_ROUNDS_BETWEEN_DEPOSIT_WITHDRAWAL = 10
CASE_PRICE = 2

class UserInfoRequest(BaseModel):
    user_id: str

class DepositRequest(BaseModel):
    user_id: str
    stars: int
    transaction_id: Optional[str] = None

class WithdrawRequest(BaseModel):
    user_id: str
    stars: float

class StartGameRequest(BaseModel):
    user_id: str
    bombs: int
    bet: int

class OpenCellRequest(BaseModel):
    user_id: str
    x: int
    y: int
    field: list
    step: int
    bombs: int
    bet: int

class BuyCaseRequest(BaseModel):
    user_id: str

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

def load_transactions():
    if os.path.exists(TRANSACTIONS_FILE):
        with open(TRANSACTIONS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_transactions(transactions):
    with open(TRANSACTIONS_FILE, 'w', encoding='utf-8') as f:
        json.dump(transactions, f, ensure_ascii=False, indent=2)

def create_new_user(user_id):
    return {
        "balance": 0,
        "stars_deposited": 0,
        "stars_earned": 0,
        "stars_withdrawn": 0,
        "games_played": 0,
        "wins": 0,
        "losses": 0,
        "last_deposit_time": None,
        "last_withdrawal_time": None,
        "daily_withdrawal_today": 0,
        "last_withdrawal_date": None,
        "games_since_last_deposit": 0,
        "created_at": datetime.now().isoformat()
    }

@app.get("/")
async def root():
    return {
        "message": "Miner Game API на FastAPI",
        "status": "running",
        "version": "2.0 с Telegram Stars"
    }

@app.post("/get_user_info")
async def get_user_info(request: UserInfoRequest):
    users = load_users()
    
    if request.user_id not in users:
        users[request.user_id] = create_new_user(request.user_id)
        save_users(users)
    
    user = users[request.user_id]
    
    available_withdrawal = round(user['stars_earned'] * WITHDRAWAL_PERCENT - user['stars_withdrawn'], 2)
    available_withdrawal = max(0, available_withdrawal)
    
    today = datetime.now().date().isoformat()
    if user.get('last_withdrawal_date') != today:
        user['daily_withdrawal_today'] = 0
        user['last_withdrawal_date'] = today
        save_users(users)
    
    daily_remaining = DAILY_WITHDRAWAL_LIMIT - user['daily_withdrawal_today']
    available_withdrawal = min(available_withdrawal, daily_remaining)
    
    can_withdraw = (
        user['games_played'] >= MIN_ROUNDS_FOR_WITHDRAWAL and
        user.get('games_since_last_deposit', 0) >= MIN_ROUNDS_BETWEEN_DEPOSIT_WITHDRAWAL and
        available_withdrawal > 0
    )
    
    return {
        'balance': user['balance'],
        'stars_deposited': user['stars_deposited'],
        'stars_earned': round(user['stars_earned'], 2),
        'stars_withdrawn': user['stars_withdrawn'],
        'games_played': user['games_played'],
        'wins': user['wins'],
        'losses': user['losses'],
        'available_withdrawal': available_withdrawal,
        'can_withdraw': can_withdraw,
        'min_rounds_needed': MIN_ROUNDS_FOR_WITHDRAWAL,
        'daily_limit_remaining': daily_remaining,
        'games_since_deposit': user.get('games_since_last_deposit', 0)
    }

@app.post("/deposit_stars")
async def deposit_stars(request: DepositRequest):
    if request.stars <= 0:
        raise HTTPException(status_code=400, detail="Неверная сумма")
    
    users = load_users()
    
    if request.user_id not in users:
        users[request.user_id] = create_new_user(request.user_id)
    
    user = users[request.user_id]
    
    balance_add = request.stars * 100
    user['balance'] += balance_add
    user['stars_deposited'] += request.stars
    user['last_deposit_time'] = datetime.now().isoformat()
    user['games_since_last_deposit'] = 0
    
    save_users(users)
    
    transactions = load_transactions()
    transactions.append({
        'user_id': request.user_id,
        'type': 'deposit',
        'stars': request.stars,
        'balance_add': balance_add,
        'transaction_id': request.transaction_id,
        'timestamp': datetime.now().isoformat()
    })
    save_transactions(transactions)
    
    return {
        'success': True,
        'balance': user['balance'],
        'stars_deposited': user['stars_deposited'],
        'message': f'Зачислено {request.stars} Stars ({balance_add} единиц)'
    }

@app.post("/withdraw_stars")
async def withdraw_stars(request: WithdrawRequest):
    users = load_users()
    
    if request.user_id not in users:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    user = users[request.user_id]
    
    if user['games_played'] < MIN_ROUNDS_FOR_WITHDRAWAL:
        raise HTTPException(
            status_code=400,
            detail=f"Нужно сыграть минимум {MIN_ROUNDS_FOR_WITHDRAWAL} раундов. Сыграно: {user['games_played']}"
        )
    
    if user.get('games_since_last_deposit', 0) < MIN_ROUNDS_BETWEEN_DEPOSIT_WITHDRAWAL:
        raise HTTPException(
            status_code=400,
            detail=f"Нужно сыграть {MIN_ROUNDS_BETWEEN_DEPOSIT_WITHDRAWAL} игр после пополнения. Сыграно: {user.get('games_since_last_deposit', 0)}"
        )
    
    available = round(user['stars_earned'] * WITHDRAWAL_PERCENT - user['stars_withdrawn'], 2)
    
    if request.stars > available or request.stars <= 0:
        raise HTTPException(
            status_code=400,
            detail=f"Можно вывести максимум {available} Stars"
        )
    
    today = datetime.now().date().isoformat()
    if user.get('last_withdrawal_date') != today:
        user['daily_withdrawal_today'] = 0
        user['last_withdrawal_date'] = today
    
    if user['daily_withdrawal_today'] + request.stars > DAILY_WITHDRAWAL_LIMIT:
        remaining = DAILY_WITHDRAWAL_LIMIT - user['daily_withdrawal_today']
        raise HTTPException(
            status_code=400,
            detail=f"Дневной лимит: осталось {remaining} Stars"
        )
    
    user['stars_withdrawn'] += request.stars
    user['daily_withdrawal_today'] += request.stars
    user['last_withdrawal_time'] = datetime.now().isoformat()
    
    save_users(users)
    
    transactions = load_transactions()
    transactions.append({
        'user_id': request.user_id,
        'type': 'withdrawal',
        'stars': request.stars,
        'timestamp': datetime.now().isoformat()
    })
    save_transactions(transactions)
    
    return {
        'success': True,
        'stars_withdrawn': request.stars,
        'total_withdrawn': user['stars_withdrawn'],
        'message': f'Отправлен подарок на {request.stars} Stars'
    }

@app.post("/buy_case")
async def buy_case(request: BuyCaseRequest):
    users = load_users()
    
    if request.user_id not in users:
        users[request.user_id] = create_new_user(request.user_id)
    
    user = users[request.user_id]
    
    cost = CASE_PRICE * 100
    
    if user['balance'] < cost:
        raise HTTPException(status_code=400, detail="Недостаточно средств")
    
    user['balance'] -= cost
    prize = random.randint(50, 500)
    user['balance'] += prize
    
    save_users(users)
    
    return {
        'success': True,
        'prize': prize,
        'balance': user['balance'],
        'message': f'Вы выиграли {prize} единиц!'
    }

@app.post("/start_game")
async def start_game(request: StartGameRequest):
    users = load_users()

    if request.user_id not in users:
        users[request.user_id] = create_new_user(request.user_id)

    user = users[request.user_id]

    if user['balance'] < request.bet:
        raise HTTPException(status_code=400, detail="Недостаточно средств")
    
    if request.bombs not in multipliers:
        raise HTTPException(status_code=400, detail="Неверное количество мин")
    
    user['balance'] -= request.bet
    user['games_played'] += 1
    user['games_since_last_deposit'] = user.get('games_since_last_deposit', 0) + 1

    field = [[0 for _ in range(5)] for _ in range(5)]
    positions = [(i, j) for i in range(5) for j in range(5)]
    bomb_positions = random.sample(positions, request.bombs)

    for x, y in bomb_positions:
        field[x][y] = -1

    save_users(users)

    return {
        'field': field,
        'bombs': request.bombs,
        'bet': request.bet,
        'multipliers': multipliers[request.bombs],
        'balance': user['balance']
    }

@app.post("/open_cell")
async def open_cell(request: OpenCellRequest):
    users = load_users()
    user = users.get(request.user_id)

    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    if request.field[request.x][request.y] == -1:
        user['losses'] += 1
        save_users(users)
        return {'result': 'lose', 'multiplier': 0, 'balance': user['balance']}
    
    step = request.step + 1
    multiplier = (
        multipliers[request.bombs][step - 1] 
        if step <= len(multipliers[request.bombs]) 
        else multipliers[request.bombs][-1]
    )
    
    win_amount = round(request.bet * multiplier, 2)
    earned_this_round = win_amount - request.bet
    
    user['balance'] += win_amount
    user['wins'] += 1
    
    if earned_this_round > 0:
        user['stars_earned'] += earned_this_round / 100

    save_users(users)

    return {
        'result': 'win',
        'step': step,
        'multiplier': multiplier,
        'field': request.field,
        'balance': user['balance'],
        'earned': round(earned_this_round, 2)
    }

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=5000)
