# Form implementation generated from reading ui file './server/gui/server_gui.ui'
#
# Created by: PyQt6 UI code generator 6.4.0
#
# WARNING: Any manual changes made to this file will be lost when pyuic6 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt6 import QtCore, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(300, 273)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.groupBox = QtWidgets.QGroupBox(self.centralwidget)
        self.groupBox.setObjectName("groupBox")
        self.formLayout_2 = QtWidgets.QFormLayout(self.groupBox)
        self.formLayout_2.setObjectName("formLayout_2")
        self.labelIP = QtWidgets.QLabel(self.groupBox)
        self.labelIP.setObjectName("labelIP")
        self.formLayout_2.setWidget(0, QtWidgets.QFormLayout.ItemRole.LabelRole, self.labelIP)
        self.lineEditIP = QtWidgets.QLineEdit(self.groupBox)
        self.lineEditIP.setObjectName("lineEditIP")
        self.formLayout_2.setWidget(0, QtWidgets.QFormLayout.ItemRole.FieldRole, self.lineEditIP)
        self.labelPort = QtWidgets.QLabel(self.groupBox)
        self.labelPort.setObjectName("labelPort")
        self.formLayout_2.setWidget(1, QtWidgets.QFormLayout.ItemRole.LabelRole, self.labelPort)
        self.lineEditPort = QtWidgets.QLineEdit(self.groupBox)
        self.lineEditPort.setObjectName("lineEditPort")
        self.formLayout_2.setWidget(1, QtWidgets.QFormLayout.ItemRole.FieldRole, self.lineEditPort)
        self.verticalLayout.addWidget(self.groupBox)
        self.pushButtonStartServer = QtWidgets.QPushButton(self.centralwidget)
        self.pushButtonStartServer.setObjectName("pushButtonStartServer")
        self.verticalLayout.addWidget(self.pushButtonStartServer)
        self.pushButtonAddContact = QtWidgets.QPushButton(self.centralwidget)
        self.pushButtonAddContact.setObjectName("pushButtonAddContact")
        self.verticalLayout.addWidget(self.pushButtonAddContact)
        self.pushButtonDeleteContact = QtWidgets.QPushButton(self.centralwidget)
        self.pushButtonDeleteContact.setObjectName("pushButtonDeleteContact")
        self.verticalLayout.addWidget(self.pushButtonDeleteContact)
        self.pushButtonClients = QtWidgets.QPushButton(self.centralwidget)
        self.pushButtonClients.setObjectName("pushButtonClients")
        self.verticalLayout.addWidget(self.pushButtonClients)
        self.pushButtonHistory = QtWidgets.QPushButton(self.centralwidget)
        self.pushButtonHistory.setObjectName("pushButtonHistory")
        self.verticalLayout.addWidget(self.pushButtonHistory)
        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "JIM-сервер"))
        self.groupBox.setTitle(_translate("MainWindow", "Настройки сервера"))
        self.labelIP.setText(_translate("MainWindow", "IP адрес"))
        self.labelPort.setText(_translate("MainWindow", "Порт"))
        self.pushButtonStartServer.setText(_translate("MainWindow", "Запуск сервера"))
        self.pushButtonAddContact.setText(_translate("MainWindow", "Добавить пользователя"))
        self.pushButtonDeleteContact.setText(_translate("MainWindow", "Удалить пользователя"))
        self.pushButtonClients.setText(_translate("MainWindow", "Просмотр списка клиентов"))
        self.pushButtonHistory.setText(_translate("MainWindow", "Просмотр истории клиентов"))


if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec())