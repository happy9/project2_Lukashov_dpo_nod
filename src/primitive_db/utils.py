import json


def load_metadata(filepath: str) -> dict:
    """Загрузка метаданных из JSON."""
    try:
        with open(filepath, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}


def save_metadata(filepath: str, data: dict) -> None:
    """Сохранение метаданных в JSON."""
    with open(filepath, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)
        

def load_table_data(table_name: str) -> list[dict]:
    """Загрузка данных таблицы."""
    filepath = f"data/{table_name}.json"
    try:
        with open(filepath, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        return []


def save_table_data(table_name: str, data: list[dict]) -> None:
    """Сохранение данных таблицы."""
    filepath = f"data/{table_name}.json"
    with open(filepath, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)


