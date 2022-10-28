class Common:
    # Из методички: "Итоговое ограничение для JSON-объекта - 640 символов",
    # вольная трактовка - учитываем возможную двухбайтную кодировку:
    MAX_PACKAGE_LENGTH = 640 * 2
    ENCODING = "utf-8"
    DEFAULT_PORT = 7777
    EXIT_WORD = "exit"


class Sever:
    DEFAULT_LISTENER_ADDRESS = "0.0.0.0"
    MAX_CONNECTIONS = 5


class Client:
    DEFAULT_SERVER_IP = "127.0.0.1"
