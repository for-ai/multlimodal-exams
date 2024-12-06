# Cohere For AI Community, Danylo Boiko, 2024

import json
import argparse

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.text import Text
from rich.tree import Tree


class ValidationError:
    def __init__(self, entity_index: int, message: str) -> None:
        self.entity_index = entity_index
        self.message = message


class DatasetValidator:
    def __init__(self, json_file: str, language_code: str) -> None:
        self.json_file: str = json_file
        self.json_entries: list[dict] = []
        self.language_code: str = language_code.lower()
        self.console: Console = Console()
        self.errors: list[ValidationError] = []

    def validate(self) -> None:
        self.console.print("Starting validation...", style="bold green")
        self.console.print(f"JSON file: {self.json_file}", style="cyan")
        self.console.print(f"Language code: {self.language_code}", style="cyan")

        if not self._load_json():
            return

        self._validate_entries()

        self._print_validation_report()

    def _load_json(self) -> bool:
        try:
            with open(self.json_file, "r", encoding="utf-8") as file:
                entries = json.load(file)

                if not isinstance(entries, list):
                    raise ValueError(f"The file must contain a JSON array (list of entries)")

                self.json_entries = entries

            return True
        except Exception as error:
            self.console.print(f"Error loading file {self.json_file}: {error}", style="red")

        return False

    def _validate_entries(self) -> None:
        pass

    def _print_validation_report(self) -> None:
        if len(self.errors) == 0:
            return self.console.print("Congratulations, the JSON file is valid!", style="green")

        self.console.print("The following errors were found, fix them and try again:", style="red")

        for error in self.errors:
            self.console.print(Panel(self._create_error_tree(error), expand=False, border_style="red"))

    def _create_error_tree(self, error: ValidationError) -> Tree:
        entry = self.json_entries[error.entity_index]

        tree = Tree(f"Error in entry with index {error.entity_index}", style="red")
        tree.add(Text(error.message, style="yellow"))

        question_node = tree.add("Question")
        question_node.add(Syntax(entry.get("question", "[N/A]"), "text", word_wrap=True))

        options_node = tree.add("Options")
        for option_num, option_value in enumerate(entry.get("options", []), 1):
            options_node.add(f"{option_num}. {option_value}")

        answer_node = tree.add("Answer")
        answer_node.add(str(entry.get("answer", "[N/A]")))

        return tree


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--json_file", type=str, required=True, help="Path to the JSON file to be validated")
    parser.add_argument("--language_code", type=str, required=True, help="The language code for the dataset")
    args = parser.parse_args()

    validator = DatasetValidator(args.json_file, args.language_code)
    validator.validate()
