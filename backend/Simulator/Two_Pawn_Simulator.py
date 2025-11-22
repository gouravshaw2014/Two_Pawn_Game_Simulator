from dataclasses import dataclass, field
from typing import Set, Dict, List, Union
import matplotlib.pyplot as plt
from .test_networkx import draw_game_state


@dataclass(frozen=True)
class GameState:
    """Represents a snapshot of the game state."""
    p1_pos: str
    p2_pos: str
    p1_pawns: Set[str]
    p2_pawns: Set[str]
    current_player: int
    phase: str = 'move'
    k_grabs_made: int = 0
    message: str = ""

class PawnGame:
    """The core game engine, supporting all specified rule variations."""
    def __init__(self, graph: Dict[str, List[str]], pawn_ownership: Dict[str, Union[str, Set[str]]], target_vertex: str, grabbing_rule: str, k_grab_limit: int = 0):
        self.graph = graph
        self.target_vertex = target_vertex
        self.grabbing_rule = grabbing_rule.lower()
        self.k_grab_limit = k_grab_limit
        self.ownership: Dict[str, Set[str]] = {}
        for vertex, pawns in pawn_ownership.items():
            if isinstance(pawns, str):
                self.ownership[vertex] = {pawns}
            else:
                self.ownership[vertex] = set(pawns)

    def get_initial_state(self, start_vertex: str, p1_initial_pawns: Set[str], p2_initial_pawns: Set[str]) -> GameState:
        return GameState(start_vertex, None, p1_initial_pawns, p2_initial_pawns, 1)


    def is_win(self, state: GameState) -> bool:
        target_pawns = self.ownership.get(self.target_vertex, set())
        return state.p1_pos == self.target_vertex and any(p in state.p1_pawns for p in target_pawns)

    def get_valid_actions(self, state: GameState) -> List[str]:
        actions = []
        player, opponent = (1, 2) if state.current_player == 1 else (2, 1)
        player_pos = state.p1_pos if player == 1 else state.p2_pos
        player_pawns = state.p1_pawns if player == 1 else state.p2_pawns
        opponent_pawns = state.p2_pawns if player == 1 else state.p1_pawns

        if state.phase == 'grab':
            for pawn in opponent_pawns: actions.append(f"grab {pawn}")
        elif state.phase == 'grab_or_give':
            for pawn in opponent_pawns: actions.append(f"grab {pawn}")
            for pawn in player_pawns: actions.append(f"give {pawn}")
        elif state.phase == 'k_grab':
            if state.k_grabs_made < self.k_grab_limit:
                for pawn in opponent_pawns: actions.append(f"grab {pawn}")
            actions.append("pass")
        elif state.phase == 'move':
            if player_pos in self.graph:
                for neighbor in self.graph[player_pos]:
                    pawns_needed = self.ownership.get(neighbor, set())
                    if any(p in player_pawns for p in pawns_needed):
                        actions.append(f"move {neighbor}")
            if self.grabbing_rule == 'optional-grabbing':
                for pawn in opponent_pawns: actions.append(f"grab {pawn}")

        # Deterministic ordering of actions for consistent UX across runs
        def _action_key(a: str):
            parts = a.split()
            cmd = parts[0]
            arg = parts[1] if len(parts) > 1 else ''
            return (cmd, arg)
        return sorted(actions, key=_action_key)

    def apply_action(self, state: GameState, action: str) -> GameState:
        parts = action.strip().split()
        command, arg = parts[0], parts[1] if len(parts) > 1 else None
        p1_pos, p2_pos = state.p1_pos, state.p2_pos
        p1_pawns, p2_pawns = set(state.p1_pawns), set(state.p2_pawns)
        current_player, next_player = state.current_player, 2 if state.current_player == 1 else 1
        next_phase, k_grabs_made, message = 'move', state.k_grabs_made, ""

        if command == "move":
            if current_player == 1: p1_pos = arg
            else: p2_pos = arg
            message = f"Player {current_player} moves to {arg}."
            if self.grabbing_rule == 'always-grabbing':
                next_phase = 'grab'
                message += f" Now Player {next_player} MUST grab a pawn."
            elif self.grabbing_rule == 'always-grabbing-or-giving':
                next_phase = 'grab_or_give'
                message += f" Now Player {next_player} MUST grab or give a pawn."
            elif self.grabbing_rule == 'k-grabbing' and current_player == 2:
                next_player, next_phase, k_grabs_made = 1, 'k_grab', 0
                message += f" Now Player 1 may grab up to {self.k_grab_limit} pawns."
        elif command == "grab":
            (grabber_pawns, giver_pawns) = (p1_pawns, p2_pawns) if current_player == 1 else (p2_pawns, p1_pawns)
            if arg in giver_pawns:
                giver_pawns.remove(arg); grabber_pawns.add(arg)
                message = f"Player {current_player} grabs the '{arg}' pawn."
                if state.phase == 'k_grab':
                    k_grabs_made += 1
                    if k_grabs_made < self.k_grab_limit and len(giver_pawns) > 0:
                        next_player, next_phase = current_player, 'k_grab'
                        message += f" ({k_grabs_made}/{self.k_grab_limit} grabs made)"
                    else:
                        message += " P1 ends their grabbing phase."; next_player = 2
            else: return state
        elif command == "give":
            (giver_pawns, grabber_pawns) = (p1_pawns, p2_pawns) if current_player == 1 else (p2_pawns, p1_pawns)
            if arg in giver_pawns:
                giver_pawns.remove(arg); grabber_pawns.add(arg)
                message = f"Player {current_player} gives the '{arg}' pawn."
            else: return state
        elif command == "pass" and state.phase == 'k_grab':
            message = "Player 1 passes their remaining grabs."; next_player = 2
        else: return state
        return GameState(p1_pos, p2_pos, p1_pawns, p2_pawns, next_player, next_phase, k_grabs_made, message)

def run_interactive_session(game_config):

    engine = PawnGame(**game_config['rules'])
    state = engine.get_initial_state(**game_config['initial'])

    print("\n" + "--- 2-Pawn Game Simulator ---")
    print(f"Rules: Grabbing is '{engine.grabbing_rule}'", end="")
    if engine.grabbing_rule == 'k-grabbing': print(f" (k={engine.k_grab_limit})")
    else: print()
    
    turn = 1
    while not engine.is_win(state):
        if draw_game_state is not None:
            try:
                draw_game_state(engine.graph, engine.ownership, state)
            except Exception as _e:
                # Continue without visualization
                pass

        print(f"\nTurn {turn}")
        print(f"  P1 Pos: {state.p1_pos} | P2 Pos: {state.p2_pos}")
        print(f"  P1 Pawns: {sorted(list(state.p1_pawns))} | P2 Pawns: {sorted(list(state.p2_pawns))}")
        print(f"\n Player {state.current_player}'s Turn (Phase: {state.phase})")
        
        valid_actions = engine.get_valid_actions(state)
        if not valid_actions:
            print("No valid actions available for P1.\n")
            print("P2 wins.")
            break
            
        print("Valid actions:", valid_actions)
        # display numbered options
        for i, act in enumerate(valid_actions, 1):
            print(f"  {i}. {act}")

        # Keep the visualization displayed until the next input is provided
        action_input = input("Enter your action (or number): ").strip()
        valid_actions_canonical = [a.lower() for a in valid_actions]
        chosen_action = None
        if action_input.isdigit():
            idx_num = int(action_input)
            if 1 <= idx_num <= len(valid_actions):
                chosen_action = valid_actions[idx_num - 1]
        if chosen_action is None:
            if action_input.lower() not in valid_actions_canonical:
                print("INVALID ACTION")
                continue
            chosen_action = valid_actions[valid_actions_canonical.index(action_input.lower())]

        state = engine.apply_action(state, chosen_action)
        print(f"\nAction taken: {state.message}")
        if state.phase != 'k_grab' or state.current_player != 1:
            turn += 1

    # Final draw when game ends (P1 win or P2 win), to reflect terminal state
    status_text = "P1 wins." if engine.is_win(state) else "P2 wins."
    if draw_game_state is not None:
        try:
            draw_game_state(engine.graph, engine.ownership, state, status=status_text)
            # Keep the final image open for 5 seconds
            plt.pause(5)
        except Exception:
            pass

    if engine.is_win(state):
        print(" P1 wins.")


def build_game_configuration_interactively():
    """Asks the user for game rules and builds the configuration dictionary."""
    
    # Base Game Data
    base_graph = { 'Start': ['A', 'B'], 
                  'A': ['C', 'E'], 
                  'B': ['E'], 
                  'C': [], 
                  'E': ['Target', 'D'], 
                  'D': [], 
                  'Target': [] }
    
    # If we can do the graph generation dynamically.
        # graph input code from gfg.
        # make UI for adjacency list, to form the lists from data taken by the user.
        # make an image which updates after each moves, which would show the progression of the graph as the user adds edges. Also, show the color of pawns which both the players have while the game goes on.
        

    initial_state_config = { 'start_vertex': 'Start', 'p1_initial_pawns': {'Red', 'Blue', 'Green'}, 'p2_initial_pawns': set() }
    
    # Predefined Ownership Models
    ownerships = {
        "1": ("One Vertex per Pawn (OVPP)", {'Start': 'Meta', 'A': 'Red', 'B': 'Blue', 'C':'Red', 'D':'Blue', 'E':'Green', 'Target':'Green'}),
        "2": ("Multiple Vertices per Pawn (MVPP)", {'A': 'Red', 'C': 'Red', 'B': 'Blue', 'D': 'Blue', 'E': 'Green', 'Target': 'Green'}),
        "3": ("Overlapping Multiple Vertices (OMVPP)", {'A': 'Red', 'C': 'Red', 'B': 'Blue', 'D': 'Blue', 'E': {'Green', 'Blue'}, 'Target': 'Green'})
    }

    # Predefined Grabbing Rules 
    grabbing_rules = {
        "1": "always-grabbing",
        "2": "always-grabbing-or-giving",
        "3": "optional-grabbing",
        "4": "k-grabbing"
    }

    # Setup
    print("--- Build Your Pawn Game Configuration ---")
    
    # 1. Choose Ownership Model
    print("\nStep 1: Choose an Ownership of Vertices model:")
    for key, (name, _) in ownerships.items():
        print(f"  {key}: {name}")
    choice = input("Enter your choice (1-3): ")
    selected_ownership = ownerships.get(choice, ownerships["2"])[1] # Default to MVPP

    # 2. Choose Grabbing Mechanism
    print("\nStep 2: Choose a Grabbing Mechanism:")
    for key, name in grabbing_rules.items():
        print(f"  {key}: {name.replace('-', ' ').title()}")
    choice = input("Enter your choice (1-4): ")
    selected_grabbing = grabbing_rules.get(choice, grabbing_rules["1"]) # Default to always-grabbing

    # 3. Handle k-Grabbing specific input
    k_limit = 0
    if selected_grabbing == 'k-grabbing':
        while True:
            try:
                k_limit = int(input("Enter the value for k (e.g., 2): "))
                if k_limit > 0:
                    break
                else:
                    print("Please enter a positive integer.")
            except ValueError:
                print("Invalid input. Please enter an integer.")

    # Final Configuration
    final_config = {
        'rules': {
            'graph': base_graph,
            'pawn_ownership': selected_ownership,
            'target_vertex': 'Target',
            'grabbing_rule': selected_grabbing,
            'k_grab_limit': k_limit
        },
        'initial': initial_state_config
    }
    return final_config


if __name__ == '__main__':
    game_config = build_game_configuration_interactively()
    run_interactive_session(game_config)