import inspect
from functools import wraps


def log(logger):
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
    @wraps(fnc)
    def check(*args, **kwargs):
        return fnc(*args, **kwargs)

    return check
