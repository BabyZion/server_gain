# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'window.ui'
#
# Created by: PyQt5 UI code generator 5.15.1
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(852, 729)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.textBrowser = QtWidgets.QTextBrowser(self.centralwidget)
        font = QtGui.QFont()
        font.setPointSize(11)
        self.textBrowser.setFont(font)
        self.textBrowser.setObjectName("textBrowser")
        self.verticalLayout.addWidget(self.textBrowser)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.labelImei = QtWidgets.QLabel(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.labelImei.sizePolicy().hasHeightForWidth())
        self.labelImei.setSizePolicy(sizePolicy)
        self.labelImei.setMaximumSize(QtCore.QSize(35, 16777215))
        self.labelImei.setObjectName("labelImei")
        self.horizontalLayout.addWidget(self.labelImei)
        self.comboBox = QtWidgets.QComboBox(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.comboBox.sizePolicy().hasHeightForWidth())
        self.comboBox.setSizePolicy(sizePolicy)
        self.comboBox.setMinimumSize(QtCore.QSize(150, 0))
        self.comboBox.setMaximumSize(QtCore.QSize(225, 16777215))
        self.comboBox.setObjectName("comboBox")
        self.horizontalLayout.addWidget(self.comboBox)
        self.labelClients = QtWidgets.QLabel(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.labelClients.sizePolicy().hasHeightForWidth())
        self.labelClients.setSizePolicy(sizePolicy)
        self.labelClients.setMaximumSize(QtCore.QSize(40, 16777215))
        self.labelClients.setObjectName("labelClients")
        self.horizontalLayout.addWidget(self.labelClients)
        self.labelCount = QtWidgets.QLabel(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.labelCount.sizePolicy().hasHeightForWidth())
        self.labelCount.setSizePolicy(sizePolicy)
        self.labelCount.setMaximumSize(QtCore.QSize(25, 16777215))
        self.labelCount.setObjectName("labelCount")
        self.horizontalLayout.addWidget(self.labelCount)
        self.pushButtonDisconnect = QtWidgets.QPushButton(self.centralwidget)
        self.pushButtonDisconnect.setMaximumSize(QtCore.QSize(80, 16777215))
        self.pushButtonDisconnect.setCheckable(False)
        self.pushButtonDisconnect.setChecked(False)
        self.pushButtonDisconnect.setObjectName("pushButtonDisconnect")
        self.horizontalLayout.addWidget(self.pushButtonDisconnect)
        spacerItem = QtWidgets.QSpacerItem(13, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.labelPort = QtWidgets.QLabel(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.labelPort.sizePolicy().hasHeightForWidth())
        self.labelPort.setSizePolicy(sizePolicy)
        self.labelPort.setMaximumSize(QtCore.QSize(30, 16777215))
        self.labelPort.setObjectName("labelPort")
        self.horizontalLayout.addWidget(self.labelPort)
        self.spinBox = QtWidgets.QSpinBox(self.centralwidget)
        self.spinBox.setMaximumSize(QtCore.QSize(80, 16777215))
        self.spinBox.setFrame(True)
        self.spinBox.setReadOnly(False)
        self.spinBox.setAccelerated(True)
        self.spinBox.setMaximum(65535)
        self.spinBox.setProperty("value", 6969)
        self.spinBox.setObjectName("spinBox")
        self.horizontalLayout.addWidget(self.spinBox)
        self.radioButtonTCP = QtWidgets.QRadioButton(self.centralwidget)
        self.radioButtonTCP.setMaximumSize(QtCore.QSize(50, 16777215))
        self.radioButtonTCP.setChecked(True)
        self.radioButtonTCP.setObjectName("radioButtonTCP")
        self.buttonGroup = QtWidgets.QButtonGroup(MainWindow)
        self.buttonGroup.setObjectName("buttonGroup")
        self.buttonGroup.addButton(self.radioButtonTCP)
        self.horizontalLayout.addWidget(self.radioButtonTCP)
        self.radioButtonUDP = QtWidgets.QRadioButton(self.centralwidget)
        self.radioButtonUDP.setMaximumSize(QtCore.QSize(50, 16777215))
        self.radioButtonUDP.setChecked(False)
        self.radioButtonUDP.setObjectName("radioButtonUDP")
        self.buttonGroup.addButton(self.radioButtonUDP)
        self.horizontalLayout.addWidget(self.radioButtonUDP)
        self.pushButtonStart = QtWidgets.QPushButton(self.centralwidget)
        self.pushButtonStart.setMaximumSize(QtCore.QSize(80, 16777215))
        self.pushButtonStart.setObjectName("pushButtonStart")
        self.horizontalLayout.addWidget(self.pushButtonStart)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.lineEdit = QtWidgets.QLineEdit(self.centralwidget)
        self.lineEdit.setObjectName("lineEdit")
        self.horizontalLayout_2.addWidget(self.lineEdit)
        self.checkBox = QtWidgets.QCheckBox(self.centralwidget)
        self.checkBox.setChecked(False)
        self.checkBox.setObjectName("checkBox")
        self.horizontalLayout_2.addWidget(self.checkBox)
        self.spinBoxSeconds = QtWidgets.QSpinBox(self.centralwidget)
        self.spinBoxSeconds.setMinimumSize(QtCore.QSize(35, 0))
        self.spinBoxSeconds.setMaximum(10000)
        self.spinBoxSeconds.setProperty("value", 10)
        self.spinBoxSeconds.setObjectName("spinBoxSeconds")
        self.horizontalLayout_2.addWidget(self.spinBoxSeconds)
        self.pushButtonSend = QtWidgets.QPushButton(self.centralwidget)
        self.pushButtonSend.setObjectName("pushButtonSend")
        self.horizontalLayout_2.addWidget(self.pushButtonSend)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 852, 22))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.labelImei.setText(_translate("MainWindow", "IMEI:"))
        self.labelClients.setText(_translate("MainWindow", "Clients:"))
        self.labelCount.setText(_translate("MainWindow", "0"))
        self.pushButtonDisconnect.setText(_translate("MainWindow", "Disconnect"))
        self.labelPort.setText(_translate("MainWindow", "Port:"))
        self.radioButtonTCP.setText(_translate("MainWindow", "TCP"))
        self.radioButtonUDP.setText(_translate("MainWindow", "UDP"))
        self.pushButtonStart.setText(_translate("MainWindow", "Start"))
        self.checkBox.setText(_translate("MainWindow", "Automatic"))
        self.pushButtonSend.setText(_translate("MainWindow", "Send"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())
