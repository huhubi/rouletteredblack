from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import random
import threading
import time

app = Flask(__name__)
socketio = SocketIO(app)

game_data = {
    "balance": 100,
    "history": [],
    "current_bet": {"color": None, "amount": 0},
    "running": True,
    "result": None
}

def get_color(number):
    if number == 0:
        return "grün"
    elif number in [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]:
        return "rot"
    else:
        return "schwarz"

def play_game():
    while game_data["running"]:
        time.sleep(10)  
        
        number = random.randint(0, 36)
        color = get_color(number)
        game_data["history"].append((number, color))
        game_data["result"] = {"number": number, "color": color}
        
        if game_data["current_bet"]["amount"] > 0:
            if game_data["current_bet"]["color"] == color:
                if color == "grün":
                    winnings = game_data["current_bet"]["amount"] * 35  
                else:
                    winnings = game_data["current_bet"]["amount"] * 2
                game_data["balance"] += winnings
                result_text = f"Gewonnen! Du erhältst {winnings}€."
            else:
                game_data["balance"] -= game_data["current_bet"]["amount"]
                result_text = f"Verloren. Du verlierst {game_data['current_bet']['amount']}€."
        else:
            result_text = "Kein Einsatz gemacht."
        
        game_data["current_bet"] = {"color": None, "amount": 0}

        total_games = len(game_data["history"])
        red_count = sum(1 for _, color in game_data["history"] if color == "rot")
        black_count = sum(1 for _, color in game_data["history"] if color == "schwarz")
        green_count = sum(1 for _, color in game_data["history"] if color == "grün")
        red_prob = (red_count / total_games) * 100 if total_games > 0 else 0
        black_prob = (black_count / total_games) * 100 if total_games > 0 else 0
        green_prob = (green_count / total_games) * 100 if total_games > 0 else 0

        socketio.emit('game_update', {
            "result": {"number": number, "color": color},
            "balance": game_data["balance"],
            "result_text": result_text,
            "statistics": {
                "total_games": total_games,
                "red_prob": red_prob,
                "black_prob": black_prob,
                "green_prob": green_prob
            }
        })

@app.route('/')
def index():
    return render_template('index.html', balance=game_data["balance"])

@app.route('/place_bet', methods=['POST'])
def place_bet():
    data = request.json
    color = data.get('color')
    amount = data.get('amount')

    if not color or color not in ['rot', 'schwarz', 'grün']:
        return jsonify({"error": "Ungültige Farbe."}), 400
    if amount <= 0 or amount > game_data["balance"]:
        return jsonify({"error": "Ungültiger Betrag."}), 400

    game_data["current_bet"] = {"color": color, "amount": amount}
    return jsonify({"message": f"Einsatz von {amount}€ auf {color.upper()} platziert!"})

@app.route('/reset', methods=['POST'])
def reset_balance():
    game_data["balance"] = 100
    return jsonify({"message": "Guthaben wurde zurückgesetzt!", "balance": game_data["balance"]})

threading.Thread(target=play_game, daemon=True).start()

if __name__ == '__main__':
    socketio.run(app, debug=True)