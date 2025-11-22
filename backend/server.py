from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import base64
from io import BytesIO
import matplotlib.pyplot as plt
# must be first import to override backend BEFORE pyplot loads
import Simulator.matplotlib_patch  

from Simulator.Two_Pawn_Simulator import *

from Simulator.test_networkx import draw_game_state

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow your React app
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = None
current_state = None

class InitRequest(BaseModel):
    rules: dict
    initial: dict

class ActionRequest(BaseModel):
    action: str

def state_to_json(state: GameState):
    return {
        "p1_pos": state.p1_pos,
        "p2_pos": state.p2_pos,
        "p1_pawns": list(state.p1_pawns),
        "p2_pawns": list(state.p2_pawns),
        "current_player": state.current_player,
        "phase": state.phase,
        "k_grabs_made": state.k_grabs_made,
        "message": state.message,
    }

def render_state_image():
    fig = draw_game_state(engine.graph, engine.ownership, current_state)
    buf = BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    return base64.b64encode(buf.getvalue()).decode()
    

def state_with_actions():
    return {
        "state": state_to_json(current_state),
        "valid_actions": engine.get_valid_actions(current_state),
        "image": render_state_image()
    }


@app.post("/start")
def start_game(req: InitRequest):
    global engine, current_state
    engine = PawnGame(**req.rules)
    current_state = engine.get_initial_state(**req.initial)
    return state_with_actions()


@app.post("/action")
def play_action(req: ActionRequest):
    global current_state
    current_state = engine.apply_action(current_state, req.action)
    return state_with_actions()
