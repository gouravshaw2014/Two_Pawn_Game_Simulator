from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import base64
from io import BytesIO
import matplotlib.pyplot as plt
import logging
from typing import Optional, List, Dict, Any
from pathlib import Path

# must be first import to override backend BEFORE pyplot loads
from backend.Simulator import matplotlib_patch

from backend.Simulator.Two_Pawn_Simulator import *
from backend.Simulator.test_networkx import draw_game_state

# Import AI framework
try:
    from backend.AI import get_ai_manager, MLEvaluator, StrategyFactory
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False
    get_ai_manager = None

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow your React app
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

engine = None
current_state = None

# AI Manager instance
ai_manager = get_ai_manager() if AI_AVAILABLE else None

class InitRequest(BaseModel):
    rules: dict
    initial: dict

class ActionRequest(BaseModel):
    action: str

# AI-related models
class AIInitRequest(BaseModel):
    model_path: Optional[str] = None
    strategy: str = "greedy"
    enable: bool = True

class AISuggestionRequest(BaseModel):
    game_state: Optional[dict] = None  # Use current if not provided
    valid_actions: Optional[List[str]] = None  # Use engine.get_valid_actions if not provided

class AIStrategyRequest(BaseModel):
    strategy: str
    temperature: Optional[float] = None
    epsilon: Optional[float] = None

class AIEnableRequest(BaseModel):
    enabled: bool

class AIEvaluationResponse(BaseModel):
    action: str
    win_probability: float
    confidence: float = 1.0

class AISuggestionResponse(BaseModel):
    action: str
    win_probability: float
    evaluations: List[AIEvaluationResponse]  # All actions ranked

class AIStatusResponse(BaseModel):
    enabled: bool
    available: bool
    evaluator_type: str
    strategy_type: str
    model_path: Optional[str]
    has_model: bool

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


# ============================================================================
# AI ENDPOINTS
# ============================================================================

@app.get("/ai/status")
def get_ai_status() -> AIStatusResponse:
    """
    Get current AI configuration and status.
    
    Returns:
        AI status including availability, model info, and strategy
    """
    if not AI_AVAILABLE or not ai_manager:
        return AIStatusResponse(
            enabled=False,
            available=False,
            evaluator_type="None",
            strategy_type="None",
            model_path=None,
            has_model=False
        )
    
    status = ai_manager.get_status()
    return AIStatusResponse(
        enabled=status['enabled'],
        available=True,
        evaluator_type=status['evaluator_type'],
        strategy_type=status['strategy_type'],
        model_path=status['model_path'],
        has_model=status['model_path'] is not None
    )


@app.post("/ai/init")
def initialize_ai(req: AIInitRequest):
    """
    Initialize AI with model and strategy.
    
    Args:
        model_path: Path to trained ML model (.joblib)
        strategy: Strategy to use (greedy, explore, epsilon-greedy, random)
        enable: Whether to enable AI
        
    Returns:
        Updated AI status
    """
    if not AI_AVAILABLE or not ai_manager:
        raise HTTPException(status_code=500, detail="AI framework not available")
    
    try:
        # Load model if provided
        if req.model_path:
            model_path = Path(req.model_path)
            if not model_path.exists():
                raise HTTPException(status_code=404, detail=f"Model not found: {model_path}")
            
            success = ai_manager.load_ml_model(str(model_path))
            if not success:
                raise HTTPException(status_code=400, detail="Failed to load ML model")
            logger.info(f"Loaded ML model: {model_path}")
        
        # Set strategy
        ai_manager.set_strategy(req.strategy)
        logger.info(f"Set strategy: {req.strategy}")
        
        # Enable/disable
        ai_manager.enable(req.enable)
        logger.info(f"AI enabled: {req.enable}")
        
        status = ai_manager.get_status()
        return AIStatusResponse(
            enabled=status['enabled'],
            available=True,
            evaluator_type=status['evaluator_type'],
            strategy_type=status['strategy_type'],
            model_path=status['model_path'],
            has_model=status['model_path'] is not None
        )
    
    except Exception as e:
        logger.error(f"Error initializing AI: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/ai/strategy")
def set_strategy(req: AIStrategyRequest):
    """
    Change the AI decision strategy.
    
    Args:
        req: Request body containing strategy and optional parameters
        
    Returns:
        Updated AI status
    """
    if not AI_AVAILABLE or not ai_manager:
        raise HTTPException(status_code=500, detail="AI framework not available")
    
    try:
        kwargs = {}
        if req.temperature is not None:
            kwargs['temperature'] = req.temperature
        if req.epsilon is not None:
            kwargs['epsilon'] = req.epsilon
        
        ai_manager.set_strategy(req.strategy, **kwargs)
        logger.info(f"Strategy set to: {req.strategy} with params {kwargs}")
        
        status = ai_manager.get_status()
        return {
            "success": True,
            "strategy": req.strategy,
            "config": status['config']
        }
    
    except Exception as e:
        logger.error(f"Error setting strategy: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/ai/enable")
def set_ai_enabled(req: AIEnableRequest):
    """
    Enable or disable AI.
    
    Args:
        req: Request body containing enabled flag
        
    Returns:
        Updated AI status
    """
    if not AI_AVAILABLE or not ai_manager:
        raise HTTPException(status_code=500, detail="AI framework not available")
    
    ai_manager.enable(req.enabled)
    logger.info(f"AI enabled: {req.enabled}")
    
    status = ai_manager.get_status()
    return {"success": True, "enabled": status['enabled']}


@app.post("/ai/suggest")
def suggest_move(req: AISuggestionRequest) -> AISuggestionResponse:
    """
    Get AI suggestion for the next move.
    
    Args:
        game_state: Optional game state (uses current if not provided)
        valid_actions: Optional valid actions (gets from engine if not provided)
        
    Returns:
        Best suggested action with win probability and all action evaluations
    """
    if not AI_AVAILABLE or not ai_manager or not ai_manager.is_enabled():
        raise HTTPException(status_code=403, detail="AI not enabled")
    
    if engine is None or current_state is None:
        raise HTTPException(status_code=400, detail="Game not started")
    
    try:
        # Get valid actions
        valid_actions = req.valid_actions if req.valid_actions else engine.get_valid_actions(current_state)
        
        if not valid_actions:
            raise HTTPException(status_code=400, detail="No valid actions available")
        
        # Get best action
        best_action, best_prob = ai_manager.evaluator.get_best_action(
            engine, current_state, valid_actions
        )
        
        # Get all evaluations for reference
        all_evals = ai_manager.evaluator.evaluate_actions(
            engine, current_state, valid_actions
        )
        
        evaluations = [
            AIEvaluationResponse(
                action=e.action,
                win_probability=e.win_probability,
                confidence=e.confidence
            )
            for e in all_evals
        ]
        
        logger.info(f"AI suggested: {best_action} (prob={best_prob:.4f})")
        
        return AISuggestionResponse(
            action=best_action,
            win_probability=best_prob,
            evaluations=evaluations
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error suggesting move: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ai/evaluate")
def evaluate_all_actions(req: AISuggestionRequest) -> Dict[str, Any]:
    """
    Evaluate all valid actions with win probabilities.
    
    Args:
        game_state: Optional game state (uses current if not provided)
        valid_actions: Optional valid actions (gets from engine if not provided)
        
    Returns:
        List of all actions with their evaluated win probabilities
    """
    if not AI_AVAILABLE or not ai_manager or not ai_manager.is_enabled():
        raise HTTPException(status_code=403, detail="AI not enabled")
    
    if engine is None or current_state is None:
        raise HTTPException(status_code=400, detail="Game not started")
    
    try:
        # Get valid actions
        valid_actions = req.valid_actions if req.valid_actions else engine.get_valid_actions(current_state)
        
        if not valid_actions:
            raise HTTPException(status_code=400, detail="No valid actions available")
        
        # Evaluate all
        evals = ai_manager.evaluator.evaluate_actions(
            engine, current_state, valid_actions
        )
        
        evaluations = [
            {
                "action": e.action,
                "win_probability": e.win_probability,
                "confidence": e.confidence,
                "rank": i + 1
            }
            for i, e in enumerate(evals)
        ]
        
        logger.info(f"Evaluated {len(evaluations)} actions")
        
        return {
            "total_actions": len(evaluations),
            "evaluations": evaluations,
            "best_action": evaluations[0] if evaluations else None
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error evaluating actions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/ai/models/available")
def get_available_models() -> Dict[str, Any]:
    """
    Get list of available models in the ML models directory.
    
    Returns:
        List of available trained models
    """
    try:
        models_dir = Path(__file__).parent.parent / "ML" / "models"
        if not models_dir.exists():
            return {"models": [], "message": "Models directory not found"}
        
        models = []
        for model_file in models_dir.rglob("*.joblib"):
            models.append({
                "path": str(model_file),
                "name": model_file.parent.name,
                "filename": model_file.name
            })
        
        return {
            "models": sorted(models, key=lambda x: x['path']),
            "count": len(models)
        }
    
    except Exception as e:
        logger.error(f"Error listing models: {e}")
        return {"models": [], "error": str(e)}


@app.get("/ai/strategies/available")
def get_available_strategies() -> Dict[str, Any]:
    """
    Get list of available decision strategies.
    
    Returns:
        List of strategy names and descriptions
    """
    strategies = {
        "greedy": {
            "name": "Greedy",
            "description": "Always select the action with highest win probability",
            "parameters": []
        },
        "explore": {
            "name": "Exploration",
            "description": "Balance exploration and exploitation with temperature scaling",
            "parameters": [
                {
                    "name": "temperature",
                    "type": "float",
                    "default": 1.5,
                    "description": "Temperature for softmax (1.0=greedy, >1.0=explore)"
                }
            ]
        },
        "epsilon-greedy": {
            "name": "Epsilon-Greedy",
            "description": "With probability epsilon, pick random; otherwise pick best",
            "parameters": [
                {
                    "name": "epsilon",
                    "type": "float",
                    "default": 0.1,
                    "description": "Probability of random action (0-1)"
                }
            ]
        },
        "random": {
            "name": "Random",
            "description": "Pick random action (baseline, no AI used)",
            "parameters": []
        }
    }
    
    return strategies
