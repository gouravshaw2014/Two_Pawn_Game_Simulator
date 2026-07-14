"""
Abstract base classes for game state evaluators (ML, RL, heuristics, etc.)
Provides a common interface for move evaluation in the pawn game.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass


@dataclass
class EvaluationResult:
    """Result of evaluating a game state or move."""
    action: str
    win_probability: float  # Probability that current player wins from this action
    confidence: float = 1.0  # Confidence in the evaluation (0-1)
    explanation: Optional[str] = None  # Optional explanation


class Evaluator(ABC):
    """
    Abstract base class for game state evaluators.
    
    An evaluator can assess the quality of moves or game states.
    It returns win probabilities which guide move selection.
    """

    @abstractmethod
    def is_loaded(self) -> bool:
        """Check if evaluator is ready to use (e.g., model loaded)."""
        pass

    @abstractmethod
    def evaluate_actions(
        self,
        game_engine: Any,
        current_state: Any,
        valid_actions: List[str]
    ) -> List[EvaluationResult]:
        """
        Evaluate all valid actions from current state.
        
        For each action, simulate it and evaluate the resulting state.
        Returns actions ranked by win probability.
        
        Args:
            game_engine: PawnGame instance
            current_state: Current GameState
            valid_actions: List of valid action strings
            
        Returns:
            List of EvaluationResult, sorted by win_probability (descending)
        """
        pass

    @abstractmethod
    def evaluate_state(
        self,
        game_engine: Any,
        game_state: Any,
        game_config: Dict[str, Any]
    ) -> float:
        """
        Evaluate a single game state/configuration.
        
        Args:
            game_engine: PawnGame instance
            game_state: Current GameState
            game_config: Dict with grabbing_rule, ownership_mechanism, etc.
            
        Returns:
            Win probability (0-1) for current player
        """
        pass

    @abstractmethod
    def get_best_action(
        self,
        game_engine: Any,
        current_state: Any,
        valid_actions: List[str],
        temperature: float = 1.0
    ) -> Tuple[str, float]:
        """
        Select the best action based on evaluations.
        
        Args:
            game_engine: PawnGame instance
            current_state: Current GameState
            valid_actions: List of valid actions
            temperature: Softmax temperature for exploration (1.0 = greedy)
                        Higher values = more exploration
            
        Returns:
            Tuple of (best_action, win_probability)
        """
        pass


class DummyEvaluator(Evaluator):
    """
    Placeholder evaluator for when no AI is available.
    Returns equal scores for all actions.
    """

    def is_loaded(self) -> bool:
        return True

    def evaluate_actions(
        self,
        game_engine: Any,
        current_state: Any,
        valid_actions: List[str]
    ) -> List[EvaluationResult]:
        """All actions equally valuable."""
        return [
            EvaluationResult(action=action, win_probability=0.5)
            for action in valid_actions
        ]

    def evaluate_state(
        self,
        game_engine: Any,
        game_state: Any,
        game_config: Dict[str, Any]
    ) -> float:
        """No information - neutral evaluation."""
        return 0.5

    def get_best_action(
        self,
        game_engine: Any,
        current_state: Any,
        valid_actions: List[str],
        temperature: float = 1.0
    ) -> Tuple[str, float]:
        """Return first action."""
        return (valid_actions[0], 0.5) if valid_actions else ("", 0.5)
