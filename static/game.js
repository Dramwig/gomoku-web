const socket = io();
const boardSize = 15;
let board = [];
let currentPlayer = 1; // 1: 黑棋, 2: 白棋
let gameOver = false;

const connectionStatusElement = document.getElementById('connection-status');
const boardElement = document.getElementById('board');
const statusElement = document.getElementById('status');
const messageElement = document.getElementById('message');
const restartButton = document.getElementById('restart');

// 初始化棋盘
function initBoard() {
    board = Array.from({ length: boardSize }, () => 
        Array.from({ length: boardSize }, () => 0)
    );
    
    boardElement.innerHTML = '';
    for (let i = 0; i < boardSize; i++) {
        for (let j = 0; j < boardSize; j++) {
            const cell = document.createElement('div');
            cell.dataset.row = i;
            cell.dataset.col = j;
            cell.addEventListener('click', handleCellClick);
            boardElement.appendChild(cell);
        }
    }
}

// 处理点击事件
function handleCellClick(event) {
    if (gameOver) return;
    const row = parseInt(event.target.dataset.row);
    const col = parseInt(event.target.dataset.col);

    if (board[row][col] !== 0) {
        showMessage("该位置已有棋子，请选择其他位置！");
        return;
    }

    socket.emit('make_move', { x: col, y: row });
}

// 显示提示信息
function showMessage(message) {
    messageElement.textContent = message;
    messageElement.classList.add('show');
    setTimeout(() => {
        messageElement.classList.remove('show');
    }, 1000); // 1秒后隐藏提示信息
}

// 更新棋盘状态
function updateBoard(newBoard, turn) {
    board = newBoard;
    currentPlayer = turn;
    
    boardElement.childNodes.forEach((cell, index) => {
        const row = Math.floor(index / boardSize);
        const col = index % boardSize;
        const value = board[row][col];
        
        cell.className = '';
        if (value === 1) {
            cell.classList.add('black');
        } else if (value === 2) {
            cell.classList.add('white');
        }
    });
    
    statusElement.textContent = `当前玩家：${currentPlayer === 1 ? '黑棋' : '白棋'}`;
}

// 游戏结束处理
function handleGameOver(winner, lineBegin, lineEnd) {
    gameOver = true;
    statusElement.textContent = `游戏结束，${winner === 1 ? '黑棋' : '白棋'}获胜！`;
}

// 重新开始游戏
function restartGame() {
    socket.emit("restart_game");
}

// WebSocket事件监听
socket.on('connect', () => {
    socket.emit('join_game');
});

socket.on('game_start', (data) => {
    initBoard();
    updateBoard(data.board, data.turn);
    gameOver = false;
});

socket.on('update_board', (data) => {
    updateBoard(data.board, data.turn);
});

socket.on('game_over', (data) => {
    handleGameOver(data.winner, data.line_begin, data.line_end);
});

socket.on('player_left', () => {
    statusElement.textContent = '对手已离开，游戏结束';
    gameOver = true;
});

socket.on("connection_status", (data) => {
	connectionStatusElement.textContent = data;
});

socket.on("message", (data) => {
    showMessage(data);
});

// 绑定事件监听器
restartButton.addEventListener('click', restartGame);

// 初始化游戏
initBoard();
