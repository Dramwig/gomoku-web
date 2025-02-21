from flask import Flask, render_template, request
from flask_socketio import SocketIO
import random

app = Flask(__name__, template_folder="static")
app.config["SECRET_KEY"] = "secret!"
socketio = SocketIO(app)

BOARD_SIZE = 15
players = {}
games = {}


class Game:
    def __init__(self):
        self.board = [[0] * BOARD_SIZE for _ in range(BOARD_SIZE)]
        self.players = []
        self.current_player = 1
        self.game_over = False

    def add_player(self, sid):
        print(f"Player {sid} joined game {id(self)}")
        if len(self.players) < 2:
            self.players.append(sid)
            return True
        return False

    def del_player(self, sid):
        print(f"Player {sid} leave game {id(self)}")
        if sid in self.players:
            self.players.remove(sid)

    def make_move(self, x, y):
        if self.board[y][x] != 0 or self.game_over:
            return False

        self.board[y][x] = self.current_player
        if self.check_win(x, y):
            self.game_over = True
            return "win"

        self.current_player = 3 - self.current_player
        return True

    def check_win(self, x, y):
        directions = [(1, 0), (0, 1), (1, 1), (1, -1)]

        for dx, dy in directions:
            count = 1
            self.winbegin = (x, y)
            self.winend = (x, y)
            for i in range(1, 5):
                if self.is_same(x + i * dx, y + i * dy, self.board[y][x]):
                    count += 1
                    self.winbegin = (x + i * dx, y + i * dy)
                else:
                    break
            for i in range(1, 5):
                if self.is_same(x - i * dx, y - i * dy, self.board[y][x]):
                    count += 1
                    self.winend = (x - i * dx, y - i * dy)
                else:
                    break
            if count >= 5:
                return True
        return False

    def is_same(self, x, y, value):
        if x < 0 or x >= BOARD_SIZE or y < 0 or y >= BOARD_SIZE:
            return False
        return self.board[y][x] == value


def find_available_game():
    for game in games.values():
        if len(game.players) < 2:
            return game
    game = Game()
    games[id(game)] = game
    print(f"Game {id(game)} created")
    return game


@app.route("/")
def index():
    return render_template("index.html")


@socketio.on("connect")
def handle_connect():
    socketio.emit("connection_status", "连接成功", room=request.sid)


@socketio.on("join_game")
def handle_join_game():
    sid = request.sid
    game = find_available_game()

    if not game.add_player(sid):
        socketio.emit("game_full", room=sid)
        return

    players[sid] = game
    socketio.emit(
        "game_start", {"board": game.board, "turn": game.current_player}, room=sid
    )
    socketio.emit(
        "connection_status", f"在线人数:{len(game.players)}", room=game.players
    )


@socketio.on("restart_game")
def handle_restart_game():
    game = players.get(request.sid)
    if not game:
        return

    game.board = [[0] * BOARD_SIZE for _ in range(BOARD_SIZE)]
    game.current_player = 1
    game.game_over = False

    socketio.emit(
        "game_start",
        {"board": game.board, "turn": game.current_player},
        room=game.players,
    )


@socketio.on("make_move")
def handle_make_move(data):
    game = players.get(request.sid)
    if not game or game.game_over:
        return

    result = game.make_move(data["x"], data["y"])
    if result == "win":
        socketio.emit(
            "update_board",
            {"board": game.board, "turn": game.current_player},
            room=game.players,
        )
        socketio.emit(
            "game_over",
            {
                "winner": game.current_player,
                "line_begin": game.winbegin,
                "line_end": game.winend,
            },
            room=game.players,
        )
    elif result:
        socketio.emit(
            "update_board",
            {"board": game.board, "turn": game.current_player},
            room=game.players,
        )


@socketio.on("disconnect")
def handle_disconnect():
    sid = request.sid
    game = players.get(sid)
    if game:
        game.del_player(sid)
        if len(game.players) > 0:
            socketio.emit("player_left", room=game.players[0])
        if len(game.players) == 0:
            print(f"Game {id(game)} deleted")
            del games[id(game)]
        socketio.emit(
            "connection_status", f"在线人数:{len(game.players)}", room=game.players
        )


if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
