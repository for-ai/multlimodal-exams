# Cohere For AI Community, Danylo Boiko, 2024

from argparse import ArgumentParser

from rich.console import Console


class DatasetValidator:
    def __init__(self, json_path: str, language_code: str) -> None:
        self.json_path = json_path
        self.language_code = language_code.lower()
        self.console = Console()

    def validate(self):
        pass


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument("--json_path", type=str, required=True, help="Path to the JSON file to be validated")
    parser.add_argument("--language_code", type=str, required=True, help="The language code for the dataset")
    args = parser.parse_args()

    validator = DatasetValidator(args.json_path, args.language_code)
    validator.validate()
