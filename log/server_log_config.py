import logging
from logging.handlers import TimedRotatingFileHandler

from common.config import Common, Server

logger = logging.getLogger(Server.MAIN_LOGGER_NAME)
formatter = logging.Formatter(Server.MAIN_LOGGER_FORMAT)
logger.setLevel(Server.MAIN_LOGGER_LEVEL)

file_handler = TimedRotatingFileHandler(
    filename=Server.LOG_FILE_PATH,
    encoding=Common.ENCODING,
    when="D",
    interval=1,
    backupCount=7,
)
file_handler.setLevel(Server.LOG_FILE_LEVEL)
file_handler.setFormatter(formatter)

console_handler = logging.StreamHandler()
console_handler.setLevel(Server.CONSOLE_LOG_LEVEL)
console_handler.setFormatter(formatter)

logger.addHandler(console_handler)
logger.addHandler(file_handler)

if __name__ == "__main__":
    logger.info("Тестовый запуск логирования")
