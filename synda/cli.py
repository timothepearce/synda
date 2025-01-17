import argparse

from dotenv import load_dotenv

from synda.config import Config
from synda.pipeline import Pipeline


load_dotenv()


def main():
    parser = argparse.ArgumentParser(
        description='Synda - Synthetic data generator pipeline'
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
