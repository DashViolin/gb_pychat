import dis


class JIMMeta(type):
    """
    Метакласс служит для проверки корректности инициализации сокетов на предмет допустимых вызовов
    в классах сервера и клиента транспортных модулей
    """

    def __init__(self, clsname, bases, clsdict):
        method_calls = set()
        attrs = set()
        for func in clsdict:
            try:
                instructions = list(dis.get_instructions(clsdict[func]))
                for instr in instructions:
                    if instr.opname == "LOAD_METHOD":
                        method_calls.add(instr.argval)
                    elif instr.opname == "LOAD_GLOBAL":
                        attrs.add(instr.argval)
            except (SyntaxError, TypeError):  # dis.get_instructions() for docstring causes SyntaxError
                pass

        if "server" in clsname.lower() or "client" in clsname.lower():
            if not ("SOCK_STREAM" in attrs and "AF_INET" in attrs):
                raise TypeError("Некорректная инициализация сокета, необходимо использовать SOCK_STREAM и AF_INET.")
        if "server" in clsname.lower():
            if "connect" in method_calls:
                raise TypeError('Использование метода "connect" недопустимо в серверном классе')
        if "client" in clsname.lower():
            for banned_method in ("accept", "listen"):
                if banned_method in method_calls:
                    raise TypeError(f'В классе клиента нельзя использовать метод "{banned_method}"')

        super().__init__(clsname, bases, clsdict)
