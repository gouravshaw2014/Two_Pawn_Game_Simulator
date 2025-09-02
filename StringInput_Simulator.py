from typing import List, Dict, Set, Union
import matplotlib.pyplot as plt
from Simulator.Two_Pawn_Simulator import PawnGame, build_game_configuration_interactively
from Simulator.test_networkx import draw_game_state


def _parse_tokens(s: str) -> List[str]:
    # Spliting
    tokens: List[str] = []
    for part in s.replace(',', ' ').split():
        t = part.strip()
        if t:
            tokens.append(t)
    return tokens


def run_scripted_session(game_config: Dict):
    engine = PawnGame(**game_config['rules'])
    state = engine.get_initial_state(**game_config['initial'])

    print(f"Rules: Grabbing is '{engine.grabbing_rule}'", end="")
    if engine.grabbing_rule == 'k-grabbing':
        print(f" (k={engine.k_grab_limit})")
    else:
        print()

    # Inputs
    route_str = input("Enter P1's route (e.g., A C E Target): ")
    p2_str = input("Enter P2's grab order (e.g., Blue Red Green): ")

    route: List[str] = _parse_tokens(route_str)
    p2_grabs: List[str] = _parse_tokens(p2_str)

    if not route:
        print("No route provided.")
        return

    print(f"\nStart at: {state.p1_pos}")
    print(f"P1 initial pawns: {sorted(list(state.p1_pawns))}")
    print(f"P2 initial pawns: {sorted(list(state.p2_pawns))}")

    p2_idx = 0
    step = 1

    def end_with_status(status_text: str):
        if draw_game_state is not None:
            try:
                draw_game_state(engine.graph, engine.ownership, state, status=status_text)
                plt.pause(15)
            except Exception:
                pass
        print(status_text)

    for next_vertex in route:

        # Ensure it is P1's move phase before processing the next hop
        if state.current_player != 1 or state.phase != 'move':
            print(f"Unexpected game phase before step {step}: current_player={state.current_player}, phase={state.phase}")
            print("Cannot continue scripted run from a non-move phase for P1.")
            end_with_status("P2 wins.")
            return

        print(f"\nStep {step}: Attempt move to '{next_vertex}' from '{state.p1_pos}'")
        valid_actions = engine.get_valid_actions(state)
        move_cmd = f"move {next_vertex}"

        if move_cmd not in valid_actions:

            # Find reason
            current = state.p1_pos
            neighbors = set(engine.graph.get(current, []))
            if next_vertex not in neighbors:
                print(f"Blocked: No edge from '{current}' to '{next_vertex}'.")
                end_with_status("P2 wins.")
                return
            
            # Edge exists; check ownership requirement
            required: Set[str] = engine.ownership.get(next_vertex, set())
            have: Set[str] = state.p1_pawns
            if required and not (required & have):
                print(f"Blocked: '{next_vertex}' requires one of {sorted(list(required))}, but P1 has {sorted(list(have))}.")
                print(f"P2 currently has {sorted(list(state.p2_pawns))} (grabbed the needed color).")
            else:
                print(f"Blocked: Move to '{next_vertex}' is not permitted by the current rules from '{current}'.")
            end_with_status("P2 wins.")
            return

        # Apply the move
        state = engine.apply_action(state, move_cmd)
        print(f"Action: {state.message}")

        # Check for win immediately after P1 move
        if engine.is_win(state):
            end_with_status("P1 wins.")
            return

        # Handle P2's mandatory grab for 'always-grabbing'
        if engine.grabbing_rule == 'always-grabbing':
            # Expect it's now P2's turn, phase == 'grab'
            valid_actions = engine.get_valid_actions(state)
            grab_actions = [a for a in valid_actions if a.startswith('grab ')]

            if not grab_actions:
                # No grab possible (e.g., P1 has no pawns). Treat as continuation.
                print("Note: P2 had no valid grab actions.")
            else:
                if p2_idx >= len(p2_grabs):
                    print("Script ended: P2 was required to grab, but no more colors were provided.")
                    end_with_status("P2 wins.")
                    return
                requested = p2_grabs[p2_idx]
                p2_idx += 1
                cmd = f"grab {requested}"
                if cmd not in grab_actions:
                    print(f"Script mismatch: P2 attempted to '{cmd}', but valid grabs are: {grab_actions}.")
                    print(f"P1 currently has: {sorted(list(state.p1_pawns))}")
                    end_with_status("P2 wins.")
                    return
                state = engine.apply_action(state, cmd)
                print(f"Action: {state.message}")

        step += 1

    # Route exhausted
    if engine.is_win(state):
        end_with_status("P1 wins.")
    else:
        # Provide where we ended
        print(f"\nRoute exhausted at node '{state.p1_pos}'. Target not reached.")
        required_target = engine.ownership.get(engine.target_vertex, set())
        print(f"Target '{engine.target_vertex}' requires one of {sorted(list(required_target))}.")
        print(f"P1 now has: {sorted(list(state.p1_pawns))}")
        print(f"P2 now has: {sorted(list(state.p2_pawns))}")
        end_with_status("P2 wins.")


if __name__ == '__main__':
    # same configuration as the simulator
    game_config = build_game_configuration_interactively()
    run_scripted_session(game_config)
