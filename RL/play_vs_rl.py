import argparse
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from Simulator.Two_Pawn_Simulator import PawnGame, GameState, build_game_configuration_interactively, run_interactive_session
from RL.rl_env import PawnReachabilityEnv

LAST_PLAY_CONFIG_PATH = ROOT_DIR / "RL" / ".last_play_vs_rl_config.json"


def _load_rl_dependencies():
    try:
        from sb3_contrib import MaskablePPO
    except ImportError as exc:
        raise RuntimeError(
            "Missing RL dependencies. Install with: pip install gymnasium stable-baselines3 sb3-contrib"
        ) from exc
    return {"MaskablePPO": MaskablePPO}


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
    return {
        "rules": {
            "graph": payload["rules"]["graph"],
            "pawn_ownership": {k: set(v) for k, v in payload["rules"]["pawn_ownership"].items()},
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


def _save_last_config(game_config: dict) -> None:
    LAST_PLAY_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    LAST_PLAY_CONFIG_PATH.write_text(json.dumps(_serialize_game_config(game_config), indent=2), encoding="utf-8")


def _load_last_config() -> dict:
    if not LAST_PLAY_CONFIG_PATH.exists():
        raise FileNotFoundError(f"No replay configuration found at {LAST_PLAY_CONFIG_PATH}. Run once without --replay first.")
    return _deserialize_game_config(json.loads(LAST_PLAY_CONFIG_PATH.read_text(encoding="utf-8")))


def _build_rl_action_selector(model, max_vertices: int, human_player: int):
    ai_player = 2 if human_player == 1 else 1

    def _selector(engine: PawnGame, state: GameState, valid_actions, turn_index: int):
        env_adapter = PawnReachabilityEnv(max_vertices=max_vertices)
        env_adapter.engine = engine
        env_adapter.state = state
        env_adapter.current_game = None
        action_masks = env_adapter.action_masks()

        obs = env_adapter._get_observation()
        action_id, _ = model.predict(obs, action_masks=action_masks, deterministic=True)
        command = env_adapter.action_to_command(int(action_id))

        if command not in valid_actions:
            if valid_actions:
                command = valid_actions[0]
            else:
                return None

        return command, f"RL chooses: {command}"

    return _selector


def play_vs_rl(model_path: Path, human_player: int, replay: bool, max_vertices: int) -> None:
    deps = _load_rl_dependencies()
    if not model_path.exists():
        raise FileNotFoundError(f"RL model not found: {model_path}")

    model = deps["MaskablePPO"].load(str(model_path))

    if replay:
        game_config = _load_last_config()
        print("Loaded previous setup using --replay.")
    else:
        game_config = build_game_configuration_interactively()
        _save_last_config(game_config)

    ai_player = 2 if human_player == 1 else 1
    print("\n--- Play vs RL Model ---")
    print(f"You are Player {human_player}; RL is Player {ai_player}.")
    print(f"Target vertex: {game_config['rules']['target_vertex']}")

    selector = _build_rl_action_selector(model, max_vertices=max_vertices, human_player=human_player)
    run_interactive_session(
        game_config,
        human_player=human_player,
        automated_action_selector=selector,
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Play against trained RL model.")
    parser.add_argument("--model", type=Path, required=True, help="Path to trained RL model (.zip).")
    parser.add_argument("--human-player", type=int, choices=[1, 2], default=1, help="Human-controlled player number.")
    parser.add_argument("--replay", action="store_true", help="Reuse previous setup and skip prompts.")
    parser.add_argument("--max-vertices", type=int, default=10, help="Max vertices used by RL action mapping.")
    return parser


if __name__ == "__main__":
    args = build_arg_parser().parse_args()
    play_vs_rl(
        model_path=args.model,
        human_player=args.human_player,
        replay=args.replay,
        max_vertices=args.max_vertices,
    )
