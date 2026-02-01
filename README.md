# project2_Lukashov_dpo_nod

## Управление таблицами

Модуль поддерживает команды управления таблицами. Метаданные таблиц хранятся в файле `db_meta.json`.

### Команды

- `create_table <имя_таблицы> <столбец1:тип> <столбец2:тип> ...` — создать таблицу  
  Поддерживаемые типы: `int`, `str`, `bool`.  
  Если столбец `ID` не указан пользователем, он добавляется автоматически как `ID:int`.

- `list_tables` — показать список таблиц

- `drop_table <имя_таблицы>` — удалить таблицу

- `help` — показать справку

- `exit` — выйти

### Пример

```text
$ database

***База данных***

Функции:
<command> create_table <имя_таблицы> <столбец1:тип> .. - создать таблицу
<command> list_tables - показать список всех таблиц
<command> drop_table <имя_таблицы> - удалить таблицу

Общие команды:
<command> exit - выход из программы
<command> help - справочная информация

Введите команду: create_table users name:str age:int is_active:bool
Таблица "users" успешно создана со столбцами: ID:int, name:str, age:int, is_active:bool

Введите команду: list_tables
- users

Введите команду: drop_table users
Таблица "users" успешно удалена.

Введите команду: exit

## Демонстрация

### Запуск БД и манипуляции с таблицами
[![asciinema](https://asciinema.org/a/f1YwNIUeE8R6RX7M.svg)](https://asciinema.org/a/f1YwNIUeE8R6RX7M)

