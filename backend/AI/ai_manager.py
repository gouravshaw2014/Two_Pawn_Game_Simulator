"""
AI Manager: Central configuration and management of AI evaluators and strategies.
Provides a single interface to enable/disable AI, switch models, etc.
"""

import logging
from typing import Optional, Dict, Any
from pathlib import Path

from .evaluator import Evaluator, DummyEvaluator
from .ml_evaluator import MLEvaluator
from .strategy import GameStrategy, StrategyFactory


logger = logging.getLogger(__name__)


class AIManager:
    """
    Centralized AI management for the game simulator.
    Handles model loading, strategy selection, and configuration.
    """

    def __init__(self, enable_ai: bool = True):
        """
        Initialize AI manager.
        
        Args:
            enable_ai: Whether AI is enabled. If False, uses DummyEvaluator.
        """
        self.enabled = enable_ai
        self.evaluator: Evaluator = DummyEvaluator() if not enable_ai else DummyEvaluator()
        self.strategy: GameStrategy = StrategyFactory.create('random')
        self.config: Dict[str, Any] = {}

    def enable(self, enabled: bool = True) -> None:
        """Enable or disable AI."""
        self.enabled = enabled
        if not enabled and not isinstance(self.evaluator, DummyEvaluator):
            logger.info("AI disabled, using dummy evaluator")
            self.evaluator = DummyEvaluator()

    def is_enabled(self) -> bool:
        """Check if AI is enabled."""
        return self.enabled

    def load_ml_model(self, model_path: str) -> bool:
        """
        Load an ML model.
        
        Args:
            model_path: Path to .joblib model file
            
        Returns:
            True if loaded successfully
        """
        model_path = Path(model_path)
        
        if not model_path.exists():
            logger.error(f"Model not found: {model_path}")
            return False
        
        try:
            evaluator = MLEvaluator(str(model_path))
            if evaluator.is_loaded():
                self.evaluator = evaluator
                self.enabled = True
                logger.info(f"Loaded ML model: {model_path}")
                return True
            else:
                logger.error(f"Failed to load ML model: {model_path}")
                return False
        except Exception as e:
            logger.error(f"Error loading ML model: {e}")
            return False

    def set_strategy(
        self,
        strategy_type: str,
        **kwargs
    ) -> GameStrategy:
        """
        Set the decision strategy.
        
        Args:
            strategy_type: One of 'greedy', 'explore', 'epsilon-greedy', 'random'
            **kwargs: Additional parameters for the strategy
            
        Returns:
            The created strategy
        """
        self.strategy = StrategyFactory.create(strategy_type, self.evaluator, **kwargs)
        self.config['strategy'] = strategy_type
        self.config['strategy_params'] = kwargs
        logger.info(f"Strategy set to: {strategy_type} with params {kwargs}")
        return self.strategy

    def get_strategy(self) -> GameStrategy:
        """Get the current strategy."""
        return self.strategy

    def get_evaluator(self) -> Evaluator:
        """Get the current evaluator."""
        return self.evaluator

    def select_action(
        self,
        game_engine: Any,
        current_state: Any,
        valid_actions: list
    ) -> str:
        """
        Select an action using the current strategy.
        
        Args:
            game_engine: PawnGame instance
            current_state: Current GameState
            valid_actions: List of valid actions
            
        Returns:
            Selected action
        """
        if not self.enabled:
            return valid_actions[0] if valid_actions else ""
        
        try:
            return self.strategy.select_action(game_engine, current_state, valid_actions)
        except Exception as e:
            logger.error(f"Error selecting action: {e}")
            return valid_actions[0] if valid_actions else ""

    def evaluate_actions(
        self,
        game_engine: Any,
        current_state: Any,
        valid_actions: list
    ):
        """
        Evaluate all valid actions.
        
        Returns:
            List of EvaluationResult
        """
        return self.evaluator.evaluate_actions(game_engine, current_state, valid_actions)

    def get_status(self) -> Dict[str, Any]:
        """Get current AI status and configuration."""
        return {
            "enabled": self.enabled,
            "evaluator_type": type(self.evaluator).__name__,
            "strategy_type": type(self.strategy).__name__,
            "model_path": getattr(self.evaluator, 'model_path', None),
            "config": self.config,
        }


# Global AI manager instance
_global_ai = AIManager(enable_ai=False)  # Disabled by default


def get_ai_manager() -> AIManager:
    """Get the global AI manager instance."""
    return _global_ai


def reset_ai_manager() -> None:
    """Reset AI manager to default state."""
    global _global_ai
    _global_ai = AIManager(enable_ai=False)
