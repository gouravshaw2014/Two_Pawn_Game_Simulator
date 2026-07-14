# Backend AI Integration Guide

## Quick Start

### 1. Test the AI framework (without model)

```bash
python backend/test_ai_integration.py
```

This tests:

- State feature extraction
- Strategy creation
- AI manager configuration

### 2. Play an AI game (random strategy)

```bash
python backend/example_ai_game.py --strategy random --human 1
```

This starts an interactive game where you play as P1 and AI plays randomly.

### 3. When you have a trained model

```bash
python backend/test_ai_integration.py --model ML/models/data_iter100000/pawn_outcome_model.joblib

python backend/example_ai_game.py --ai-model ML/models/data_iter100000/pawn_outcome_model.joblib --strategy greedy --human 1
```

## Architecture

```
backend/
├── Simulator/
│   ├── Two_Pawn_Simulator.py    (Game engine)
│   ├── test_networkx.py          (Visualization)
│   └── matplotlib_patch.py        (Matplotlib config)
├── AI/
│   ├── evaluator.py             (Base interface)
│   ├── ml_evaluator.py          (ML-based evaluator)
│   ├── state_converter.py       (State → Features)
│   ├── strategy.py              (Decision strategies)
│   ├── ai_manager.py            (Central manager)
│   ├── ARCHITECTURE.md          (Detailed docs)
│   └── __init__.py              (Module exports)
├── RL/
│   └── __init__.py              (Placeholder for future)
│
├── server.py                    (FastAPI server)
├── test_ai_integration.py       (Test suite)
└── example_ai_game.py           (Example game loop)
```

## How ML Evaluation Works

### Step 1: Game State → Features

```python
state = GameState(p1_pos='A', p2_pos='Start', ...)
action = 'move B'

features = {
    'grabbing_rule': 'always-grabbing',
    'phase': 'move',
    'p1_pawn_count': 3,
    'p2_pawn_count': 0,
    'chosen_action': 'move B',
    # ... more features
}
```

### Step 2: ML Model Predicts

```python
evaluator = MLEvaluator("model.joblib")
win_probability = evaluator.evaluate_state(engine, state, game_config, action="move B")
# Returns: 0.75 (75% chance P1 wins if they take this action)
```

### Step 3: Select Best Action

```python
for action in valid_actions:
    prob = evaluator.evaluate_state(...)
    # collect (action, prob)

best_action = max by prob
# Example:
# move A → 0.65
# move B → 0.75  ← BEST
# move C → 0.58
```

## Core Components

### Evaluator Interface

All evaluators (ML, RL, heuristics) implement:

```python
class Evaluator(ABC):
    def is_loaded() -> bool
    def evaluate_actions(...) -> List[EvaluationResult]
    def evaluate_state(...) -> float
    def get_best_action(...) -> Tuple[str, float]
```

### MLEvaluator

```python
from backend.AI import MLEvaluator

evaluator = MLEvaluator("path/to/model.joblib")
results = evaluator.evaluate_actions(engine, state, valid_actions)
# Returns: [
#   EvaluationResult(action='move A', win_probability=0.75, ...),
#   EvaluationResult(action='move C', win_probability=0.58, ...),
#   ...
# ]
```

### Decision Strategies

Different ways to use evaluations:

```python
from backend.AI import StrategyFactory

# Greedy: always pick best
strategy = StrategyFactory.create('greedy', evaluator)

# Exploration: randomness based on probabilities
strategy = StrategyFactory.create('explore', evaluator, temperature=2.0)

# Epsilon-greedy: 10% random, 90% best
strategy = StrategyFactory.create('epsilon-greedy', evaluator, epsilon=0.1)

# Random: baseline
strategy = StrategyFactory.create('random', evaluator)
```

### AI Manager

Centralized configuration:

```python
from backend.AI import get_ai_manager

ai = get_ai_manager()
ai.enable(True)
ai.load_ml_model("model.joblib")
ai.set_strategy('greedy')

best_action = ai.select_action(engine, state, valid_actions)
```

## Integration Points

### 1. Game Loop

```python
from backend.AI import StrategyFactory, MLEvaluator
from backend.Simulator.Two_Pawn_Simulator import PawnGame

engine = PawnGame(...)
state = engine.get_initial_state(...)
evaluator = MLEvaluator("model.joblib")
strategy = StrategyFactory.create('greedy', evaluator)

while not engine.is_win(state):
    valid_actions = engine.get_valid_actions(state)
    action = strategy.select_action(engine, state, valid_actions)
    state = engine.apply_action(state, action)
```

### 2. REST API

```python
@app.post("/api/suggest-move")
def suggest_move(request):
    ai = get_ai_manager()
    if not ai.is_enabled():
        return {"error": "AI not enabled"}

    best_action, prob = ai.evaluator.get_best_action(
        engine, state, valid_actions
    )
    return {
        "action": best_action,
        "win_probability": prob
    }
```

### 3. Web UI

```javascript
// In web app
async function getAIMove() {
  const response = await fetch("/api/suggest-move", {
    method: "POST",
    body: JSON.stringify({
      gameState: currentState,
      validActions: validMoves,
    }),
  });
  const { action, win_probability } = await response.json();
  return action;
}
```

## Feature Set

The `StateConverter` extracts these features for the ML model:

**Categorical:**

- `grabbing_rule`: 'always-grabbing', 'always-grabbing-or-giving', 'optional-grabbing', 'k-grabbing'
- `ownership_mechanism`: 'OVPP', 'MVPP', 'OMVPP'
- `phase`: 'move', 'grab', 'grab_or_give', 'k_grab'
- `chosen_action`: 'move A', 'grab Red', etc.

**Numeric:**

- `current_player`: 1 or 2
- `p1_pos`, `p2_pos`: Current vertex
- `p1_pawn_count`, `p2_pawn_count`: Number of pawns held
- `target_vertex`: Target vertex name
- `graph_size`: Number of vertices
- `k_grabs_made`: Grabs made in current k-grabbing phase
- `k_grab_limit`: Max grabs allowed
- `avg_vertex_degree`, `max_vertex_degree`: Graph properties
- `total_edges`: Number of edges
- `p1_distance_to_target`, `p2_distance_to_target`: Shortest path distances

## Running Tests

### All tests (no model)

```bash
python backend/test_ai_integration.py
```

Output:

```
TEST 1: State Converter
Extracted features: 20 features
✓ State converter test passed

TEST 2: ML Evaluator
No model path provided, skipping ML evaluator test
(To test with a model, run: python test_ai_integration.py --model <path>)

TEST 3: State Evaluation
No evaluator available (skipping state evaluation test)

TEST 4: Strategies
  greedy: selected 'move A'
  random: selected 'move B'
  ✓ Strategy test passed

TEST 5: AI Manager
✓ AI manager test passed

All tests completed!
```

### With model

```bash
python backend/test_ai_integration.py --model ML/models/data_iter100000/pawn_outcome_model.joblib --verbose
```

## Examples

### Example 1: Load Model and Get Best Move

```python
from backend.AI import MLEvaluator, StrategyFactory
from backend.Simulator.Two_Pawn_Simulator import PawnGame

# Setup
engine = PawnGame(...)
state = engine.get_initial_state(...)

# Load model
evaluator = MLEvaluator("ML/models/data_iter100000/pawn_outcome_model.joblib")
strategy = StrategyFactory.create('greedy', evaluator)

# Get best move
valid_actions = engine.get_valid_actions(state)
best_action = strategy.select_action(engine, state, valid_actions)
print(f"Best move: {best_action}")
```

### Example 2: Evaluate All Actions

```python
from backend.AI import MLEvaluator

evaluator = MLEvaluator("model.joblib")
results = evaluator.evaluate_actions(engine, state, valid_actions)

for result in results:
    print(f"{result.action}: {result.win_probability:.2%}")
```

### Example 3: Play Interactive Game

```bash
python backend/example_ai_game.py --ai-model model.joblib --strategy greedy --human 1
```

### Example 4: AI vs AI

```bash
python backend/example_ai_game.py --ai-vs-ai --strategy greedy --quiet
```

## Future: RL Integration

The same interface works for RL:

```python
# In the future...
from backend.RL import RLEvaluator

evaluator = RLEvaluator("rl_model.pth")
strategy = StrategyFactory.create('greedy', evaluator)

# Use exactly the same way!
best_action = strategy.select_action(engine, state, valid_actions)
```

No changes to game code needed because `RLEvaluator` inherits from `Evaluator`.

## Environment Setup

Ensure these packages are installed:

```bash
pip install pandas scikit-learn joblib numpy
```

Optional:

```bash
pip install pytorch  # For future RL
pip install tensorflow  # Alternative for RL
```

## Troubleshooting

**Q: "Model file not found"**

- A: Check the path is correct and file exists
- Use absolute paths or paths relative to project root

**Q: "Missing dependencies: pandas"**

- A: Install with `pip install pandas scikit-learn joblib`

**Q: "Features validation failed"**

- A: Run `test_ai_integration.py` to inspect features
- Check that all categorical features have expected values

**Q: "Model predictions are always 0.5"**

- A: Check if model is actually loaded with `evaluator.is_loaded()`
- Verify features are being extracted correctly

## Performance

Typical performance on CPU:

- Model loading: ~100-500ms (one-time)
- Feature extraction: ~1-5ms per action
- Prediction: ~1-5ms per action
- Total per move (5 actions): ~50-150ms

## Next Steps

1. **Generate dataset**: `python ML/iterative_dataset_generator.py`
2. **Train model**: `python ML/ML_model.py --dataset ...`
3. **Test integration**: `python backend/test_ai_integration.py --model ...`
4. **Integrate with server**: Add API endpoints to `backend/server.py`
5. **Prepare for RL**: Design `backend.RL.RLEvaluator` following same interface

## Files Summary

| File                     | Purpose                                 |
| ------------------------ | --------------------------------------- |
| `evaluator.py`           | Base interface for all evaluators       |
| `ml_evaluator.py`        | ML-based evaluator using trained models |
| `state_converter.py`     | Convert game state to ML features       |
| `strategy.py`            | Decision-making strategies              |
| `ai_manager.py`          | Central configuration manager           |
| `test_ai_integration.py` | Comprehensive test suite                |
| `example_ai_game.py`     | Interactive game example                |
| `ARCHITECTURE.md`        | Detailed architecture documentation     |

---

For detailed architecture and design decisions, see [ARCHITECTURE.md](./ARCHITECTURE.md)
