import json
from pathlib import Path
import shutil
import argparse


def process_data(source_path):
    source_path = Path(source_path)
    dataset_dir = source_path.parent
    images_dir = dataset_dir / "images"
    image_basedir = f"/data/local-files/?d={dataset_dir.name}/images/"

    dest_path = source_path.with_name(f"{source_path.stem}_label_studio.json")
    black_image = image_basedir + "Black.png"

    # Copy default black image
    black_image_file = source = Path(__file__).parent / "img" / "Black.png"
    shutil.copy(black_image_file, images_dir)

    with open(source_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    output_data = []
    for item in data:
        assert item["original_question_num"] is not None, "Invalid Question Number"
        item["id"] = item["original_question_num"]
        answer = item["options"][item["answer"]]

        if item["image_png"]:
            item["image_png"] = image_basedir + item["image_png"]
        else:
            item["image_png"] = black_image

        if answer.endswith(".png"):
            answer = image_basedir + answer
            item["answer_img"] = answer
            item["answer"] = ""
        else:
            item["answer_img"] = black_image
            item["answer"] = answer

        item["option_img"] = ["", "", "", ""]
        for i, option in enumerate(item.get("options", [])):
            if option.endswith(".png"):
                item["options"][i] = ""
                option = image_basedir + option
                item["option_img"][i] = option
            else:
                item["option_img"][i] = black_image

        output_data.append(item)

    with open(dest_path, "w", encoding="utf-8") as file:
        json.dump(output_data, file, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process JSON data for Label Studio.")
    parser.add_argument("--source_path", type=str, help="Full path to the source JSON file.")

    args = parser.parse_args()
    process_data(args.source_path)
