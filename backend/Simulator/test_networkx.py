import networkx as nx
import matplotlib.pyplot as plt
from typing import Dict, List, Set, Union


global engine, _pos_cache, _current_fig, _current_ax

#  manage persistent figure between updates
_current_fig = None
_current_ax = None
_pos_cache = None  # cache positions to avoid jitter between draws
_p1_text_artist = None
_p2_text_artist = None
_keep_on_top = True
_status_text_artist = None


# keep the figure window on top depending on backend
def _set_window_on_top(manager, on: bool = True) -> None:
    try:
        win = manager.window
    except Exception:
        return
    # Tk backend
    try:
        if hasattr(win, 'attributes'):
            win.attributes('-topmost', 1 if on else 0)
            if on:
                if hasattr(win, 'deiconify'):
                    win.deiconify()
                if hasattr(win, 'lift'):
                    win.lift()
            return
    except Exception:
        pass
    # Qt backend (PyQt5 / PySide2)
    try:
        # Try PyQt5 first
        from PyQt5 import QtCore  # type: ignore
        flags = win.windowFlags()
        if on:
            win.setWindowFlags(flags | QtCore.Qt.WindowStaysOnTopHint)
        else:
            win.setWindowFlags(flags & ~QtCore.Qt.WindowStaysOnTopHint)
        win.show()
        return
    except Exception:
        try:
            from PySide2 import QtCore  # type: ignore
            flags = win.windowFlags()
            if on:
                win.setWindowFlags(flags | QtCore.Qt.WindowStaysOnTopHint)
            else:
                win.setWindowFlags(flags & ~QtCore.Qt.WindowStaysOnTopHint)
            win.show()
            return
        except Exception:
            pass
    # wx backend
    try:
        if on and hasattr(win, 'SetWindowStyleFlag') and hasattr(win, 'GetWindowStyleFlag'):
            win.SetWindowStyleFlag(win.GetWindowStyleFlag() | 0x4000)  # wx.STAY_ON_TOP
            if hasattr(win, 'Raise'):
                win.Raise()
        return
    except Exception:
        pass

# Optional public toggle; call set_keep_on_top(False) from client code to disable
def set_keep_on_top(on: bool) -> None:
    global _keep_on_top
    _keep_on_top = bool(on)
    if _current_fig is not None:
        try:
            _set_window_on_top(_current_fig.canvas.manager, _keep_on_top)
        except Exception:
            pass


def _compute_positions(G: Union[nx.Graph, nx.DiGraph]):
    """Compute and cache node positions for a consistent layout across draws.
       Deterministic BFS-based layered layout
    """
    global _pos_cache
    nodes = list(G.nodes)
    if not nodes:
        return {}

    if _pos_cache is None or set(_pos_cache.get('nodes', [])) != set(nodes):
        pos = None

        if pos is None:
            # BFS-based layered layout
            # Determine roots (in-degree 0 for DiGraph; else any node)
            if isinstance(G, nx.DiGraph):
                roots = [n for n, d in G.in_degree() if d == 0]
            else:
                roots = list(G.nodes)[:1]
            if not roots:
                roots = list(G.nodes)[:1]

            # BFS to assign levels
            from collections import deque
            level = {n: None for n in G.nodes}
            q = deque()
            for r in roots:
                level[r] = 0
                q.append(r)
            while q:
                u = q.popleft()
                for v in G.successors(u) if isinstance(G, nx.DiGraph) else G.neighbors(u):
                    if level[v] is None or (level[u] is not None and level[v] > level[u] + 1):
                        level[v] = (level[u] or 0) + 1
                        q.append(v)

            # Unreached nodes -> next available level
            max_level = max([lv for lv in level.values() if lv is not None] or [0])
            for n in nodes:
                if level[n] is None:
                    max_level += 1
                    level[n] = max_level

            # Group nodes by level and assign coordinates
            by_level = {}
            for n in nodes:
                by_level.setdefault(level[n], []).append(n)

            pos = {}
            dx, dy = 3.0, 1.8  # spacing
            for L in sorted(by_level.keys()):
                layer_nodes = sorted(by_level[L])
                # center nodes vertically around 0
                offset = - (len(layer_nodes) - 1) * dy / 2.0
                for i, n in enumerate(layer_nodes):
                    pos[n] = (L * dx, offset + i * dy)

        _pos_cache = {'nodes': nodes, 'pos': pos}
    return _pos_cache['pos']


def draw_game_state(graph: Dict[str, List[str]],
                    ownership: Dict[str, Union[str, Set[str]]],
                    state,
                    status: str = None) -> plt.Figure:
    """
    Draw the current game graph with colored vertices and overlay text showing
    what colors P1 and P2 have.

    Parameters:
      - graph: adjacency list as a dict
      - ownership: mapping vertex -> required/owned pawn color(s)
      - state: object having attributes p1_pos, p2_pos, p1_pawns, p2_pawns

    Returns:
      Figure used for the drawing.
    """
    global _current_fig, _current_ax

    # Build a directed graph based on adjacency list
    G = nx.DiGraph()
    for u, nbrs in graph.items():
        if u not in G:
            G.add_node(u)
        for v in nbrs:
            G.add_edge(u, v)

            # NetworkX auto-adds nodes when adding edges; no extra add_node needed.

    pos = _compute_positions(G)

    # Normalize ownership colors to actual matplotlib colors
    base_color_map = {
        'red': 'red', 'blue': 'blue', 'green': 'green',
        'Red': 'red', 'Blue': 'blue', 'Green': 'green',
        'Meta': 'gray', 'meta': 'gray'
    }

    node_colors: List[str] = []
    for n in G.nodes:
        own = ownership.get(n)
        color = 'lightgray'
        if isinstance(own, set):
            if len(own) == 1:
                only = next(iter(own))
                color = base_color_map.get(only, 'lightgray')
            elif len(own) > 1:
                # overlapping ownership; display as a distinctive color
                color = 'purple'
        elif isinstance(own, str):
            color = base_color_map.get(own, 'lightgray')
        node_colors.append(color)

    # Create or reuse a single persistent figure
    global _first_shown
    if _current_fig is None or _current_ax is None:
        _current_fig, _current_ax = plt.subplots(figsize=(7.5, 5.5))
        # Show the window once without blocking
        try:
            # Set a descriptive window title if supported
            # try:
            #     _current_fig.canvas.manager.set_window_title("Two Pawn Game")
            # except Exception:
            #     pass
            _current_fig.show()
            # Keep on top so focusing the terminal won't minimize the figure
            try:
                _set_window_on_top(_current_fig.canvas.manager, _keep_on_top)
            except Exception:
                pass
            # Try to place the window on the right side of the screen
            try:
                win = _current_fig.canvas.manager.window
                sw = win.winfo_screenwidth() if hasattr(win, 'winfo_screenwidth') else None
                sh = win.winfo_screenheight() if hasattr(win, 'winfo_screenheight') else None
                w, h = 1000, 800
                if sw and sh and hasattr(win, 'wm_geometry'):
                    x = int(sw * 0.55)
                    y = int(sh * 0.05)
                    win.wm_geometry(f"{w}x{h}+{x}+{y}")
            except Exception:
                pass
        except Exception:
            pass
    else:
        _current_ax.clear()
    ax = _current_ax

    # Draw components
    nx.draw_networkx_edges(G, pos, ax=ax, arrows=True, arrowstyle='-|>', arrowsize=40, width=1.5)
    nx.draw_networkx_nodes(G, pos, ax=ax, node_color=node_colors, node_size=800, edgecolors='black')
    nx.draw_networkx_labels(G, pos, ax=ax, font_size=10)

    # Highlight player positions with colored outlines (gold: P1, cyan: P2) P2 only grabs for now so no need afaik
    p1_pos = getattr(state, 'p1_pos', None)
    # p2_pos = getattr(state, 'p2_pos', None)
    if p1_pos:
        nx.draw_networkx_nodes(G, pos, nodelist=[p1_pos], node_size=1000, node_color='none', edgecolors='gold', linewidths=5, ax=ax)
    # if p2_pos:
    #     nx.draw_networkx_nodes(G, pos, nodelist=[p2_pos], node_size=1000, node_color='none', edgecolors='cyan', linewidths=3, ax=ax)

    ax.set_axis_off()

    # Two lines of overlay text for players' current pawn colors
    p1_text = f"P1 has: {', '.join(sorted(list(getattr(state, 'p1_pawns', []))))}"
    p2_text = f"P2 has: {', '.join(sorted(list(getattr(state, 'p2_pawns', []))))}"

    # Place/update text in figure coordinates (top-left) without stacking
    global _p1_text_artist, _p2_text_artist
    bbox = dict(boxstyle='round', facecolor='white', alpha=0.7, edgecolor='none')
    if _p1_text_artist is None:
        _p1_text_artist = _current_fig.text(0.01, 0.98, p1_text, va='top', ha='left', fontsize=11, bbox=bbox, zorder=10)
    else:
        _p1_text_artist.set_text(p1_text)
    if _p2_text_artist is None:
        _p2_text_artist = _current_fig.text(0.01, 0.93, p2_text, va='top', ha='left', fontsize=11, bbox=bbox, zorder=10)
    else:
        _p2_text_artist.set_text(p2_text)

    # Status overlay ("P2 wins" or "P1 wins") placed at top-right
    global _status_text_artist
    if status:
        s = status.lower().strip()
        # print(s)
        color = 'crimson' if 'p2' in s else 'green'
        bbox2 = dict(boxstyle='round', facecolor='white', alpha=0.8, edgecolor='none')
        
        if _status_text_artist is None:
            _status_text_artist = _current_fig.text(0.99, 0.98, status, va='top', ha='right', fontsize=13, fontweight='bold', color=color, bbox=bbox2, zorder=11)
        else:
            _status_text_artist.set_text(status)
            _status_text_artist.set_color(color)
    else:
        # Clear previous status if any
        if _status_text_artist is not None:
            _status_text_artist.set_text("")

    plt.tight_layout()
    # Update the existing window without blocking
    _current_fig.canvas.draw_idle()
    _current_fig.canvas.flush_events()
    plt.pause(0.001)

    return _current_fig


