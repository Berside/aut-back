import json


def extend_json(data: dict, additional_data: dict) -> dict:
    data.update(additional_data)
    return data


def write_json_to_file(data: dict, file_path: str) -> None:
    print(file_path)
    with open('config/swagger.json', "w", encoding="utf-8") as file:
        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=4
        )
