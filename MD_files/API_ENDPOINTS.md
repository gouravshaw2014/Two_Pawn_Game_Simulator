# AI API Endpoints Documentation

## Overview

The backend server now includes 8 AI endpoints that allow the frontend to:

- Initialize AI with ML models
- Get move suggestions with win probabilities
- Evaluate all possible actions
- Switch between strategies
- Manage AI configuration

All endpoints are prefixed with `/ai/`

---

## Endpoints

### 1. GET `/ai/status`

Get current AI configuration and status.

**Request:**

```bash
GET /ai/status
```

**Response:**

```json
{
  "enabled": true,
  "available": true,
  "evaluator_type": "MLEvaluator",
  "strategy_type": "GreedyStrategy",
  "model_path": "ML/models/data_iter100000/pawn_outcome_model.joblib",
  "has_model": true
}
```

**Use Case:** Check AI readiness, display current strategy on UI

---

### 2. POST `/ai/init`

Initialize AI with a model and strategy.

**Request:**

```json
{
  "model_path": "ML/models/data_iter100000/pawn_outcome_model.joblib",
  "strategy": "greedy",
  "enable": true
}
```

**Parameters:**

- `model_path` (string, optional): Path to trained ML model
- `strategy` (string): One of `greedy`, `explore`, `epsilon-greedy`, `random`
- `enable` (boolean): Whether to enable AI

**Response:**

```json
{
  "enabled": true,
  "available": true,
  "evaluator_type": "MLEvaluator",
  "strategy_type": "GreedyStrategy",
  "model_path": "ML/models/data_iter100000/pawn_outcome_model.joblib",
  "has_model": true
}
```

**Example (Python):**

```python
import requests

response = requests.post('http://localhost:8000/ai/init', json={
    'model_path': 'ML/models/data_iter100000/pawn_outcome_model.joblib',
    'strategy': 'greedy',
    'enable': True
})
print(response.json())
```

**Example (JavaScript/Fetch):**

```javascript
const response = await fetch("/ai/init", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    model_path: "ML/models/data_iter100000/pawn_outcome_model.joblib",
    strategy: "greedy",
    enable: true,
  }),
});
const data = await response.json();
console.log(data);
```

---

### 3. POST `/ai/suggest`

Get AI's suggested next move for the current game state.

**Request:**

```json
{
  "game_state": null,
  "valid_actions": null
}
```

**Parameters:**

- `game_state` (dict, optional): Game state override (uses current if null)
- `valid_actions` (list, optional): Valid actions override (auto-detected from engine if null)

**Response:**

```json
{
  "action": "move C",
  "win_probability": 0.88,
  "evaluations": [
    {
      "action": "move C",
      "win_probability": 0.88,
      "confidence": 1.0
    },
    {
      "action": "move A",
      "win_probability": 0.75,
      "confidence": 1.0
    },
    {
      "action": "move B",
      "win_probability": 0.42,
      "confidence": 1.0
    }
  ]
}
```

**Example (JavaScript):**

```javascript
// Get AI suggestion for current game state
const response = await fetch("/ai/suggest", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    game_state: null, // Uses current game state
    valid_actions: null, // Auto-detect
  }),
});
const { action, win_probability, evaluations } = await response.json();
console.log(`AI suggests: ${action} (${(win_probability * 100).toFixed(1)}%)`);
```

**Use Case:** Display AI suggestion on UI, let human player review before accepting

---

### 4. POST `/ai/evaluate`

Evaluate all valid actions with win probabilities.

**Request:**

```json
{
  "game_state": null,
  "valid_actions": null
}
```

**Response:**

```json
{
  "total_actions": 3,
  "evaluations": [
    {
      "action": "move C",
      "win_probability": 0.88,
      "confidence": 1.0,
      "rank": 1
    },
    {
      "action": "move A",
      "win_probability": 0.75,
      "confidence": 1.0,
      "rank": 2
    },
    {
      "action": "move B",
      "win_probability": 0.42,
      "confidence": 1.0,
      "rank": 3
    }
  ],
  "best_action": {
    "action": "move C",
    "win_probability": 0.88,
    "confidence": 1.0,
    "rank": 1
  }
}
```

**Example (JavaScript):**

```javascript
// Get evaluation of all moves
const response = await fetch("/ai/evaluate", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({}),
});
const { evaluations, best_action } = await response.json();

// Display all options with probabilities
evaluations.forEach((eval) => {
  console.log(
    `${eval.rank}. ${eval.action}: ${(eval.win_probability * 100).toFixed(1)}%`,
  );
});
```

**Use Case:** Show decision heatmap, help understand AI reasoning

---

### 5. POST `/ai/strategy`

Change the AI decision strategy.

**Request:**

```json
{
  "strategy": "explore",
  "temperature": 1.5,
  "epsilon": null
}
```

**Parameters:**

- `strategy` (string): Strategy name (required)
- `temperature` (float, optional): For explore strategy (default 1.5)
- `epsilon` (float, optional): For epsilon-greedy (default 0.1)

**Response:**

```json
{
  "success": true,
  "strategy": "explore",
  "config": {
    "strategy": "explore",
    "strategy_params": {
      "temperature": 1.5
    }
  }
}
```

**Example (JavaScript):**

```javascript
// Switch to exploration mode
await fetch("/ai/strategy", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    strategy: "explore",
    temperature: 2.0,
  }),
});

// Or switch to epsilon-greedy
await fetch("/ai/strategy", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    strategy: "epsilon-greedy",
    epsilon: 0.2,
  }),
});
```

**Strategies:**

- **greedy**: Always pick best (deterministic)
- **explore**: Softmax with temperature (balanced)
- **epsilon-greedy**: Random with probability (research)
- **random**: Baseline (no AI)

---

### 6. POST `/ai/enable`

Enable or disable AI.

**Request:**

```json
{
  "enabled": true
}
```

**Response:**

```json
{
  "success": true,
  "enabled": true
}
```

**Example (JavaScript):**

```javascript
// Disable AI
await fetch("/ai/enable", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ enabled: false }),
});

// Enable AI
await fetch("/ai/enable", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ enabled: true }),
});
```

---

### 7. GET `/ai/models/available`

Get list of available trained models.

**Request:**

```bash
GET /ai/models/available
```

**Response:**

```json
{
  "models": [
    {
      "path": "ML/models/data_iter100000/pawn_outcome_model.joblib",
      "name": "data_iter100000",
      "filename": "pawn_outcome_model.joblib"
    }
  ],
  "count": 1
}
```

**Example (JavaScript):**

```javascript
// Show available models in dropdown
const response = await fetch("/ai/models/available");
const { models } = await response.json();

models.forEach((model) => {
  console.log(`${model.name}: ${model.path}`);
});
```

**Use Case:** Populate model selection dropdown in settings UI

---

### 8. GET `/ai/strategies/available`

Get list of available strategies with descriptions.

**Request:**

```bash
GET /ai/strategies/available
```

**Response:**

```json
{
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
```

**Example (JavaScript):**

```javascript
// Show available strategies with settings
const response = await fetch("/ai/strategies/available");
const strategies = await response.json();

Object.entries(strategies).forEach(([key, strategy]) => {
  console.log(`${strategy.name}: ${strategy.description}`);
  strategy.parameters.forEach((param) => {
    console.log(`  - ${param.name} (default: ${param.default})`);
  });
});
```

**Use Case:** Populate strategy selection and parameter configuration UI

---

## Complete Integration Example

### 1. Initialize AI on Game Start

```javascript
async function initializeAI() {
  // Get available models
  const modelsResponse = await fetch("/ai/models/available");
  const { models } = await modelsResponse.json();

  if (models.length === 0) {
    console.warn("No trained models available");
    return false;
  }

  // Initialize with first available model
  const modelPath = models[0].path;
  const initResponse = await fetch("/ai/init", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      model_path: modelPath,
      strategy: "greedy",
      enable: true,
    }),
  });

  const status = await initResponse.json();
  console.log("AI initialized:", status);
  return status.enabled;
}
```

### 2. Display AI Suggestion in Game UI

```javascript
async function showAISuggestion() {
  try {
    const response = await fetch("/ai/suggest", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({}),
    });

    if (!response.ok) {
      console.log("AI not available");
      return;
    }

    const { action, win_probability, evaluations } = await response.json();

    // Display suggestion
    document.getElementById("ai-suggestion").innerHTML = `
            <strong>AI suggests:</strong> ${action}
            <br/>Win probability: ${(win_probability * 100).toFixed(1)}%
        `;

    // Display all options
    const options = evaluations
      .map((e) => `${e.action}: ${(e.win_probability * 100).toFixed(1)}%`)
      .join("<br/>");
    document.getElementById("ai-options").innerHTML = options;
  } catch (error) {
    console.error("Error getting AI suggestion:", error);
  }
}
```

### 3. Strategy Settings Panel

```javascript
async function setupStrategySettings() {
  // Get available strategies
  const response = await fetch("/ai/strategies/available");
  const strategies = await response.json();

  // Populate dropdown
  const dropdown = document.getElementById("strategy-select");
  Object.keys(strategies).forEach((key) => {
    const option = document.createElement("option");
    option.value = key;
    option.textContent = strategies[key].name;
    dropdown.appendChild(option);
  });

  // On selection change
  dropdown.addEventListener("change", async (e) => {
    const strategy = e.target.value;
    const params = {};

    if (strategy === "explore") {
      params.temperature = document.getElementById("temp-slider").value;
    } else if (strategy === "epsilon-greedy") {
      params.epsilon = document.getElementById("epsilon-slider").value;
    }

    await fetch("/ai/strategy", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ strategy, ...params }),
    });
  });
}
```

---

## Error Handling

All endpoints return appropriate HTTP status codes:

| Code | Meaning      | Example                              |
| ---- | ------------ | ------------------------------------ |
| 200  | Success      | Model loaded, suggestion returned    |
| 403  | Forbidden    | AI not enabled                       |
| 404  | Not Found    | Model file doesn't exist             |
| 400  | Bad Request  | Invalid parameters, no valid actions |
| 500  | Server Error | Unexpected error, framework issue    |

**Example Error Handling:**

```javascript
async function suggestMove() {
  try {
    const response = await fetch("/ai/suggest", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({}),
    });

    if (response.status === 403) {
      console.log("AI not enabled");
      return null;
    }

    if (response.status === 400) {
      const error = await response.json();
      console.error("Bad request:", error.detail);
      return null;
    }

    if (!response.ok) {
      throw new Error(`Server error: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error("Error:", error);
    return null;
  }
}
```

---

## Workflow Examples

### Workflow 1: Auto AI Opponent

```javascript
// Start AI opponent automatically
async function startAIOpponent() {
  // Initialize AI
  await fetch("/ai/init", {
    method: "POST",
    body: JSON.stringify({
      model_path: "ML/models/data_iter100000/pawn_outcome_model.joblib",
      strategy: "greedy",
      enable: true,
    }),
  });

  // Get AI move automatically
  const { action } = await (
    await fetch("/ai/suggest", {
      method: "POST",
      body: "{}",
    })
  ).json();

  // Play AI move
  await fetch("/action", {
    method: "POST",
    body: JSON.stringify({ action }),
  });
}
```

### Workflow 2: Analysis Mode

```javascript
// Show detailed analysis of all moves
async function analyzePosition() {
  const { evaluations } = await (
    await fetch("/ai/evaluate", {
      method: "POST",
      body: "{}",
    })
  ).json();

  // Display heatmap
  evaluations.forEach((e) => {
    const bar = "█".repeat(Math.round(e.win_probability * 50));
    console.log(
      `${e.action.padEnd(10)} ${bar} ${(e.win_probability * 100).toFixed(1)}%`,
    );
  });
}
```

### Workflow 3: Experiment with Strategies

```javascript
// Test different strategies
async function compareStrategies() {
  const strategies = ["greedy", "random", "explore"];

  for (const strategy of strategies) {
    await fetch("/ai/strategy", {
      method: "POST",
      body: JSON.stringify({ strategy }),
    });

    const { action, win_probability } = await (
      await fetch("/ai/suggest", {
        method: "POST",
        body: "{}",
      })
    ).json();

    console.log(
      `${strategy}: ${action} (${(win_probability * 100).toFixed(1)}%)`,
    );
  }
}
```

---

## Testing

### Test with curl

```bash
# Check AI status
curl http://localhost:8000/ai/status

# Initialize AI
curl -X POST http://localhost:8000/ai/init \
  -H "Content-Type: application/json" \
  -d '{"model_path": "ML/models/data_iter100000/pawn_outcome_model.joblib", "strategy": "greedy", "enable": true}'

# Get suggestion
curl -X POST http://localhost:8000/ai/suggest \
  -H "Content-Type: application/json" \
  -d '{}'

# Get all evaluations
curl -X POST http://localhost:8000/ai/evaluate \
  -H "Content-Type: application/json" \
  -d '{}'
```

### Test with Python

```python
import requests

base_url = 'http://localhost:8000'

# Check status
status = requests.get(f'{base_url}/ai/status').json()
print(f"AI enabled: {status['enabled']}")

# Initialize
init_resp = requests.post(f'{base_url}/ai/init', json={
    'model_path': 'ML/models/data_iter100000/pawn_outcome_model.joblib',
    'strategy': 'greedy',
    'enable': True
})
print(f"Initialized: {init_resp.json()}")

# Get suggestion
suggest = requests.post(f'{base_url}/ai/suggest', json={}).json()
print(f"Suggestion: {suggest['action']} ({suggest['win_probability']:.1%})")

# Evaluate all
evals = requests.post(f'{base_url}/ai/evaluate', json={}).json()
for e in evals['evaluations']:
    print(f"  {e['action']}: {e['win_probability']:.1%}")
```

---

## Performance Notes

- **Suggestion endpoint**: ~50-150ms (depends on number of valid actions)
- **Evaluate endpoint**: ~50-200ms (evaluates all actions)
- **Model initialization**: ~100-500ms (one-time, on startup)

Suggestions can be cached if game state hasn't changed.

---

## Next Steps

1. Test endpoints with curl or Postman
2. Update React frontend to use endpoints
3. Add AI settings UI component
4. Display win probabilities on action buttons
5. Add strategy selection to settings
