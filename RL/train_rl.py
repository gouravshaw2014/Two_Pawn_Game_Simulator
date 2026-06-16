import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import List

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


class LiveTrainingPlotCallback:
    def __init__(
        self,
        base_callback_cls,
        run_dir: Path,
        plot_every_episodes: int = 5,
        rolling_window: int = 50,
        output_filename: str = "live_training_plot.png",
        window_title: str = "RL Training Live Metrics",
    ):
        class _Impl(base_callback_cls):
            def __init__(self, outer):
                super().__init__(verbose=0)
                self.outer = outer
                self.enabled = True
                self.episode_rewards: List[float] = []
                self.episode_lengths: List[float] = []
                self._plt = None
                self.fig = None
                self.ax_reward = None
                self.ax_len = None
                self.reward_line = None
                self.reward_avg_line = None
                self.len_line = None
                self.len_avg_line = None

            def _on_training_start(self) -> None:
                try:
                    import matplotlib.pyplot as plt
                    self._plt = plt
                    if self.fig is not None:
                        return
                    plt.ion()
                    self.fig, (self.ax_reward, self.ax_len) = plt.subplots(2, 1, figsize=(8, 6))
                    self.fig.canvas.manager.set_window_title(self.outer.window_title)

                    self.reward_line, = self.ax_reward.plot([], [], label="Episode Reward", color="tab:blue")
                    self.reward_avg_line, = self.ax_reward.plot([], [], label=f"Reward MA({self.outer.rolling_window})", color="tab:orange")
                    self.ax_reward.set_title("Episode Reward")
                    self.ax_reward.set_xlabel("Episode")
                    self.ax_reward.set_ylabel("Reward")
                    self.ax_reward.legend()

                    self.len_line, = self.ax_len.plot([], [], label="Episode Length", color="tab:green")
                    self.len_avg_line, = self.ax_len.plot([], [], label=f"Length MA({self.outer.rolling_window})", color="tab:red")
                    self.ax_len.set_title("Episode Length")
                    self.ax_len.set_xlabel("Episode")
                    self.ax_len.set_ylabel("Steps")
                    self.ax_len.legend()

                    self.fig.tight_layout()
                except Exception:
                    self.enabled = False

            def _moving_average(self, values: List[float], window: int) -> List[float]:
                if not values:
                    return []
                ma = []
                for idx in range(len(values)):
                    start = max(0, idx - window + 1)
                    segment = values[start:idx + 1]
                    ma.append(sum(segment) / len(segment))
                return ma

            def _refresh_plot(self):
                if not self.enabled or self.fig is None:
                    return

                episodes = list(range(1, len(self.episode_rewards) + 1))
                reward_ma = self._moving_average(self.episode_rewards, self.outer.rolling_window)
                len_ma = self._moving_average(self.episode_lengths, self.outer.rolling_window)

                self.reward_line.set_data(episodes, self.episode_rewards)
                self.reward_avg_line.set_data(episodes, reward_ma)
                self.len_line.set_data(episodes, self.episode_lengths)
                self.len_avg_line.set_data(episodes, len_ma)

                self.ax_reward.relim()
                self.ax_reward.autoscale_view()
                self.ax_len.relim()
                self.ax_len.autoscale_view()

                self.fig.canvas.draw_idle()
                self.fig.canvas.flush_events()
                self._plt.pause(0.001)

            def _on_step(self) -> bool:
                infos = self.locals.get("infos", [])
                if infos:
                    for info in infos:
                        episode = info.get("episode")
                        if episode:
                            self.episode_rewards.append(float(episode.get("r", 0.0)))
                            self.episode_lengths.append(float(episode.get("l", 0.0)))

                if self.enabled and self.episode_rewards and len(self.episode_rewards) % self.outer.plot_every_episodes == 0:
                    self._refresh_plot()

                return True

            def _on_training_end(self) -> None:
                if not self.enabled or self.fig is None:
                    return
                self._refresh_plot()
                output_path = self.outer.run_dir / self.outer.output_filename
                self.fig.savefig(output_path, dpi=140)

        self.run_dir = run_dir
        self.plot_every_episodes = max(1, int(plot_every_episodes))
        self.rolling_window = max(2, int(rolling_window))
        self.output_filename = output_filename
        self.window_title = window_title
        self.impl = _Impl(self)


def _load_rl_dependencies():
    try:
        from sb3_contrib import MaskablePPO
        from sb3_contrib.common.maskable.callbacks import MaskableEvalCallback
        from sb3_contrib.common.maskable.utils import get_action_masks
        from stable_baselines3.common.callbacks import BaseCallback, CallbackList
        from stable_baselines3.common.monitor import Monitor
    except ImportError as exc:
        raise RuntimeError(
            "Missing RL dependencies. Install with: pip install gymnasium stable-baselines3 sb3-contrib"
        ) from exc

    return {
        "MaskablePPO": MaskablePPO,
        "MaskableEvalCallback": MaskableEvalCallback,
        "get_action_masks": get_action_masks,
        "BaseCallback": BaseCallback,
        "CallbackList": CallbackList,
        "Monitor": Monitor,
    }


def _resolve_run_dir(run_name: str | None, total_timesteps: int) -> Path:
    if run_name:
        return Path("RL/runs") / run_name
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return Path("RL/runs") / f"run_{stamp}_it{total_timesteps}"


def _safe_learn(model, *, total_timesteps: int, progress_bar: bool, **learn_kwargs):
    try:
        model.learn(total_timesteps=total_timesteps, progress_bar=progress_bar, **learn_kwargs)
    except ImportError as exc:
        if progress_bar:
            print(
                "Progress bar dependencies are unavailable. "
                "Retrying without progress bar. "
                "Install with: pip install tqdm rich"
            )
            model.learn(total_timesteps=total_timesteps, progress_bar=False, **learn_kwargs)
            return
        raise exc


def _global_update_count(model, n_steps: int) -> int:
    step_size = max(1, int(n_steps))
    return int(model.num_timesteps // step_size)


def train_rl(args):
    deps = _load_rl_dependencies()
    try:
        from RL.rl_env import PawnReachabilityEnv
    except ImportError:
        from rl_env import PawnReachabilityEnv

    run_dir = _resolve_run_dir(args.run_name, args.total_timesteps)
    run_dir.mkdir(parents=True, exist_ok=True)

    def _build_env(seed_offset: int, learning_player: int, trace_prefix: str):
        env_obj = PawnReachabilityEnv(
            seed=args.seed + seed_offset,
            max_vertices=args.max_vertices,
            max_steps=args.max_steps,
            opponent_policy=args.opponent_policy,
            ownership_mechanism=args.ownership_mechanism,
            grabbing_rule=args.grabbing_rule,
            learning_player=learning_player,
            trace_dir=str(run_dir / "traces") if args.trace_episodes > 0 else None,
            trace_prefix=trace_prefix,
            trace_max_episodes=args.trace_episodes,
        )
        return env_obj

    def _build_model(env_obj, seed_value: int):
        return deps["MaskablePPO"](
            policy="MlpPolicy",
            env=deps["Monitor"](env_obj),
            learning_rate=args.learning_rate,
            n_steps=args.n_steps,
            batch_size=args.batch_size,
            gamma=args.gamma,
            gae_lambda=0.95,
            ent_coef=0.01,
            vf_coef=0.5,
            max_grad_norm=0.5,
            verbose=1,
            device=args.device,
            seed=seed_value,
            tensorboard_log=str(run_dir / "tb") if args.tensorboard else None,
        )

    if args.self_play:
        p1_env = _build_env(seed_offset=0, learning_player=1, trace_prefix="train_p1")
        p2_env = _build_env(seed_offset=1, learning_player=2, trace_prefix="train_p2")

        p1_model = _build_model(p1_env, args.seed)
        p2_model = _build_model(p2_env, args.seed + 1)

        p1_callback = None
        p2_callback = None
        if args.live_plot:
            p1_live_plot = LiveTrainingPlotCallback(
                base_callback_cls=deps["BaseCallback"],
                run_dir=run_dir,
                plot_every_episodes=args.plot_every_episodes,
                rolling_window=args.plot_rolling_window,
                output_filename="live_training_plot_p1.png",
                window_title="RL Self-Play Live Metrics (P1)",
            )
            p2_live_plot = LiveTrainingPlotCallback(
                base_callback_cls=deps["BaseCallback"],
                run_dir=run_dir,
                plot_every_episodes=args.plot_every_episodes,
                rolling_window=args.plot_rolling_window,
                output_filename="live_training_plot_p2.png",
                window_title="RL Self-Play Live Metrics (P2)",
            )
            p1_callback = p1_live_plot.impl
            p2_callback = p2_live_plot.impl

        round_steps = max(1, args.total_timesteps // max(1, args.self_play_rounds))

        for _round in range(1, args.self_play_rounds + 1):
            print(f"\n=== Self-play round {_round}/{args.self_play_rounds}: Training P1 specialist ===")
            p1_updates_before = _global_update_count(p1_model, args.n_steps)
            p1_env.set_opponent_model(p2_model, deterministic=True)
            _safe_learn(
                p1_model,
                total_timesteps=round_steps,
                reset_num_timesteps=False,
                callback=p1_callback,
                progress_bar=args.progress_bar,
            )
            p1_updates_after = _global_update_count(p1_model, args.n_steps)
            print(
                f"P1 cumulative updates: {p1_updates_after} "
                f"(added {p1_updates_after - p1_updates_before}), total_timesteps={p1_model.num_timesteps}"
            )

            print(f"\n=== Self-play round {_round}/{args.self_play_rounds}: Training P2 specialist ===")
            p2_updates_before = _global_update_count(p2_model, args.n_steps)
            p2_env.set_opponent_model(p1_model, deterministic=True)
            _safe_learn(
                p2_model,
                total_timesteps=round_steps,
                reset_num_timesteps=False,
                callback=p2_callback,
                progress_bar=args.progress_bar,
            )
            p2_updates_after = _global_update_count(p2_model, args.n_steps)
            print(
                f"P2 cumulative updates: {p2_updates_after} "
                f"(added {p2_updates_after - p2_updates_before}), total_timesteps={p2_model.num_timesteps}"
            )

        final_model_path = run_dir / "p1_specialist.zip"
        p1_model.save(str(final_model_path))
        p2_model_path = run_dir / "p2_specialist.zip"
        p2_model.save(str(p2_model_path))
    else:
        env = _build_env(seed_offset=0, learning_player=1, trace_prefix="train")
        eval_env = deps["Monitor"](_build_env(seed_offset=1, learning_player=1, trace_prefix="eval"))

        model = _build_model(env, args.seed)

        eval_callback = deps["MaskableEvalCallback"](
            eval_env=eval_env,
            best_model_save_path=str(run_dir / "best_model"),
            log_path=str(run_dir / "eval"),
            eval_freq=max(2000, args.n_steps),
            deterministic=True,
            render=False,
            n_eval_episodes=args.eval_episodes,
        )

        callbacks = [eval_callback]
        if args.live_plot:
            live_plot = LiveTrainingPlotCallback(
                base_callback_cls=deps["BaseCallback"],
                run_dir=run_dir,
                plot_every_episodes=args.plot_every_episodes,
                rolling_window=args.plot_rolling_window,
            )
            callbacks.append(live_plot.impl)

        callback = callbacks[0] if len(callbacks) == 1 else deps["CallbackList"](callbacks)

        _safe_learn(
            model,
            total_timesteps=args.total_timesteps,
            callback=callback,
            progress_bar=args.progress_bar,
        )
        final_model_path = run_dir / "rl_model.zip"
        model.save(str(final_model_path))

    metadata = {
        "run_dir": str(run_dir),
        "model_path": str(final_model_path),
        "total_timesteps": args.total_timesteps,
        "seed": args.seed,
        "max_vertices": args.max_vertices,
        "max_steps": args.max_steps,
        "opponent_policy": args.opponent_policy,
        "ownership_mechanism": args.ownership_mechanism,
        "grabbing_rule": args.grabbing_rule,
        "learning_rate": args.learning_rate,
        "n_steps": args.n_steps,
        "batch_size": args.batch_size,
        "gamma": args.gamma,
        "device": args.device,
        "self_play": args.self_play,
        "self_play_rounds": args.self_play_rounds,
        "trace_episodes": args.trace_episodes,
    }

    metadata_path = run_dir / "run_metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    print(f"RL model saved to: {final_model_path}")
    if args.self_play:
        print(f"P2 specialist saved to: {run_dir / 'p2_specialist.zip'}")
    print(f"Run metadata: {metadata_path}")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Train RL model for Two Pawn reachability game.")
    parser.add_argument("--total-timesteps", dest="total_timesteps", type=int, default=200000, help="Total RL training timesteps.")
    parser.add_argument("--timesteps", dest="total_timesteps", type=int, help=argparse.SUPPRESS)
    parser.add_argument("--seed", type=int, default=42, help="Random seed.")
    parser.add_argument("--run-name", type=str, default=None, help="Optional run directory name under RL/runs.")
    parser.add_argument("--max-vertices", type=int, default=10, help="Maximum vertices in sampled games.")
    parser.add_argument("--max-steps", type=int, default=200, help="Max steps per episode.")
    parser.add_argument("--opponent-policy", type=str, default="random", choices=["random"], help="Opponent policy.")
    parser.add_argument("--ownership-mechanism", type=str, default=None, choices=["OVPP", "MVPP", "OMVPP"], help="Fix ownership mechanism during training.")
    parser.add_argument("--grabbing-rule", type=str, default=None, choices=["always-grabbing", "always-grabbing-or-giving", "optional-grabbing", "k-grabbing"], help="Fix grabbing rule during training.")
    parser.add_argument("--learning-rate", type=float, default=3e-4, help="Learning rate.")
    parser.add_argument("--n-steps", type=int, default=1024, help="Rollout steps per update.")
    parser.add_argument("--batch-size", type=int, default=256, help="Batch size.")
    parser.add_argument("--gamma", type=float, default=0.99, help="Discount factor.")
    parser.add_argument("--device", type=str, default="auto", choices=["auto", "cpu", "cuda"], help="Training device selection.")
    parser.add_argument("--eval-episodes", type=int, default=30, help="Eval episodes during training.")
    parser.add_argument("--trace-episodes", type=int, default=0, help="Save detailed trace JSON files for first N episodes.")
    parser.add_argument("--self-play", action="store_true", help="Train two specialists (P1 and P2) in alternating self-play rounds.")
    parser.add_argument("--self-play-rounds", type=int, default=10, help="Alternating rounds in self-play mode.")
    parser.add_argument("--tensorboard", action="store_true", help="Enable tensorboard logging under run_dir/tb.")
    parser.add_argument("--progress-bar", action="store_true", help="Enable SB3 progress bar (requires tqdm and rich).")
    parser.add_argument("--live-plot", action="store_true", help="Show live matplotlib plots while training.")
    parser.add_argument("--plot-every-episodes", type=int, default=5, help="Refresh live plot every N finished episodes.")
    parser.add_argument("--plot-rolling-window", type=int, default=50, help="Rolling average window for live plot curves.")
    return parser


if __name__ == "__main__":
    parser = build_arg_parser()
    args = parser.parse_args()
    train_rl(args)
