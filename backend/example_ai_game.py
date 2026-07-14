"""
Example: AI-powered game loop

This script demonstrates how to:
1. Set up simulator with AI
2. Run a game with AI vs random player
3. Display results

Usage:
    python backend/example_ai_game.py

Or with a specific model:
    python backend/example_ai_game.py --ai-model path/to/model.joblib
"""

import sys
import argparse
import random
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.Simulator.Two_Pawn_Simulator import PawnGame, GameState
from backend.AI import StrategyFactory, MLEvaluator, DummyEvaluator
from backend.AI.ai_manager import AIManager


def create_sample_game():
    """Create a sample game configuration."""
    graph = {
        'Start': ['A', 'B'],
        'A': ['C', 'E'],
        'B': ['D', 'E'],
        'C': ['F'],
        'D': ['F'],
        'E': ['F'],
        'F': ['Target'],
        'Target': []
    }
    
    ownership = {
        'A': 'Red',
        'B': 'Blue',
        'C': 'Red',
        'D': 'Blue',
        'E': 'Green',
        'F': 'Green',
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
    
    return engine, state


def print_game_state(state, turn, max_turns=500):
    """Pretty print game state."""
    print(f"\n{'='*60}")
    print(f"Turn {turn}")
    print(f"{'='*60}")
    print(f"P1 Position: {state.p1_pos}")
    print(f"P2 Position: {state.p2_pos}")
    print(f"P1 Pawns: {sorted(list(state.p1_pawns)) if state.p1_pawns else 'None'}")
    print(f"P2 Pawns: {sorted(list(state.p2_pawns)) if state.p2_pawns else 'None'}")
    print(f"Current Player: P{state.current_player}")
    print(f"Phase: {state.phase}")
    if state.message:
        print(f"Message: {state.message}")


def play_game_human_vs_ai(
    ai_model_path=None,
    ai_strategy='greedy',
    human_player=1,
    verbose=True,
    max_turns=500
):
    """
    Play a game: human vs AI or AI vs AI.
    
    Args:
        ai_model_path: Path to ML model (None for random AI)
        ai_strategy: Strategy for AI (greedy, random, epsilon-greedy, explore)
        human_player: Which player is human (1 or 2, or None for AI vs AI)
        verbose: Print game state each turn
        max_turns: Maximum turns before timeout
        
    Returns:
        Dict with game result
    """
    
    # Create game
    engine, state = create_sample_game()
    
    # Setup AI
    if ai_model_path and Path(ai_model_path).exists():
        evaluator = MLEvaluator(ai_model_path)
        print(f"✓ Loaded ML model: {ai_model_path}")
    else:
        evaluator = DummyEvaluator()
        print(f"Using dummy evaluator (no model)")
    
    ai_strategy_obj = StrategyFactory.create(ai_strategy, evaluator)
    print(f"AI Strategy: {ai_strategy}")
    
    # Play game
    turn = 0
    move_history = []
    
    while not engine.is_win(state) and turn < max_turns:
        turn += 1
        if verbose:
            print_game_state(state, turn, max_turns)
        
        valid_actions = engine.get_valid_actions(state)
        
        if not valid_actions:
            print(f"No valid actions for P{state.current_player}")
            break
        
        # Get action
        if human_player == state.current_player:
            print(f"\nP{state.current_player} turn (Human)")
            print(f"Valid actions: {valid_actions}")
            while True:
                try:
                    idx = int(input("Enter action number (or 0 for random): "))
                    if idx == 0:
                        action = random.choice(valid_actions)
                    elif 1 <= idx <= len(valid_actions):
                        action = valid_actions[idx - 1]
                    else:
                        print("Invalid index")
                        continue
                    break
                except ValueError:
                    print("Invalid input")
        else:
            print(f"\nP{state.current_player} turn (AI)")
            
            # Evaluate actions
            if hasattr(evaluator, 'evaluate_actions'):
                evals = evaluator.evaluate_actions(engine, state, valid_actions)
                print(f"Evaluations:")
                for e in evals[:3]:  # Show top 3
                    print(f"  {e.action}: {e.win_probability:.4f}")
            
            action = ai_strategy_obj.select_action(engine, state, valid_actions)
        
        print(f"Action: {action}")
        move_history.append({
            'turn': turn,
            'player': state.current_player,
            'action': action,
            'phase': state.phase
        })
        
        state = engine.apply_action(state, action)
    
    # Game end
    print(f"\n{'='*60}")
    print(f"GAME END - Turn {turn}")
    print(f"{'='*60}")
    
    if engine.is_win(state):
        winner = 1 if engine.is_win(state) else 2
        print(f"✓ P1 WINS!")
    elif turn >= max_turns:
        print(f"✗ TIMEOUT (max {max_turns} turns)")
        winner = 2
    else:
        print(f"✗ P2 WINS!")
        winner = 2
    
    return {
        'winner': winner,
        'turns': turn,
        'moves': move_history,
        'final_state': state
    }


def main():
    parser = argparse.ArgumentParser(description="AI Game Example")
    parser.add_argument(
        '--ai-model',
        type=str,
        default=None,
        help='Path to trained ML model (.joblib)'
    )
    parser.add_argument(
        '--strategy',
        type=str,
        default='greedy',
        choices=['greedy', 'random', 'epsilon-greedy', 'explore'],
        help='AI strategy'
    )
    parser.add_argument(
        '--human',
        type=int,
        default=1,
        choices=[0, 1, 2],
        help='Human player (0=AI vs AI, 1=Human vs AI, 2=AI vs Human)'
    )
    parser.add_argument(
        '--ai-vs-ai',
        action='store_true',
        help='AI vs AI mode'
    )
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Minimal output'
    )
    
    args = parser.parse_args()
    
    human_player = None if args.ai_vs_ai else args.human
    verbose = not args.quiet
    
    print("\n" + "="*60)
    print("Pawn Game - AI Example")
    print("="*60)
    
    if args.ai_model:
        print(f"Model: {args.ai_model}")
    print(f"Strategy: {args.strategy}")
    print(f"Human player: {human_player if human_player else 'AI vs AI'}")
    
    # Play
    result = play_game_human_vs_ai(
        ai_model_path=args.ai_model,
        ai_strategy=args.strategy,
        human_player=human_player,
        verbose=verbose,
        max_turns=500
    )
    
    print(f"\nResult: P{result['winner']} won in {result['turns']} turns")


if __name__ == '__main__':
    main()
