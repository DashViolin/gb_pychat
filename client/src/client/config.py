import os
import pathlib

from common.config import CommonConf


class ClientConf(CommonConf):
    """
    Настройки клиента по умолчанию
    """

    ROOT_DIR = pathlib.Path().resolve()
    LOGS_DIR = ROOT_DIR / "logs"
    DATA_DIR = ROOT_DIR / "data"
    DEFAULT_SERVER_IP = "127.0.0.1"
    MAIN_LOG_FILE_PATH = LOGS_DIR / "client.error.log"
    CALL_LOG_FILE_PATH = LOGS_DIR / "client.calls.log"


os.makedirs(ClientConf.LOGS_DIR, exist_ok=True)
os.makedirs(ClientConf.DATA_DIR, exist_ok=True)
