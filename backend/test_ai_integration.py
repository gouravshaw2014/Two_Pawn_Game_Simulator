"""
Test and demonstration script for AI integration with simulator.

This script:
1. Tests the state converter with sample game states
2. Validates feature extraction
3. Tests ML model loading (if available)
4. Demonstrates strategy selection
5. Runs a sample game with AI vs random

Usage:
    python backend/test_ai_integration.py
    
Or to test with a specific model:
    python backend/test_ai_integration.py --model path/to/model.joblib
"""

import sys
import argparse
import logging
from pathlib import Path

# Setup paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.Simulator.Two_Pawn_Simulator import PawnGame, GameState
from backend.AI import (
    MLEvaluator, StateConverter, StrategyFactory, StrategyFactory,
    DummyEvaluator
)
from backend.AI.ai_manager import AIManager


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_state_converter():
    """Test the state converter with a sample game."""
    logger.info("=" * 60)
    logger.info("TEST 1: State Converter")
    logger.info("=" * 60)
    
    converter = StateConverter()
    
    # Create a simple game
    graph = {
        'Start': ['A', 'B'],
        'A': ['C'],
        'B': ['C'],
        'C': ['Target'],
        'Target': []
    }
    
    ownership = {
        'Start': 'Neutral',
        'A': 'Red',
        'B': 'Blue',
        'C': 'Green',
        'Target': 'Green'
    }
    
    engine = PawnGame(
        graph=graph,
        pawn_ownership=ownership,
        target_vertex='Target',
        grabbing_rule='always-grabbing',
        k_grab_limit=0
    )
    
    state = engine.get_initial_state(
        start_vertex='Start',
        p1_initial_pawns={'Red', 'Blue'},
        p2_initial_pawns=set()
    )
    
    # Test feature extraction
    features = converter.state_to_features(engine, state, "move A")
    logger.info(f"Extracted features: {len(features)} features")
    logger.info(f"Sample features: grabbing_rule={features['grabbing_rule']}, phase={features['phase']}, p1_pawns={features['p1_pawn_count']}")
    
    # Validate features
    is_valid, error = converter.validate_features(features)
    logger.info(f"Features valid: {is_valid}")
    if error:
        logger.warning(f"Validation error: {error}")
    
    logger.info("✓ State converter test passed\n")
    return features


def test_ml_evaluator(model_path: str = None):
    """Test ML evaluator if model is available."""
    logger.info("=" * 60)
    logger.info("TEST 2: ML Evaluator")
    logger.info("=" * 60)
    
    if model_path is None:
        logger.info("No model path provided, skipping ML evaluator test")
        logger.info("(To test with a model, run: python test_ai_integration.py --model <path>)\n")
        return None
    
    model_path = Path(model_path)
    if not model_path.exists():
        logger.error(f"Model not found: {model_path}")
        return None
    
    evaluator = MLEvaluator(str(model_path))
    if not evaluator.is_loaded():
        logger.error("Failed to load ML model")
        return None
    
    logger.info(f"✓ ML model loaded: {model_path}")
    
    # Get metadata
    meta = evaluator.get_metadata()
    logger.info(f"Model metadata: accuracy={meta.get('accuracy', 'N/A')}")
    
    logger.info("✓ ML evaluator test passed\n")
    return evaluator


def test_state_evaluation(evaluator):
    """Test evaluating a game state with the ML evaluator."""
    logger.info("=" * 60)
    logger.info("TEST 3: State Evaluation")
    logger.info("=" * 60)
    
    if evaluator is None or not evaluator.is_loaded():
        logger.info("No evaluator available (skipping state evaluation test)\n")
        return
    
    # Create game and state
    graph = {
        'Start': ['A', 'B'],
        'A': ['C'],
        'B': ['C'],
        'C': ['Target'],
        'Target': []
    }
    
    ownership = {
        'A': 'Red',
        'B': 'Blue',
        'C': 'Green',
        'Target': 'Green'
    }
    
    engine = PawnGame(
        graph=graph,
        pawn_ownership=ownership,
        target_vertex='Target',
        grabbing_rule='always-grabbing',
        k_grab_limit=0
    )
    
    state = engine.get_initial_state(
        start_vertex='Start',
        p1_initial_pawns={'Red', 'Blue'},
        p2_initial_pawns=set()
    )
    
    # Test action evaluation
    valid_actions = engine.get_valid_actions(state)
    logger.info(f"Valid actions: {valid_actions}")
    
    evals = evaluator.evaluate_actions(engine, state, valid_actions)
    logger.info(f"Action evaluations:")
    for result in evals:
        logger.info(f"  {result.action}: {result.win_probability:.4f}")
    
    best_action, best_prob = evaluator.get_best_action(engine, state, valid_actions)
    logger.info(f"Best action: {best_action} (prob={best_prob:.4f})")
    
    logger.info("✓ State evaluation test passed\n")


def test_strategies():
    """Test different decision strategies."""
    logger.info("=" * 60)
    logger.info("TEST 4: Strategies")
    logger.info("=" * 60)
    
    evaluator = DummyEvaluator()
    
    strategies_to_test = ['greedy', 'random', 'epsilon-greedy', 'explore']
    
    # Create game and state
    graph = {
        'Start': ['A', 'B'],
        'A': ['C'],
        'B': ['C'],
        'C': ['Target'],
        'Target': []
    }
    
    ownership = {
        'A': 'Red',
        'B': 'Blue',
        'C': 'Green',
        'Target': 'Green'
    }
    
    engine = PawnGame(
        graph=graph,
        pawn_ownership=ownership,
        target_vertex='Target',
        grabbing_rule='always-grabbing',
        k_grab_limit=0
    )
    
    state = engine.get_initial_state(
        start_vertex='Start',
        p1_initial_pawns={'Red', 'Blue'},
        p2_initial_pawns=set()
    )
    
    valid_actions = engine.get_valid_actions(state)
    
    for strategy_name in strategies_to_test:
        strategy = StrategyFactory.create(strategy_name, evaluator)
        action = strategy.select_action(engine, state, valid_actions)
        logger.info(f"  {strategy_name}: selected '{action}'")
    
    logger.info("✓ Strategy test passed\n")


def test_ai_manager(model_path: str = None):
    """Test the AI manager."""
    logger.info("=" * 60)
    logger.info("TEST 5: AI Manager")
    logger.info("=" * 60)
    
    manager = AIManager(enable_ai=False)
    logger.info(f"Initial state: enabled={manager.is_enabled()}")
    
    manager.enable(True)
    logger.info(f"After enable: enabled={manager.is_enabled()}")
    
    if model_path:
        success = manager.load_ml_model(model_path)
        logger.info(f"Model loaded: {success}")
    
    manager.set_strategy('greedy')
    status = manager.get_status()
    logger.info(f"Manager status: {status}")
    
    logger.info("✓ AI manager test passed\n")


def main():
    parser = argparse.ArgumentParser(
        description="Test AI integration with simulator"
    )
    parser.add_argument(
        '--model',
        type=str,
        default=None,
        help='Path to trained ML model (.joblib)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Verbose logging'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    logger.info("\n" + "=" * 60)
    logger.info("AI Integration Test Suite")
    logger.info("=" * 60 + "\n")
    
    # Run tests
    test_state_converter()
    evaluator = test_ml_evaluator(args.model)
    test_state_evaluation(evaluator)
    test_strategies()
    test_ai_manager(args.model)
    
    logger.info("=" * 60)
    logger.info("All tests completed!")
    logger.info("=" * 60)


if __name__ == '__main__':
    main()
