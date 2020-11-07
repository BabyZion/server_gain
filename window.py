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
        MainWindow.resize(799, 656)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.textBrowser = QtWidgets.QTextBrowser(self.centralwidget)
        self.textBrowser.setGeometry(QtCore.QRect(10, 10, 781, 521))
        self.textBrowser.setObjectName("textBrowser")
        self.layoutWidget = QtWidgets.QWidget(self.centralwidget)
        self.layoutWidget.setGeometry(QtCore.QRect(10, 580, 781, 26))
        self.layoutWidget.setObjectName("layoutWidget")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout(self.layoutWidget)
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.lineEdit = QtWidgets.QLineEdit(self.layoutWidget)
        self.lineEdit.setObjectName("lineEdit")
        self.horizontalLayout_2.addWidget(self.lineEdit)
        self.checkBox = QtWidgets.QCheckBox(self.layoutWidget)
        self.checkBox.setChecked(False)
        self.checkBox.setObjectName("checkBox")
        self.horizontalLayout_2.addWidget(self.checkBox)
        self.spinBoxSeconds = QtWidgets.QSpinBox(self.layoutWidget)
        self.spinBoxSeconds.setMinimumSize(QtCore.QSize(35, 0))
        self.spinBoxSeconds.setMaximum(10000)
        self.spinBoxSeconds.setProperty("value", 10)
        self.spinBoxSeconds.setObjectName("spinBoxSeconds")
        self.horizontalLayout_2.addWidget(self.spinBoxSeconds)
        self.pushButtonSend = QtWidgets.QPushButton(self.layoutWidget)
        self.pushButtonSend.setObjectName("pushButtonSend")
        self.horizontalLayout_2.addWidget(self.pushButtonSend)
        self.layoutWidget1 = QtWidgets.QWidget(self.centralwidget)
        self.layoutWidget1.setGeometry(QtCore.QRect(10, 540, 391, 31))
        self.layoutWidget1.setObjectName("layoutWidget1")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.layoutWidget1)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.labelImei = QtWidgets.QLabel(self.layoutWidget1)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.labelImei.sizePolicy().hasHeightForWidth())
        self.labelImei.setSizePolicy(sizePolicy)
        self.labelImei.setMaximumSize(QtCore.QSize(35, 16777215))
        self.labelImei.setObjectName("labelImei")
        self.horizontalLayout.addWidget(self.labelImei)
        self.comboBox = QtWidgets.QComboBox(self.layoutWidget1)
        self.comboBox.setObjectName("comboBox")
        self.horizontalLayout.addWidget(self.comboBox)
        self.labelClients = QtWidgets.QLabel(self.layoutWidget1)
        self.labelClients.setMaximumSize(QtCore.QSize(40, 16777215))
        self.labelClients.setObjectName("labelClients")
        self.horizontalLayout.addWidget(self.labelClients)
        self.labelCount = QtWidgets.QLabel(self.layoutWidget1)
        self.labelCount.setMaximumSize(QtCore.QSize(25, 16777215))
        self.labelCount.setObjectName("labelCount")
        self.horizontalLayout.addWidget(self.labelCount)
        self.pushButtonDisconnect = QtWidgets.QPushButton(self.layoutWidget1)
        self.pushButtonDisconnect.setMaximumSize(QtCore.QSize(80, 16777215))
        self.pushButtonDisconnect.setObjectName("pushButtonDisconnect")
        self.horizontalLayout.addWidget(self.pushButtonDisconnect)
        self.horizontalLayoutWidget = QtWidgets.QWidget(self.centralwidget)
        self.horizontalLayoutWidget.setGeometry(QtCore.QRect(450, 540, 341, 31))
        self.horizontalLayoutWidget.setObjectName("horizontalLayoutWidget")
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout(self.horizontalLayoutWidget)
        self.horizontalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.labelPort = QtWidgets.QLabel(self.horizontalLayoutWidget)
        self.labelPort.setMaximumSize(QtCore.QSize(30, 16777215))
        self.labelPort.setObjectName("labelPort")
        self.horizontalLayout_3.addWidget(self.labelPort)
        self.spinBox = QtWidgets.QSpinBox(self.horizontalLayoutWidget)
        self.spinBox.setFrame(True)
        self.spinBox.setReadOnly(False)
        self.spinBox.setAccelerated(True)
        self.spinBox.setMaximum(65535)
        self.spinBox.setProperty("value", 7253)
        self.spinBox.setObjectName("spinBox")
        self.horizontalLayout_3.addWidget(self.spinBox)
        self.radioButtonTCP = QtWidgets.QRadioButton(self.horizontalLayoutWidget)
        self.radioButtonTCP.setChecked(True)
        self.radioButtonTCP.setObjectName("radioButtonTCP")
        self.buttonGroup = QtWidgets.QButtonGroup(MainWindow)
        self.buttonGroup.setObjectName("buttonGroup")
        self.buttonGroup.addButton(self.radioButtonTCP)
        self.horizontalLayout_3.addWidget(self.radioButtonTCP)
        self.radioButtonUDP = QtWidgets.QRadioButton(self.horizontalLayoutWidget)
        self.radioButtonUDP.setChecked(False)
        self.radioButtonUDP.setObjectName("radioButtonUDP")
        self.buttonGroup.addButton(self.radioButtonUDP)
        self.horizontalLayout_3.addWidget(self.radioButtonUDP)
        self.pushButtonStart = QtWidgets.QPushButton(self.horizontalLayoutWidget)
        self.pushButtonStart.setObjectName("pushButtonStart")
        self.horizontalLayout_3.addWidget(self.pushButtonStart)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 799, 21))
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
        self.checkBox.setText(_translate("MainWindow", "Automatic"))
        self.pushButtonSend.setText(_translate("MainWindow", "Send"))
        self.labelImei.setText(_translate("MainWindow", "IMEI:"))
        self.labelClients.setText(_translate("MainWindow", "Clients:"))
        self.labelCount.setText(_translate("MainWindow", "0"))
        self.pushButtonDisconnect.setText(_translate("MainWindow", "Disconnect"))
        self.labelPort.setText(_translate("MainWindow", "Port:"))
        self.radioButtonTCP.setText(_translate("MainWindow", "TCP"))
        self.radioButtonUDP.setText(_translate("MainWindow", "UDP"))
        self.pushButtonStart.setText(_translate("MainWindow", "Start"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())
