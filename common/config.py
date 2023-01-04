import os
import pathlib


class CommonConf:
    """
    Содержит общие глобальные настройки проекта по умолчанию
    """

    MAX_PACKAGE_LENGTH = 640 * 2
    ENCODING = "utf-8"
    DEFAULT_PORT = 7777
    ROOT_DIR = pathlib.Path().resolve()
    LOGS_DIR = ROOT_DIR / "logs"
    DATA_DIR = ROOT_DIR / "data"


os.makedirs(CommonConf.LOGS_DIR, exist_ok=True)
os.makedirs(CommonConf.DATA_DIR, exist_ok=True)
