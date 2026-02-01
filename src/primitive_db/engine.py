import shlex

import prompt
from prettytable import PrettyTable

from .core import create_table, delete, drop_table, insert, select, update
from .parser import parse_set, parse_where
from .utils import load_metadata, load_table_data, save_metadata, save_table_data

DB_META_FILEPATH = "db_meta.json"


def print_help() -> None:
    """Печатает справку."""
    print("\n***Операции с данными***\n")
    print("Функции:")
    print('<command> insert into <имя_таблицы> values ("строка", 1, true)\
- создать запись.')
    print("<command> select from <имя_таблицы> where <столбец> = <значение>\
- прочитать по условию.")
    print("<command> select from <имя_таблицы> - прочитать все записи.")
    print(
        "<command> update <имя_таблицы> set <столбец> = <значение> where <столбец>\
= <значение> - обновить."
    )
    print("<command> delete from <имя_таблицы> where <столбец> = <значение> - удалить.")
    print("<command> info <имя_таблицы> - вывести информацию о таблице.\n")

    print("***Управление таблицами***\n")
    print("<command> create_table <имя_таблицы> <столбец1:тип> .. - создать таблицу")
    print("<command> list_tables - показать список всех таблиц")
    print("<command> drop_table <имя_таблицы> - удалить таблицу\n")

    print("Общие команды:")
    print("<command> exit - выход из программы")
    print("<command> help - справочная информация\n")


def run() -> None:
    """Основной цикл."""
    print_help()

    while True:
        metadata = load_metadata(DB_META_FILEPATH)

        user_input = prompt.string(prompt="Введите команду: ")
        if user_input is None:
            continue

        user_input = user_input.strip()
        if not user_input:
            continue

        try:
            args = shlex.split(user_input)
        except ValueError as exc:
            print(f"Некорректное значение: {exc}. Попробуйте снова.")
            continue

        if not args:
            continue

        cmd = args[0]
        low = user_input.lower()

        if cmd == "exit":
            break

        if cmd == "help":
            print_help()
            continue

        if cmd == "list_tables":
            for name in metadata:
                print(f"- {name}")
            continue

        if cmd == "create_table":
            if len(args) < 3:
                print("Некорректное значение: create_table. Попробуйте снова.")
                continue
            table_name = args[1]
            columns = args[2:]
            updated = create_table(metadata, table_name, columns)
            if updated is not metadata:
                save_metadata(DB_META_FILEPATH, updated)
            continue

        if cmd == "drop_table":
            if len(args) != 2:
                print("Некорректное значение: drop_table. Попробуйте снова.")
                continue
            table_name = args[1]
            updated = drop_table(metadata, table_name)
            if updated is not metadata:
                save_metadata(DB_META_FILEPATH, updated)
            continue

        if low.startswith("insert into "):
            _handle_insert(user_input, metadata)
            continue

        if low.startswith("select from "):
            _handle_select(user_input, metadata)
            continue

        if low.startswith("update "):
            _handle_update(user_input, metadata)
            continue

        if low.startswith("delete from "):
            _handle_delete(user_input, metadata)
            continue

        if low.startswith("info "):
            _handle_info(user_input, metadata)
            continue

        print(f"Функции {cmd} нет. Попробуйте снова.")


def _handle_insert(user_input: str, metadata: dict) -> None:
    """insert into <table> values (...)"""
    try:
        table_name, values = _parse_insert(user_input)
    except ValueError as exc:
        print(f"Некорректное значение: {exc}. Попробуйте снова.")
        return

    if table_name not in metadata:
        print(f'Ошибка: Таблица "{table_name}" не существует.')
        return

    insert(metadata, table_name, values)


def _handle_select(user_input: str, metadata: dict) -> None:
    """select from <table> [where ...]"""
    try:
        table_name, where_text = _parse_select(user_input)
    except ValueError as exc:
        print(f"Некорректное значение: {exc}. Попробуйте снова.")
        return

    if table_name not in metadata:
        print(f'Ошибка: Таблица "{table_name}" не существует.')
        return

    schema = metadata[table_name]
    columns = list(schema.keys())
    table_data = load_table_data(table_name)

    where_clause = None
    if where_text is not None:
        try:
            where_clause = parse_where(where_text)
            where_clause = _cast_clause(schema, where_clause)
        except ValueError as exc:
            print(f"Некорректное значение: {exc}. Попробуйте снова.")
            return

    rows = select(table_data, where_clause=where_clause)
    _print_rows(rows, columns)


def _handle_update(user_input: str, metadata: dict) -> None:
    """update <table> set ... where ..."""
    try:
        table_name, set_text, where_text = _parse_update(user_input)
    except ValueError as exc:
        print(f"Некорректное значение: {exc}. Попробуйте снова.")
        return

    if table_name not in metadata:
        print(f'Ошибка: Таблица "{table_name}" не существует.')
        return

    schema = metadata[table_name]
    table_data = load_table_data(table_name)

    before = [row.copy() for row in table_data]

    try:
        set_clause = _cast_clause(schema, parse_set(set_text))
        where_clause = _cast_clause(schema, parse_where(where_text))
    except ValueError as exc:
        print(f"Некорректное значение: {exc}. Попробуйте снова.")
        return

    after = update(table_data, set_clause=set_clause, where_clause=where_clause)

    if after != before:
        save_table_data(table_name, after)

        # Если обновили ровно одну запись — выведем ID
        ids_before = {row.get("ID") for row in before}
        ids_after = {row.get("ID") for row in after}
        _ = ids_before, ids_after

        changed_ids = []
        for b, a in zip(before, after, strict=False):
            if b != a and isinstance(a.get("ID"), int):
                changed_ids.append(a["ID"])

        if len(changed_ids) == 1:
            print(f'Запись с ID={changed_ids[0]} в таблице "{table_name}\
" успешно обновлена.')
        else:
            print(f'Записи в таблице "{table_name}" успешно обновлены.')
        return

    print("Записи для обновления не найдены.")



def _handle_delete(user_input: str, metadata: dict) -> None:
    """delete from <table> where ..."""
    try:
        table_name, where_text = _parse_delete(user_input)
    except ValueError as exc:
        print(f"Некорректное значение: {exc}. Попробуйте снова.")
        return

    if table_name not in metadata:
        print(f'Ошибка: Таблица "{table_name}" не существует.')
        return

    schema = metadata[table_name]
    table_data = load_table_data(table_name)

    try:
        where_clause = _cast_clause(schema, parse_where(where_text))
    except ValueError as exc:
        print(f"Некорректное значение: {exc}. Попробуйте снова.")
        return

    # Ищем ID удаляемой записи
    w_key, w_val = next(iter(where_clause.items()))
    target_id = None
    for row in table_data:
        if row.get(w_key) == w_val and isinstance(row.get("ID"), int):
            target_id = row["ID"]
            break

    new_data = delete(table_data, where_clause=where_clause)

    if target_id is not None and len(new_data) < len(table_data):
        save_table_data(table_name, new_data)
        print(f'Запись с ID={target_id} успешно удалена из таблицы "{table_name}".')
        return

    if len(new_data) < len(table_data):
        save_table_data(table_name, new_data)
        print(f'Удалено записей: {len(table_data) - len(new_data)}.')
        return

    print("Записи для удаления не найдены.")



def _handle_info(user_input: str, metadata: dict) -> None:
    """info <table>"""
    parts = user_input.split(maxsplit=1)
    if len(parts) != 2:
        print("Некорректное значение: info. Попробуйте снова.")
        return

    table_name = parts[1].strip()
    if table_name not in metadata:
        print(f'Ошибка: Таблица "{table_name}" не существует.')
        return

    schema = metadata[table_name]
    columns_str = ", ".join(f"{k}:{v}" for k, v in schema.items())
    count = len(load_table_data(table_name))

    print(f"Таблица: {table_name}")
    print(f"Столбцы: {columns_str}")
    print(f"Количество записей: {count}")


def _parse_insert(user_input: str) -> tuple[str, list[object]]:
    """Парсит insert."""
    rest = user_input[len("insert into ") :].strip()
    if " " not in rest:
        raise ValueError("insert")

    table_name, tail = rest.split(" ", 1)
    tail = tail.strip()

    if not tail.lower().startswith("values"):
        raise ValueError("insert")

    lpar = tail.find("(")
    rpar = tail.rfind(")")
    if lpar == -1 or rpar == -1 or rpar < lpar:
        raise ValueError("values (...)")

    inside = tail[lpar + 1 : rpar].strip()
    if not inside:
        raise ValueError("values")

    return table_name, _parse_values_list(inside)


def _parse_select(user_input: str) -> tuple[str, str | None]:
    """Парсит select."""
    rest = user_input[len("select from ") :].strip()
    if not rest:
        raise ValueError("select")

    low = rest.lower()
    if " where " in low:
        idx = low.find(" where ")
        table_name = rest[:idx].strip()
        where_text = rest[idx + len(" where ") :].strip()
        if not table_name or not where_text:
            raise ValueError("select where")
        return table_name, where_text

    return rest.strip(), None


def _parse_update(user_input: str) -> tuple[str, str, str]:
    """Парсит update."""
    rest = user_input[len("update ") :].strip()
    if not rest:
        raise ValueError("update")

    low = rest.lower()
    set_idx = low.find(" set ")
    where_idx = low.find(" where ")

    if set_idx == -1 or where_idx == -1 or where_idx < set_idx:
        raise ValueError("update set/where")

    table_name = rest[:set_idx].strip()
    set_text = rest[set_idx + len(" set ") : where_idx].strip()
    where_text = rest[where_idx + len(" where ") :].strip()

    if not table_name or not set_text or not where_text:
        raise ValueError("update")

    return table_name, set_text, where_text


def _parse_delete(user_input: str) -> tuple[str, str]:
    """Парсит delete."""
    rest = user_input[len("delete from ") :].strip()
    if not rest:
        raise ValueError("delete")

    low = rest.lower()
    where_idx = low.find(" where ")
    if where_idx == -1:
        raise ValueError("delete where")

    table_name = rest[:where_idx].strip()
    where_text = rest[where_idx + len(" where ") :].strip()

    if not table_name or not where_text:
        raise ValueError("delete")

    return table_name, where_text


def _parse_values_list(text: str) -> list[object]:
    """Парсит значения для insert."""
    parts: list[str] = []
    current: list[str] = []
    in_quotes = False

    for ch in text:
        if ch == '"':
            in_quotes = not in_quotes
            current.append(ch)
            continue

        if ch == "," and not in_quotes:
            parts.append("".join(current).strip())
            current = []
            continue

        current.append(ch)

    if current:
        parts.append("".join(current).strip())

    return [_parse_scalar(p) for p in parts]


def _parse_scalar(token: str) -> object:
    """Парсит одно значение."""
    t = token.strip()
    if not t:
        raise ValueError("значение")

    low = t.lower()
    if low == "true":
        return True
    if low == "false":
        return False

    try:
        return int(t)
    except ValueError:
        pass

    if len(t) >= 2 and t[0] == '"' and t[-1] == '"':
        return t[1:-1]

    raise ValueError("строки должны быть в кавычках")


def _cast_clause(schema: dict, clause: dict) -> dict:
    """Проверяет столбец и тип."""
    col, value = next(iter(clause.items()))
    if col not in schema:
        raise ValueError(f"столбец {col}")

    col_type = schema[col]
    if col_type == "int":
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(f"тип {col}")
        return {col: value}

    if col_type == "bool":
        if not isinstance(value, bool):
            raise ValueError(f"тип {col}")
        return {col: value}

    if col_type == "str":
        if not isinstance(value, str):
            raise ValueError(f"тип {col}")
        return {col: value}

    raise ValueError(f"тип {col}")


def _print_rows(rows: list[dict], columns: list[str]) -> None:
    """Печатает таблицу."""
    table = PrettyTable()
    table.field_names = columns
    for row in rows:
        table.add_row([row.get(col) for col in columns])
    print(table)

