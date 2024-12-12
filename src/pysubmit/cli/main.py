import argparse
from pathlib import Path
from src.pysubmit.simulation.config_handler import load
from src.pysubmit.simulation import analyze


def parse_args():
    parser = argparse.ArgumentParser(
        description="Process paths for HFSS-related files with optional output directory."
    )

    # Adding long and short notation arguments
    parser.add_argument(
        '-c', '--config',
        type=str,
        required=True,
        help="Path to the config file"
    )

    return parser.parse_args()


def main():
    args = parse_args()

    config_path = Path(args.config)

    config = load(config_path)

    analyze.main(config)


if __name__ == '__main__':
    main()
