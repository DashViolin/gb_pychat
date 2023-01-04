from common.config import CommonConf


class ClientConf(CommonConf):
    """
    Настройки клиента по умолчанию
    """

    DEFAULT_SERVER_IP = "127.0.0.1"
    MAIN_LOG_FILE_PATH = CommonConf.LOGS_DIR / "client.error.log"
    CALL_LOG_FILE_PATH = CommonConf.LOGS_DIR / "client.calls.log"
