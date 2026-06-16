import argparse
import csv
import json
import random
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from Simulator.Graph_Generator import generate_vertex_labels
from Simulator.Two_Pawn_Simulator import PawnGame
from ML.feature_utils import (
    compute_static_features,
    compute_state_features,
    combine_features,
    ownership_to_color_groups,
)

GRABBING_RULES = [
    "always-grabbing",
    "always-grabbing-or-giving",
    "optional-grabbing",
    "k-grabbing",
]
OWNERSHIP_MECHANISMS = ["OVPP", "MVPP", "OMVPP"]


def _slugify(text: str) -> str:
    cleaned = []
    for ch in text.lower():
        if ch.isalnum():
            cleaned.append(ch)
        else:
            cleaned.append("-")
    slug = "".join(cleaned)
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug.strip("-")


def _resolve_output_dir(explicit_out_dir: Path, custom_tags: List[str], iterations: int) -> Path:
    if explicit_out_dir is not None:
        return explicit_out_dir
    if not custom_tags:
        return Path(f"ML/datasets/data_iter{iterations}")
    suffix = "-".join(custom_tags + [f"it-{iterations}"])
    return Path(f"ML/datasets/data_{suffix}")


def _validate_constraints(
    ownership_mechanism: str,
    vertex_count: int,
    vertex_min: int,
    vertex_max: int,
    target_index: int,
    grabbing_rule: str,
    k_grab_limit: int,
    edge_prob_min: float,
    edge_prob_max: float,
) -> None:
    if edge_prob_min <= 0 or edge_prob_max <= 0 or edge_prob_min > 1 or edge_prob_max > 1:
        raise ValueError("Edge probability bounds must be in (0, 1].")
    if edge_prob_min > edge_prob_max:
        raise ValueError("edge-prob-min cannot be greater than edge-prob-max.")

    if vertex_count is not None:
        if vertex_count < 2:
            raise ValueError("vertex-count must be at least 2.")
        if ownership_mechanism == "OVPP" and vertex_count != 3:
            raise ValueError("OVPP requires vertex-count to be exactly 3.")
    else:
        if vertex_min < 2 or vertex_max < 2 or vertex_min > vertex_max:
            raise ValueError("Invalid vertex range. Ensure 2 <= vertex-min <= vertex-max.")
        if ownership_mechanism == "OVPP" and (vertex_min > 3 or vertex_max < 3):
            raise ValueError("OVPP random generation requires vertex 3 to be included in range.")

    if target_index is not None and target_index < 2:
        raise ValueError("target-index must be at least 2 (start is index 1).")

    if grabbing_rule != "k-grabbing" and k_grab_limit is not None:
        raise ValueError("k-grab-limit can only be set when grabbing-rule is k-grabbing.")


def _build_random_graph(vertex_labels: List[str], edge_probability: float) -> Dict[str, List[str]]:
    graph: Dict[str, List[str]] = {v: [] for v in vertex_labels}
    for src in vertex_labels:
        for dst in vertex_labels:
            if src == dst:
                continue
            if random.random() < edge_probability:
                graph[src].append(dst)

    start = vertex_labels[0]
    if not graph[start] and len(vertex_labels) > 1:
        graph[start].append(random.choice(vertex_labels[1:]))

    return graph


def _generate_random_ownership(vertex_labels: List[str], mechanism: str) -> Dict[str, Set[str]]:
    colors = ["Red", "Blue", "Green"]

    if mechanism == "OVPP":
        if len(vertex_labels) != 3:
            raise ValueError("OVPP generation requires exactly 3 vertices in this simulator setup.")
        shuffled_vertices = vertex_labels[:]
        random.shuffle(shuffled_vertices)
        return {
            shuffled_vertices[0]: {"Red"},
            shuffled_vertices[1]: {"Blue"},
            shuffled_vertices[2]: {"Green"},
        }

    if mechanism == "MVPP":
        ownership = {}
        for label in vertex_labels:
            ownership[label] = {random.choice(colors)}
        return ownership

    ownership = {}
    overlap_added = False
    for label in vertex_labels:
        primary = random.choice(colors)
        picks = {primary}
        if random.random() < 0.35:
            picks.add(random.choice(colors))
        if len(picks) > 1:
            overlap_added = True
        ownership[label] = picks

    if not overlap_added and len(vertex_labels) > 0:
        chosen = random.choice(vertex_labels)
        extra_color = random.choice([c for c in colors if c not in ownership[chosen]])
        ownership[chosen].add(extra_color)

    return ownership


def _graph_edges_as_pairs(graph: Dict[str, List[str]], ordered_labels: List[str]) -> List[Tuple[int, int]]:
    label_to_index = {label: idx + 1 for idx, label in enumerate(ordered_labels)}
    pairs: List[Tuple[int, int]] = []
    for src in ordered_labels:
        for dst in graph.get(src, []):
            pairs.append((label_to_index[src], label_to_index[dst]))
    return pairs


def _simulate_random_game(
    graph: Dict[str, List[str]],
    ownership_map: Dict[str, Set[str]],
    target_vertex: str,
    grabbing_rule: str,
    ownership_mechanism: str,
    k_grab_limit: int,
    max_steps: int,
) -> Dict[str, Any]:
    engine = PawnGame(
        graph=graph,
        pawn_ownership=ownership_map,
        target_vertex=target_vertex,
        grabbing_rule=grabbing_rule,
        k_grab_limit=k_grab_limit,
    )

    state = engine.get_initial_state(
        start_vertex=sorted(graph.keys())[0],
        p1_initial_pawns={"Red", "Blue", "Green"},
        p2_initial_pawns=set(),
    )

    static_features = compute_static_features(
        graph=graph,
        ownership=ownership_map,
        target_vertex=target_vertex,
        grabbing_rule=grabbing_rule,
        ownership_mechanism=ownership_mechanism,
        k_grab_limit=k_grab_limit,
    )

    steps: List[Dict[str, Any]] = []
    state_rows: List[Dict[str, Any]] = []
    winner = "P2"
    termination = "no_valid_actions"

    for turn in range(1, max_steps + 1):
        valid_actions = engine.get_valid_actions(state)
        state_features = compute_state_features(graph, target_vertex, state)
        feature_row = combine_features(static_features, state_features, turn)
        feature_row["chosen_action"] = ""
        state_rows.append(feature_row)

        if engine.is_win(state):
            winner = "P1"
            termination = "p1_reached_target"
            break

        if not valid_actions:
            winner = "P2"
            termination = "no_valid_actions"
            break

        action = random.choice(valid_actions)
        state_rows[-1]["chosen_action"] = action

        pre_state = {
            "p1_pos": state.p1_pos,
            "p2_pos": state.p2_pos,
            "p1_pawns": sorted(list(state.p1_pawns)),
            "p2_pawns": sorted(list(state.p2_pawns)),
            "current_player": state.current_player,
            "phase": state.phase,
            "k_grabs_made": state.k_grabs_made,
        }

        state = engine.apply_action(state, action)

        steps.append(
            {
                "turn": turn,
                "valid_actions": valid_actions,
                "action": action,
                "before": pre_state,
                "after": {
                    "p1_pos": state.p1_pos,
                    "p2_pos": state.p2_pos,
                    "p1_pawns": sorted(list(state.p1_pawns)),
                    "p2_pawns": sorted(list(state.p2_pawns)),
                    "current_player": state.current_player,
                    "phase": state.phase,
                    "k_grabs_made": state.k_grabs_made,
                    "message": state.message,
                },
            }
        )

        if engine.is_win(state):
            winner = "P1"
            termination = "p1_reached_target"
            break
    else:
        winner = "P2"
        termination = "max_steps_reached"

    label = 1 if winner == "P1" else 0
    for row in state_rows:
        row["p1_wins"] = label

    return {
        "winner": winner,
        "termination": termination,
        "steps": steps,
        "state_rows": state_rows,
        "final_state": {
            "p1_pos": state.p1_pos,
            "p2_pos": state.p2_pos,
            "p1_pawns": sorted(list(state.p1_pawns)),
            "p2_pawns": sorted(list(state.p2_pawns)),
            "current_player": state.current_player,
            "phase": state.phase,
        },
    }


def generate_dataset(
    iterations: int,
    out_dir: Path,
    seed: int,
    max_steps: int,
    grabbing_rule: str,
    ownership_mechanism: str,
    vertex_count: int,
    vertex_min: int,
    vertex_max: int,
    target_index: int,
    k_grab_limit: int,
    edge_prob_min: float,
    edge_prob_max: float,
) -> None:
    random.seed(seed)
    out_dir.mkdir(parents=True, exist_ok=True)
    logs_dir = out_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    games_csv_path = out_dir / "games_dataset.csv"
    states_csv_path = out_dir / "states_dataset.csv"
    config_jsonl_path = out_dir / "game_configs.jsonl"

    game_rows: List[Dict[str, Any]] = []
    state_rows_all: List[Dict[str, Any]] = []

    with config_jsonl_path.open("w", encoding="utf-8") as config_jsonl:
        for i in range(1, iterations + 1):
            current_ownership_mechanism = ownership_mechanism or random.choice(OWNERSHIP_MECHANISMS)

            if vertex_count is not None:
                current_vertex_count = vertex_count
            elif current_ownership_mechanism == "OVPP":
                current_vertex_count = 3
            else:
                current_vertex_count = random.randint(vertex_min, vertex_max)

            labels = generate_vertex_labels(current_vertex_count)
            edge_prob = random.uniform(edge_prob_min, edge_prob_max)
            graph = _build_random_graph(labels, edge_prob)

            if target_index is not None:
                if target_index > current_vertex_count:
                    raise ValueError(
                        f"target-index {target_index} exceeds vertex count {current_vertex_count}."
                    )
                current_target_index = target_index
            else:
                current_target_index = random.randint(2, current_vertex_count)
            target_vertex = labels[current_target_index - 1]

            current_grabbing_rule = grabbing_rule or random.choice(GRABBING_RULES)
            if current_grabbing_rule == "k-grabbing":
                current_k_grab_limit = k_grab_limit if k_grab_limit is not None else random.randint(1, 4)
            else:
                current_k_grab_limit = 0

            ownership_map = _generate_random_ownership(labels, current_ownership_mechanism)

            simulation = _simulate_random_game(
                graph=graph,
                ownership_map=ownership_map,
                target_vertex=target_vertex,
                grabbing_rule=current_grabbing_rule,
                ownership_mechanism=current_ownership_mechanism,
                k_grab_limit=current_k_grab_limit,
                max_steps=max_steps,
            )

            edges_pairs = _graph_edges_as_pairs(graph, labels)
            color_groups = ownership_to_color_groups(ownership_map, labels)

            run_record = {
                "iteration": i,
                "seed": seed,
                "config": {
                    "vertex_count": current_vertex_count,
                    "edge_probability": edge_prob,
                    "vertices": labels,
                    "edges_numeric": edges_pairs,
                    "target_index": current_target_index,
                    "target_vertex": target_vertex,
                    "grabbing_rule": current_grabbing_rule,
                    "k_grab_limit": current_k_grab_limit,
                    "ownership_mechanism": current_ownership_mechanism,
                    "ownership_color_groups": color_groups,
                },
                "result": {
                    "winner": simulation["winner"],
                    "termination": simulation["termination"],
                    "turns": len(simulation["steps"]),
                    "final_state": simulation["final_state"],
                },
                "steps": simulation["steps"],
            }

            log_file = logs_dir / f"game_{i:06d}.json"
            with log_file.open("w", encoding="utf-8") as handle:
                json.dump(run_record, handle, indent=2)

            config_jsonl.write(json.dumps(run_record) + "\n")

            game_rows.append(
                {
                    "iteration": i,
                    "seed": seed,
                    "vertex_count": current_vertex_count,
                    "edge_count": len(edges_pairs),
                    "edge_probability": edge_prob,
                    "edges_numeric": json.dumps(edges_pairs),
                    "target_index": current_target_index,
                    "target_vertex": target_vertex,
                    "grabbing_rule": current_grabbing_rule,
                    "k_grab_limit": current_k_grab_limit,
                    "ownership_mechanism": current_ownership_mechanism,
                    "ownership_color_groups": json.dumps(color_groups),
                    "winner": simulation["winner"],
                    "termination": simulation["termination"],
                    "turns": len(simulation["steps"]),
                    "log_file": str(log_file.relative_to(out_dir)),
                }
            )

            for row in simulation["state_rows"]:
                row["iteration"] = i
                state_rows_all.append(row)

    if game_rows:
        with games_csv_path.open("w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=list(game_rows[0].keys()))
            writer.writeheader()
            writer.writerows(game_rows)

    if state_rows_all:
        with states_csv_path.open("w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=list(state_rows_all[0].keys()))
            writer.writeheader()
            writer.writerows(state_rows_all)

    print(f"Generated {iterations} games")
    print(f"Output directory: {out_dir}")
    print(f"Game-level dataset: {games_csv_path}")
    print(f"State-level dataset: {states_csv_path}")
    print(f"Detailed logs directory: {logs_dir}")
    print(f"JSONL log file: {config_jsonl_path}")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate iterative random dataset for Two Pawn games.")
    parser.add_argument("--iterations", type=int, default=500, help="Number of random game iterations.")
    parser.add_argument("--out-dir", type=Path, default=None, help="Output directory for datasets/logs.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed.")
    parser.add_argument("--max-steps", type=int, default=250, help="Max simulation steps per game.")
    parser.add_argument(
        "--grabbing-rule",
        choices=GRABBING_RULES,
        default=None,
        help="Fix grabbing rule. Default: random per iteration.",
    )
    parser.add_argument(
        "--ownership-mechanism",
        choices=OWNERSHIP_MECHANISMS,
        default=None,
        help="Fix ownership mechanism. Default: random per iteration.",
    )
    parser.add_argument("--vertex-count", type=int, default=None, help="Fix graph vertex count.")
    parser.add_argument("--vertex-min", type=int, default=4, help="Min vertices when vertex count is random.")
    parser.add_argument("--vertex-max", type=int, default=14, help="Max vertices when vertex count is random.")
    parser.add_argument("--target-index", type=int, default=None, help="Fix target vertex index (1-based).")
    parser.add_argument("--k-grab-limit", type=int, default=None, help="Fix k for k-grabbing mode.")
    parser.add_argument("--edge-prob-min", type=float, default=0.18, help="Min edge probability.")
    parser.add_argument("--edge-prob-max", type=float, default=0.42, help="Max edge probability.")
    return parser


if __name__ == "__main__":
    args = build_arg_parser().parse_args()

    _validate_constraints(
        ownership_mechanism=args.ownership_mechanism,
        vertex_count=args.vertex_count,
        vertex_min=args.vertex_min,
        vertex_max=args.vertex_max,
        target_index=args.target_index,
        grabbing_rule=args.grabbing_rule,
        k_grab_limit=args.k_grab_limit,
        edge_prob_min=args.edge_prob_min,
        edge_prob_max=args.edge_prob_max,
    )

    custom_tags: List[str] = []
    if args.grabbing_rule:
        custom_tags.append(f"gr-{_slugify(args.grabbing_rule)}")
    if args.ownership_mechanism:
        custom_tags.append(f"own-{_slugify(args.ownership_mechanism)}")
    if args.vertex_count is not None:
        custom_tags.append(f"v-{args.vertex_count}")
    else:
        if args.vertex_min != 4 or args.vertex_max != 14:
            custom_tags.append(f"v-{args.vertex_min}-{args.vertex_max}")
    if args.target_index is not None:
        custom_tags.append(f"t-{args.target_index}")
    if args.k_grab_limit is not None:
        custom_tags.append(f"k-{args.k_grab_limit}")
    if args.edge_prob_min != 0.18 or args.edge_prob_max != 0.42:
        custom_tags.append(f"e-{str(args.edge_prob_min).replace('.', 'p')}-{str(args.edge_prob_max).replace('.', 'p')}")

    resolved_out_dir = _resolve_output_dir(args.out_dir, custom_tags, args.iterations)

    generate_dataset(
        iterations=args.iterations,
        out_dir=resolved_out_dir,
        seed=args.seed,
        max_steps=args.max_steps,
        grabbing_rule=args.grabbing_rule,
        ownership_mechanism=args.ownership_mechanism,
        vertex_count=args.vertex_count,
        vertex_min=args.vertex_min,
        vertex_max=args.vertex_max,
        target_index=args.target_index,
        k_grab_limit=args.k_grab_limit,
        edge_prob_min=args.edge_prob_min,
        edge_prob_max=args.edge_prob_max,
    )
