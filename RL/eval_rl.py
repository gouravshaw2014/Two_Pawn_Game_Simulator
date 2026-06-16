import argparse
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


def _load_rl_dependencies():
    try:
        from sb3_contrib import MaskablePPO
        from sb3_contrib.common.maskable.utils import get_action_masks
    except ImportError as exc:
        raise RuntimeError(
            "Missing RL dependencies. Install with: pip install gymnasium stable-baselines3 sb3-contrib"
        ) from exc

    return {
        "MaskablePPO": MaskablePPO,
        "get_action_masks": get_action_masks,
    }


def evaluate(args):
    deps = _load_rl_dependencies()
    try:
        from RL.rl_env import PawnReachabilityEnv
    except ImportError:
        from rl_env import PawnReachabilityEnv

    model_path = Path(args.model)
    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")

    model = deps["MaskablePPO"].load(str(model_path))

    env = PawnReachabilityEnv(
        seed=args.seed,
        max_vertices=args.max_vertices,
        max_steps=args.max_steps,
        opponent_policy=args.opponent_policy,
        ownership_mechanism=args.ownership_mechanism,
        grabbing_rule=args.grabbing_rule,
        learning_player=args.learning_player,
        trace_dir=args.trace_dir,
        trace_prefix="eval",
        trace_max_episodes=args.trace_episodes,
    )

    wins = 0
    losses = 0
    truncated = 0
    total_reward = 0.0
    total_steps = 0

    for _ in range(args.episodes):
        obs, _ = env.reset()
        done = False
        episode_reward = 0.0
        episode_steps = 0

        while not done:
            action_masks = env.action_masks()
            action, _ = model.predict(obs, action_masks=action_masks, deterministic=args.deterministic)
            obs, reward, terminated, is_truncated, info = env.step(int(action))
            done = terminated or is_truncated
            episode_reward += reward
            episode_steps += 1

            if done:
                winner = info.get("winner", "P2")
                if winner == "P1":
                    wins += 1
                else:
                    losses += 1
                if is_truncated:
                    truncated += 1

        total_reward += episode_reward
        total_steps += episode_steps

    win_rate = wins / max(1, args.episodes)
    avg_reward = total_reward / max(1, args.episodes)
    avg_steps = total_steps / max(1, args.episodes)

    metrics = {
        "episodes": args.episodes,
        "wins_p1": wins,
        "losses_p1": losses,
        "truncated": truncated,
        "win_rate": win_rate,
        "accuracy_like_metric": win_rate,
        "avg_reward": avg_reward,
        "avg_steps": avg_steps,
        "model_path": str(model_path),
        "seed": args.seed,
        "deterministic": args.deterministic,
        "max_vertices": args.max_vertices,
        "max_steps": args.max_steps,
        "ownership_mechanism": args.ownership_mechanism,
        "grabbing_rule": args.grabbing_rule,
        "learning_player": args.learning_player,
    }

    output_dir = Path(args.output_dir) if args.output_dir else model_path.parent
    output_dir.mkdir(parents=True, exist_ok=True)

    metrics_json = output_dir / "rl_eval.metrics.json"
    metrics_txt = output_dir / "rl_eval.metrics.txt"
    metrics_json.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    metrics_txt.write_text(
        "RL Evaluation Metrics\n"
        f"Episodes: {args.episodes}\n"
        f"P1 Wins: {wins}\n"
        f"P1 Losses: {losses}\n"
        f"Win Rate (accuracy-like): {win_rate:.4f}\n"
        f"Average Reward: {avg_reward:.4f}\n"
        f"Average Steps: {avg_steps:.2f}\n",
        encoding="utf-8",
    )

    print(f"Evaluation metrics saved to: {metrics_json}")
    print(f"Evaluation summary saved to: {metrics_txt}")
    print(f"Win Rate (accuracy-like): {win_rate:.4f}")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Evaluate trained RL model.")
    parser.add_argument("--model", type=str, required=True, help="Path to RL model zip file.")
    parser.add_argument("--episodes", type=int, default=200, help="Evaluation episodes.")
    parser.add_argument("--seed", type=int, default=123, help="Evaluation seed.")
    parser.add_argument("--deterministic", action="store_true", help="Use deterministic policy actions.")
    parser.add_argument("--output-dir", type=str, default=None, help="Directory to write metrics files.")
    parser.add_argument("--max-vertices", type=int, default=10, help="Maximum sampled vertices.")
    parser.add_argument("--max-steps", type=int, default=200, help="Maximum steps per episode.")
    parser.add_argument("--opponent-policy", type=str, default="random", choices=["random"], help="Opponent policy.")
    parser.add_argument("--ownership-mechanism", type=str, default=None, choices=["OVPP", "MVPP", "OMVPP"], help="Fixed ownership mechanism for eval.")
    parser.add_argument("--grabbing-rule", type=str, default=None, choices=["always-grabbing", "always-grabbing-or-giving", "optional-grabbing", "k-grabbing"], help="Fixed grabbing rule for eval.")
    parser.add_argument("--learning-player", type=int, default=1, choices=[1, 2], help="Which player side the RL model controls during evaluation.")
    parser.add_argument("--trace-episodes", type=int, default=0, help="Save detailed traces for first N eval episodes.")
    parser.add_argument("--trace-dir", type=str, default=None, help="Directory for eval trace JSON files.")
    return parser


if __name__ == "__main__":
    parser = build_arg_parser()
    args = parser.parse_args()
    evaluate(args)
