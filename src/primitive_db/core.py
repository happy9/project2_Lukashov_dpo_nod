from .utils import load_table_data, save_table_data

ALLOWED_TYPES = {"int", "str", "bool"}


def create_table(metadata: dict, table_name: str, columns: list[str]) -> dict:
    """Создать таблицу."""
    if table_name in metadata:
        print(f'Ошибка: Таблица "{table_name}" уже существует.')
        return metadata

    parsed: list[tuple[str, str]] = []
    for col in columns:
        if ":" not in col:
            print(f"Некорректное значение: {col}. Попробуйте снова.")
            return metadata

        name, col_type = col.split(":", 1)
        name = name.strip()
        col_type = col_type.strip()

        if not name or not col_type:
            print(f"Некорректное значение: {col}. Попробуйте снова.")
            return metadata

        if col_type not in ALLOWED_TYPES:
            print(f"Некорректное значение: {col_type}. Попробуйте снова.")
            return metadata

        parsed.append((name, col_type))

    has_id = any(name.lower() == "id" for name, _ in parsed)
    final_cols: list[tuple[str, str]] = []

    if not has_id:
        final_cols.append(("ID", "int"))
    final_cols.extend(parsed)

    new_metadata = dict(metadata)
    new_metadata[table_name] = {name: col_type for name, col_type in final_cols}

    cols_str = ", ".join(f"{name}:{col_type}" for name, col_type in final_cols)
    print(f'Таблица "{table_name}" успешно создана со столбцами: {cols_str}')

    return new_metadata

def drop_table(metadata: dict, table_name: str) -> dict:
    """Удалить таблицу."""
    if table_name not in metadata:
        print(f'Ошибка: Таблица "{table_name}" не существует.')
        return metadata

    new_metadata = dict(metadata)
    del new_metadata[table_name]

    print(f'Таблица "{table_name}" успешно удалена.')
    return new_metadata


def _cast_value(value: object, target_type: str) -> object | None:
    """Приведение к типу."""
    if target_type == "int":
        if isinstance(value, bool):
            return None
        if isinstance(value, int):
            return value
        if isinstance(value, str):
            try:
                return int(value)
            except ValueError:
                return None
        return None

    if target_type == "bool":
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            v = value.strip().lower()
            if v == "true":
                return True
            if v == "false":
                return False
        return None

    if target_type == "str":
        if isinstance(value, str):
            return value
        return None

    return None


def insert(metadata: dict, table_name: str, values: list[object]) -> list[dict]:
    """Добавить запись."""
    if table_name not in metadata:
        print(f'Ошибка: Таблица "{table_name}" не существует.')
        return []

    schema: dict = metadata[table_name]
    columns = list(schema.keys())

    non_id_columns = [c for c in columns if c.lower() != "id"]
    if len(values) != len(non_id_columns):
        print("Некорректное значение: количество значений. Попробуйте снова.")
        return load_table_data(table_name)

    row: dict = {}
    for col_name, raw_value in zip(non_id_columns, values, strict=True):
        col_type = schema[col_name]
        casted = _cast_value(raw_value, col_type)
        if casted is None:
            print(f"Некорректное значение: {raw_value}. Попробуйте снова.")
            return load_table_data(table_name)
        row[col_name] = casted

    table_data = load_table_data(table_name)
    max_id = 0
    for record in table_data:
        rec_id = record.get("ID")
        if isinstance(rec_id, int) and rec_id > max_id:
            max_id = rec_id

    new_id = max_id + 1
    row["ID"] = new_id

    ordered_row = {}
    for col in columns:
        if col in row:
            ordered_row[col] = row[col]
        elif col.lower() == "id":
            ordered_row[col] = new_id

    table_data.append(ordered_row)
    save_table_data(table_name, table_data)

    print(f'Запись с ID={new_id} успешно добавлена в таблицу "{table_name}".')
    return table_data


def select(table_data: list[dict], where_clause: dict | None = None) -> list[dict]:
    """Выбрать записи."""
    if where_clause is None:
        return table_data

    if len(where_clause) != 1:
        return []

    key, value = next(iter(where_clause.items()))
    return [row for row in table_data if row.get(key) == value]


def update(table_data: list[dict], set_clause: dict, where_clause: dict) -> list[dict]:
    """Обновить записи."""
    if len(where_clause) != 1:
        return table_data

    w_key, w_val = next(iter(where_clause.items()))
    updated = False

    for row in table_data:
        if row.get(w_key) == w_val:
            for s_key, s_val in set_clause.items():
                if s_key in row:
                    row[s_key] = s_val
                    updated = True

    if not updated:
        return table_data

    return table_data


def delete(table_data: list[dict], where_clause: dict) -> list[dict]:
    """Удалить записи."""
    if len(where_clause) != 1:
        return table_data

    key, value = next(iter(where_clause.items()))
    return [row for row in table_data if row.get(key) != value]
