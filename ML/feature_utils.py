from collections import deque
from typing import Dict, List, Set, Any


def _label_to_index_map(graph: Dict[str, List[str]]) -> Dict[str, int]:
    ordered = sorted(graph.keys())
    return {label: idx + 1 for idx, label in enumerate(ordered)}


def _distance_to_target(graph: Dict[str, List[str]], start: str, target: str) -> int:
    if start == target:
        return 0
    visited = {start}
    queue = deque([(start, 0)])
    while queue:
        node, dist = queue.popleft()
        for nxt in graph.get(node, []):
            if nxt in visited:
                continue
            if nxt == target:
                return dist + 1
            visited.add(nxt)
            queue.append((nxt, dist + 1))
    return -1


def compute_static_features(
    graph: Dict[str, List[str]],
    ownership: Dict[str, Set[str]],
    target_vertex: str,
    grabbing_rule: str,
    ownership_mechanism: str,
    k_grab_limit: int,
) -> Dict[str, Any]:
    vertex_count = len(graph)
    edge_count = sum(len(v) for v in graph.values())
    max_edges = vertex_count * (vertex_count - 1) if vertex_count > 1 else 1
    density = edge_count / max_edges
    index_map = _label_to_index_map(graph)

    overlap_vertices = sum(1 for colors in ownership.values() if len(colors) > 1)

    return {
        "vertex_count": vertex_count,
        "edge_count": edge_count,
        "edge_density": density,
        "target_index": index_map.get(target_vertex, -1),
        "grabbing_rule": grabbing_rule,
        "ownership_mechanism": ownership_mechanism,
        "k_grab_limit": k_grab_limit,
        "overlap_vertex_count": overlap_vertices,
        "red_vertex_count": sum(1 for c in ownership.values() if "Red" in c),
        "blue_vertex_count": sum(1 for c in ownership.values() if "Blue" in c),
        "green_vertex_count": sum(1 for c in ownership.values() if "Green" in c),
    }


def compute_state_features(
    graph: Dict[str, List[str]],
    target_vertex: str,
    state,
) -> Dict[str, Any]:
    p1_pos = getattr(state, "p1_pos", None)
    p1_pawns = set(getattr(state, "p1_pawns", set()))
    p2_pawns = set(getattr(state, "p2_pawns", set()))

    return {
        "current_player": getattr(state, "current_player", -1),
        "phase": getattr(state, "phase", "unknown"),
        "k_grabs_made": getattr(state, "k_grabs_made", 0),
        "p1_pawn_count": len(p1_pawns),
        "p2_pawn_count": len(p2_pawns),
        "p1_has_red": int("Red" in p1_pawns),
        "p1_has_blue": int("Blue" in p1_pawns),
        "p1_has_green": int("Green" in p1_pawns),
        "p2_has_red": int("Red" in p2_pawns),
        "p2_has_blue": int("Blue" in p2_pawns),
        "p2_has_green": int("Green" in p2_pawns),
        "distance_to_target": _distance_to_target(graph, p1_pos, target_vertex) if p1_pos else -1,
        "out_degree_p1_pos": len(graph.get(p1_pos, [])) if p1_pos else 0,
        "is_at_target": int(p1_pos == target_vertex),
    }


def combine_features(static_features: Dict[str, Any], state_features: Dict[str, Any], turn_index: int) -> Dict[str, Any]:
    merged = {**static_features, **state_features}
    merged["turn_index"] = turn_index
    return merged


def ownership_to_color_groups(ownership: Dict[str, Set[str]], ordered_labels: List[str]) -> Dict[str, List[int]]:
    label_to_index = {label: idx + 1 for idx, label in enumerate(ordered_labels)}
    groups = {"Red": [], "Blue": [], "Green": []}
    for label, colors in ownership.items():
        idx = label_to_index[label]
        for color in colors:
            if color in groups:
                groups[color].append(idx)

    for color in groups:
        groups[color] = sorted(groups[color])
    return groups
