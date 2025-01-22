# Cohere For AI Community, Danylo Boiko, 2024

import os
import json
import argparse

from typing import Union, Literal, Optional

from pydantic import BaseModel, ValidationError, field_validator, model_validator
from pydantic_core.core_schema import ValidationInfo
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.text import Text
from rich.tree import Tree


MIN_OPTIONS_COUNT = 2


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
    image_information: Optional[Literal["useful", "essential"]]
    image_type: Optional[Literal["graph", "table", "diagram", "scientific formula", "text", "figure", "map", "photo"]]
    parallel_question_id: Optional[tuple[str, int]]

    @staticmethod
    def _validate_string(value: str) -> str:
        if not value.strip():
            raise ValueError("Value cannot be empty or whitespace")

        if value.startswith(" ") or value.endswith(" "):
            raise ValueError("Value cannot have leading or trailing spaces")

        return value

    @staticmethod
    def _validate_image(image_name: str, config: ValidationInfo) -> None:
        images_path = config.context.get("images_path")

        if os.path.basename(image_name) != image_name:
            raise ValueError(f"The image name '{image_name}' must not include directories")

        if not os.path.isfile(os.path.join(images_path, image_name)):
            raise ValueError(f"The specified image '{image_name}' does not exist in {images_path}")

    @field_validator("language")
    def validate_language(cls, language: str, config: ValidationInfo) -> str:
        dataset_language = config.context.get("dataset_language")

        if language != dataset_language:
            raise ValueError(f"Expected '{dataset_language}', but got '{language}'")

        return cls._validate_string(language)

    @field_validator("options")
    def validate_options(cls, options: list[str], config: ValidationInfo) -> list[str]:
        for option in options:
            cls._validate_string(option)

            if option.lower().endswith(".png"):
                cls._validate_image(option, config)

        if len(options) < MIN_OPTIONS_COUNT:
            raise ValueError(f"Expected at least {MIN_OPTIONS_COUNT} options, but got {len(options)}")

        if len(set(options)) != len(options):
            raise ValueError("All values must be unique")

        return options

    @field_validator("answer")
    def validate_answer(cls, answer: int, config: ValidationInfo) -> int:
        options_count = len(config.data.get("options", []))

        if options_count > 0 and not (0 <= answer < options_count):
            raise ValueError(f"Expected value from 0 to {options_count - 1}, but got {answer}")

        return answer

    @field_validator("image_png")
    def validate_image_png(cls, image_png: Optional[str], config: ValidationInfo) -> Optional[str]:
        if isinstance(image_png, str):
            cls._validate_string(image_png)

            if not image_png.lower().endswith(".png"):
                raise ValueError(f"The file '{image_png}' is not a PNG image")

            cls._validate_image(image_png, config)

        return image_png

    @field_validator("parallel_question_id")
    def validate_parallel_question_id(cls, parallel_question_id: Optional[tuple[str, int]]) -> Optional[tuple[str, int]]:
        if isinstance(parallel_question_id, tuple) and isinstance(parallel_question_id[0], str):
            cls._validate_string(parallel_question_id[0])

        return parallel_question_id

    @field_validator(
        "country", "file_name", "source", "license", "level", "category_en",
        "category_original_lang", "original_question_num", "question"
    )
    def validate_string_fields(cls, value: Optional[str]) -> Optional[str]:
        return cls._validate_string(value) if isinstance(value, str) else value

    @model_validator(mode="after")
    def validate_image_data(cls, model: "EntrySchema") -> "EntrySchema":
        image_data = [model.image_png, model.image_information, model.image_type]

        if any(image_data) and not all(image_data):
            raise ValueError(
                "All fields related to image data (prefixed with 'image_') must be specified if any one of them is specified"
            )

        return model

    class Config:
        extra = "forbid"


class EntryError:
    def __init__(self, index: int, message: str, location: Optional[tuple] = None) -> None:
        self.index = index
        self.message = message
        self.location = location

    def __str__(self) -> str:
        message = self.message.removeprefix("Value error, ")

        if self.location:
            location = str(self.location).strip(",()")
            return f"Location: {location}, error: {message.lower()}"

        return message


class DatasetValidator:
    def __init__(self, json_file: str, language_code: str) -> None:
        self.json_file: str = json_file
        self.json_entries: list[dict] = []
        self.language_code: str = language_code.lower()
        self.images_path: str = os.path.join(os.path.dirname(json_file), "images")
        self.console: Console = Console()
        self.errors: list[EntryError] = []

    def validate(self) -> None:
        self.console.print("Starting validation...", style="green")
        self.console.print(f"JSON file: {self.json_file}", style="cyan")
        self.console.print(f"Images path: {self.images_path}", style="cyan")
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
                    raise ValueError("The file must contain a JSON array (list of entries)")

                self.json_entries = entries
            return True
        except Exception as e:
            self.console.print(f"Error loading file {self.json_file}: {e}", style="red")
            return False

    def _validate_entries(self) -> None:
        seen_entries = {}

        for index, entry in enumerate(self.json_entries):
            try:
                entry_model = EntrySchema.model_validate(entry, context={
                    "dataset_language": self.language_code,
                    "images_path": self.images_path,
                })

                entry_hash = (entry_model.question, entry_model.image_png, tuple(opt for opt in entry_model.options))

                if entry_hash not in seen_entries:
                    seen_entries[entry_hash] = index
                else:
                    self.errors.append(EntryError(index, f"Duplicate of entry with index {seen_entries[entry_hash]}"))
            except ValidationError as e:
                self.errors.extend([
                    EntryError(index, error.get("msg"), error.get("loc", None)) for error in e.errors()
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
