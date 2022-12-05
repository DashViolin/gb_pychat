import logging
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler

from config import CommonConf, ServerConf

main_logger = logging.getLogger("server.main")
main_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(module)s - %(message)s")
main_logger.setLevel(logging.DEBUG)

file_handler = TimedRotatingFileHandler(
    filename=ServerConf.MAIN_LOG_FILE_PATH,
    encoding=CommonConf.ENCODING,
    when="D",
    interval=1,
    backupCount=7,
)
file_handler.setLevel(logging.WARNING)
file_handler.setFormatter(main_formatter)
main_logger.addHandler(file_handler)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(main_formatter)
main_logger.addHandler(console_handler)


call_logger = logging.getLogger("server.calls")
call_logger.setLevel(logging.DEBUG)
call_handler = RotatingFileHandler(
    filename=ServerConf.CALL_LOG_FILE_PATH,
    maxBytes=1024 * 100000,  # 100000 KiB
    backupCount=7,
    encoding=CommonConf.ENCODING,
)
call_formatter = logging.Formatter("%(asctime)s - %(message)s")
call_handler.setFormatter(call_formatter)
call_handler.setLevel(logging.DEBUG)
call_logger.addHandler(call_handler)