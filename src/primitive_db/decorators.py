import time
from functools import wraps


def handle_db_errors(func):
    """Централизованная обработка ошибок БД."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except FileNotFoundError:
            print("Ошибка: Файл данных не найден. Возможно, база данных не \
инициализирована.")
        except KeyError as exc:
            print(f"Ошибка: Таблица или столбец {exc} не найден.")
        except ValueError as exc:
            print(f"Ошибка валидации: {exc}")
        except Exception as exc:
            print(f"Произошла непредвиденная ошибка: {exc}")
        return None
    return wrapper



def confirm_action(action_name: str):
    """Запрашивает подтверждение опасного действия."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            answer = input(
                f'Вы уверены, что хотите выполнить "{action_name}"? [y/n]: '
            ).strip().lower()

            if answer != "y":
                print("Операция отменена.")
                return None

            return func(*args, **kwargs)
        return wrapper
    return decorator
    

def log_time(func):
    """Логирует время выполнения функции."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.monotonic()
        result = func(*args, **kwargs)
        end = time.monotonic()
        duration = end - start
        print(f"Функция {func.__name__} выполнилась за {duration:.3f} секунд.")
        return result
    return wrapper
    
    
def create_cacher():
    """Создаёт кэширующую функцию."""
    cache: dict = {}

    def cache_result(key, value_func):
        if key in cache:
            return cache[key]
        result = value_func()
        cache[key] = result
        return result

    return cache_result

