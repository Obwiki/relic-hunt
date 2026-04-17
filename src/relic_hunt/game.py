from __future__ import annotations

from dataclasses import dataclass, field, asdict
import json
import random
from pathlib import Path
from typing import Iterable

SAVE_FILE = Path("savegame.json")

WALL = "#"
FLOOR = "."
PLAYER = "@"
EXIT = "E"
RELIC = "R"
POTION = "!"
KEY = "K"
TRAP = "^"
ENEMY = "M"
LOCKED = "D"
TREASURE = "$"

DISPLAY_NAMES = {
    WALL: "wall",
    FLOOR: "floor",
    EXIT: "exit",
    RELIC: "relic",
    POTION: "potion",
    KEY: "key",
    TRAP: "trap",
    ENEMY: "monster",
    LOCKED: "locked door",
    TREASURE: "treasure",
}

DIRS = {
    "w": (0, -1),
    "s": (0, 1),
    "a": (-1, 0),
    "d": (1, 0),
}


@dataclass
class Position:
    x: int
    y: int


@dataclass
class PlayerState:
    hp: int = 14
    max_hp: int = 14
    attack: int = 4
    potions: int = 1
    keys: int = 0
    gold: int = 0
    has_relic: bool = False
    turns: int = 0


@dataclass
class GameState:
    width: int = 17
    height: int = 11
    seed: int = 0
    grid: list[list[str]] = field(default_factory=list)
    explored: list[list[bool]] = field(default_factory=list)
    player: Position = field(default_factory=lambda: Position(1, 1))
    exit_pos: Position = field(default_factory=lambda: Position(1, 1))
    player_state: PlayerState = field(default_factory=PlayerState)
    messages: list[str] = field(default_factory=list)
    finished: bool = False
    victory: bool = False

    @classmethod
    def new(cls, width: int = 17, height: int = 11, seed: int | None = None) -> "GameState":
        rng_seed = random.randint(1, 10_000_000) if seed is None else seed
        rng = random.Random(rng_seed)
        grid = [[WALL for _ in range(width)] for _ in range(height)]
        explored = [[False for _ in range(width)] for _ in range(height)]

        for y in range(1, height - 1):
            for x in range(1, width - 1):
                grid[y][x] = FLOOR if rng.random() > 0.16 else WALL

        start = Position(1, 1)
        exit_pos = Position(width - 2, height - 2)
        grid[start.y][start.x] = FLOOR
        grid[exit_pos.y][exit_pos.x] = EXIT

        # Carve a guaranteed rough path from start to exit.
        x, y = start.x, start.y
        while x < exit_pos.x:
            grid[y][x] = FLOOR
            x += 1
        while y < exit_pos.y:
            grid[y][x] = FLOOR
            y += 1
        grid[exit_pos.y][exit_pos.x] = EXIT

        free_tiles = [(xx, yy) for yy in range(1, height - 1) for xx in range(1, width - 1)
                      if grid[yy][xx] == FLOOR and (xx, yy) not in {(start.x, start.y), (exit_pos.x, exit_pos.y)}]
        rng.shuffle(free_tiles)

        def place(symbol: str, count: int) -> None:
            nonlocal free_tiles
            for _ in range(count):
                if not free_tiles:
                    return
                xx, yy = free_tiles.pop()
                grid[yy][xx] = symbol

        place(POTION, 4)
        place(KEY, 2)
        place(TRAP, 7)
        place(ENEMY, 8)
        place(TREASURE, 5)
        place(LOCKED, 2)
        place(RELIC, 1)

        state = cls(
            width=width,
            height=height,
            seed=rng_seed,
            grid=grid,
            explored=explored,
            player=start,
            exit_pos=exit_pos,
            player_state=PlayerState(),
            messages=["You enter the catacombs. Find the relic and escape."],
        )
        state.reveal()
        return state

    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def tile(self, x: int, y: int) -> str:
        return self.grid[y][x]

    def set_tile(self, x: int, y: int, value: str) -> None:
        self.grid[y][x] = value

    def add_message(self, text: str) -> None:
        self.messages.append(text)
        self.messages = self.messages[-6:]

    def reveal(self) -> None:
        for yy in range(max(0, self.player.y - 2), min(self.height, self.player.y + 3)):
            for xx in range(max(0, self.player.x - 2), min(self.width, self.player.x + 3)):
                self.explored[yy][xx] = True

    def render(self) -> str:
        lines: list[str] = []
        header = (
            f"HP {self.player_state.hp}/{self.player_state.max_hp} | "
            f"ATK {self.player_state.attack} | Potions {self.player_state.potions} | "
            f"Keys {self.player_state.keys} | Gold {self.player_state.gold} | "
            f"Relic {'yes' if self.player_state.has_relic else 'no'} | Turns {self.player_state.turns}"
        )
        lines.append(header)
        lines.append("=" * len(header))
        for y in range(self.height):
            row = []
            for x in range(self.width):
                if self.player.x == x and self.player.y == y:
                    row.append(PLAYER)
                elif not self.explored[y][x]:
                    row.append("?")
                else:
                    tile = self.grid[y][x]
                    row.append(tile)
            lines.append("".join(row))
        lines.append("")
        lines.append("Recent events:")
        for msg in self.messages[-5:]:
            lines.append(f"- {msg}")
        lines.append("")
        lines.append("Commands: w/a/s/d move | h heal | i info | save | load | q")
        return "\n".join(lines)

    def inventory_text(self) -> str:
        ps = self.player_state
        return (
            f"HP: {ps.hp}/{ps.max_hp}\n"
            f"Attack: {ps.attack}\n"
            f"Potions: {ps.potions}\n"
            f"Keys: {ps.keys}\n"
            f"Gold: {ps.gold}\n"
            f"Relic: {'yes' if ps.has_relic else 'no'}\n"
            f"Turns: {ps.turns}"
        )

    def try_heal(self) -> None:
        ps = self.player_state
        if ps.potions <= 0:
            self.add_message("No potions left.")
            return
        if ps.hp >= ps.max_hp:
            self.add_message("You're already at full health.")
            return
        ps.potions -= 1
        healed = min(6, ps.max_hp - ps.hp)
        ps.hp += healed
        self.add_message(f"You drink a potion and recover {healed} HP.")

    def perform_enemy_attack(self) -> None:
        damage = random.randint(1, 4)
        self.player_state.hp -= damage
        self.add_message(f"The monster hits you for {damage} damage.")
        if self.player_state.hp <= 0:
            self.finished = True
            self.victory = False
            self.add_message("You fall in the dark. Game over.")

    def fight_enemy(self) -> None:
        damage = random.randint(self.player_state.attack - 1, self.player_state.attack + 2)
        damage = max(1, damage)
        enemy_hp = random.randint(3, 7)
        self.add_message(f"A monster appears with {enemy_hp} HP.")
        enemy_hp -= damage
        self.add_message(f"You strike for {damage} damage.")
        if enemy_hp > 0:
            self.perform_enemy_attack()
        else:
            self.add_message("Monster defeated.")
            if random.random() < 0.35:
                self.player_state.gold += 3
                self.add_message("You loot 3 gold from the monster.")

    def move(self, direction: str) -> None:
        if direction not in DIRS or self.finished:
            return
        dx, dy = DIRS[direction]
        nx, ny = self.player.x + dx, self.player.y + dy
        if not self.in_bounds(nx, ny):
            self.add_message("You can't go that way.")
            return

        target = self.tile(nx, ny)
        if target == WALL:
            self.add_message("A wall blocks your path.")
            return
        if target == LOCKED:
            if self.player_state.keys <= 0:
                self.add_message("The door is locked. You need a key.")
                return
            self.player_state.keys -= 1
            self.set_tile(nx, ny, FLOOR)
            self.add_message("You unlock the door with a key.")
            target = FLOOR

        self.player = Position(nx, ny)
        self.player_state.turns += 1
        self.resolve_tile(target)
        self.reveal()
        self.check_endgame()

    def resolve_tile(self, target: str) -> None:
        if target == FLOOR:
            self.add_message("You move carefully through the corridor.")
        elif target == POTION:
            self.player_state.potions += 1
            self.set_tile(self.player.x, self.player.y, FLOOR)
            self.add_message("You found a potion.")
        elif target == KEY:
            self.player_state.keys += 1
            self.set_tile(self.player.x, self.player.y, FLOOR)
            self.add_message("You picked up a key.")
        elif target == TRAP:
            dmg = random.randint(1, 4)
            self.player_state.hp -= dmg
            self.set_tile(self.player.x, self.player.y, FLOOR)
            self.add_message(f"A trap snaps! You take {dmg} damage.")
            if self.player_state.hp <= 0:
                self.finished = True
                self.victory = False
                self.add_message("The trap was fatal.")
        elif target == TREASURE:
            gain = random.randint(4, 10)
            self.player_state.gold += gain
            self.set_tile(self.player.x, self.player.y, FLOOR)
            self.add_message(f"You collect {gain} gold.")
        elif target == ENEMY:
            self.set_tile(self.player.x, self.player.y, FLOOR)
            self.fight_enemy()
        elif target == RELIC:
            self.player_state.has_relic = True
            self.player_state.attack += 1
            self.set_tile(self.player.x, self.player.y, FLOOR)
            self.add_message("You found the Relic. Power hums through your hands.")
        elif target == EXIT:
            if self.player_state.has_relic:
                self.finished = True
                self.victory = True
                self.add_message("You escape with the Relic. Victory!")
            else:
                self.add_message("You found the exit, but the Relic is still inside.")

    def check_endgame(self) -> None:
        if self.player_state.hp <= 0 and not self.finished:
            self.finished = True
            self.victory = False
            self.add_message("You collapse from your wounds.")

    def score(self) -> int:
        ps = self.player_state
        base = ps.gold + ps.turns
        if self.victory:
            return 100 + ps.gold + ps.hp * 3 - ps.turns
        return max(0, base)

    def to_dict(self) -> dict:
        return {
            "width": self.width,
            "height": self.height,
            "seed": self.seed,
            "grid": self.grid,
            "explored": self.explored,
            "player": asdict(self.player),
            "exit_pos": asdict(self.exit_pos),
            "player_state": asdict(self.player_state),
            "messages": self.messages,
            "finished": self.finished,
            "victory": self.victory,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "GameState":
        return cls(
            width=data["width"],
            height=data["height"],
            seed=data["seed"],
            grid=data["grid"],
            explored=data["explored"],
            player=Position(**data["player"]),
            exit_pos=Position(**data["exit_pos"]),
            player_state=PlayerState(**data["player_state"]),
            messages=list(data["messages"]),
            finished=bool(data["finished"]),
            victory=bool(data["victory"]),
        )

    def save(self, path: Path = SAVE_FILE) -> None:
        path.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")
        self.add_message(f"Game saved to {path}.")

    @classmethod
    def load(cls, path: Path = SAVE_FILE) -> "GameState":
        data = json.loads(path.read_text(encoding="utf-8"))
        state = cls.from_dict(data)
        state.add_message(f"Loaded save from {path}.")
        return state


def run_command(state: GameState, command: str) -> GameState:
    command = command.strip().lower()
    if command in DIRS:
        state.move(command)
        return state
    if command == "h":
        state.try_heal()
        return state
    if command == "i":
        state.add_message(state.inventory_text().replace("\n", " | "))
        return state
    if command == "save":
        state.save()
        return state
    if command == "load":
        if SAVE_FILE.exists():
            return GameState.load()
        state.add_message("No save file found.")
        return state
    if command == "q":
        state.finished = True
        state.victory = False
        state.add_message("You leave the dungeon behind.")
        return state
    state.add_message("Unknown command.")
    return state
