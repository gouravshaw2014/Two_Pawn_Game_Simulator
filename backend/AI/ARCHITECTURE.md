"""
AI Module Documentation

This document explains the AI integration framework for the Pawn Game Simulator.

## Overview

The AI module provides a pluggable, modular system for game state evaluation and
move selection. It's designed to be:

1. **Switchable**: Easy to enable/disable AI
2. **Extensible**: Supports different evaluator types (ML, RL, heuristics)
3. **Modular**: Each component (evaluator, strategy) is independent
4. **Future-proof**: Built for easy RL integration

## Architecture

```
AI Module
├── evaluator.py          (Base interface + DummyEvaluator)
├── ml_evaluator.py       (ML-based evaluator)
├── state_converter.py    (State → Features)
├── strategy.py           (Decision strategies)
├── ai_manager.py         (Central configuration)
└── __init__.py          (Exports)

RL Module (placeholder for future)
├── __init__.py
└── [future RL implementations]
```

## Usage

### 1. Basic Usage: Load Model and Play

```python
from backend.AI import MLEvaluator, StrategyFactory
from backend.Simulator.Two_Pawn_Simulator import PawnGame

# Load model
evaluator = MLEvaluator(model_path="ML/models/data_iter100000/pawn_outcome_model.joblib")

# Create strategy
strategy = StrategyFactory.create('greedy', evaluator)

# Create game
engine = PawnGame(
    graph={...},
    pawn_ownership={...},
    target_vertex='Target',
    grabbing_rule='always-grabbing',
    k_grab_limit=0
)

# Get initial state
state = engine.get_initial_state(...)

# Play one move
valid_actions = engine.get_valid_actions(state)
best_action = strategy.select_action(engine, state, valid_actions)
new_state = engine.apply_action(state, best_action)
```

### 2. Using AI Manager (Recommended)

```python
from backend.AI.ai_manager import get_ai_manager

# Get global AI manager
ai_manager = get_ai_manager()

# Load model
ai_manager.load_ml_model("ML/models/data_iter100000/pawn_outcome_model.joblib")

# Set strategy
ai_manager.set_strategy('epsilon-greedy', epsilon=0.1)

# Use in game loop
best_action = ai_manager.select_action(engine, state, valid_actions)
```

### 3. Different Strategies

```python
# Greedy: Always pick best action
strategy = StrategyFactory.create('greedy', evaluator)

# Exploration: Use temperature scaling (more randomness)
strategy = StrategyFactory.create('explore', evaluator, temperature=2.0)

# Epsilon-greedy: Random action 10% of the time
strategy = StrategyFactory.create('epsilon-greedy', evaluator, epsilon=0.1)

# Random: Baseline (no evaluation used)
strategy = StrategyFactory.create('random', evaluator)
```

## Core Components

### Evaluator (evaluator.py)

Base class for state evaluation. All evaluators implement:

```python
class Evaluator(ABC):
    def is_loaded(self) -> bool:
        """Is evaluator ready?"""

    def evaluate_actions(...) -> List[EvaluationResult]:
        """Evaluate all valid actions"""

    def evaluate_state(...) -> float:
        """Get win probability for a state"""

    def get_best_action(...) -> Tuple[str, float]:
        """Select best action"""
```

### MLEvaluator (ml_evaluator.py)

Loads and uses a trained ML model:

```python
evaluator = MLEvaluator("path/to/model.joblib")

# For each action:
# 1. Convert state + action to features
# 2. Predict win probability
# 3. Select action with highest probability
```

### StateConverter (state_converter.py)

Converts GameState + game config to ML input features:

```python
converter = StateConverter()
features = converter.state_to_features(engine, state, action="move A")
# Returns dict with: grabbing_rule, phase, p1_pawn_count, ...
```

### Strategy (strategy.py)

Decision-making policies:

- **GreedyStrategy**: Always pick best (max probability)
- **ExplorationStrategy**: Temperature-scaled softmax
- **EpsilonGreedyStrategy**: Random with probability epsilon
- **RandomStrategy**: Fully random
- **StrategyFactory**: Helper for creating strategies

### AIManager (ai_manager.py)

Central management interface:

```python
manager = AIManager(enable_ai=True)
manager.load_ml_model("model.joblib")
manager.set_strategy('greedy')
best_action = manager.select_action(engine, state, valid_actions)
```

## How It Works: Move Selection

Given a game state with valid moves [Move A, Move B, Move C]:

1. **For each action:**
   - Create features with `chosen_action = action`
   - ML model predicts win probability
2. **Select best action:** Pick the one with highest probability

3. **Apply action:** Update game state

Example with probabilities:

```
Move A → 0.75 win probability
Move B → 0.42 win probability
Move C → 0.88 win probability (BEST)
```

## Feature Engineering

The StateConverter extracts:

- **Game Config**: grabbing_rule, ownership_mechanism, k_grab_limit
- **State**: current_player, phase, k_grabs_made, positions
- **Pawn Count**: p1_pawn_count, p2_pawn_count
- **Action**: chosen_action (the move being evaluated)
- **Graph**: vertices, edges, degrees
- **Distance**: shortest path to target
- **Position**: p1_pos, p2_pos, target_vertex

## Integration with Simulator

### In backend/server.py

```python
from backend.AI.ai_manager import get_ai_manager

ai_manager = get_ai_manager()

@app.post("/api/suggest-move")
def suggest_move(request):
    """Get AI suggestion for next move."""
    ai_manager.load_ml_model(...)
    ai_manager.set_strategy('greedy')
    best_action, prob = ai_manager.evaluator.get_best_action(...)
    return {"action": best_action, "win_probability": prob}
```

### In backend/AI/

Each strategy can be used as an AI player:

```python
# Player 1 = Human, Player 2 = AI
while not engine.is_win(state):
    if state.current_player == 1:
        # Human decision
        action = user_input()
    else:
        # AI decision
        action = ai_strategy.select_action(engine, state, valid_actions)

    state = engine.apply_action(state, action)
```

## Testing

Run the test suite:

```bash
python backend/test_ai_integration.py

# With a model:
python backend/test_ai_integration.py --model path/to/model.joblib --verbose
```

Tests:

1. State converter
2. ML model loading
3. State evaluation
4. Decision strategies
5. AI manager

## Future: RL Integration

The RL module will follow the same interface:

```python
# Future (same interface as ML)
from backend.RL import RLEvaluator

evaluator = RLEvaluator(model_path="path/to/rl_model")
strategy = StrategyFactory.create('greedy', evaluator)

# Works exactly the same as ML!
best_action = strategy.select_action(engine, state, valid_actions)
```

Because both inherit from `Evaluator`, **no changes needed to game code**.

## Configuration Examples

### Production Mode (Greedy ML)

```python
ai_manager = get_ai_manager()
ai_manager.load_ml_model("ML/models/best_model.joblib")
ai_manager.set_strategy('greedy')
ai_manager.enable()
```

### Exploration Mode

```python
ai_manager = get_ai_manager()
ai_manager.load_ml_model("ML/models/best_model.joblib")
ai_manager.set_strategy('explore', temperature=1.5)
ai_manager.enable()
```

### Baseline (Random)

```python
ai_manager = get_ai_manager()
ai_manager.set_strategy('random')
ai_manager.enable()
```

### Disabled

```python
ai_manager = get_ai_manager()
ai_manager.enable(False)
# Falls back to first valid action
```

## Detailed Implementation Notes

### 1. Feature Handling

The StateConverter ensures features match training format:

- Categorical features: grabbing_rule, ownership_mechanism, phase, chosen_action
- Numeric features: positions, pawn counts, distances, graph properties

### 2. Model Assumptions

The ML model expects:

- Trained on data with columns: p1_wins (label), chosen_action, phase, etc.
- Binary classification: 1 = P1 wins, 0 = P2 wins
- For each valid action, create a feature row with that action
- Predict win probability for each
- Pick the action with highest probability

### 3. Error Handling

- If model not loaded: uses DummyEvaluator (all actions equal)
- If feature validation fails: logs warning, returns 0.5 probability
- If prediction fails: returns 0.5 probability

### 4. Temperature Scaling

Used in ExplorationStrategy:

```
scaled_prob = prob ^ (1/temperature)
```

- temperature=1.0: Greedy (no change)
- temperature>1.0: More exploration (probabilities closer to uniform)
- temperature<1.0: Less exploration (probabilities more extreme)

## Performance Considerations

1. **Model Loading**: Done once at startup (not per prediction)
2. **Feature Extraction**: O(n) where n = features (typically 20-30)
3. **Prediction**: ~1-5ms per action on CPU
4. **Total per move**: ~50-150ms for typical game (5-10 valid actions)

## Debugging

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

evaluator = MLEvaluator("model.joblib")
# Now logs feature extraction, predictions, etc.
```

Check feature extraction:

```python
converter = StateConverter()
features = converter.state_to_features(engine, state, action)
print(features)  # See what features are being sent to model
```

## Common Issues

**Issue**: Model not found

- **Fix**: Check path, use absolute paths

**Issue**: Features mismatch between training and runtime

- **Fix**: Run test_ai_integration.py, inspect feature dict

**Issue**: Predictions always 0.5

- **Fix**: Check if model is actually loaded with evaluator.is_loaded()

**Issue**: Memory issues with large models

- **Fix**: Use smaller model or reduce batch size (not applicable here, predictions are single)

## Files Created

```
backend/
├── AI/
│   ├── __init__.py              (Exports)
│   ├── evaluator.py             (Base interface)
│   ├── ml_evaluator.py          (ML implementation)
│   ├── state_converter.py       (Feature extraction)
│   ├── strategy.py              (Decision strategies)
│   └── ai_manager.py            (Central manager)
├── RL/
│   └── __init__.py              (Placeholder)
└── test_ai_integration.py       (Test suite)
```

## Next Steps

1. Generate or locate states_dataset.csv
2. Train ML model if not exists: `python ML/ML_model.py --dataset ...`
3. Run tests: `python backend/test_ai_integration.py --model <path>`
4. Integrate with server/web UI
5. Prepare for RL experiments by maintaining same interface
   """
