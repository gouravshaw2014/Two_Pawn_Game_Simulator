from collections import deque

class InteractivePawnGame:
    def __init__(self):
        self.graph = {
            'Start': ['A', 'B'],
            'A': ['C', 'E'],
            'B': ['E'],
            'C': [],
            'E': ['Target', 'D'],
            'D': [],
            'Target': []
        }

        self.ownership = {
            'A': 'red', 'C': 'red',
            'B': 'blue', 'D': 'blue',
            'E': 'green', 'Target': 'green'
        }

        self.color_sets = {
            'red': {'A', 'C'},
            'blue': {'B', 'D'},
            'green': {'E', 'Target'}
        }

        self.p1_pos = 'Start'
        self.p2_pos = 'Start'
        self.p1_colors = set()
        self.p2_colors = set()
        self.p1_last_color = None
        self.p2_last_color = None

    def is_color_blocked(self, color, blocker_pos):
        return blocker_pos in self.color_sets[color]

    def print_state(self):
        print(f"\nP1 at {self.p1_pos}, owns: {self.p1_colors}")
        print(f"P2 at {self.p2_pos}, owns: {self.p2_colors}")
        print(f"Available moves from {self.p1_pos}: {self.graph[self.p1_pos]}")
        print("Available colors to grab:")
        for color, nodes in self.color_sets.items():
            if color not in self.p1_colors and not self.is_color_blocked(color, self.p2_pos):
                print(f"  - {color} ({nodes})")

    def move_player(self, player):
        current_pos = self.p1_pos if player == 1 else self.p2_pos
        current_colors = self.p1_colors if player == 1 else self.p2_colors
        opponent_colors = self.p2_colors if player == 1 else self.p1_colors
        opponent_pos = self.p2_pos if player == 1 else self.p1_pos
        last_color = self.p1_last_color if player == 1 else self.p2_last_color

        while True:
            if player == 1:
                self.print_state()
            choice = input(f"\nPlayer {player}: Enter 'move <to>' or 'grab <color>': ").strip().split()

            if not choice or len(choice) != 2:
                print("Invalid input.")
                continue

            cmd, arg = choice[0], choice[1]

            if cmd == 'move':
                if arg not in self.graph[current_pos]:
                    print("Invalid move. Not a neighbor.")
                    continue
                color = self.ownership.get(arg)
                if color not in current_colors and color in opponent_colors:
                    print("That color is currently owned by the other player. You cannot move there.")
                    continue

                if arg == opponent_pos:
                    print("That vertex is occupied by the other player.")
                    continue
                if player == 1:
                    self.p1_pos = arg
                else:
                    self.p2_pos = arg
                break

            elif cmd == 'grab':
                if arg not in self.color_sets:
                    print("Invalid color.")
                    continue
                if arg in current_colors:
                    print("You already control this color.")
                    continue
                if self.is_color_blocked(arg, opponent_pos):
                    print("Cannot grab this color. Blocked by opponent.")
                    continue
                if player == 1:
                    if self.p1_last_color and not self.is_color_blocked(self.p1_last_color, self.p2_pos):
                        self.p1_colors.discard(self.p1_last_color)
                        self.p2_colors.add(self.p1_last_color)
                    self.p1_colors.add(arg)
                    self.p1_last_color = arg
                else:
                    if self.p2_last_color and not self.is_color_blocked(self.p2_last_color, self.p1_pos):
                        self.p2_colors.discard(self.p2_last_color)
                        self.p1_colors.add(self.p2_last_color)
                    self.p2_colors.add(arg)
                    self.p2_last_color = arg
                break
            else:
                print("Unknown command.")

    def play(self):
        print("Game Start! Player 1 starts at 'Start'. Player 2 starts off board.")
        self.p2_pos = 'Start'  # Start undefined for P2
        turn = 1
        while True:
            if self.p1_pos == 'Target' and self.ownership['Taget'] in self.p1_colors:
                print("\n🎉 Player 1 reached Target and wins!")
                break
            if self.p2_pos == 'Target' and self.ownership['Taget'] in self.p2_colors:
                print("\n🎉 Player 2 reached Target and wins!")
                break

            self.move_player(turn)
            turn = 2 if turn == 1 else 1

# To use this, copy the code into a Python script and run it in a terminal
game = InteractivePawnGame()
game.play()
