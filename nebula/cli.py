import argparse

from dotenv import load_dotenv

from nebula.config import Config
from nebula.pipeline import Pipeline


load_dotenv()


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
    config = Config.load_config(args.input)
    pipeline = Pipeline(config)

    pipeline.execute()


if __name__ == '__main__':
    main()
