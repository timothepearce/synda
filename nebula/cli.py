import argparse

from nebula.config import load_config
from nebula.pipeline import Pipeline


def main():
    parser = argparse.ArgumentParser(
        description='Nebula - Synthetic data generator pipeline'
    )

    parser.add_argument(
        '-i', '--input',
        required=True,
        help='Path to YAML file'
    )

    args = parser.parse_args()
    config = load_config(args.input)
    pipeline = Pipeline(config)

    pipeline.execute()


if __name__ == '__main__':
    main()
