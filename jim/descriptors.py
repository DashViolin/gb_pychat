class PortDescriptor:
    def __get__(self, instance, instance_type):
        return instance.__dict__[self.name]

    def __set__(self, instance, value):
        if not 1023 < value < 65536:
            raise ValueError("Номер порта должен быть положительным числом в диапазоне [1024, 65535].")
        instance.__dict__[self.name] = value

    def __set_name__(self, owner, name):
        self.name = name

    def __delete__(self, instance):
        raise AttributeError("Невозможно удалить атрибут.")