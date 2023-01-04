import platform
import subprocess
import sys
from time import sleep


def launch_processes(clients_count: int = 3):
    if clients_count < 1:
        print("Количество клиентов не должно быть меньше 1.")
        sys.exit(1)

    tasks = []
    if platform.system().lower() == "windows":
        tasks.append(subprocess.Popen("poetry run python server.pyw"))
        print("Запущен сервер.")
        sleep(0.5)
        for num in range(1, clients_count + 1):
            task = subprocess.Popen("poetry run python client.pyw")
            tasks.append(task)
            print(f"Запущен клиент {num}")
    else:
        base_cmd = ["poetry", "run", "python"]
        server_cmd = ["server.pyw"]
        tasks.append(subprocess.Popen(base_cmd + server_cmd))
        print("Запущен сервер.")
        sleep(0.5)
        for num in range(1, clients_count + 1):
            client_cmd = ["client.pyw"]
            task = subprocess.Popen(base_cmd + client_cmd)
            tasks.append(task)
            print(f"Запущен клиент {num}")

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
        clients = input("Введите количество клиентов (по умолчанию - 3): ").strip()
        if not clients:
            launch_processes()
        else:
            launch_processes(clients_count=int(clients))
    except Exception as ex:
        print(ex)
