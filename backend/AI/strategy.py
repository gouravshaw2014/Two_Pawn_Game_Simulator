"""
Game-playing strategies that use evaluators to select moves.
Provides different ways to turn evaluations into action decisions.
"""

from typing import Any, List, Optional, Tuple, Callable
import logging
import random

from .evaluator import Evaluator, DummyEvaluator


logger = logging.getLogger(__name__)


class GameStrategy:
    """
    Base class for game strategies using evaluators.
    Defines the interface for selecting moves in a game.
    """

    def __init__(self, evaluator: Optional[Evaluator] = None):
        """
        Initialize strategy with an evaluator.
        
        Args:
            evaluator: Evaluator instance. If None, uses DummyEvaluator.
        """
        self.evaluator = evaluator or DummyEvaluator()

    def select_action(
        self,
        game_engine: Any,
        current_state: Any,
        valid_actions: List[str]
    ) -> str:
        """
        Select an action using the strategy.
        
        Args:
            game_engine: PawnGame instance
            current_state: Current GameState
            valid_actions: List of valid actions to choose from
            
        Returns:
            Selected action string
        """
        if not valid_actions:
            raise ValueError("No valid actions available")
        
        action, _ = self.evaluator.get_best_action(
            game_engine, current_state, valid_actions
        )
        return action


class GreedyStrategy(GameStrategy):
    """
    Greedy strategy: always select the action with highest win probability.
    No exploration.
    """

    def select_action(
        self,
        game_engine: Any,
        current_state: Any,
        valid_actions: List[str]
    ) -> str:
        """Select the action with highest evaluation."""
        if not valid_actions:
            raise ValueError("No valid actions available")
        
        evals = self.evaluator.evaluate_actions(
            game_engine, current_state, valid_actions
        )
        
        if evals:
            return evals[0].action  # Highest evaluation first
        return valid_actions[0]


class ExplorationStrategy(GameStrategy):
    """
    Exploration strategy: use temperature scaling for more exploration.
    Higher temperature = more randomness.
    """

    def __init__(self, evaluator: Optional[Evaluator] = None, temperature: float = 1.5):
        """
        Initialize with temperature parameter.
        
        Args:
            evaluator: Evaluator instance
            temperature: Temperature for softmax scaling (1.0 = greedy, >1 = explore)
        """
        super().__init__(evaluator)
        self.temperature = temperature

    def select_action(
        self,
        game_engine: Any,
        current_state: Any,
        valid_actions: List[str]
    ) -> str:
        """Select action using temperature-scaled softmax."""
        if not valid_actions:
            raise ValueError("No valid actions available")
        
        action, _ = self.evaluator.get_best_action(
            game_engine, current_state, valid_actions, temperature=self.temperature
        )
        return action


class EpsilonGreedyStrategy(GameStrategy):
    """
    Epsilon-greedy strategy: with probability epsilon, pick random action,
    otherwise pick best action.
    """

    def __init__(self, evaluator: Optional[Evaluator] = None, epsilon: float = 0.1):
        """
        Initialize with epsilon parameter.
        
        Args:
            evaluator: Evaluator instance
            epsilon: Probability of random action (0-1)
        """
        super().__init__(evaluator)
        self.epsilon = max(0.0, min(1.0, epsilon))

    def select_action(
        self,
        game_engine: Any,
        current_state: Any,
        valid_actions: List[str]
    ) -> str:
        """Select random action with probability epsilon, else greedy."""
        if not valid_actions:
            raise ValueError("No valid actions available")
        
        if random.random() < self.epsilon:
            return random.choice(valid_actions)
        
        evals = self.evaluator.evaluate_actions(
            game_engine, current_state, valid_actions
        )
        if evals:
            return evals[0].action
        return valid_actions[0]


class RandomStrategy(GameStrategy):
    """
    Random strategy: always pick a random valid action.
    Useful for baseline and exploration.
    """

    def select_action(
        self,
        game_engine: Any,
        current_state: Any,
        valid_actions: List[str]
    ) -> str:
        """Return random valid action."""
        if not valid_actions:
            raise ValueError("No valid actions available")
        return random.choice(valid_actions)


class StrategyFactory:
    """
    Factory for creating game strategies.
    Simplifies initialization with common presets.
    """

    @staticmethod
    def create(
        strategy_type: str,
        evaluator: Optional[Evaluator] = None,
        **kwargs
    ) -> GameStrategy:
        """
        Create a strategy by name.
        
        Args:
            strategy_type: One of 'greedy', 'explore', 'epsilon-greedy', 'random'
            evaluator: Evaluator instance
            **kwargs: Additional parameters (e.g., temperature, epsilon)
            
        Returns:
            GameStrategy instance
        """
        strategy_type = strategy_type.lower()
        
        if strategy_type == 'greedy':
            return GreedyStrategy(evaluator)
        elif strategy_type == 'explore':
            temperature = kwargs.get('temperature', 1.5)
            return ExplorationStrategy(evaluator, temperature)
        elif strategy_type == 'epsilon-greedy':
            epsilon = kwargs.get('epsilon', 0.1)
            return EpsilonGreedyStrategy(evaluator, epsilon)
        elif strategy_type == 'random':
            return RandomStrategy(evaluator)
        else:
            logger.warning(f"Unknown strategy '{strategy_type}', using greedy")
            return GreedyStrategy(evaluator)

    @staticmethod
    def list_strategies() -> List[str]:
        """List available strategies."""
        return ['greedy', 'explore', 'epsilon-greedy', 'random']
