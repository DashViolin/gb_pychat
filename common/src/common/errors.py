class ServerDisconnectError(Exception):
    """
    Исключение - сервер отключился
    """

    def __str__(self):
        return "Потеряно соединение с сервером."


class IncorrectDataRecivedError(Exception):
    """
    Исключение - некорректные данные получены от сокета
    """

    def __str__(self):
        return "Принято некорректное сообщение от удалённого компьютера."


class NonDictInputError(Exception):
    """
    Исключение - аргумент функции не словарь
    """

    def __str__(self):
        return "Аргумент функции должен быть словарём."


class ReqiuredFieldMissingError(Exception):
    """
    Ошибка - отсутствует обязательное поле в принятом словаре
    """

    def __init__(self, missing_fields: set):
        self.missing_fields = list(sorted(missing_fields))

    def __str__(self):
        return f'В принятом словаре отсутствуют обязательные поля: {", ".join(self.missing_fields)}.'
