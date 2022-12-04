import logging
from logging.handlers import RotatingFileHandler

from config import ClientConf, CommonConf

main_logger = logging.getLogger("client.main")
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(module)s - %(message)s")
main_logger.setLevel(logging.DEBUG)

file_handler = logging.FileHandler(
    ClientConf.MAIN_LOG_FILE_PATH,
    encoding=CommonConf.ENCODING,
)
file_handler.setLevel(logging.WARNING)
file_handler.setFormatter(formatter)
main_logger.addHandler(file_handler)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)
main_logger.addHandler(console_handler)


call_logger = logging.getLogger("client.call")
call_logger.setLevel(logging.DEBUG)
call_handler = RotatingFileHandler(
    filename=ClientConf.CALL_LOG_FILE_PATH,
    maxBytes=1024 * 100000,  # 100000 KiB
    encoding=CommonConf.ENCODING,
    backupCount=7,
)
call_formatter = logging.Formatter("%(asctime)s - %(message)s")
call_handler.setFormatter(call_formatter)
call_handler.setLevel(logging.DEBUG)
call_logger.addHandler(call_handler)
