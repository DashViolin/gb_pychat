import os
import pathlib


class CommonConf:
    MAX_PACKAGE_LENGTH = 640 * 2
    ENCODING = "utf-8"
    DEFAULT_PORT = 7777
    EXIT_WORD = "quit"
    ROOT_DIR = pathlib.Path().resolve()
    LOGS_DIR = ROOT_DIR / "logs"


class ServerConf:
    DEFAULT_LISTENER_ADDRESS = "0.0.0.0"
    MAX_CONNECTIONS = 5
    MSG_DATA_DIR = CommonConf.ROOT_DIR / "data"
    MSG_DUMP_FILE = MSG_DATA_DIR / "message_queue_dump.json"
    MAIN_LOG_FILE_PATH = CommonConf.LOGS_DIR / "server.error.log"
    CALL_LOG_FILE_PATH = CommonConf.LOGS_DIR / "server.calls.log"


class ClientConf:
    DEFAULT_SERVER_IP = "127.0.0.1"
    MAIN_LOG_FILE_PATH = CommonConf.LOGS_DIR / "client.error.log"
    CALL_LOG_FILE_PATH = CommonConf.LOGS_DIR / "client.calls.log"


os.makedirs(CommonConf.LOGS_DIR, exist_ok=True)
