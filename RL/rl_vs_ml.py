import argparse
import json
import random
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from Simulator.Two_Pawn_Simulator import PawnGame
from RL.rl_env import PawnReachabilityEnv, sample_random_game_config
from ML.feature_utils import compute_static_features, compute_state_features, combine_features


def _load_dependencies():
    try:
        from sb3_contrib import MaskablePPO
        from joblib import load as joblib_load
        import pandas as pd
    except ImportError as exc:
        raise RuntimeError(
            "Missing dependencies. Install with: pip install gymnasium stable-baselines3 sb3-contrib pandas scikit-learn joblib"
        ) from exc

    return {
        "MaskablePPO": MaskablePPO,
        "joblib_load": joblib_load,
        "pd": pd,
    }


def _ml_choose_action(ml_model, pd, engine, state, static_features, turn_index: int, player: int, valid_actions):
    if not valid_actions:
        return None

    state_features = compute_state_features(engine.graph, engine.target_vertex, state)
    rows = []
    for action in valid_actions:
        features = combine_features(static_features, state_features, turn_index)
        features["chosen_action"] = action
        rows.append(features)

    frame = pd.DataFrame(rows)
    if hasattr(ml_model, "predict_proba"):
        p1_win_probs = ml_model.predict_proba(frame)[:, 1]
    else:
        p1_win_probs = ml_model.predict(frame)

    if player == 1:
        best_idx = int(p1_win_probs.argmax())
    else:
        best_idx = int((1.0 - p1_win_probs).argmax())
    return valid_actions[best_idx]


def _set_ml_n_jobs(ml_model, n_jobs: int) -> bool:
    target = ml_model
    if hasattr(ml_model, "steps") and ml_model.steps:
        target = ml_model.steps[-1][1]
    if hasattr(target, "n_jobs"):
        target.n_jobs = n_jobs
        return True
    return False


def _rl_choose_action(rl_model, engine, state, valid_actions, max_vertices: int):
    env_adapter = PawnReachabilityEnv(max_vertices=max_vertices)
    env_adapter.engine = engine
    env_adapter.state = state
    env_adapter.current_game = None
    action_masks = env_adapter.action_masks()
    obs = env_adapter._get_observation()
    action_id, _ = rl_model.predict(obs, action_masks=action_masks, deterministic=True)
    command = env_adapter.action_to_command(int(action_id))
    if command in valid_actions:
        return command
    return valid_actions[0] if valid_actions else None


def _serialize_game_config(config):
    return {
        "graph": config.graph,
        "ownership": {vertex: sorted(list(colors)) for vertex, colors in config.ownership.items()},
        "target_vertex": config.target_vertex,
        "start_vertex": config.start_vertex,
        "grabbing_rule": config.grabbing_rule,
        "ownership_mechanism": config.ownership_mechanism,
        "k_grab_limit": config.k_grab_limit,
    }


def _serialize_state(state):
    return {
        "p1_pos": state.p1_pos,
        "p2_pos": state.p2_pos,
        "p1_pawns": sorted(list(state.p1_pawns)),
        "p2_pawns": sorted(list(state.p2_pawns)),
        "current_player": state.current_player,
        "phase": state.phase,
        "k_grabs_made": state.k_grabs_made,
    }


def _simulate_one_game(
    rl_model,
    ml_model,
    pd,
    rng: random.Random,
    max_vertices: int,
    max_steps: int,
    rl_player: int,
    collect_trace: bool = False,
):
    config = sample_random_game_config(rng=rng, max_vertices=max_vertices)

    engine = PawnGame(
        graph=config.graph,
        pawn_ownership=config.ownership,
        target_vertex=config.target_vertex,
        grabbing_rule=config.grabbing_rule,
        k_grab_limit=config.k_grab_limit,
    )
    state = engine.get_initial_state(
        start_vertex=config.start_vertex,
        p1_initial_pawns={"Red", "Blue", "Green"},
        p2_initial_pawns=set(),
    )

    static_features = compute_static_features(
        graph=engine.graph,
        ownership=engine.ownership,
        target_vertex=engine.target_vertex,
        grabbing_rule=engine.grabbing_rule,
        ownership_mechanism=config.ownership_mechanism,
        k_grab_limit=engine.k_grab_limit,
    )

    trace_steps = []
    termination_reason = "max_steps"

    for turn in range(1, max_steps + 1):
        if engine.is_win(state):
            termination_reason = "p1_reached_target"
            break

        valid_actions = engine.get_valid_actions(state)
        if not valid_actions:
            termination_reason = "no_valid_actions"
            return "P2", config, trace_steps if collect_trace else None, termination_reason

        current_player = state.current_player
        controller = "RL" if current_player == rl_player else "ML"
        before_state = _serialize_state(state) if collect_trace else None
        if current_player == rl_player:
            action = _rl_choose_action(rl_model, engine, state, valid_actions, max_vertices=max_vertices)
        else:
            action = _ml_choose_action(ml_model, pd, engine, state, static_features, turn, current_player, valid_actions)

        if action is None:
            termination_reason = "action_selection_failed"
            return "P2", config, trace_steps if collect_trace else None, termination_reason

        next_state = engine.apply_action(state, action)
        if collect_trace:
            trace_steps.append(
                {
                    "turn": turn,
                    "controller": controller,
                    "acting_player": current_player,
                    "action": action,
                    "valid_actions": list(valid_actions),
                    "state_before": before_state,
                    "state_after": _serialize_state(next_state),
                }
            )
        state = next_state

    winner = "P1" if engine.is_win(state) else "P2"
    if winner == "P1" and termination_reason == "max_steps":
        termination_reason = "p1_reached_target"
    return winner, config, trace_steps if collect_trace else None, termination_reason


def _write_game_trace(
    trace_dir: Path,
    side_label: str,
    episode_idx: int,
    rl_player: int,
    winner: str,
    config,
    steps,
    termination_reason: str,
):
    payload = {
        "side": side_label,
        "episode": episode_idx,
        "rl_player": rl_player,
        "winner": winner,
        "termination_reason": termination_reason,
        "config": _serialize_game_config(config),
        "steps": steps,
    }
    output_path = trace_dir / f"{side_label}_{episode_idx:06d}.json"
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def run_standoff(args):
    deps = _load_dependencies()

    rl_model_path = Path(args.rl_model) if args.rl_model else None
    rl_p1_model_path = Path(args.rl_p1_model) if args.rl_p1_model else None
    rl_p2_model_path = Path(args.rl_p2_model) if args.rl_p2_model else None
    ml_model_path = Path(args.ml_model)
    if rl_model_path is None and (rl_p1_model_path is None or rl_p2_model_path is None):
        raise ValueError("Provide either --rl-model or both --rl-p1-model and --rl-p2-model.")
    if rl_model_path is not None and not rl_model_path.exists():
        raise FileNotFoundError(f"RL model not found: {rl_model_path}")
    if rl_p1_model_path is not None and not rl_p1_model_path.exists():
        raise FileNotFoundError(f"RL P1 model not found: {rl_p1_model_path}")
    if rl_p2_model_path is not None and not rl_p2_model_path.exists():
        raise FileNotFoundError(f"RL P2 model not found: {rl_p2_model_path}")
    if not ml_model_path.exists():
        raise FileNotFoundError(f"ML model not found: {ml_model_path}")

    if rl_model_path is not None:
        rl_model_p1 = deps["MaskablePPO"].load(str(rl_model_path))
        rl_model_p2 = rl_model_p1
    else:
        rl_model_p1 = deps["MaskablePPO"].load(str(rl_p1_model_path))
        rl_model_p2 = deps["MaskablePPO"].load(str(rl_p2_model_path))
    ml_model = deps["joblib_load"](str(ml_model_path))
    pd = deps["pd"]

    applied_n_jobs = _set_ml_n_jobs(ml_model, args.ml_n_jobs)
    if applied_n_jobs:
        print(f"Configured ML predictor n_jobs={args.ml_n_jobs}")

    rng = random.Random(args.seed)

    trace_dir = None
    if args.save_games:
        base_parent = rl_model_path.parent if rl_model_path is not None else rl_p1_model_path.parent
        trace_dir = Path(args.game_trace_dir) if args.game_trace_dir else (base_parent / "standoff_game_traces")
        trace_dir.mkdir(parents=True, exist_ok=True)
        print(f"Saving per-game traces to: {trace_dir}")

    stats = {
        "episodes": args.episodes,
        "rl_as_p1": {"wins": 0, "losses": 0},
        "rl_as_p2": {"wins": 0, "losses": 0},
    }

    for episode_idx in range(1, args.episodes + 1):
        winner, config, trace_steps, termination_reason = _simulate_one_game(
            rl_model=rl_model_p1,
            ml_model=ml_model,
            pd=pd,
            rng=rng,
            max_vertices=args.max_vertices,
            max_steps=args.max_steps,
            rl_player=1,
            collect_trace=args.save_games,
        )
        if winner == "P1":
            stats["rl_as_p1"]["wins"] += 1
        else:
            stats["rl_as_p1"]["losses"] += 1

        if args.save_games and trace_dir is not None:
            _write_game_trace(
                trace_dir=trace_dir,
                side_label="rl_as_p1",
                episode_idx=episode_idx,
                rl_player=1,
                winner=winner,
                config=config,
                steps=trace_steps,
                termination_reason=termination_reason,
            )

        if args.progress_every > 0 and episode_idx % args.progress_every == 0:
            print(
                f"[RL as P1] {episode_idx}/{args.episodes} "
                f"wins={stats['rl_as_p1']['wins']} losses={stats['rl_as_p1']['losses']}"
            )

    for episode_idx in range(1, args.episodes + 1):
        winner, config, trace_steps, termination_reason = _simulate_one_game(
            rl_model=rl_model_p2,
            ml_model=ml_model,
            pd=pd,
            rng=rng,
            max_vertices=args.max_vertices,
            max_steps=args.max_steps,
            rl_player=2,
            collect_trace=args.save_games,
        )
        if winner == "P2":
            stats["rl_as_p2"]["wins"] += 1
        else:
            stats["rl_as_p2"]["losses"] += 1

        if args.save_games and trace_dir is not None:
            _write_game_trace(
                trace_dir=trace_dir,
                side_label="rl_as_p2",
                episode_idx=episode_idx,
                rl_player=2,
                winner=winner,
                config=config,
                steps=trace_steps,
                termination_reason=termination_reason,
            )

        if args.progress_every > 0 and episode_idx % args.progress_every == 0:
            print(
                f"[RL as P2] {episode_idx}/{args.episodes} "
                f"wins={stats['rl_as_p2']['wins']} losses={stats['rl_as_p2']['losses']}"
            )

    total_games = args.episodes * 2
    total_wins = stats["rl_as_p1"]["wins"] + stats["rl_as_p2"]["wins"]
    win_rate = total_wins / max(1, total_games)

    report = {
        "rl_model": str(rl_model_path) if rl_model_path is not None else None,
        "rl_p1_model": str(rl_p1_model_path) if rl_p1_model_path is not None else str(rl_model_path),
        "rl_p2_model": str(rl_p2_model_path) if rl_p2_model_path is not None else str(rl_model_path),
        "ml_model": str(ml_model_path),
        "seed": args.seed,
        "episodes_per_side": args.episodes,
        "total_games": total_games,
        "rl_total_wins": total_wins,
        "rl_win_rate": win_rate,
        "details": stats,
    }

    base_parent = rl_model_path.parent if rl_model_path is not None else rl_p1_model_path.parent
    output_dir = Path(args.output_dir) if args.output_dir else base_parent
    output_dir.mkdir(parents=True, exist_ok=True)
    output_json = output_dir / "rl_vs_ml.metrics.json"
    output_txt = output_dir / "rl_vs_ml.metrics.txt"

    output_json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    output_txt.write_text(
        "RL vs ML Standoff\n"
        f"RL total wins: {total_wins}/{total_games}\n"
        f"RL overall win rate: {win_rate:.4f}\n"
        f"RL as P1 wins: {stats['rl_as_p1']['wins']}/{args.episodes}\n"
        f"RL as P2 wins: {stats['rl_as_p2']['wins']}/{args.episodes}\n",
        encoding="utf-8",
    )

    print(f"Standoff metrics saved to: {output_json}")
    print(f"Standoff summary saved to: {output_txt}")
    print(f"RL overall win rate: {win_rate:.4f}")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run RL vs ML standoff experiments.")
    parser.add_argument("--rl-model", type=str, default=None, help="Single RL model used for both sides (.zip)")
    parser.add_argument("--rl-p1-model", type=str, default=None, help="RL P1 specialist model (.zip)")
    parser.add_argument("--rl-p2-model", type=str, default=None, help="RL P2 specialist model (.zip)")
    parser.add_argument("--ml-model", type=str, required=True, help="Path to ML model (.joblib)")
    parser.add_argument("--episodes", type=int, default=200, help="Episodes per side (RL as P1 and as P2)")
    parser.add_argument("--seed", type=int, default=123, help="Random seed")
    parser.add_argument("--max-vertices", type=int, default=10, help="Max sampled vertices")
    parser.add_argument("--max-steps", type=int, default=200, help="Max steps per game")
    parser.add_argument("--ml-n-jobs", type=int, default=1, help="Number of CPU workers used by ML predictor (default 1 for stability).")
    parser.add_argument("--progress-every", type=int, default=10, help="Print progress every N episodes per side (0 disables).")
    parser.add_argument("--save-games", action="store_true", help="Save each played game with per-move RL/ML actions as JSON trace files.")
    parser.add_argument("--game-trace-dir", type=str, default=None, help="Directory for standoff game trace JSON files.")
    parser.add_argument("--output-dir", type=str, default=None, help="Output directory for report files")
    return parser


if __name__ == "__main__":
    parser = build_arg_parser()
    args = parser.parse_args()
    run_standoff(args)
