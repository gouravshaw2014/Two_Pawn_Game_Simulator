## ML Workflow

Use the scripts in `ML/` to generate training data, train a model, and play against it.

### Installation

From project root:

```bash
pip install -r requirements.txt
```

1. **Generate dataset**

   ```bash
   python ML/iterative_dataset_generator.py --iterations 5000 --seed 42
   ```

   `--seed` sets the random seed for dataset generation, so randomness becomes reproducible.

   - Same `--seed` + same args ⇒ same generated graphs, rules, ownership assignments, random actions, and outcomes.
   - Different `--seed` ⇒ a different random dataset.
   - Useful for debugging and fair experiment comparisons (you can rerun exactly the same data later).

   Optional custom generation constraints:
   - `--grabbing-rule` (`always-grabbing`, `always-grabbing-or-giving`, `optional-grabbing`, `k-grabbing`)
   - `--ownership-mechanism` (`OVPP`, `MVPP`, `OMVPP`)
   - `--vertex-count` (fixed graph size) or `--vertex-min` / `--vertex-max` (range)
   - `--target-index` (fixed target vertex index)
   - `--k-grab-limit` (only with `--grabbing-rule k-grabbing`)
   - `--edge-prob-min` / `--edge-prob-max` (graph density range)

   Example with custom settings:

   ```bash
   python ML/iterative_dataset_generator.py --iterations 5000 --seed 42 --grabbing-rule optional-grabbing --ownership-mechanism MVPP --vertex-count 8 --target-index 5
   ```

   Output directory behavior:
   - Default run (no custom constraints) writes to `ML/datasets/data_iter<iterations>`.
   - Custom run (with constraints) auto-writes to `ML/datasets/data_<custom-args-joined-by-hyphen>-it-<iterations>`.
   - You can still override location explicitly with `--out-dir`.

    Notes:
    - Start vertex is treated as **neutral** (not owned by Red/Blue/Green).
    - Default random vertex range is `4..14` for non-OVPP random runs.
       - `14` is just a practical default upper bound to keep random generation/training manageable.
       - You can change it with `--vertex-max`.

2. **Train model**

   ```bash
   python ML/ML_model.py --dataset ML/datasets/data_iter5000/states_dataset.csv
   ```

    Model output behavior:
    - Default save path: `ML/models/<dataset-folder>/pawn_outcome_model.joblib`
    - Example dataset `ML/datasets/data_gr-always-grabbing-own-ovpp-v-3-14-it-100000/states_dataset.csv`
       saves to `ML/models/data_gr-always-grabbing-own-ovpp-v-3-14-it-100000/pawn_outcome_model.joblib`
      - Training metrics are also saved next to the model as:
         - `pawn_outcome_model.metrics.json` (structured metrics)
         - `pawn_outcome_model.metrics.txt` (readable accuracy/report)
    - You can still override with `--model-out`.

3. **Play vs trained model**

   ```bash
   python ML/play_vs_model.py --model ML/models/pawn_outcome_model.joblib --human-player 1
   ```

   Replay previous setup without re-entering graph/rules:

   ```bash
   python ML/play_vs_model.py --model ML/models/pawn_outcome_model.joblib --human-player 1 --replay
   ```

   `--replay` reuses the most recent play-vs-model configuration and immediately starts gameplay/visualization.

Generated artifacts:
- `ML/datasets/data_iter5000/games_dataset.csv` (game-level rows)
- `ML/datasets/data_iter5000/states_dataset.csv` (state-level rows used for training)
- `ML/datasets/data_iter5000/logs/*.json` (full per-iteration logs)
- `ML/models/pawn_outcome_model.joblib` (trained model)
- `ML/models/<dataset-folder>/pawn_outcome_model.metrics.json` (accuracy + classification report)
- `ML/models/<dataset-folder>/pawn_outcome_model.metrics.txt` (metrics summary)

---