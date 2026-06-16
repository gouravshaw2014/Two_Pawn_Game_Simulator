import random
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple, Any

import numpy as np

try:
    import gymnasium as gym
    from gymnasium import spaces
except ImportError:
    gym = None
    spaces = None

from Simulator.Graph_Generator import generate_vertex_labels
from Simulator.Two_Pawn_Simulator import PawnGame, GameState

GRABBING_RULES = [
    "always-grabbing",
    "always-grabbing-or-giving",
    "optional-grabbing",
    "k-grabbing",
]
OWNERSHIP_MECHANISMS = ["OVPP", "MVPP", "OMVPP"]
PAWN_COLORS = ["Red", "Blue", "Green"]
PHASES = ["move", "grab", "grab_or_give", "k_grab"]


@dataclass
class RLGameConfig:
    graph: Dict[str, List[str]]
    ownership: Dict[str, Set[str]]
    target_vertex: str
    start_vertex: str
    grabbing_rule: str
    ownership_mechanism: str
    k_grab_limit: int


def _build_random_graph(vertex_labels: List[str], edge_probability: float, rng: random.Random) -> Dict[str, List[str]]:
    graph: Dict[str, List[str]] = {v: [] for v in vertex_labels}
    for src in vertex_labels:
        for dst in vertex_labels:
            if src == dst:
                continue
            if rng.random() < edge_probability:
                graph[src].append(dst)

    start = vertex_labels[0]
    if not graph[start] and len(vertex_labels) > 1:
        graph[start].append(rng.choice(vertex_labels[1:]))
    return graph


def _generate_random_ownership(vertex_labels: List[str], mechanism: str, rng: random.Random) -> Dict[str, Set[str]]:
    ownership = {label: set() for label in vertex_labels}

    if mechanism == "OVPP":
        if len(vertex_labels) < 4:
            raise ValueError("OVPP requires at least 4 vertices (neutral start + 3 owned vertices).")
        owned_vertices = vertex_labels[1:4]
        shuffled_colors = PAWN_COLORS[:]
        rng.shuffle(shuffled_colors)
        for idx, vertex in enumerate(owned_vertices):
            ownership[vertex] = {shuffled_colors[idx]}
        return ownership

    if mechanism == "MVPP":
        for vertex in vertex_labels[1:]:
            ownership[vertex] = {rng.choice(PAWN_COLORS)}
        return ownership

    overlap_added = False
    for vertex in vertex_labels[1:]:
        colors = {rng.choice(PAWN_COLORS)}
        if rng.random() < 0.35:
            colors.add(rng.choice(PAWN_COLORS))
        if len(colors) > 1:
            overlap_added = True
        ownership[vertex] = colors

    if not overlap_added and len(vertex_labels) > 2:
        chosen = rng.choice(vertex_labels[1:])
        extra = rng.choice([c for c in PAWN_COLORS if c not in ownership[chosen]])
        ownership[chosen].add(extra)

    return ownership


def sample_random_game_config(
    rng: random.Random,
    max_vertices: int,
    ownership_mechanism: Optional[str] = None,
    grabbing_rule: Optional[str] = None,
    edge_prob_min: float = 0.18,
    edge_prob_max: float = 0.42,
    vertex_min: int = 4,
    vertex_max: int = 10,
    target_index: Optional[int] = None,
    k_grab_limit: Optional[int] = None,
) -> RLGameConfig:
    current_ownership = ownership_mechanism or rng.choice(OWNERSHIP_MECHANISMS)

    if current_ownership == "OVPP":
        vertex_count = 4
    else:
        upper = min(max_vertices, max(vertex_min, vertex_max))
        lower = min(vertex_min, upper)
        vertex_count = rng.randint(lower, upper)

    labels = generate_vertex_labels(vertex_count)
    graph = _build_random_graph(labels, rng.uniform(edge_prob_min, edge_prob_max), rng)

    if target_index is not None:
        if target_index < 2 or target_index > vertex_count:
            raise ValueError(f"target_index {target_index} out of range for vertex_count={vertex_count}")
        chosen_target_index = target_index
    else:
        chosen_target_index = rng.randint(2, vertex_count)

    target_vertex = labels[chosen_target_index - 1]
    current_grabbing = grabbing_rule or rng.choice(GRABBING_RULES)
    current_k = k_grab_limit if current_grabbing == "k-grabbing" and k_grab_limit is not None else 0
    if current_grabbing == "k-grabbing" and current_k <= 0:
        current_k = rng.randint(1, 4)

    ownership = _generate_random_ownership(labels, current_ownership, rng)
    if not ownership.get(target_vertex):
        ownership[target_vertex] = {"Green"}

    return RLGameConfig(
        graph=graph,
        ownership=ownership,
        target_vertex=target_vertex,
        start_vertex=labels[0],
        grabbing_rule=current_grabbing,
        ownership_mechanism=current_ownership,
        k_grab_limit=current_k,
    )


_BaseEnv = gym.Env if gym is not None else object


class PawnReachabilityEnv(_BaseEnv):
    metadata = {"render_modes": ["human"]}

    def __init__(
        self,
        seed: int = 42,
        max_vertices: int = 10,
        max_steps: int = 200,
        opponent_policy: str = "random",
        fixed_game_config: Optional[RLGameConfig] = None,
        ownership_mechanism: Optional[str] = None,
        grabbing_rule: Optional[str] = None,
        learning_player: int = 1,
        trace_dir: Optional[str] = None,
        trace_prefix: str = "episode_trace",
        trace_max_episodes: int = 0,
    ):
        if gym is None or spaces is None:
            raise RuntimeError(
                "Missing RL dependencies. Install with: pip install gymnasium stable-baselines3 sb3-contrib"
            )
        super().__init__()
        self.rng = random.Random(seed)
        self.max_vertices = max_vertices
        self.max_steps = max_steps
        self.opponent_policy = opponent_policy
        self.learning_player = learning_player
        self.fixed_game_config = fixed_game_config
        self.fixed_ownership_mechanism = ownership_mechanism
        self.fixed_grabbing_rule = grabbing_rule
        self.opponent_model = None
        self.opponent_deterministic = True

        self.trace_dir = Path(trace_dir) if trace_dir else None
        self.trace_prefix = trace_prefix
        self.trace_max_episodes = max(0, int(trace_max_episodes))
        self.trace_written_count = 0
        self._episode_trace: List[Dict[str, Any]] = []
        self._episode_index = 0
        if self.trace_dir:
            self.trace_dir.mkdir(parents=True, exist_ok=True)

        self.action_space = spaces.Discrete(self.max_vertices + 7)
        self.observation_space = spaces.Box(low=-1.0, high=1.0, shape=(25,), dtype=np.float32)

        self.engine: Optional[PawnGame] = None
        self.state: Optional[GameState] = None
        self.current_game: Optional[RLGameConfig] = None
        self.turn_count = 0

    def set_opponent_model(self, model, deterministic: bool = True):
        self.opponent_model = model
        self.opponent_deterministic = deterministic

    def clear_opponent_model(self):
        self.opponent_model = None

    def _snapshot_state(self) -> Dict[str, Any]:
        assert self.state is not None
        return {
            "p1_pos": self.state.p1_pos,
            "p2_pos": self.state.p2_pos,
            "p1_pawns": sorted(list(self.state.p1_pawns)),
            "p2_pawns": sorted(list(self.state.p2_pawns)),
            "current_player": self.state.current_player,
            "phase": self.state.phase,
            "k_grabs_made": self.state.k_grabs_made,
        }

    def _trace_event(self, event: Dict[str, Any]):
        if self.trace_max_episodes <= 0:
            return
        self._episode_trace.append(event)

    def _flush_episode_trace(self, winner: str, reason: str, episode_reward: float):
        if self.trace_max_episodes <= 0:
            return
        if self.trace_written_count >= self.trace_max_episodes:
            return
        if self.trace_dir is None:
            return

        payload = {
            "episode": self._episode_index,
            "learning_player": self.learning_player,
            "winner": winner,
            "reason": reason,
            "episode_reward": episode_reward,
            "steps": self._episode_trace,
            "config": {
                "target_vertex": self.current_game.target_vertex if self.current_game else None,
                "grabbing_rule": self.current_game.grabbing_rule if self.current_game else None,
                "ownership_mechanism": self.current_game.ownership_mechanism if self.current_game else None,
                "k_grab_limit": self.current_game.k_grab_limit if self.current_game else 0,
            },
        }
        file_path = self.trace_dir / f"{self.trace_prefix}_{self._episode_index:06d}.json"
        file_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        self.trace_written_count += 1

    def _label_order(self) -> List[str]:
        assert self.engine is not None
        return sorted(self.engine.graph.keys())

    def _label_to_index(self, label: Optional[str]) -> int:
        if label is None:
            return 0
        order = self._label_order()
        try:
            return order.index(label) + 1
        except ValueError:
            return 0

    def action_to_command(self, action_id: int) -> Optional[str]:
        if self.engine is None:
            return None
        labels = self._label_order()

        if 0 <= action_id < self.max_vertices:
            idx = action_id + 1
            if idx <= len(labels):
                return f"move {labels[idx - 1]}"
            return None

        base = self.max_vertices
        if base <= action_id < base + 3:
            color = PAWN_COLORS[action_id - base]
            return f"grab {color}"

        base += 3
        if base <= action_id < base + 3:
            color = PAWN_COLORS[action_id - base]
            return f"give {color}"

        if action_id == self.max_vertices + 6:
            return "pass"

        return None

    def command_to_action(self, command: str) -> Optional[int]:
        if self.engine is None:
            return None
        labels = self._label_order()

        parts = command.split()
        if not parts:
            return None

        cmd = parts[0]
        arg = parts[1] if len(parts) > 1 else None

        if cmd == "move" and arg in labels:
            return labels.index(arg)
        if cmd == "grab" and arg in PAWN_COLORS:
            return self.max_vertices + PAWN_COLORS.index(arg)
        if cmd == "give" and arg in PAWN_COLORS:
            return self.max_vertices + 3 + PAWN_COLORS.index(arg)
        if cmd == "pass":
            return self.max_vertices + 6

        return None

    def action_masks(self) -> np.ndarray:
        mask = np.zeros(self.action_space.n, dtype=bool)
        if self.engine is None or self.state is None:
            return mask

        valid_actions = self.engine.get_valid_actions(self.state)
        for action in valid_actions:
            action_id = self.command_to_action(action)
            if action_id is not None:
                mask[action_id] = True
        return mask

    def _phase_one_hot(self, phase: str) -> List[float]:
        return [1.0 if phase == p else 0.0 for p in PHASES]

    def _infer_ownership_mechanism(self) -> str:
        assert self.engine is not None
        owned_vertices = [
            colors for label, colors in self.engine.ownership.items() if label in self.engine.graph and len(colors) > 0
        ]
        if not owned_vertices:
            return "MVPP"
        if all(len(colors) == 1 for colors in owned_vertices):
            color_counts = {"Red": 0, "Blue": 0, "Green": 0}
            for colors in owned_vertices:
                color = next(iter(colors))
                if color in color_counts:
                    color_counts[color] += 1
            if len(owned_vertices) == 3 and all(v == 1 for v in color_counts.values()):
                return "OVPP"
            return "MVPP"
        return "OMVPP"

    def _distance_to_target(self, start: str, target: str) -> int:
        if start == target:
            return 0
        visited = {start}
        queue: List[Tuple[str, int]] = [(start, 0)]
        while queue:
            node, dist = queue.pop(0)
            for nxt in self.engine.graph.get(node, []):
                if nxt in visited:
                    continue
                if nxt == target:
                    return dist + 1
                visited.add(nxt)
                queue.append((nxt, dist + 1))
        return -1

    def _get_observation(self) -> np.ndarray:
        assert self.engine is not None and self.state is not None
        graph = self.engine.graph
        edge_count = sum(len(v) for v in graph.values())
        vertex_count = len(graph)
        max_edges = max(1, vertex_count * (vertex_count - 1))

        if self.learning_player == 1:
            agent_pos = self.state.p1_pos
            agent_pawns = self.state.p1_pawns
            opponent_pawns = self.state.p2_pawns
        else:
            agent_pos = self.state.p2_pos
            agent_pawns = self.state.p2_pawns
            opponent_pawns = self.state.p1_pawns

        pos_for_graph = agent_pos if agent_pos in graph else self.state.p1_pos
        dist = self._distance_to_target(pos_for_graph, self.engine.target_vertex) if pos_for_graph else -1
        out_degree = len(graph.get(pos_for_graph, [])) if pos_for_graph else 0

        ownership_overlap = sum(1 for colors in self.engine.ownership.values() if len(colors) > 1)
        ownership_mechanism = self.current_game.ownership_mechanism if self.current_game is not None else self._infer_ownership_mechanism()

        obs = [
            float(vertex_count / max(1, self.max_vertices)),
            float(edge_count / max_edges),
            float(self._label_to_index(self.engine.target_vertex) / max(1, self.max_vertices)),
            float(GRABBING_RULES.index(self.engine.grabbing_rule) / max(1, len(GRABBING_RULES) - 1)),
            float(OWNERSHIP_MECHANISMS.index(ownership_mechanism) / max(1, len(OWNERSHIP_MECHANISMS) - 1)),
            float(self.engine.k_grab_limit / 5.0),
            float(ownership_overlap / max(1, vertex_count)),
            float(self.state.current_player == self.learning_player),
            *self._phase_one_hot(self.state.phase),
            float(self._label_to_index(pos_for_graph) / max(1, self.max_vertices)),
            float("Red" in agent_pawns),
            float("Blue" in agent_pawns),
            float("Green" in agent_pawns),
            float("Red" in opponent_pawns),
            float("Blue" in opponent_pawns),
            float("Green" in opponent_pawns),
            float(len(agent_pawns) / 3.0),
            float(len(opponent_pawns) / 3.0),
            float(-1 if dist < 0 else dist / max(1, self.max_vertices)),
            float(out_degree / max(1, self.max_vertices - 1)),
            float(self.turn_count / max(1, self.max_steps)),
            float(pos_for_graph == self.engine.target_vertex),
        ]
        return np.array(obs, dtype=np.float32)

    def _select_opponent_action(self, valid_actions: List[str]) -> Optional[str]:
        if not valid_actions:
            return None
        if self.opponent_model is not None:
            action_masks = self.action_masks()
            obs = self._get_observation()
            action_id, _ = self.opponent_model.predict(obs, action_masks=action_masks, deterministic=self.opponent_deterministic)
            command = self.action_to_command(int(action_id))
            if command in valid_actions:
                return command
        if self.opponent_policy == "random":
            return self.rng.choice(valid_actions)
        return self.rng.choice(valid_actions)

    def reset(self, *, seed: Optional[int] = None, options: Optional[dict] = None):
        if seed is not None:
            self.rng.seed(seed)

        if self.fixed_game_config is not None:
            game_config = self.fixed_game_config
        else:
            game_config = sample_random_game_config(
                rng=self.rng,
                max_vertices=self.max_vertices,
                ownership_mechanism=self.fixed_ownership_mechanism,
                grabbing_rule=self.fixed_grabbing_rule,
            )

        self.current_game = game_config
        self.engine = PawnGame(
            graph=game_config.graph,
            pawn_ownership=game_config.ownership,
            target_vertex=game_config.target_vertex,
            grabbing_rule=game_config.grabbing_rule,
            k_grab_limit=game_config.k_grab_limit,
        )
        self.state = self.engine.get_initial_state(
            start_vertex=game_config.start_vertex,
            p1_initial_pawns={"Red", "Blue", "Green"},
            p2_initial_pawns=set(),
        )
        self.turn_count = 0
        self._episode_index += 1
        self._episode_trace = []

        while self.state.current_player != self.learning_player:
            opp_valid = self.engine.get_valid_actions(self.state)
            if not opp_valid:
                break
            opp_action = self._select_opponent_action(opp_valid)
            if opp_action is None:
                break
            before = self._snapshot_state()
            self.state = self.engine.apply_action(self.state, opp_action)
            self._trace_event({
                "turn": self.turn_count,
                "actor": "opponent",
                "action": opp_action,
                "before": before,
                "after": self._snapshot_state(),
            })

        return self._get_observation(), {}

    def step(self, action: int):
        assert self.engine is not None and self.state is not None

        self.turn_count += 1
        done = False
        truncated = False
        reward = -0.01
        episode_reward = 0.0
        info: Dict[str, Any] = {}

        valid_actions = self.engine.get_valid_actions(self.state)
        chosen_command = self.action_to_command(action)

        if not valid_actions:
            winner = "P1" if self.learning_player == 1 else "P2"
            loss_winner = "P2" if winner == "P1" else "P1"
            info = {"winner": loss_winner, "reason": "no_valid_actions"}
            self._flush_episode_trace(winner=loss_winner, reason="no_valid_actions", episode_reward=-1.0)
            return self._get_observation(), -1.0, True, False, info

        if chosen_command not in valid_actions:
            winner = "P1" if self.learning_player == 1 else "P2"
            loss_winner = "P2" if winner == "P1" else "P1"
            info = {"winner": loss_winner, "reason": "invalid_action"}
            self._flush_episode_trace(winner=loss_winner, reason="invalid_action", episode_reward=-1.0)
            return self._get_observation(), -1.0, True, False, info

        pre_dist = self._distance_to_target(self.state.p1_pos, self.engine.target_vertex)
        before = self._snapshot_state()
        self.state = self.engine.apply_action(self.state, chosen_command)
        self._trace_event({
            "turn": self.turn_count,
            "actor": "learner",
            "action": chosen_command,
            "before": before,
            "after": self._snapshot_state(),
        })

        if self.engine.is_win(self.state):
            p1_won = True
            learner_won = (self.learning_player == 1 and p1_won) or (self.learning_player == 2 and not p1_won)
            reward = 1.0 if learner_won else -1.0
            done = True
            info["winner"] = "P1"
            info["reason"] = "p1_reached_target"

        if not done:
            post_dist = self._distance_to_target(self.state.p1_pos, self.engine.target_vertex)
            if pre_dist >= 0 and post_dist >= 0 and post_dist < pre_dist:
                reward += 0.03

        while not done and self.state.current_player != self.learning_player:
            opp_valid = self.engine.get_valid_actions(self.state)
            if not opp_valid:
                reward = 1.0
                done = True
                info["winner"] = "P1" if self.learning_player == 1 else "P2"
                info["reason"] = "no_valid_actions"
                break
            opp_action = self._select_opponent_action(opp_valid)
            before_opp = self._snapshot_state()
            self.state = self.engine.apply_action(self.state, opp_action)
            self._trace_event({
                "turn": self.turn_count,
                "actor": "opponent",
                "action": opp_action,
                "before": before_opp,
                "after": self._snapshot_state(),
            })

            if self.engine.is_win(self.state):
                p1_won = True
                learner_won = (self.learning_player == 1 and p1_won) or (self.learning_player == 2 and not p1_won)
                reward = 1.0 if learner_won else -1.0
                done = True
                info["winner"] = "P1"
                info["reason"] = "p1_reached_target"
                break

        if not done and self.turn_count >= self.max_steps:
            truncated = True
            done = True
            reward = -0.5
            info["winner"] = "P2" if self.learning_player == 1 else "P1"
            info["reason"] = "max_steps_reached"

        episode_reward += reward
        if done:
            self._flush_episode_trace(
                winner=info.get("winner", "P2"),
                reason=info.get("reason", "unknown"),
                episode_reward=episode_reward,
            )

        return self._get_observation(), reward, done, truncated, info

    def render(self):
        return None
