import pathlib
import platform
import sys
from threading import Thread
from subprocess import Popen

from PyQt6 import QtCore, QtWidgets

from server.config import ServerConf
from server.gui.clients_window import Ui_ClientsWindow
from server.gui.history_window import Ui_HistoryWindow
from server.gui.main_window import Ui_MainWindow
from server.storage import ServerStorage
from server.transport import JIMServer


class Application:
    """
    Класс, задающий поведение главного окна графического интерфейса сервера
    """

    def __init__(self) -> None:
        self.app = QtWidgets.QApplication(sys.argv)
        self.main_window = QtWidgets.QMainWindow()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self.main_window)
        self.ui.lineEditIP.setText(ServerConf.DEFAULT_LISTENER_ADDRESS)
        self.ui.lineEditPort.setText(str(ServerConf.DEFAULT_PORT))
        self.clients_window = ClientsWindow()
        self.history_window = HistoryWindow()
        self.server_storage = ServerStorage()
        self.add_user_dialog = AddUserDialog()
        self._create_bindings()
        self.server_task = None

    def run(self):
        """Запускает отображение интерфейса"""
        self.main_window.show()
        ret_code = self.app.exec()
        self._on_click_stop_server()
        sys.exit(ret_code)

    def _create_bindings(self):
        self.add_user_dialog.accept_creds.connect(self._accept_creds_slot)
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
            self.server_task.terminate()
            self.server_task = None
            self.ui.pushButtonStartServer.setText("Запустить сервер")
            self.ui.pushButtonStartServer.clicked.connect(self._on_click_start_server)

    def _start_server(self):
        address = self.ui.lineEditIP.text().strip()
        port = self.ui.lineEditPort.text().strip()
        bin_path = pathlib.Path().resolve() / 'run_server_cli'
        if not bin_path.exists():
            server_path = pathlib.Path().resolve() / 'src/server/run_server_cli.py'
            if not server_path.exists():
                server_path = pathlib.Path().resolve() / 'run_server_cli.py'
            server_cmd = f'python {server_path} -a {address} -p {port}'
        else:
            server_cmd = f'{bin_path} -a {address} -p {port}'
        if platform.system().lower() == "windows":
            self.server_task = Popen(server_cmd, creationflags=subprocess.CREATE_NEW_CONSOLE)  # type: ignore
        else:
            self.server_task = Popen(server_cmd, executable='/bin/bash', shell=True)

    def _on_click_show_history(self):
        self.history_window.show()

    def _on_click_show_clients(self):
        self.clients_window.show()

    def _on_click_add_user(self):
        self.add_user_dialog.clear_data()
        self.add_user_dialog.show()

    def _accept_creds_slot(self, username: str, password: str):
        if username and password:
            if not self.server_storage.check_user_exists(username=username):
                self.server_storage.add_user(username=username, password=password)
                self._show_standard_notification(
                    title="Успешно", info=f'Пользователь "{username}" добавлен', is_warning=False
                )
            else:
                self._show_standard_notification(info="Пользовтель с таким именем уже существует")
        else:
            self._show_standard_notification(info='Поля "имя пользователя" и "пароль" не должны быть пустыми')

    def _on_click_del_user(self):
        username, ok = QtWidgets.QInputDialog.getText(self.main_window, "Удаление пользователя", "Введите имя:")
        if ok:
            if self.server_storage.check_user_exists(username=username):
                res = self.server_storage.remove_user(username=username)
                if res:
                    self._show_standard_notification(
                        title="Успешно", info=f'Пользователь "{username}" удален', is_warning=False
                    )
                else:
                    self._show_standard_notification(info="Ошибка удаления пользователя")
            else:
                self._show_standard_notification(info="Пользователь с таким именем отсутсвует")

    def _show_standard_notification(self, info: str, title: str = "Ошибка", is_warning: bool = True):
        msg = QtWidgets.QMessageBox()
        if is_warning:
            msg.setWindowIcon(self.app.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_MessageBoxWarning))
        else:
            msg.setWindowIcon(self.app.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_MessageBoxInformation))
        msg.setWindowTitle(title)
        msg.setInformativeText(info)
        msg.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Ok)
        msg.exec()


class HistoryWindow:
    """
    Класс окна просмотра истории входов клиентов
    """

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
    """
    Класс окна просмотра активных клиентов
    """

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


class AddUserDialog(QtWidgets.QDialog):
    """
    Класс диалога добавления пользователя
    """

    accept_creds = QtCore.pyqtSignal(str, str)

    def __init__(self, parent=None):
        super(AddUserDialog, self).__init__(parent)
        self.labelUsername = QtWidgets.QLabel(self)
        self.labelUsername.setText("Имя пользователя:")
        self.usernameLineEdit = QtWidgets.QLineEdit(self)
        self.labelPasswd1 = QtWidgets.QLabel(self)
        self.labelPasswd1.setText("Пароль:")
        self.passwd1LineEdit = QtWidgets.QLineEdit(self)
        self.passwd2LineEdit = QtWidgets.QLineEdit(self)
        self.labelPasswd2 = QtWidgets.QLabel(self)
        self.labelPasswd2.setText("Повторите пароль:")
        self.passwd1LineEdit.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
        self.passwd2LineEdit.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
        self.buttonSaveUser = QtWidgets.QPushButton("Сохранить")
        self.buttonSaveUser.clicked.connect(self.handle_registration)
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.labelUsername)
        layout.addWidget(self.usernameLineEdit)
        layout.addWidget(self.labelPasswd1)
        layout.addWidget(self.passwd1LineEdit)
        layout.addWidget(self.labelPasswd2)
        layout.addWidget(self.passwd2LineEdit)
        layout.addWidget(self.buttonSaveUser)

    def handle_registration(self):
        if self.passwd1LineEdit.text() == self.passwd2LineEdit.text():
            username = self.usernameLineEdit.text()
            password1 = self.passwd1LineEdit.text()
            password2 = self.passwd2LineEdit.text()
            if password1 == password2:
                self.accept_creds.emit(username, password1)
                self.close()
        else:
            QtWidgets.QMessageBox.warning(self, "Ошибка", "Пароли не совпадают")

    def clear_data(self):
        self.usernameLineEdit.clear()
        self.passwd1LineEdit.clear()
        self.passwd2LineEdit.clear()
