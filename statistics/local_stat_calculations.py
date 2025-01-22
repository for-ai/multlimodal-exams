import os
import json


def merge_json_files(directory):
    merged_data = []
    
    for filename in os.listdir(directory):
        if filename.endswith('.json'):
            filepath = os.path.join(directory, filename)
            with open(filepath, 'r') as file:
                data = json.load(file)
                merged_data.append(data)
    
    return merged_data


def get_question_count_by_cat(merged_data, cat):
    language_counts = {}
    
    for exam in merged_data:
        for question in exam:
            language = question.get(cat)
            if language:
                if language not in language_counts:
                    language_counts[language] = 0
                language_counts[language] += 1
    
    return language_counts


def count_image_related_questions(merged_data):
    image_question_count = 0
    for exam in merged_data:
        for question in exam:
            if 'image_png' in question and question['image_png'] != '' and question['image_png'] != None:
                image_question_count += 1
                continue
            for option in question.get('options', []):
                if option.endswith(('.png', '.jpg', '.jpeg', '.gif')):
                    image_question_count += 1
                    break
    return image_question_count


exams_directory = './exams' # Modify this to your need, note that this has to be a subfolder in the repo
merged_data = merge_json_files(exams_directory)

print("Number of exams:", len(merged_data))

for cat in ["language", "country", "level", "category_en", "image_type", "image_information"]:
    question_counts = get_question_count_by_cat(merged_data, cat)
    print(f"Question counts by {cat}:", question_counts)

image_question_count = count_image_related_questions(merged_data)
print("Number of image related questions:", image_question_count)
