import sys
from textwrap import dedent
from threading import Thread

from jinja2 import Template
from PyQt6 import QtGui, QtWidgets

from config import ClientConf
from gui_client.main_window import Ui_MainWindow
from jim.client import JIMClient

browser_msg_template = dedent(
    """
    <style>
        div.user {
            text-align: right;
        }
    </style>
    {% for message in messages %}
        <div class="{% if message.sender==current_user %}user{% else %}contact{% endif %}">
            <p>
                <u><b>{{ message.sender }}</b>(<i> {{ message.time }}</i>)</u>
                <br/>
                {{ message.text }}
                <br/>
            </p>
        </div>
    {% endfor %}"""
)


class Application:
    def __init__(self) -> None:
        self.app = QtWidgets.QApplication(sys.argv)
        self.main_window = QtWidgets.QMainWindow()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self.main_window)

        self._connect_btn_label = "Подключиться"
        self._disconnect_btn_label = "Отключиться"

        self.client: JIMClient | None = None
        self.prev_contact_item: QtWidgets.QListWidgetItem | None = None
        self.chat_tamplate = Template(browser_msg_template)
        self._create_bindings()
        self._set_defaults()

    def run(self):
        self.main_window.show()
        sys.exit(self.app.exec())

    def _set_defaults(self):
        self.ui.pushButtonConnect.setText(self._connect_btn_label)
        self.ui.listWidgetContacts.clear()
        self.ui.textBrowserChat.clear()
        self.ui.textEditMessage.clear()
        self.ui.lineEditIP.setText(ClientConf.DEFAULT_SERVER_IP)
        self.ui.lineEditPort.setText(str(ClientConf.DEFAULT_PORT))
        self.ui.textBrowserChat.setReadOnly(True)
        self._switch_controls(is_enabled=False)

    def _switch_controls(self, is_enabled: bool):
        self.ui.pushButtonAddContact.setEnabled(is_enabled)
        self.ui.pushButtonDeleteContact.setEnabled(is_enabled)
        self.ui.pushButtonSend.setEnabled(is_enabled)

    def _create_bindings(self):
        self.ui.pushButtonConnect.clicked.connect(self._on_click_connect)
        self.ui.pushButtonAddContact.clicked.connect(self._on_click_add_contact)
        self.ui.pushButtonDeleteContact.clicked.connect(self._on_click_delete_contact)
        self.ui.pushButtonSend.clicked.connect(self._on_click_send)
        self.ui.listWidgetContacts.doubleClicked.connect(self._on_contact_double_click)

    def _bind_client_signals(self):
        if self.client:
            self.client.notifier.new_message.connect(self._on_accepted_new_message)
            self.client.notifier.connection_lost.connect(self._on_connection_lost)

    def show_standard_warning(self, info: str, title: str = "Ошибка", text: str = ""):
        msg = QtWidgets.QMessageBox()
        msg.setWindowIcon(self.app.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_MessageBoxWarning))
        msg.setWindowTitle(title)
        msg.setText(text)
        msg.setInformativeText(info)
        msg.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Ok)
        msg.exec()

    def _on_click_connect(self):
        def show_empty_params_message(empty_params):
            text = "Ошибка подключения к серверу."
            info = f"Не указаны параметры: {', '.join(empty_params)}"
            self.show_standard_warning(info=info, text=text)

        if self.ui.pushButtonConnect.text() == self._connect_btn_label:
            ip = self.ui.lineEditIP.text()
            port = self.ui.lineEditPort.text()
            username = self.ui.lineEditUsername.text()
            password = self.ui.lineEditPasswd.text()
            conn_params = {
                "IP адрес": ip,
                "Порт сервера": port,
                "Имя пользователя": username,
                "Пароль": password,
            }
            if all(conn_params.values()):
                self.client = JIMClient(ip=ip, port=int(port), username=username, password=password)
                self.client_task = Thread(target=self.client.run)
                self.client_task.daemon = True
                self.client_task.start()
                self._bind_client_signals()
                self._switch_controls(is_enabled=True)
                self._fill_contacts()
                self.ui.pushButtonConnect.setText(self._disconnect_btn_label)
            else:
                empty_params = [key for key, value in conn_params.items() if not value]
                show_empty_params_message(empty_params)
        else:
            if self.client:
                self.client.close()
            self._set_defaults()

    def _fill_contacts(self):
        self.ui.listWidgetContacts.clear()
        if self.client:
            contacts = self.client.storage.get_contact_list()
            for contact, is_active in contacts:
                item = QtWidgets.QListWidgetItem()
                item.setText(contact)
                if is_active:
                    item.setForeground(QtGui.QColor("gray"))
                self.ui.listWidgetContacts.addItem(item)

    def _fill_chat(self, contact_name):
        self.ui.textBrowserChat.setText(f"Пока пусто...")
        if self.client:
            messages = [
                {"sender": sender, "text": text, "time": timestamp.replace(microsecond=0).isoformat().replace("T", " ")}
                for text, sender, timestamp in self.client.storage.get_chat_messages(
                    user=self.client.username, contact=contact_name
                )
            ]
            if messages:
                chat_text = self._make_chat_text(messages=messages, current_user=self.client.username)
                self.ui.textBrowserChat.setText(chat_text)
                self.ui.textBrowserChat.verticalScrollBar().setValue(
                    self.ui.textBrowserChat.verticalScrollBar().maximum()
                )

    def _make_chat_text(self, messages: list[dict], current_user: str):
        data = {
            "messages": messages,
            "current_user": current_user,
        }
        text = self.chat_tamplate.render(**data)
        return text

    def _on_contact_double_click(self):
        contact_item = self.ui.listWidgetContacts.currentItem()
        originalBG = contact_item.background()
        if self.prev_contact_item:
            self.prev_contact_item.setBackground(originalBG)
        contact_item.setBackground(QtGui.QColor("lightBlue"))
        self.prev_contact_item = contact_item
        contact_name = contact_item.text()
        self._fill_chat(contact_name=contact_name)

    def _on_click_send(self):
        contact = self.ui.listWidgetContacts.currentItem().text()
        if self.client and contact:
            msg_text = self.ui.textEditMessage.toPlainText()
            if msg_text:
                self.client.send_msg(contact=contact, msg_text=msg_text)
                self._fill_chat(contact_name=contact)
                self.ui.textEditMessage.clear()

    def _on_click_add_contact(self):
        contact = self.show_add_contact_dialog()
        if contact and self.client:
            self.client.add_contact(contact_name=contact)
            self._fill_contacts()

    def _on_click_delete_contact(self):
        contact = self.ui.listWidgetContacts.currentItem().text()
        if contact and self.client:
            self.client.delete_contact(contact_name=contact)
            self._fill_contacts()

    def show_add_contact_dialog(self):
        contact, ok = QtWidgets.QInputDialog.getText(self.main_window, "Добавление пользователя", "Введите имя:")
        if ok:
            return contact
        return None

    def _on_accepted_new_message(self, sender):
        if sender == self.ui.listWidgetContacts.currentItem().text():
            self._fill_chat(sender)
        else:
            self._fill_contacts()

    def _on_connection_lost(self):
        self.show_standard_warning(info="Потеряно соединение с сервером.")

        self._set_defaults()
        if self.client:
            self.client.close()
