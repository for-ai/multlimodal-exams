import os
from openai import OpenAI
import re
import time
import json
import base64
import backoff
import argparse


def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def backoff_hdlr(details):
    print(
        "Backing off {wait:0.1f} seconds after {tries} tries "
        "calling function {target}".format(**details)
    )


@backoff.on_exception(backoff.expo, Exception, on_backoff=backoff_hdlr)
def predict(client, model, prmopt, image_url, max_tokens=500, temperature=0.0):
    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prmopt},
                    {"type": "image_url", "image_url": {"url": image_url}},
                ],
            }
        ],
        max_tokens=max_tokens,
        temperature=temperature,
    )
    return response.choices[0].message.content


def extract_class(text, class_list):
    cat_pattern = r"(" + "|".join(re.escape(cat) for cat in class_list) + r")"
    matches = re.findall(cat_pattern, text, re.IGNORECASE)
    return matches[-1] if matches else None


PROMPT_IMAGE_TYPE = """
You are an image classifier assistant. Your task is to take a look at an image and classify it by its main category using the following rubric:

'graph': Images showing data plotted on axes (line graphs, bar charts, scatter plots, pie charts, flowcharts, organizational charts, etc.).
'table': Structured data arranged in rows and columns.
'diagram': Technical or schematic drawings illustrating processes, structures, or concepts.
'scientific formula': Mathematical equations, chemical formulas, mathematical diagrams, or related.
'text': Images containing primarily textual information.
'figure': Illustrations, drawings, or visual representations of objects, patterns, or symbols.
'map': Geographical or spatial representations.
'photo': Photographic images of real-world scenes, objects, or people.

If categories overlap for the image, choose which's best representative of it.

Answer in this format:

Explanation:
{Explanation}

Category:
{Category}
"""

PROMPT_IMAGE_USEFUL = """
You are an advanced image utility assessment assistant. Your role is to evaluate whether an image is essential or useful for answering a given question by following these precise guidelines:

- Essential Image Criteria:
  - The question DIRECTLY references or requires specific visual information from the image.
  - Answering the question would be impossible without examining the image.
  - The question asks about the content, details, or specifics visible in the image.

- Useful Image Criteria:
  - The image provides supplementary or supporting information.
  - The question can be answered comprehensively without the image.
  - The image offers additional context or insights but is not critical to the core answer.

Output Format:
  - If the image is essential: output "essential".
  - If the image is useful: output "useful".

Answer in this format:

Explanation:
{{Explanation}}

Utility:
{{essential or useful}}


Given Question: {}
"""


def extract_meatadata(client, model, query, image_path):
    print("Extracting metadata for query:", query, "\nand image:", image_path)
    print("-" * 70)
    base64_image = encode_image(image_path)
    image_url = f"data:image/png;base64,{base64_image}"

    question = PROMPT_IMAGE_TYPE
    output = predict(client, model, question, image_url)
    print(output)
    print("-" * 70)
    classes = [
        "graph",
        "table",
        "diagram",
        "scientific formula",
        "text",
        "figure",
        "map",
        "photo",
    ]
    category = extract_class(output, classes)
    print("Category >>", category)
    print("-" * 70)

    question = PROMPT_IMAGE_USEFUL
    output = predict(client, model, question.format(query), image_url)
    print(output)
    print("-" * 70)
    classes = ["essential", "useful"]
    utility = extract_class(output, classes)
    print("Utility >>", utility)
    print("=" * 70)

    return category, utility


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--api_base_url", type=str, default="https://openrouter.ai/api/v1"
    )
    parser.add_argument("--api_key", type=str, required=True)
    parser.add_argument(
        "--model", type=str, default="meta-llama/llama-3.2-90b-vision-instruct:free"
    )
    parser.add_argument("--input_json", type=str, required=True)
    args = parser.parse_args()

    output_json = args.input_json.replace(".json", "_with_metadata.json")

    client = OpenAI(
        base_url=args.api_base_url,
        api_key=args.api_key,
    )

    with open(args.input_json, "r", encoding="utf-8") as json_file:
        dataset = json.load(json_file)

    json_dir = os.path.dirname(args.input_json)
    output_dataset = []

    for data in dataset:
        image_path = data["image_png"]
        query = data["question"]
        if not image_path:
            output_dataset.append(data)
            continue

        image_path = os.path.join(json_dir, "images", image_path)
        category, utility = extract_meatadata(client, args.model, query, image_path)
        data["image_type"] = category
        data["image_information"] = utility
        output_dataset.append(data)

    with open(output_json, "w", encoding="utf-8") as json_file:
        json.dump(output_dataset, json_file, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
