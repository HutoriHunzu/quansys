import argparse
from pathlib import Path
from ..simulation.config_handler import load
from ..job_handler.prepare import prepare_dir


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
    parser.add_argument(
        '-a', '--aedt',
        type=str,
        default=None,
        help="Path to the AEDT file"
    )
    parser.add_argument(
        '-o', '--output',
        type=str,
        required=True,
        help="Directory to save output files (optional)"
    )

    return parser.parse_args()


def main():
    args = parse_args()

    config_path = Path(args.config)
    config = load(config_path)

    if args.aedt is None:
        aedt_path = Path(config.config_project.path)
    else:
        aedt_path = Path(args.aedt)

    output_dir = Path(args.output_dir)

    prepare_dir(aedt_path, config, output_dir)


if __name__ == '__main__':
    main()
