"""Usage: python -m generator [--seed 42] [--start 2024-01-01] [--end 2026-09-30] [--scale 1.0] [--out data/raw]"""

from __future__ import annotations

import argparse
from datetime import date, datetime, time
from pathlib import Path

from generator import config, messy, writers
from generator.simulate import Simulator, World


def generate(seed: int, start: date, end: date, scale: float) -> World:
    world = Simulator(seed, start, end, scale).run()
    messy.apply(world, seed, extracted_at=datetime.combine(end, time(23, 59, 59)))
    return world


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Fieldcraft's raw source data.")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--start", type=date.fromisoformat, default=config.DEFAULT_START)
    parser.add_argument("--end", type=date.fromisoformat, default=config.DEFAULT_END)
    parser.add_argument("--scale", type=float, default=1.0, help="multiplier on daily signups")
    parser.add_argument("--out", type=Path, default=Path("data/raw"))
    args = parser.parse_args()

    counts = writers.write(generate(args.seed, args.start, args.end, args.scale), args.out)
    width = max(map(len, counts))
    for name, count in counts.items():
        print(f"{name:<{width}}  {count:>8,}")


if __name__ == "__main__":
    main()
