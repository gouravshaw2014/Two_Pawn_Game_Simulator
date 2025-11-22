# app.py

from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os

# Add repo root to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import your Python modules
from directed_graph_class import create_directed_graph as class_graph
from directed_graph_dict import create_directed_graph as dict_graph
from Simulator.Two_Pawn_Simulator import Simulator as TwoPawnSimulator

app = Flask(__name__)
CORS(app)  # Allow requests from React dev server

# Store current game session (in-memory)
game_session = {
    "graph": None,
    "colors": {},
    "labels": {},
    "simulator": None,
    "game_state": {}
}

@app.route("/api/create_graph", methods=["POST"])
def create_graph():
    """
    Accepts JSON:
    {
        "V": 5,
        "labels": {0: "A", 1: "B", ...},
        "colors": {0: "red", 1: "blue", ...},
        "edges": [[0,1],[1,2],...]
    }
    Returns adjacency matrix, labels, colors.
    """
    data = request.json
    V = data.get("V")
    labels = data.get("labels", {})
    colors = data.get("colors", {})
    edges = data.get("edges", [])

    # You can choose which backend to use: class or dict
    mat, colors, labels = dict_graph(V=V, labels=labels, colors=colors, edges=edges)

    # Save to session
    game_session["graph"] = mat
    game_session["colors"] = colors
    game_session["labels"] = labels

    return jsonify({
        "adjacency_matrix": mat,
        "labels": labels,
        "colors": colors
    })


@app.route("/api/start_game", methods=["POST"])
def start_game():
    """
    Accepts JSON:
    {
        "ownership": "MVPP",
        "rule": "always-grabbing",
        "k_value": 2
    }
    Initializes the simulator.
    """
    data = request.json
    ownership = data.get("ownership", "MVPP")
    rule = data.get("rule", "always-grabbing")
    k_value = data.get("k_value", 2)

    if game_session["graph"] is None:
        return jsonify({"error": "Graph not created yet"}), 400

    # Initialize your Two Pawn Simulator with current graph
    sim = TwoPawnSimulator(
        adjacency_matrix=game_session["graph"],
        labels=game_session["labels"],
        colors=game_session["colors"],
        ownership_model=ownership,
        grabbing_rule=rule,
        k_value=k_value
    )

    game_session["simulator"] = sim
    game_session["game_state"] = sim.get_current_state()  # assumes your class has this

    return jsonify({"game_state": game_session["game_state"]})


@app.route("/api/make_move", methods=["POST"])
def make_move():
    """
    Accepts JSON:
    {
        "player": 1,
        "action": "move A" or "grab Red"
    }
    Returns updated game state.
    """
    data = request.json
    sim = game_session.get("simulator")
    if sim is None:
        return jsonify({"error": "Game not started yet"}), 400

    player = data.get("player")
    action = data.get("action")

    # Apply move in your simulator (assumes method apply_action exists)
    result = sim.apply_action(player, action)
    game_session["game_state"] = sim.get_current_state()
    return jsonify({"result": result, "game_state": game_session["game_state"]})


@app.route("/api/graph_state", methods=["GET"])
def graph_state():
    """
    Returns current graph info: adjacency matrix, labels, colors.
    """
    return jsonify({
        "adjacency_matrix": game_session.get("graph"),
        "labels": game_session.get("labels"),
        "colors": game_session.get("colors")
    })


if __name__ == "__main__":
    app.run(debug=True)
