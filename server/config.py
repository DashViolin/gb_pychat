from client.common.config import CommonConf


class ServerConf(CommonConf):
    """
    Настройки сервера по умолчанию
    """

    DB_NAME = "jim_server_db.sqlite"
    DB_PATH = CommonConf.DATA_DIR / DB_NAME
    DB_CONFIG = {
        "TEST_URL": "sqlite:///:memory:",
        "URL": f"sqlite:///data/{DB_NAME}",
        "USER": "",
        "PSWD": "",
    }

    DEFAULT_LISTENER_ADDRESS = "0.0.0.0"
    MAX_CONNECTIONS = 5
    MAIN_LOG_FILE_PATH = CommonConf.LOGS_DIR / "server.error.log"
    CALL_LOG_FILE_PATH = CommonConf.LOGS_DIR / "server.calls.log"
