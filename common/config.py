import logging
import os
import pathlib


class Common:
    MAX_PACKAGE_LENGTH = 640 * 2
    ENCODING = "utf-8"
    DEFAULT_PORT = 7777
    EXIT_WORD = "exit"
    LOGS_DIR = pathlib.Path().resolve() / "logs"


class Server:
    DEFAULT_LISTENER_ADDRESS = "0.0.0.0"
    MAX_CONNECTIONS = 5
    MAIN_LOGGER_NAME = "server.main"
    MAIN_LOGGER_LEVEL = logging.DEBUG
    MAIN_LOGGER_FORMAT = "%(asctime)s - %(levelname)s - %(module)s - %(message)s"
    LOG_FILE_PATH = Common.LOGS_DIR / "server.main.log"
    LOG_FILE_LEVEL = logging.DEBUG
    CONSOLE_LOG_LEVEL = logging.DEBUG


class Client:
    DEFAULT_SERVER_IP = "127.0.0.1"
    MAIN_LOGGER_NAME = "client.main"
    MAIN_LOGGER_LEVEL = logging.DEBUG
    MAIN_LOGGER_FORMAT = "%(asctime)s - %(levelname)s - %(module)s - %(message)s"
    LOG_FILE_PATH = Common.LOGS_DIR / "client.main.log"
    LOG_FILE_LEVEL = logging.DEBUG
    CONSOLE_LOG_LEVEL = logging.DEBUG


os.makedirs(Common.LOGS_DIR, exist_ok=True)
