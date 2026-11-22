"""Run or independently replay the Phase 2.5 development comparison."""

import argparse
from pathlib import Path

from star_evrp.experiment_phase25 import run


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=Path("configs/phase25.yaml"))
    parser.add_argument("--output", type=Path, default=Path("results/phase25"))
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    run(Path(__file__).resolve().parents[1], args.config.resolve(), args.output.resolve(), verify=args.verify)


if __name__ == "__main__":
    main()
