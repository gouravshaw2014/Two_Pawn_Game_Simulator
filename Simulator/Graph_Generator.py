import re
from typing import Dict, List, Set, Tuple

PAWN_COLORS = ["Red", "Blue", "Green"]
OWNERSHIP_PRESETS = {
    "1": "OVPP",
    "2": "MVPP",
    "3": "OMVPP",
}


def generate_vertex_labels(vertex_count: int) -> List[str]:
    if vertex_count <= 0:
        raise ValueError("vertex_count must be a positive integer")

    labels: List[str] = []
    for i in range(vertex_count):
        n = i
        label = ""
        while True:
            n, rem = divmod(n, 26)
            label = chr(ord('A') + rem) + label
            if n == 0:
                break
            n -= 1
        labels.append(label)
    return labels


def parse_numeric_edges(edges_text: str, vertex_count: int) -> List[Tuple[int, int]]:
    pairs = re.findall(r"[\{\(\[]\s*(\d+)\s*,\s*(\d+)\s*[\}\)\]]", edges_text)
    if not pairs:
        raise ValueError("No valid edges found. Use format like {1,2},{2,3}")

    parsed: List[Tuple[int, int]] = []
    for a_str, b_str in pairs:
        a, b = int(a_str), int(b_str)
        if a < 1 or a > vertex_count or b < 1 or b > vertex_count:
            raise ValueError(f"Edge {{{a},{b}}} is out of range. Valid vertices are 1..{vertex_count}.")
        parsed.append((a, b))
    return parsed


def build_directed_graph(vertex_count: int, edges: List[Tuple[int, int]]) -> Dict[str, List[str]]:
    labels = generate_vertex_labels(vertex_count)
    graph: Dict[str, List[str]] = {label: [] for label in labels}

    for src_num, dst_num in edges:
        src = labels[src_num - 1]
        dst = labels[dst_num - 1]
        if dst not in graph[src]:
            graph[src].append(dst)

    return graph


def generate_ownership_map(vertex_labels: List[str], model: str) -> Dict[str, Set[str]]:
    if not vertex_labels:
        raise ValueError("vertex_labels cannot be empty")

    ownership: Dict[str, Set[str]] = {}
    count = len(vertex_labels)

    if model == "1":
        for i, vertex in enumerate(vertex_labels):
            ownership[vertex] = {PAWN_COLORS[i % len(PAWN_COLORS)]}
        return ownership

    if model == "2":
        block_size = max(1, count // len(PAWN_COLORS))
        for i, vertex in enumerate(vertex_labels):
            color_index = min(i // block_size, len(PAWN_COLORS) - 1)
            ownership[vertex] = {PAWN_COLORS[color_index]}
        return ownership

    for i, vertex in enumerate(vertex_labels):
        base = PAWN_COLORS[i % len(PAWN_COLORS)]
        if i % 4 == 0:
            overlap = PAWN_COLORS[(i + 1) % len(PAWN_COLORS)]
            ownership[vertex] = {base, overlap}
        else:
            ownership[vertex] = {base}
    return ownership


def parse_color_group_ownership_input(ownership_text: str, vertex_count: int, vertex_labels: List[str]) -> Dict[str, Set[str]]:
    pattern = r"(?i)\b(red|blue|green)\s*:\s*[\{\[\(]\s*([^\}\]\)]*?)\s*[\}\]\)]"
    matches = re.findall(pattern, ownership_text)
    if not matches:
        raise ValueError(
            "No valid ownership groups found. Use format like Red:{1,4}, Blue:{2,5}, Green:{3}."
        )

    seen_colors = set()
    ownership: Dict[str, Set[str]] = {label: set() for label in vertex_labels}

    for color_raw, indices_text in matches:
        color = color_raw.capitalize()
        color_key = color.lower()
        if color_key in seen_colors:
            raise ValueError(f"Duplicate color group '{color}'. Provide each color only once.")
        seen_colors.add(color_key)

        index_tokens = [token.strip() for token in indices_text.split(',') if token.strip()]
        for token in index_tokens:
            if not token.isdigit():
                raise ValueError(f"Invalid vertex index '{token}' in {color} group.")
            vertex_index = int(token)
            if vertex_index < 1 or vertex_index > vertex_count:
                raise ValueError(
                    f"Vertex index {vertex_index} is out of range. Valid vertices are 1..{vertex_count}."
                )
            label = vertex_labels[vertex_index - 1]
            ownership[label].add(color)

    start_label = vertex_labels[0]
    missing_vertices = []
    for idx, label in enumerate(vertex_labels, 1):
        if label == start_label:
            continue
        if not ownership[label]:
            missing_vertices.append(str(idx))

    if missing_vertices:
        raise ValueError(
            "Each non-start vertex must belong to at least one color. Missing indices: " + ", ".join(missing_vertices)
        )

    return ownership


def validate_ownership_by_preset(ownership: Dict[str, Set[str]], preset: str, start_vertex: str) -> None:
    owned_vertices = {vertex: colors for vertex, colors in ownership.items() if vertex != start_vertex and len(colors) > 0}

    if preset == "1":
        if len(owned_vertices) != 3:
            raise ValueError(
                "OVPP requires exactly 3 owned vertices (one for each pawn color: Red, Blue, Green), with Start neutral."
            )
        for vertex, colors in owned_vertices.items():
            if len(colors) != 1:
                raise ValueError(f"OVPP requires exactly one color per vertex. Vertex '{vertex}' has {sorted(list(colors))}.")
        for color in PAWN_COLORS:
            count = sum(1 for colors in owned_vertices.values() if color in colors)
            if count != 1:
                raise ValueError(f"OVPP requires color '{color}' to appear exactly once, but found {count} times.")
        return

    if preset == "2":
        for vertex, colors in owned_vertices.items():
            if len(colors) != 1:
                raise ValueError(
                    f"MVPP does not allow overlap; vertex '{vertex}' has multiple colors {sorted(list(colors))}."
                )
        return

    if preset == "3":
        overlap_count = sum(1 for colors in owned_vertices.values() if len(colors) > 1)
        if overlap_count == 0:
            raise ValueError("OMVPP requires at least one overlapping vertex (a vertex with multiple colors).")
        return

    raise ValueError("Invalid ownership preset.")


def build_graph_interactively() -> Dict[str, object]:
    while True:
        try:
            vertex_count = int(input("Enter number of vertices: ").strip())
            if vertex_count <= 0:
                print("Please enter a positive integer.")
                continue
            break
        except ValueError:
            print("Invalid input. Please enter an integer.")

    labels = generate_vertex_labels(vertex_count)
    print("\nVertex index mapping:")
    print(", ".join([f"{idx + 1}:{label}" for idx, label in enumerate(labels)]))

    while True:
        edges_text = input("Enter directed edges like {1,2},{2,3}: ").strip()
        try:
            edges = parse_numeric_edges(edges_text, vertex_count)
            break
        except ValueError as exc:
            print(str(exc))

    default_target_index = vertex_count
    while True:
        target_input = input(
            f"Enter target vertex number (1-{vertex_count}) [default {default_target_index}]: "
        ).strip()
        if target_input == "":
            target_index = default_target_index
            break
        try:
            target_index = int(target_input)
            if 1 <= target_index <= vertex_count:
                break
            print(f"Please enter a value between 1 and {vertex_count}.")
        except ValueError:
            print("Invalid input. Please enter an integer.")

    graph = build_directed_graph(vertex_count, edges)
    target_vertex = labels[target_index - 1]

    print("\nChoose ownership preset:")
    print("  1: OVPP (Start neutral + exactly 3 owned vertices; each color used once, no overlap)")
    print("  2: MVPP (no overlap; each vertex has exactly one color)")
    print("  3: OMVPP (overlap allowed and required)")
    while True:
        ownership_preset = input("Enter preset (1-3): ").strip()
        if ownership_preset in OWNERSHIP_PRESETS:
            break
        print("Invalid preset. Please enter 1, 2, or 3.")

    print("Enter ownership by color groups. Example: Red:{2,4}, Blue:{3,5}, Green:{6}")
    print("Start vertex is neutral by default, so index 1 can be omitted.")
    print("You can overlap ownership by repeating indices across color groups.")
    while True:
        ownership_text = input("Ownership: ").strip()
        try:
            ownership_map = parse_color_group_ownership_input(ownership_text, vertex_count, labels)
            validate_ownership_by_preset(ownership_map, ownership_preset, labels[0])
            break
        except ValueError as exc:
            print(str(exc))

    print(f"Start vertex: {labels[0]} | Target vertex: {target_vertex}")
    return {
        "graph": graph,
        "vertex_labels": labels,
        "start_vertex": labels[0],
        "target_vertex": target_vertex,
        "ownership_map": ownership_map,
        "ownership_preset": OWNERSHIP_PRESETS[ownership_preset],
    }
