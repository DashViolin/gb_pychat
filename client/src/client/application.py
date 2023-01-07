import sys
from textwrap import dedent
from threading import Thread

from common.schema import Keys
from jinja2 import Template
from PyQt6 import QtWidgets

from .config import ClientConf
from .gui.main_window import Ui_MainWindow
from .transport import JIMClient


def get_html_message_template() -> Template:
    """Возвращает шаблон HTML-разметки для рендеринга окна чата"""
    return Template(
        dedent(
            """
    <style>
        div.user {
            text-align: right;
        }
    </style>
    {% for message in messages %}
        <div class="{% if message.is_incoming %}contact{% else %}user{% endif %}">
            <p>
                <u>
                    {% if message.is_incoming %}
                        <b>{{ contact }}</b>
                    {% else %}
                        <b>{{ current_user }}</b>
                    {% endif %}
                    (<i>{{ message.time }}</i>)
                    {% if not message.is_delivered %}
                        <b>[Не доставлено]</b>
                    {% endif %}
                </u>
                <br/>
                {{ message.text }}
                <br/>
            </p>
        </div>
    {% endfor %}"""
        )
    )


class Application:
    """
    Класс, задающий поведение графического интерфейса клиента
    """

    def __init__(self) -> None:
        self.app = QtWidgets.QApplication(sys.argv)
        self.main_window = QtWidgets.QMainWindow()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self.main_window)

        self._connect_btn_label = "Подключиться"
        self._disconnect_btn_label = "Отключиться"

        self.client: JIMClient | None = None
        self.current_chat = None
        self.prev_contact_item: QtWidgets.QListWidgetItem | None = None
        self.chat_tamplate = get_html_message_template()
        self._create_bindings()
        self._set_defaults()

    def run(self):
        """Запускает отображение интерфейса"""
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
            self.client.notifier.new_message.connect(self._on_accept_new_message)
            self.client.notifier.connection_lost.connect(self._on_connection_lost)
            self.client.notifier.contacts_updated.connect(self._fill_contacts)

    def _show_standard_warning(self, info: str, title: str = "Ошибка", text: str = "", is_warning: bool = True):
        msg = QtWidgets.QMessageBox()
        msg.resize(100, 50)
        if is_warning:
            msg.setWindowIcon(self.app.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_MessageBoxWarning))
        else:
            msg.setWindowIcon(self.app.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_MessageBoxInformation))
        msg.setWindowTitle(title)
        msg.setText(text)
        msg.setInformativeText(info)
        msg.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Ok)
        msg.exec()

    def _on_click_connect(self):
        def show_empty_params_message(empty_params):
            text = "Ошибка подключения к серверу."
            info = f"Не указаны параметры: {', '.join(empty_params)}"
            self._show_standard_warning(info=info, text=text)

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
                self.client = JIMClient(ip=ip, port=port, username=username, password=password)
                ok, resp = self.client.authenticate()
                if ok:
                    self._bind_client_signals()
                    self._switch_controls(is_enabled=True)
                    self.client_task = Thread(target=self.client.run)
                    self.client_task.daemon = True
                    self.client_task.start()
                    self._fill_contacts()
                    self.ui.pushButtonConnect.setText(self._disconnect_btn_label)
                elif resp:
                    message = resp.get(Keys.ALERT) or resp.get(Keys.ERROR)
                    self._show_standard_warning(info=message)  # type: ignore
                else:
                    self._show_standard_warning(info="Не удалось подключиться к серверу")  # type: ignore
            else:
                empty_params = [key for key, value in conn_params.items() if not value]
                show_empty_params_message(empty_params)
        else:
            if self.client:
                self.client.close()
            self._set_defaults()

    def _fill_contacts(self):
        current_contact_name = None
        current_contact = None
        try:
            current_contact_name = self.ui.listWidgetContacts.currentItem().text()
        except AttributeError:
            pass
        self.ui.listWidgetContacts.clear()
        if self.client:
            contacts = self.client.storage.get_contact_list()
            for contact in contacts:
                item = QtWidgets.QListWidgetItem()
                item.setText(contact)
                self.ui.listWidgetContacts.addItem(item)
                if contact == current_contact_name:
                    current_contact = item
        if current_contact:
            self.ui.listWidgetContacts.setCurrentItem(current_contact)

    def _fill_chat(self, contact_name):
        self.ui.textBrowserChat.setText(f"Пока пусто...")
        if self.client:
            messages = [
                {
                    "text": text,
                    "is_incoming": is_incoming,
                    "is_delivered": is_delivered,
                    "time": timestamp.replace(microsecond=0).isoformat().replace("T", " "),
                }
                for text, is_incoming, is_delivered, timestamp in self.client.storage.get_chat_messages(
                    contact=contact_name
                )
            ]
            if messages:
                chat_text = self._make_chat_text(
                    messages=messages, current_user=self.client.username, contact=contact_name
                )
                self.ui.textBrowserChat.setText(chat_text)
                self.ui.textBrowserChat.verticalScrollBar().setValue(
                    self.ui.textBrowserChat.verticalScrollBar().maximum()
                )

    def _make_chat_text(self, messages: list[dict], current_user: str, contact: str):
        data = {
            "messages": messages,
            "current_user": current_user,
            "contact": contact,
        }
        text = self.chat_tamplate.render(**data)
        return text

    def _on_contact_double_click(self):
        contact_item = self.ui.listWidgetContacts.currentItem()
        contact_name = contact_item.text()
        self.current_chat = contact_name
        self._fill_chat(contact_name=contact_name)

    def _on_click_send(self):
        try:
            contact = self.ui.listWidgetContacts.currentItem().text()
            if self.client and contact:
                self.client.resend_not_delivered(contact=contact)
                msg_text = self.ui.textEditMessage.toPlainText()
                if msg_text:
                    self.client.send_msg(contact=contact, msg_text=msg_text)
                    self.ui.textEditMessage.clear()
            self._fill_chat(contact_name=contact)
        except AttributeError:
            self._show_standard_warning("Выберите контакт из списка")

    def _on_click_add_contact(self):
        contact = self._show_add_contact_dialog()
        if self.client and contact:
            if contact == self.client.username:
                self._show_standard_warning(info="Нельзя добавлять себя в контакты")
                return
            ok = self.client.add_contact(contact_name=contact)
            if ok:
                self._fill_contacts()
            else:
                self._show_standard_warning(info="Контакт не найден")

    def _on_click_delete_contact(self):
        try:
            contact = self.ui.listWidgetContacts.currentItem().text()
            if contact and self.client:
                ok = self.client.delete_contact(contact_name=contact)
                if ok:
                    self._fill_contacts()
                    if self.current_chat == contact:
                        self.ui.textBrowserChat.clear()
                else:
                    self._show_standard_warning(info="Контакт не найден")
        except AttributeError:
            self._show_standard_warning("Выберите контакт из списка")

    def _show_add_contact_dialog(self):
        contact, ok = QtWidgets.QInputDialog.getText(self.main_window, "Добавление пользователя", "Введите имя:")
        if ok:
            return contact
        return None

    def _on_accept_new_message(self, sender):
        try:
            if sender == self.ui.listWidgetContacts.currentItem().text():
                self._fill_chat(sender)
        except AttributeError:
            pass
        finally:
            self._fill_contacts()

    def _on_connection_lost(self):
        self._show_standard_warning(info="Потеряно соединение с сервером.")

        self._set_defaults()
        if self.client:
            self.client.close()
