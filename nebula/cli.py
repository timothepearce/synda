import argparse
import sys
import yaml


def load_config(config_path: str) -> dict[any, any]:
    try:
        with open(config_path, 'r', encoding='utf-8') as file:
            return yaml.safe_load(file)
    except yaml.YAMLError as e:
        print(f"Error in YAML file: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print(f"The file {config_path} doesn't exist")
        sys.exit(1)


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
    print("YAML file loaded!")
    print(config)


if __name__ == '__main__':
    main()
