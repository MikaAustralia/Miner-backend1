let gameData = null;
let currentStep = 0;

document.addEventListener('DOMContentLoaded', () => {
    const webApp = window.Telegram?.WebApp;
    if (!webApp) {
        document.body.innerHTML = '<h1>Приложение работает только в Telegram</h1>';
        return;
    }

    webApp.ready();

    const startBtn = document.getElementById('start-btn');
    const bombsSelect = document.getElementById('bombs');
    const betInput = document.getElementById('bet');
    const board = document.getElementById('game-board');
    const resultDiv = document.getElementById('result');

    startBtn.onclick = async () => {
        const bombs = parseInt(bombsSelect.value);
        const bet = parseInt(betInput.value);

        if (bet < 15 || bet > 100) {
            alert("Ставка должна быть от 15 до 100");
            return;
        }

        try {
            const response = await fetch('https://miner-backend1-production-f41e.up.railway.app/start_game', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_id: webApp.initDataUnsafe?.user?.id || 123456,
                    bombs,
                    bet
                })
            });

            const data = await response.json();
            gameData = data;
            currentStep = 0;
            renderBoard(data.field);
            resultDiv.textContent = "";
        } catch (e) {
            resultDiv.textContent = "Ошибка: " + e.message;
        }
    };

    function renderBoard(field) {
        board.innerHTML = '';
        for (let i = 0; i < 5; i++) {
            for (let j = 0; j < 5; j++) {
                const cell = document.createElement('div');
                cell.className = 'cell';
                cell.dataset.x = i;
                cell.dataset.y = j;
                cell.onclick = () => openCell(i, j);
                board.appendChild(cell);
            }
        }
    }

    async function openCell(x, y) {
        if (!gameData) return;

        try {
            const response = await fetch('https://miner-backend1-production-f41e.up.railway.app/open_cell', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    x,
                    y,
                    field: gameData.field,
                    step: currentStep,
                    bombs: gameData.bombs,
                    user_id: webApp.initDataUnsafe?.user?.id || 123456
                })
            });

            const data = await response.json();

            if (data.result === 'lose') {
                revealMines();
                resultDiv.textContent = `💥 Вы проиграли! Множитель: 0x`;
                gameData = null;
                return;
            }

            // Открываем клетку
            const cells = document.querySelectorAll('.cell');
            const index = x * 5 + y;
            cells[index].classList.add('opened');
            currentStep = data.step;

            const multiplier = data.multiplier;
            resultDiv.textContent = `✅ Ход ${currentStep} | Множитель: ${multiplier}x`;

            // Проверяем, можно ли продолжить
            if (currentStep >= gameData.multipliers.length) {
                resultDiv.textContent = `🎉 Победа! Множитель: ${multiplier}x`;
                gameData = null;
            }
        } catch (e) {
            resultDiv.textContent = "Ошибка: " + e.message;
        }
    }

    function revealMines() {
        const cells = document.querySelectorAll('.cell');
        for (let i = 0; i < 5; i++) {
            for (let j = 0; j < 5; j++) {
                if (gameData.field[i][j] === -1) {
                    const index = i * 5 + j;
                    cells[index].classList.add('mine');
                    cells[index].textContent = '💣';
                }
            }
        }
    }
});


