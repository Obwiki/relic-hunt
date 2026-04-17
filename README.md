# Terminal Relic Hunt

A small terminal dungeon crawler written in pure Python. No external dependencies.

## Features

- Randomly generated dungeon maps
- Turn-based movement and combat
- Enemies, potions, keys, traps, treasure, and a relic
- Simple save/load system using JSON
- Score tracking and short end-of-run summary

## Run

```bash
python -m relic_hunt
```

Or, from the project root:

```bash
PYTHONPATH=src python -m relic_hunt
```

## Controls

- `w` `a` `s` `d` — move
- `h` — drink potion
- `i` — view inventory/status
- `save` — save the current run
- `load` — load the last save
- `q` — quit

## Goal

Find the **Relic**, then reach the **Exit** alive.

## Notes

- The map is fog-of-war based: you only see explored tiles.
- Some doors require a key.
- Traps deal damage when stepped on.
- You can hold potions and use them later.

## Quick start

```bash
cd terminal_relic_hunt
PYTHONPATH=src python -m relic_hunt
```
