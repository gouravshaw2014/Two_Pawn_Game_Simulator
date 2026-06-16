## RL Workspace

All Reinforcement Learning work for this project lives under `RL/`.

### Installation

From project root:

```bash
pip install -r requirements.txt
```

### Conventions

- RL training/evaluation/play scripts are created in `RL/`.
- RL scripts may import/reuse logic from:
  - `Simulator/` (core game rules, engine, visualization)
  - `ML/` (shared utilities, model comparison helpers when needed)
- Keep supervised learning scripts and artifacts in `ML/`.
- Keep game engine and interactive simulator flow in `Simulator/`.

This keeps responsibilities separated:
- `Simulator/` = game mechanics
- `ML/` = supervised learning
- `RL/` = reinforcement learning

### Scripts

1. Train RL model

```bash
python RL/train_rl.py --total-timesteps 200000 --seed 42
```

Select training device:

```bash
python RL/train_rl.py --total-timesteps 200000 --seed 42 --device auto
```

- `--device auto` (default): uses GPU if available, otherwise CPU.
- `--device cpu`: force CPU.
- `--device cuda`: force NVIDIA GPU (requires CUDA-enabled PyTorch).

Enable SB3 progress bar:

```bash
python RL/train_rl.py --total-timesteps 200000 --seed 42 --progress-bar
```

Live plot while training:

```bash
python RL/train_rl.py --total-timesteps 200000 --seed 42 --live-plot
```

Enable episode trace logging (first N episodes):

```bash
python RL/train_rl.py --total-timesteps 200000 --seed 42 --trace-episodes 50
```

True self-play training (P1 specialist + P2 specialist):

```bash
python RL/train_rl.py --total-timesteps 200000 --seed 42 --self-play --self-play-rounds 10 --trace-episodes 50
```

what each argument controls:

- `--total-timesteps 200000`
  Total training budget per specialist loop (split across self-play rounds).
- `--self-play`
  Enables alternating training of:
  - P1 specialist (learns as Player 1)
  - P2 specialist (learns as Player 2)
- `--self-play-rounds 10`
  Alternates training in 10 rounds (P1 trains, then P2 trains, repeat).
- `--trace-episodes 50`
  Saves detailed JSON traces for the first 50 episodes per training env.

Self-play progress logging:

- During self-play, SB3 `iterations` are local to each `learn()` call and may restart at 1.
- Additional round-aware logs are printed:
  - `=== Self-play round X/Y: Training P1 specialist ===`
  - `=== Self-play round X/Y: Training P2 specialist ===`
- Cumulative counters are printed after each phase:
  - `P1 cumulative updates: ... total_timesteps=...`
  - `P2 cumulative updates: ... total_timesteps=...`

Self-play with live plot:

```bash
python RL/train_rl.py --total-timesteps 200000 --seed 42 --self-play --self-play-rounds 10 --live-plot
```

Self-play live-plot outputs:
- `RL/runs/<run>/live_training_plot_p1.png`
- `RL/runs/<run>/live_training_plot_p2.png`

Progress-bar dependency note:

- `--progress-bar` uses `tqdm` and `rich`.
- If unavailable, training automatically continues without progress bar and prints a warning.

Self-play outputs:
- `RL/runs/<run>/p1_specialist.zip`
- `RL/runs/<run>/p2_specialist.zip`

Outputs under `RL/runs/<run_name_or_timestamp>/`.

2. Evaluate RL model (accuracy-like = win rate)

```bash
python RL/eval_rl.py --model RL/runs/<run>/rl_model.zip --episodes 500 --deterministic
```

Evaluate P2 specialist + save traces:

```bash
python RL/eval_rl.py --model RL/runs/<run>/p2_specialist.zip --learning-player 2 --episodes 500 --trace-episodes 100 --trace-dir RL/runs/<run>/eval_traces
```

Writes:
- `rl_eval.metrics.json`
- `rl_eval.metrics.txt`

3. Play vs RL model (with visualization)

```bash
python RL/play_vs_rl.py --model RL/runs/<run>/rl_model.zip --human-player 1
```

Replay previous setup instantly:

```bash
python RL/play_vs_rl.py --model RL/runs/<run>/rl_model.zip --human-player 1 --replay
```

4. RL vs ML standoff

```bash
python RL/rl_vs_ml.py --rl-model RL/runs/<run>/rl_model.zip --ml-model ML/models/data_iter100000/pawn_outcome_model.joblib --episodes 200
```

Specialist standoff (RL P1 specialist + RL P2 specialist vs ML):

```bash
python RL/rl_vs_ml.py --rl-p1-model RL/runs/<run>/p1_specialist.zip --rl-p2-model RL/runs/<run>/p2_specialist.zip --ml-model ML/models/data_iter100000/pawn_outcome_model.joblib --episodes 200
```

Recommended stable standoff run (visible progress + bounded ML CPU workers):

```bash
python RL/rl_vs_ml.py --rl-p1-model RL/runs/<run>/p1_specialist.zip --rl-p2-model RL/runs/<run>/p2_specialist.zip --ml-model ML/models/data_iter100000/pawn_outcome_model.joblib --episodes 200 --ml-n-jobs 1 --progress-every 10
```

Save all played games with per-move RL/ML actions:

```bash
python RL/rl_vs_ml.py --rl-p1-model RL/runs/<run>/p1_specialist.zip --rl-p2-model RL/runs/<run>/p2_specialist.zip --ml-model ML/models/data_iter100000/pawn_outcome_model.joblib --episodes 200 --save-games
```

Custom directory for per-game traces:

```bash
python RL/rl_vs_ml.py --rl-p1-model RL/runs/<run>/p1_specialist.zip --rl-p2-model RL/runs/<run>/p2_specialist.zip --ml-model ML/models/data_iter100000/pawn_outcome_model.joblib --episodes 200 --save-games --game-trace-dir RL/runs/<run>/my_game_traces
```

Writes:
- `rl_vs_ml.metrics.json`
- `rl_vs_ml.metrics.txt`

When `--save-games` is enabled, each game is also saved as JSON under:
- `RL/runs/<run>/standoff_game_traces/`

RL-vs-ML additional arguments:
- `--ml-n-jobs`: ML predictor CPU worker count (default `1` for stability).
- `--progress-every`: print per-side progress every N episodes (`0` disables).
- `--save-games`: enable per-game, per-move trace export.
- `--game-trace-dir`: custom output folder for game trace JSON files.

### Notes

- RL "accuracy" is tracked as **win rate** (accuracy-like metric).
- `RL/play_vs_rl.py` and `ML/play_vs_model.py` both reuse `Simulator/run_interactive_session` for game loop + visualization consistency.
- Episode traces are saved as JSON files when `--trace-episodes > 0`.

### Timesteps vs Iterations vs Episodes

- `--total-timesteps`: total environment steps collected during training.
- `iterations` (in SB3 logs): policy update cycles.
- `episodes`: full games from reset to terminal state.

Useful relation:

$$
  	ext{iterations} \approx \frac{\text{total timesteps}}{\text{n\_steps}}
$$

### Analysis Scripts

Use these scripts to generate trend curves and batch comparisons:

1. ML accuracy trend

```bash
python Analysis/ML/ml_accuracy_training.py --min-iterations 100 --max-iterations 100000 --step 100
```

Useful args:
- `--iterations-list 100,500,1000` to run custom points.
- `--grabbing-rule` and `--ownership-mechanism` to fix scenario type.
- `--reuse-existing` to avoid recomputing existing points.

Outputs under `Analysis/ML/<run>/` with datasets, models, summaries, and `ml_accuracy_trend.png`.

2. RL accuracy trend

```bash
python Analysis/RL/rl_accuracy_training.py --min-timesteps 100 --max-timesteps 100000 --step 100
```

Useful args:
- `--timesteps-list 100,500,1000` for custom budgets.
- `--grabbing-rule` and `--ownership-mechanism` to fix scenario type.
- `--self-play` with `--self-play-rounds` to evaluate specialist training.
- `--reuse-existing` to reuse previously trained/evaluated points.

Outputs under `Analysis/RL/<run>/` with summaries and `rl_accuracy_trend.png`.

3. RL-vs-ML batch comparisons

```bash
python Analysis/rl_ml_batch_comparison.py --episodes 100
```

Behavior:
- Runs same-iteration comparisons where RL and ML both have the same iteration value.
- Runs two default batch sweeps:
  - fixed RL at `--batchRL 500` vs all ML models
  - fixed ML at `--batchML 500` vs all RL models

Useful args:
- `--batchRL` or `--batchML` to choose different fixed capacities.
- `--ml-summary` and `--rl-summary` to select specific summary CSVs.
- `--save-games` to store move-by-move game traces for each standoff run.

Outputs under `Analysis/Comparisons/<run>/` with CSV summaries and trend plots.

With default `n_steps=1024`:

- `--total-timesteps 100000` gives about $100000 / 1024 \approx 98$ iterations.
- Episode count can be much larger (or smaller) depending on average game length.
