import platform
import subprocess
import sys

from PyQt6 import QtWidgets

from config import ServerConf
from gui_server.clients_window import Ui_ClientsWindow
from gui_server.history_window import Ui_HistoryWindow
from gui_server.main_window import Ui_MainWindow
from jim.server_storage import ServerStorage


class Application:
    def __init__(self) -> None:
        self.app = QtWidgets.QApplication(sys.argv)
        self.main_window = QtWidgets.QMainWindow()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self.main_window)
        self.ui.lineEditIP.setText(ServerConf.DEFAULT_LISTENER_ADDRESS)
        self.ui.lineEditPort.setText(str(ServerConf.DEFAULT_PORT))
        self.clients_window = ClientsWindow()
        self.history_window = HistoryWindow()
        self._create_bindings()
        self.server_task = None
        self.server_storage = ServerStorage()

    def run(self):
        self.main_window.show()
        sys.exit(self.app.exec())

    def _create_bindings(self):
        self.ui.pushButtonAddContact.clicked.connect(self._on_click_add_user)
        self.ui.pushButtonDeleteContact.clicked.connect(self._on_click_del_user)
        self.ui.pushButtonClients.clicked.connect(self._on_click_show_clients)
        self.ui.pushButtonHistory.clicked.connect(self._on_click_show_history)
        self.ui.pushButtonStartServer.clicked.connect(self._on_click_start_server)

    def _on_click_start_server(self):
        if not self.server_task:
            self._start_server()
            self.ui.pushButtonStartServer.setText("Остановить сервер")
            self.ui.pushButtonStartServer.clicked.connect(self._on_click_stop_server)

    def _on_click_stop_server(self):
        if self.server_task:
            self.server_task.kill()
            self.ui.pushButtonStartServer.setText("Запустить сервер")
            self.ui.pushButtonStartServer.clicked.connect(self._on_click_start_server)

    def _start_server(self):
        if platform.system().lower() == "windows":
            self.server_task = subprocess.Popen("poetry run python server.py", creationflags=subprocess.CREATE_NEW_CONSOLE)  # type: ignore
        else:
            address = self.ui.lineEditIP.text().strip()
            port = self.ui.lineEditPort.text().strip()
            base_cmd = ["gnome-terminal", "--", "poetry", "run", "python"]
            server_cmd = ["server.py", "-a", address, "-p", port]
            self.server_task = subprocess.Popen(base_cmd + server_cmd)

    def _on_click_show_history(self):
        self.history_window.show()

    def _on_click_show_clients(self):
        self.clients_window.show()

    def _on_click_add_user(self):
        username, ok = QtWidgets.QInputDialog.getText(self.main_window, "Добавление пользователя", "Введите имя:")
        if not ok:
            return
        password, ok = QtWidgets.QInputDialog.getText(self.main_window, "Добавление пользователя", "Введите пароль:")
        if not ok:
            return
        self.server_storage.register_user(username=username, password=password)

    def _on_click_del_user(self):
        pass


class HistoryWindow:
    def __init__(self) -> None:
        self.server_storage = ServerStorage()
        self.window = QtWidgets.QWidget()
        self.ui = Ui_HistoryWindow()
        self.ui.setupUi(self.window)

    def show(self):
        self.update_data()
        self.window.show()
        self.ui.tableWidget.show()

    def update_data(self):
        users_history = self.server_storage.get_users_history()
        header_labels = ["Имя пользователя", "IP адрес", "Дата и время входа"]
        self.ui.tableWidget.setRowCount(len(users_history))
        self.ui.tableWidget.setColumnCount(len(header_labels))
        self.ui.tableWidget.setHorizontalHeaderLabels(header_labels)
        header = self.ui.tableWidget.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeMode.Stretch)

        for index, (username, ip_address, login_timestamp) in enumerate(users_history):
            item_user = QtWidgets.QTableWidgetItem(username)
            item_ip = QtWidgets.QTableWidgetItem(ip_address)
            item_timestamp = QtWidgets.QTableWidgetItem(str(login_timestamp.replace(microsecond=0)))
            self.ui.tableWidget.setItem(index, 0, item_user)
            self.ui.tableWidget.setItem(index, 1, item_ip)
            self.ui.tableWidget.setItem(index, 2, item_timestamp)


class ClientsWindow:
    def __init__(self) -> None:
        self.server_storage = ServerStorage()
        self.window = QtWidgets.QWidget()
        self.ui = Ui_ClientsWindow()
        self.ui.setupUi(self.window)

    def show(self):
        self.update_data()
        self.window.show()
        self.ui.tableWidget.show()

    def update_data(self):
        active_users = self.server_storage.get_active_users()
        header_labels = ["Имя пользователя"]
        self.ui.tableWidget.setRowCount(len(active_users))
        self.ui.tableWidget.setColumnCount(len(header_labels))
        self.ui.tableWidget.setHorizontalHeaderLabels(header_labels)
        header = self.ui.tableWidget.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.Stretch)
        for index, user in enumerate(active_users):
            item_user = QtWidgets.QTableWidgetItem(user)
            self.ui.tableWidget.setItem(index, 0, item_user)
