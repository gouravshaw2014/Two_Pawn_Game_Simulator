import argparse
import sys
import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from Simulator.Two_Pawn_Simulator import PawnGame, GameState, build_game_configuration_interactively, run_interactive_session
from ML.feature_utils import compute_static_features, compute_state_features, combine_features

LAST_PLAY_CONFIG_PATH = ROOT_DIR / "ML" / ".last_play_vs_model_config.json"


def _load_model(model_path: Path):
    try:
        import pandas as pd
        from joblib import load
    except ImportError as exc:
        raise RuntimeError(
            "Missing dependencies to run model inference. Install with: pip install pandas scikit-learn joblib"
        ) from exc

    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")

    pipeline = load(model_path)
    return pipeline, pd


def _normalize_set_field(value):
    if isinstance(value, set):
        return sorted(list(value))
    if isinstance(value, dict):
        return {k: _normalize_set_field(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_normalize_set_field(v) for v in value]
    return value


def _serialize_game_config(game_config: dict) -> dict:
    return _normalize_set_field(game_config)


def _deserialize_game_config(payload: dict) -> dict:
    config = {
        "rules": {
            "graph": payload["rules"]["graph"],
            "pawn_ownership": {
                vertex: set(colors) for vertex, colors in payload["rules"]["pawn_ownership"].items()
            },
            "target_vertex": payload["rules"]["target_vertex"],
            "grabbing_rule": payload["rules"]["grabbing_rule"],
            "k_grab_limit": payload["rules"].get("k_grab_limit", 0),
        },
        "initial": {
            "start_vertex": payload["initial"]["start_vertex"],
            "p1_initial_pawns": set(payload["initial"]["p1_initial_pawns"]),
            "p2_initial_pawns": set(payload["initial"]["p2_initial_pawns"]),
        },
        "metadata": payload.get("metadata", {}),
    }
    return config


def _save_last_config(game_config: dict) -> None:
    LAST_PLAY_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    LAST_PLAY_CONFIG_PATH.write_text(
        json.dumps(_serialize_game_config(game_config), indent=2),
        encoding="utf-8",
    )


def _load_last_config() -> dict:
    if not LAST_PLAY_CONFIG_PATH.exists():
        raise FileNotFoundError(
            f"No replay configuration found at {LAST_PLAY_CONFIG_PATH}. Run once without --replay first."
        )
    payload = json.loads(LAST_PLAY_CONFIG_PATH.read_text(encoding="utf-8"))
    return _deserialize_game_config(payload)


def _infer_ownership_mechanism(ownership_map):
    overlap_count = sum(1 for colors in ownership_map.values() if len(colors) > 1)
    single_color = all(len(colors) == 1 for colors in ownership_map.values())

    if len(ownership_map) == 3 and single_color:
        counts = {"Red": 0, "Blue": 0, "Green": 0}
        for colors in ownership_map.values():
            for color in colors:
                if color in counts:
                    counts[color] += 1
        if all(v == 1 for v in counts.values()):
            return "OVPP"

    if overlap_count > 0:
        return "OMVPP"
    return "MVPP"


def _choose_model_action(pipeline, pd, engine, state, static_features, turn_index: int, ai_player: int):
    valid_actions = engine.get_valid_actions(state)
    if not valid_actions:
        return None, None

    best_action = None
    best_score = None

    state_features = compute_state_features(engine.graph, engine.target_vertex, state)
    for action in valid_actions:
        features = combine_features(static_features, state_features, turn_index)
        features["chosen_action"] = action
        sample_df = pd.DataFrame([features])

        if hasattr(pipeline, "predict_proba"):
            p1_win_prob = float(pipeline.predict_proba(sample_df)[0][1])
        else:
            p1_win_prob = float(pipeline.predict(sample_df)[0])

        score = p1_win_prob if ai_player == 1 else (1.0 - p1_win_prob)
        if best_score is None or score > best_score:
            best_score = score
            best_action = action

    return best_action, best_score


def _build_model_action_selector(pipeline, pd, game_config, human_player: int):
    ai_player = 2 if human_player == 1 else 1
    cached_static_features = {"value": None}

    def _selector(engine: PawnGame, state: GameState, valid_actions, turn_index: int):
        if cached_static_features["value"] is None:
            ownership_mechanism = game_config.get("metadata", {}).get("ownership_mechanism")
            if not ownership_mechanism:
                ownership_mechanism = _infer_ownership_mechanism(engine.ownership)
            cached_static_features["value"] = compute_static_features(
                graph=engine.graph,
                ownership=engine.ownership,
                target_vertex=engine.target_vertex,
                grabbing_rule=engine.grabbing_rule,
                ownership_mechanism=ownership_mechanism,
                k_grab_limit=engine.k_grab_limit,
            )

        action, confidence = _choose_model_action(
            pipeline=pipeline,
            pd=pd,
            engine=engine,
            state=state,
            static_features=cached_static_features["value"],
            turn_index=turn_index,
            ai_player=ai_player,
        )
        if action is None:
            return None
        return action, f"Model chooses: {action} (score={confidence:.3f})"

    return _selector


def play_vs_model(model_path: Path, human_player: int, replay: bool) -> None:
    pipeline, pd = _load_model(model_path)

    if replay:
        game_config = _load_last_config()
        print("Loaded previous setup using --replay.")
    else:
        game_config = build_game_configuration_interactively()
        _save_last_config(game_config)

    ai_player = 2 if human_player == 1 else 1
    target_vertex = game_config["rules"]["target_vertex"]

    print("\n--- Play vs ML Model ---")
    print(f"You are Player {human_player}; model is Player {ai_player}.")
    print(f"Target vertex: {target_vertex}")

    action_selector = _build_model_action_selector(
        pipeline=pipeline,
        pd=pd,
        game_config=game_config,
        human_player=human_player,
    )
    run_interactive_session(
        game_config,
        human_player=human_player,
        automated_action_selector=action_selector,
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Play against trained Two Pawn ML model.")
    parser.add_argument(
        "--model",
        type=Path,
        default=Path("ML/models/pawn_outcome_model.joblib"),
        help="Path to trained model file.",
    )
    parser.add_argument(
        "--human-player",
        type=int,
        choices=[1, 2],
        default=1,
        help="Choose whether you control Player 1 or Player 2.",
    )
    parser.add_argument(
        "--replay",
        action="store_true",
        help="Reuse the most recent play-vs-model setup and skip configuration prompts.",
    )
    return parser


if __name__ == "__main__":
    args = build_arg_parser().parse_args()
    play_vs_model(model_path=args.model, human_player=args.human_player, replay=args.replay)
