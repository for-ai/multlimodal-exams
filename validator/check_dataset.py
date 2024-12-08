# Cohere For AI Community, Danylo Boiko, 2024

import json
import argparse

from typing import Union, Literal, Optional

from pydantic import BaseModel, ValidationError, field_validator
from pydantic_core.core_schema import ValidationInfo
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.text import Text
from rich.tree import Tree


EXPECTED_OPTIONS_COUNT = 4


class EntrySchema(BaseModel):
    language: str
    country: str
    file_name: str
    source: str
    license: str
    level: str
    category_en: str
    category_original_lang: str
    original_question_num: Union[int, str]
    question: str
    options: list[str]
    answer: int
    image_png: Optional[str]
    image_information: Literal["useful", "essential"]
    image_type: Literal["symbols", "figures", "graph", "table", "text"]
    parallel_question_num: Optional[Union[int, str]]

    @staticmethod
    def _validate_string(value: str) -> str:
        if not value.strip():
            raise ValueError("Value cannot be empty or whitespace")

        if value.startswith(" ") or value.endswith(" "):
            raise ValueError("Value cannot have leading or trailing spaces")

        return value

    @staticmethod
    def _validate_list_uniqueness(values: list) -> list:
        if len(set(values)) != len(values):
            raise ValueError("All values must be unique")

        return values

    @staticmethod
    def _validate_list_length(values: list, expected_length: int) -> list:
        if len(values) != expected_length:
            raise ValueError(f"Expected {expected_length} values, but got {len(values)}")

        return values

    @field_validator("language")
    def validate_language(cls, language: str, config: ValidationInfo) -> str:
        expected_language = config.context.get("expected_language")

        if language != expected_language:
            raise ValueError(f"Expected '{expected_language}', but got '{language}'")

        return cls._validate_string(language)

    @field_validator("options")
    def validate_options(cls, options: list[str]) -> list[str]:
        for option in options:
            cls._validate_string(option)

        cls._validate_list_uniqueness(options)

        return cls._validate_list_length(options, EXPECTED_OPTIONS_COUNT)

    @field_validator("answer")
    def validate_answer(cls, answer: int, config: ValidationInfo) -> int:
        options_count = len(config.data.get("options", []))

        if options_count > 0 and not (0 <= answer < options_count):
            raise ValueError(f"Expected value from 0 to {options_count - 1}, but got {answer}")

        return answer

    @field_validator(
        "country", "file_name", "source", "license", "level", "category_en", "category_original_lang",
        "original_question_num", "question", "image_png", "parallel_question_num"
    )
    def validate_string_fields(cls, value: Optional[str]) -> Optional[str]:
        return cls._validate_string(value) if isinstance(value, str) else value

    class Config:
        extra = "forbid"


class EntryError:
    def __init__(self, index: int, location: tuple | None, message: str) -> None:
        self.index = index
        self.location = location
        self.message = message

    def __str__(self) -> str:
        if self.location:
            return f"Location: {str(self.location).strip("(,)")}, error: {self.message.lower()}"

        return self.message


class DatasetValidator:
    def __init__(self, json_file: str, language_code: str) -> None:
        self.json_file: str = json_file
        self.json_entries: list[dict] = []
        self.language_code: str = language_code.lower()
        self.console: Console = Console()
        self.errors: list[EntryError] = []

    def validate(self) -> None:
        self.console.print("Starting validation...", style="green")
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
        except Exception as e:
            self.console.print(f"Error loading file {self.json_file}: {e}", style="red")

        return False

    def _validate_entries(self) -> None:
        for index, entry in enumerate(self.json_entries):
            try:
                EntrySchema.model_validate(entry, context={
                    "expected_language": self.language_code
                })
            except ValidationError as e:
                self.errors.extend([
                    EntryError(index, error.get("loc", None), error.get("msg")) for error in e.errors()
                ])

    def _print_validation_report(self) -> None:
        if len(self.errors) == 0:
            return self.console.print("Congratulations, the JSON file is valid!", style="green")

        self.console.print("The following errors were found, fix them and try again:", style="red")

        for error in self.errors:
            self.console.print(Panel(self._create_error_tree(error), expand=False, border_style="red"))

    def _create_error_tree(self, error: EntryError) -> Tree:
        entry = self.json_entries[error.index]

        tree = Tree(f"Error in entry with index {error.index}", style="red")
        tree.add(Text(str(error), style="yellow"))

        question_node = tree.add("Question")
        question_node.add(Syntax(entry.get("question", "N/A"), "text", word_wrap=True))

        options_node = tree.add("Options")
        for option_num, option_value in enumerate(entry.get("options", []), 1):
            options_node.add(f"{option_num}. {option_value}")

        answer_node = tree.add("Answer")
        answer_node.add(str(entry.get("answer", "N/A")))

        return tree


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--json_file", type=str, required=True, help="Path to the JSON file to be validated")
    parser.add_argument("--language_code", type=str, required=True, help="The language code for the dataset")
    args = parser.parse_args()

    validator = DatasetValidator(args.json_file, args.language_code)
    validator.validate()
