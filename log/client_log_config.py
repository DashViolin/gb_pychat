import logging

from common.config import Client, Common

logger = logging.getLogger(Client.MAIN_LOGGER_NAME)
formatter = logging.Formatter(Client.MAIN_LOGGER_FORMAT)
logger.setLevel(Client.MAIN_LOGGER_LEVEL)

file_handler = logging.FileHandler(Client.LOG_FILE_PATH, encoding=Common.ENCODING)
file_handler.setLevel(Client.LOG_FILE_LEVEL)
file_handler.setFormatter(formatter)

console_handler = logging.StreamHandler()
console_handler.setLevel(Client.CONSOLE_LOG_LEVEL)
console_handler.setFormatter(formatter)

logger.addHandler(console_handler)
logger.addHandler(file_handler)

if __name__ == "__main__":
    logger.info("Тестовый запуск логирования")
