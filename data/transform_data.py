import json


def transform_data(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    new_data = []
    for item in data:
        new_data.append({
            "model": "recipes.ingredient",
            "fields": {
                "name": item["name"],
                "measurement_unit": item["measurement_unit"]
            }
        })

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(new_data, f, ensure_ascii=False, indent=2)


transform_data('ingredients.json', 'format_ingredients.json')
