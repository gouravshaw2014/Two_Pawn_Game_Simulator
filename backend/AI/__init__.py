"""
AI module: Pluggable game evaluation and decision-making.

Supports:
- ML-based evaluation (RandomForest model)
- Multiple decision strategies (greedy, exploration, epsilon-greedy, random)
- Easy integration with simulator
- Placeholder for future RL models

Example usage:
    from backend.AI import MLEvaluator, StrategyFactory
    
    # Load model
    evaluator = MLEvaluator(model_path="path/to/model.joblib")
    
    # Create strategy
    strategy = StrategyFactory.create('greedy', evaluator)
    
    # Use in game loop
    best_action = strategy.select_action(game_engine, state, valid_actions)

Or use the AI Manager for centralized configuration:
    from backend.AI.ai_manager import get_ai_manager
    
    ai = get_ai_manager()
    ai.load_ml_model("model.joblib")
    ai.set_strategy('greedy')
    best_action = ai.select_action(game_engine, state, valid_actions)
"""

from .evaluator import Evaluator, DummyEvaluator, EvaluationResult
from .ml_evaluator import MLEvaluator
from .state_converter import StateConverter
from .strategy import (
    GameStrategy,
    GreedyStrategy,
    ExplorationStrategy,
    EpsilonGreedyStrategy,
    RandomStrategy,
    StrategyFactory,
)
from .ai_manager import AIManager, get_ai_manager, reset_ai_manager

__all__ = [
    # Evaluators
    "Evaluator",
    "DummyEvaluator",
    "MLEvaluator",
    "EvaluationResult",
    # Strategies
    "GameStrategy",
    "GreedyStrategy",
    "ExplorationStrategy",
    "EpsilonGreedyStrategy",
    "RandomStrategy",
    "StrategyFactory",
    # Manager
    "AIManager",
    "get_ai_manager",
    "reset_ai_manager",
    # Utilities
    "StateConverter",
]
