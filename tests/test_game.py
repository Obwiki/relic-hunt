from pathlib import Path
import tempfile

from relic_hunt.game import GameState, run_command


def test_new_game_has_exit_and_player_alive():
    state = GameState.new(seed=123)
    assert state.player_state.hp > 0
    assert state.grid[state.exit_pos.y][state.exit_pos.x] == "E"


def test_heal_uses_potion():
    state = GameState.new(seed=123)
    state.player_state.hp = 5
    state.player_state.potions = 2
    run_command(state, "h")
    assert state.player_state.hp > 5
    assert state.player_state.potions == 1


def test_save_and_load_roundtrip():
    state = GameState.new(seed=456)
    state.player_state.gold = 9
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "save.json"
        state.save(path)
        loaded = GameState.load(path)
        assert loaded.player_state.gold == 9
        assert loaded.seed == 456
