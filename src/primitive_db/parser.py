import shlex


def parse_where(text: str) -> dict:
    """Парсит where: <col> = <value>."""
    tokens = shlex.split(text, posix=True)
    if len(tokens) != 3 or tokens[1] != "=":
        raise ValueError("условие where")

    col = tokens[0]
    value = _parse_value(tokens[2], raw=text)
    return {col: value}


def parse_set(text: str) -> dict:
    """Парсит set: <col> = <value>."""
    tokens = shlex.split(text, posix=True)
    if len(tokens) != 3 or tokens[1] != "=":
        raise ValueError("условие set")

    col = tokens[0]
    value = _parse_value(tokens[2], raw=text)
    return {col: value}


def _parse_value(token: str, raw: str) -> object:
    """Парсит значение."""
    low = token.lower()
    if low == "true":
        return True
    if low == "false":
        return False

    try:
        return int(token)
    except ValueError:
        pass

    if '"' in raw:
        return token

    raise ValueError("значение (строки должны быть в кавычках)")

