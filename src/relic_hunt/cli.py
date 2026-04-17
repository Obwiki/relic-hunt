from __future__ import annotations

from .game import GameState, run_command


def main() -> int:
    print("Terminal Relic Hunt")
    print("Find the Relic, then escape through the Exit.\n")
    state = GameState.new()

    while True:
        print(state.render())
        if state.finished:
            result = "Victory" if state.victory else "Run ended"
            print(f"\n{result}! Final score: {state.score()}")
            return 0
        try:
            command = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nLeaving the dungeon.")
            return 0
        state = run_command(state, command)
        print()
