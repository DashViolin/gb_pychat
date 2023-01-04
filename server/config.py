from common.config import CommonConf


class ServerConf(CommonConf):
    """
    Настройки сервера по умолчанию
    """

    DB_CONFIG = {
        "TEST_URL": "sqlite:///:memory:",
        "URL": "sqlite:///data/jim_server_db.sqlite",
        "USER": "",
        "PSWD": "",
    }
    DEFAULT_LISTENER_ADDRESS = "0.0.0.0"
    MAX_CONNECTIONS = 5
    MAIN_LOG_FILE_PATH = CommonConf.LOGS_DIR / "server.error.log"
    CALL_LOG_FILE_PATH = CommonConf.LOGS_DIR / "server.calls.log"
