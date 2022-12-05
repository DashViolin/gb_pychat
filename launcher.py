# В этом файле задание 4 а) и б) (объединены).
# Комментарий относительно пункта а: после выполнения задания урока № 8 клиенты
# работают в дуплексном режиме, снова реализовывать режим "только чтение" нецелесообразно.
# Задание 5 формально выполнено в рамках предыдущих ДЗ, так как клиент и сервер
# уже реализованы в виде классов.
import platform
import subprocess
import sys
from time import sleep


def launch_processes(clients_count: int = 1):
    if clients_count < 1:
        print("Количество клиентов не должно быть меньше 1.")
        sys.exit(1)

    tasks = []
    if platform.system().lower() == "windows":
        tasks.append(subprocess.Popen("poetry run python server.py", creationflags=subprocess.CREATE_NEW_CONSOLE))
        print("Запущен сервер.")
        sleep(0.5)
        for num in range(1, clients_count + 1):
            user = f"user{num}"
            task = subprocess.Popen(
                f"poetry run python client.py -u {user}", creationflags=subprocess.CREATE_NEW_CONSOLE
            )
            tasks.append(task)
            print(f'Запущен клиент от имени "{user}".')
    else:
        # В общем случае задачу запуска подпроцессов в отдельных терминалах под Linux решить не удалось.
        # Есть решение с использованием вызова gnome-terminal, но его нельзя назвать универсальным.
        base_cmd = ["gnome-terminal", "--", "poetry", "run", "python"]
        server_cmd = ["server.py"]
        tasks.append(subprocess.Popen(base_cmd + server_cmd))
        print("Запущен сервер.")
        sleep(0.5)
        for num in range(1, clients_count + 1):
            user = f"user{num}"
            client_cmd = ["client.py", "-u", user]
            task = subprocess.Popen(base_cmd + client_cmd)
            tasks.append(task)
            print(f'Запущен клиент от имени "{user}".')

    while True:
        try:
            action = input('Для выхода введите "q": ')
            if action.strip() == "q":
                print("Завершение работы...")
                raise KeyboardInterrupt
        except KeyboardInterrupt:
            while tasks:
                victim = tasks.pop()
                print(f"Killing {victim}...")
                victim.kill()
            sys.exit(0)


if __name__ == "__main__":
    try:
        clients = int(input("Введите количество клиентов: "))
        launch_processes(clients_count=clients)
    except Exception as ex:
        print(ex)
