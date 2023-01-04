import inspect
from functools import wraps
from http import HTTPStatus
from socket import socket


def log(logger):
    """
    Декоратор записывает в файл лога вызовов информацию при каждом вызове декорированной функции:
    имя, аргументы, откуда вызвана и название модуля
    """

    def decorator(fnc):
        @wraps(fnc)
        def wrapper(*args, **kwargs):
            fnc_args = ", ".join(map(str, list(args) + list(kwargs.values())))
            fnc_args_str = f" с аргументами [{fnc_args}]" if fnc_args else ""
            caller = inspect.stack()[1].function
            fnc_caller = f" из функции {caller}" if caller != "<module>" else ""
            fnc_call_info = f"Вызвана функция {fnc.__name__}{fnc_args_str}{fnc_caller} (модуль {fnc.__module__})"
            logger.debug(fnc_call_info)
            return fnc(*args, **kwargs)

        return wrapper

    return decorator


def login_required(fnc):
    """Декоратор проверяет, залогинен ли пользователь на сервере"""

    @wraps(fnc)
    def check(*args, **kwargs):
        server = args[0]
        for arg in args[1:]:
            if isinstance(arg, socket):
                if arg not in server.active_clients.values():
                    return HTTPStatus.FORBIDDEN, "", True
        return fnc(*args, **kwargs)

    return check
