"""
ML-based game state evaluator using trained RandomForest model.
Converts game state to features and gets win probability predictions.
"""

import os
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import logging

from .evaluator import Evaluator, EvaluationResult
from .state_converter import StateConverter


logger = logging.getLogger(__name__)


class MLEvaluator(Evaluator):
    """
    Evaluates game states using a trained ML model (RandomForest).
    
    Usage:
        evaluator = MLEvaluator(model_path="path/to/model.joblib")
        if evaluator.is_loaded():
            results = evaluator.evaluate_actions(engine, state, valid_actions)
            best_action, prob = evaluator.get_best_action(engine, state, valid_actions)
    """

    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize ML evaluator.
        
        Args:
            model_path: Path to trained .joblib model file.
                       If None, evaluator starts in unloaded state.
        """
        self.model_path = model_path
        self.model = None
        self.converter = StateConverter()
        self.is_fitted = False
        
        if model_path:
            self.load_model(model_path)

    def load_model(self, model_path: str) -> bool:
        """
        Load a trained ML model from disk.
        
        Args:
            model_path: Path to .joblib file
            
        Returns:
            True if loaded successfully, False otherwise
        """
        try:
            import joblib
        except ImportError:
            logger.error("joblib not installed. Install with: pip install joblib")
            return False
        
        model_path = Path(model_path)
        if not model_path.exists():
            logger.error(f"Model file not found: {model_path}")
            return False
        
        try:
            self.model = joblib.load(str(model_path))
            self.model_path = str(model_path)
            self.is_fitted = True
            logger.info(f"Loaded ML model from: {model_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return False

    def is_loaded(self) -> bool:
        """Check if model is loaded and ready."""
        return self.is_fitted and self.model is not None

    def evaluate_state(
        self,
        game_engine: Any,
        game_state: Any,
        game_config: Dict[str, Any],
        action: Optional[str] = None
    ) -> float:
        """
        Evaluate win probability for a game state.
        
        If action is provided, it's included in features as chosen_action.
        
        Args:
            game_engine: PawnGame instance
            game_state: Current GameState
            game_config: Dict with game configuration
            action: Optional action to include in features
            
        Returns:
            Win probability (0-1) for current player
        """
        if not self.is_loaded():
            logger.warning("Model not loaded, returning neutral evaluation (0.5)")
            return 0.5
        
        try:
            # Convert state to features
            action_str = action or "move start"  # Default action if not specified
            features = self.converter.state_to_features(
                game_engine, game_state, action_str, include_outcome=False
            )
            
            # Validate features
            is_valid, error = self.converter.validate_features(features)
            if not is_valid:
                logger.warning(f"Feature validation failed: {error}")
                return 0.5
            
            # Convert to model input format (DataFrame-like)
            try:
                import pandas as pd
                df = pd.DataFrame([features])
            except ImportError:
                logger.error("pandas required for ML evaluation")
                return 0.5
            
            # Get prediction
            win_prob = float(self.model.predict_proba(df)[0, 1])
            return min(max(win_prob, 0.0), 1.0)  # Clamp to [0, 1]
            
        except Exception as e:
            logger.error(f"Error evaluating state: {e}")
            return 0.5

    def evaluate_actions(
        self,
        game_engine: Any,
        current_state: Any,
        valid_actions: List[str]
    ) -> List[EvaluationResult]:
        """
        Evaluate all valid actions by predicting win probability for each.
        
        For each action:
        1. Create features with chosen_action = action
        2. Predict win probability
        3. Return ranked by probability (highest first)
        
        Args:
            game_engine: PawnGame instance
            current_state: Current GameState
            valid_actions: List of valid action strings
            
        Returns:
            List of EvaluationResult sorted by win_probability (descending)
        """
        if not self.is_loaded():
            logger.warning("Model not loaded")
            return [
                EvaluationResult(action=action, win_probability=0.5)
                for action in valid_actions
            ]
        
        results = []
        
        for action in valid_actions:
            try:
                win_prob = self.evaluate_state(
                    game_engine, current_state, {}, action=action
                )
                results.append(
                    EvaluationResult(
                        action=action,
                        win_probability=win_prob,
                        confidence=1.0
                    )
                )
            except Exception as e:
                logger.error(f"Error evaluating action '{action}': {e}")
                results.append(
                    EvaluationResult(action=action, win_probability=0.5, confidence=0.0)
                )
        
        # Sort by win_probability (highest first)
        results.sort(key=lambda r: r.win_probability, reverse=True)
        return results

    def get_best_action(
        self,
        game_engine: Any,
        current_state: Any,
        valid_actions: List[str],
        temperature: float = 1.0
    ) -> Tuple[str, float]:
        """
        Select best action using temperature-scaled softmax for exploration.
        
        Args:
            game_engine: PawnGame instance
            current_state: Current GameState
            valid_actions: List of valid actions
            temperature: Softmax temperature
                        1.0 = greedy (max probability)
                        > 1.0 = more exploration
                        < 1.0 = more exploitation
            
        Returns:
            Tuple of (best_action, win_probability)
        """
        if not valid_actions:
            return "", 0.5
        
        if not self.is_loaded():
            return valid_actions[0], 0.5
        
        # Evaluate all actions
        evals = self.evaluate_actions(game_engine, current_state, valid_actions)
        
        if temperature == 1.0:
            # Greedy: return best action
            best_eval = evals[0]
            return best_eval.action, best_eval.win_probability
        
        # Temperature-scaled selection
        try:
            import numpy as np
            
            # Get probabilities
            probs = np.array([e.win_probability for e in evals])
            
            # Apply temperature
            scaled_probs = probs ** (1.0 / temperature)
            scaled_probs = scaled_probs / scaled_probs.sum()
            
            # Sample action
            idx = np.random.choice(len(evals), p=scaled_probs)
            selected = evals[idx]
            return selected.action, selected.win_probability
            
        except ImportError:
            logger.warning("numpy not available, using greedy selection")
            best_eval = evals[0]
            return best_eval.action, best_eval.win_probability

    def get_metadata(self) -> Dict[str, Any]:
        """
        Get model metadata if available.
        
        Returns:
            Dictionary with model info
        """
        meta = {
            "type": "MLEvaluator",
            "model_path": str(self.model_path),
            "is_loaded": self.is_loaded(),
        }
        
        # Try to load metadata from .metadata.json if it exists
        if self.model_path:
            metadata_path = Path(str(self.model_path).replace('.joblib', '.metadata.json'))
            if metadata_path.exists():
                try:
                    import json
                    with open(metadata_path) as f:
                        meta.update(json.load(f))
                except Exception as e:
                    logger.warning(f"Could not load metadata: {e}")
        
        return meta
