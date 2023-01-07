import os
import pathlib

from common.config import CommonConf


class ServerConf(CommonConf):
    """
    Настройки сервера по умолчанию
    """

    ROOT_DIR = pathlib.Path().resolve()
    LOGS_DIR = ROOT_DIR / "logs"
    DATA_DIR = ROOT_DIR / "data"
    DB_NAME = "jim_server_db.sqlite"
    DB_PATH = DATA_DIR / DB_NAME
    DB_CONFIG = {
        "TEST_URL": "sqlite:///:memory:",
        "URL": f"sqlite:///data/{DB_NAME}",
        "USER": "",
        "PSWD": "",
    }

    DEFAULT_LISTENER_ADDRESS = "0.0.0.0"
    MAX_CONNECTIONS = 5
    MAIN_LOG_FILE_PATH = LOGS_DIR / "server.error.log"
    CALL_LOG_FILE_PATH = LOGS_DIR / "server.calls.log"


os.makedirs(ServerConf.LOGS_DIR, exist_ok=True)
os.makedirs(ServerConf.DATA_DIR, exist_ok=True)
