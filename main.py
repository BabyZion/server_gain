#!/usr/bin/python3

import sys
from datetime import datetime
from database import Database
from PyQt5 import QtWidgets, QtCore, Qt
from window import Ui_MainWindow
from beacon import Beacon
from logger import Logger
from server import Server
from dbSettings import Ui_dbSettings
from beaconSettings import Ui_BeaconSettings

__version__ = '1.2'


class Application(QtWidgets.QMainWindow):

    def __init__(self):
        super().__init__()
        self.settings = QtCore.QSettings('server_gain', 'app_settings')
        self.main_window = Ui_MainWindow()
        self.main_window.setupUi(self)
        self.main_window.pushButtonSend.pressed.connect(self.send_gprs_cmd)
        self.main_window.lineEdit.returnPressed.connect(self.send_gprs_cmd)
        self.main_window.pushButtonStart.pressed.connect(self.start_server)
        self.main_window.pushButtonDisconnect.pressed.connect(self.disconnect_client)
        self.main_window.checkBox.toggled.connect(self.auto_sending)
        self.main_window.checkBoxSSL.toggled.connect(self.check_certs)
        self.main_window.checkBoxBeacon.toggled.connect(self.beacon_test)
        self.main_window.actionSelectCert.triggered.connect(self.select_certs)
        self.main_window.actionCreateCert.triggered.connect(self.not_implemented_warning)
        self.main_window.actionDatabaseSettings.triggered.connect(self.db_settings)
        self.main_window.actionBeaconSettings.triggered.connect(self.beacon_settings)
        self.__change_server_widget_state(self.main_window.horizontalLayout_2)
        self.main_window.pushButtonDisconnect.setEnabled(False)
        self.databaseSettingsWindow = None
        self.beaconSettingsWindow = None
        self.show()
        self.time_format = '%Y.%m.%d %H:%M:%S.%f'
        self.server = Server()
        self.server.display_info.connect(self.append_text_browser)
        self.server.new_conn.connect(self.add_conn)
        self.server.closed_conn.connect(self.del_conn)
        self.server.to_db.connect(self.pass_to_database)
        self.database = Database(self.settings.value('dbname'), self.settings.value('user'),
            self.settings.value('host'), self.settings.value('password'))
        self.database.display_info.connect(self.append_text_browser)
        b_tDevices = self.settings.value('b_tDevices')
        b_period = self.settings.value('b_period')
        if b_period:
            b_period = int(b_period)
        else:
            b_period = 60
        self.beacon = Beacon(self.database, b_tDevices, b_period)
        self.beacon.display_info.connect(self.append_text_browser)
        self.logger = Logger('Application')
        self.logger.info(f"Application started.")
        self.__load_settings()
        self.server_settings_widgets = [self.main_window.labelPort, self.main_window.spinBox,
            self.main_window.radioButtonTCP, self.main_window.radioButtonUDP, self.main_window.checkBoxSSL]
        
    def append_text_browser(self, data):
        time_recv = datetime.strftime(datetime.now(), self.time_format)
        self.main_window.textBrowser.append(f'[{time_recv}] - {data}')

    def add_conn(self, imei):
        self.main_window.comboBox.addItem(imei)
        self.main_window.labelCount.setText(str(self.server.clients))
        self.main_window.pushButtonDisconnect.setEnabled(True)
        self.logger.info(f'New IMEI - {imei} added to client list. New no. of clients: {self.server.clients}.')
    
    def del_conn(self, imei):
        index = self.main_window.comboBox.findText(imei)
        self.main_window.comboBox.removeItem(index)
        self.main_window.labelCount.setText(str(self.server.clients))
        self.logger.info(f'IMEI - {imei} removed from client list. New no. of clients: {self.server.clients}.')
        if self.server.clients == 0: 
            self.main_window.pushButtonDisconnect.setEnabled(False)
            self.logger.warning(f'Server has no clients.')

    def send_gprs_cmd(self):
        cmd = self.main_window.lineEdit.text() + '\r\n'
        imei = self.main_window.comboBox.currentText()
        self.server.send_cmd(cmd, imei)
        self.logger.info(f'GPRS CMD {cmd} is sent to {imei}.')

    def start_server(self):
        # Start server
        self.trans_prot = self.main_window.buttonGroup.checkedButton().text()
        self.port = self.main_window.spinBox.value()
        self.use_ssl = self.main_window.checkBoxSSL.isChecked()
        self.__change_server_widget_state(self.server_settings_widgets)
        self.__change_server_widget_state(self.main_window.horizontalLayout_2)
        self.__inverse_start_stop_button('stop')
        self.main_window.actionSelectCert.setEnabled(False)
        self.server.create_socket(self.port, self.trans_prot, self.use_ssl)
        self.server.start()
        self.append_text_browser(f"{self.trans_prot} server started on port {self.port}. SSL enabled - {self.use_ssl}.")
        self.logger.info(f"{self.trans_prot} server started on port {self.port}. SSL enabled - {self.use_ssl}.")
        # Open connection to Database if configured.
        if self.main_window.checkBoxBeacon.isChecked():
            self.database.start()
            self.beacon.start()

    def stop_server(self):
        self.database.stop()
        self.beacon.stop()
        self.server.close()
        if self.main_window.checkBox.isChecked():
            self.main_window.checkBox.setChecked(False)
        self.__change_server_widget_state(self.server_settings_widgets)
        self.__change_server_widget_state(self.main_window.horizontalLayout_2)
        self.__inverse_start_stop_button('start')
        self.main_window.actionSelectCert.setEnabled(True)
        try:
            self.append_text_browser(f"{self.trans_prot} server on port {self.port} was closed with all it's connections.")
            self.logger.info(f"{self.trans_prot} server on port {self.port} was closed with all it's connections.")
        except AttributeError:
            pass

    def auto_sending(self):
        checked = self.main_window.checkBox.isChecked()
        period = self.main_window.spinBoxSeconds.value()
        self.server.automatic = checked
        self.server.automatic_period = period
        if checked:
            self.logger.info(f'Starting automatic GPRS CMD sending.')
            self.send_gprs_cmd()
        else:
            self.logger.info(f'Stopping automatic GPRS CMD sending.')
            self.server.stop_auto_sending()
        self.main_window.pushButtonSend.setEnabled(not checked)
        self.main_window.spinBoxSeconds.setEnabled(not checked)
        self.main_window.lineEdit.setEnabled(not checked)

    def disconnect_client(self):
        imei = self.main_window.comboBox.currentText()
        self.logger.info(f'Disconnect from client {imei} initiated by user action.')
        self.server.disconnect_client(imei)

    def cert_warning(self):
        warn = QtWidgets.QMessageBox(self)
        warn.setIcon(QtWidgets.QMessageBox.Warning)
        warn.setText("Not all certificates required for SSL communication are selected. "
            "Do you want to select them now?")
        warn.setWindowTitle("Certificate warning!")
        warn.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        ret_val = warn.exec_()
        if ret_val == QtWidgets.QMessageBox.Yes:
            self.select_certs()
            self.check_certs()
        else:
            self.main_window.checkBoxSSL.setChecked(False)
        warn.done(1)
        
    def check_certs(self):
        ssl_checkbox = self.main_window.checkBoxSSL
        if ssl_checkbox.isChecked():
            if not self.server.certfile or not self.server.keyfile:
                self.cert_warning()

    def select_certs(self):
        cert_files = QtWidgets.QFileDialog.getOpenFileNames(self, filter="Certfile, Keyfile (*.pem *.key)")
        if cert_files[0]:    
            for f in cert_files[0]:
                if f.endswith('.pem'): self.server.certfile = f
                if f.endswith('.key'): self.server.keyfile = f
            self.logger.info(f'Certificates selected - \nCertfile: {self.server.certfile}\n'
                f'Keyfile: {self.server.keyfile}')
            self.append_text_browser(f'Certificates selected - \nCertfile: {self.server.certfile}'
                f'\nKeyfile: {self.server.keyfile}')

    def db_settings(self):
        self.databaseSettingsWindow = DatabaseSettings(self.database)
        self.databaseSettingsWindow.show()

    def beacon_settings(self):
        self.beaconSettingsWindow = BeaconSettings(self.beacon)
        self.beaconSettingsWindow.show()

    def beacon_test(self):
        checked = self.main_window.checkBoxBeacon.isChecked()
        self.server.beacon = checked
        if checked:
            self.logger.info(f"Server is entering Beacon Testing mode.")
        else:
            self.logger.info(f"Server is exiting from Beacon Testing mode.")

    def pass_to_database(self, data):
        self.database.queue.put(data)

    def not_implemented_warning(self):
        warn = QtWidgets.QMessageBox(self)
        warn.setIcon(QtWidgets.QMessageBox.Warning)
        warn.setText("This feature is not yet implemented. :(")
        warn.setWindowTitle("Not implemented warning!")
        warn.setStandardButtons(QtWidgets.QMessageBox.Ok)
        self.append_text_browser(f'NOT IMPLEMENTED!!!')
        ret_val = warn.exec_()

    def closeEvent(self, event):
        self.stop_server()
        self.__save_settings()

    def __change_server_widget_state(self, layout):
        if isinstance(layout, list):
            for widget in layout:
                if widget.isEnabled():
                    widget.setEnabled(False)
                else:
                    widget.setEnabled(True)
        else:
            cnt = layout.count()
            for i in range(cnt):
                widget = layout.itemAt(i).widget()
                if widget.isEnabled():
                    widget.setEnabled(False)
                else:
                    widget.setEnabled(True)

    def __inverse_start_stop_button(self, state):
        self.main_window.pushButtonStart.setEnabled(True)
        self.main_window.pushButtonStart.disconnect()
        if state == 'start':
            self.main_window.pushButtonStart.setText('START')
            self.main_window.pushButtonStart.pressed.connect(self.start_server)
        elif state == 'stop':
            self.main_window.pushButtonStart.setText('STOP')
            self.main_window.pushButtonStart.pressed.connect(self.stop_server)

    def __load_settings(self):
        try:
            self.resize(self.settings.value('win_size'))
            self.move(self.settings.value('win_pos'))
            self.main_window.spinBox.setValue(int(self.settings.value('port')))
            for button in self.main_window.buttonGroup.buttons():
                if button.text() == self.settings.value('protocol'):
                    button.setChecked(True)
                    break
            self.server.certfile = self.settings.value('certfile')
            self.server.keyfile = self.settings.value('keyfile')
            if self.settings.value('ssl') == 'true':
                self.main_window.checkBoxSSL.setChecked(True)
            elif self.settings.value('ssl') == 'false': 
                self.main_window.checkBoxSSL.setChecked(False)
            if self.settings.value('beacon') == 'true':
                self.main_window.checkBoxBeacon.setChecked(True)
            elif self.settings.value('beacon') == 'false': 
                self.main_window.checkBoxBeacon.setChecked(False)
        except TypeError:
            pass

    def __save_settings(self):
        self.settings.setValue('win_size', self.size())
        self.settings.setValue('win_pos', self.pos())
        self.settings.setValue('port', self.main_window.spinBox.value())
        self.settings.setValue('protocol', self.main_window.buttonGroup.checkedButton().text())
        self.settings.setValue('ssl', self.main_window.checkBoxSSL.isChecked())
        self.settings.setValue('certfile', self.server.certfile)
        self.settings.setValue('keyfile', self.server.keyfile)
        self.settings.setValue('beacon', self.main_window.checkBoxBeacon.isChecked())
        self.settings.setValue('dbname', self.database.dbname)
        self.settings.setValue('user', self.database.user)
        self.settings.setValue('host', self.database.host)
        self.settings.setValue('password', self.database.password)
        self.settings.setValue('b_period', self.beacon.check_period)
        self.settings.setValue('b_tDevices', self.beacon.test_devices)


class DatabaseSettings(QtWidgets.QDialog):
    
    def __init__(self, db):
        super().__init__()
        self.settings_window = Ui_dbSettings()
        self.settings_window.setupUi(self)
        self.db = db
        self.settings_window.databaseNameLineEdit.setText(self.db.dbname)
        self.settings_window.userLineEdit.setText(self.db.user)
        self.settings_window.hostLineEdit.setText(self.db.host)
        self.settings_window.passwordLineEdit.setText(self.db.password)

    def accept(self):
        self.db.dbname = self.settings_window.databaseNameLineEdit.text()
        self.db.user = self.settings_window.userLineEdit.text()
        self.db.host = self.settings_window.hostLineEdit.text()
        self.db.password = self.settings_window.passwordLineEdit.text()
        if self.db.running:
            self.hide()
            self.db.disconnect()
            self.db.connect()
        self.done(1)


class BeaconSettings(QtWidgets.QDialog):
    
    def __init__(self, beacon):
        super().__init__()
        self.settings_window = Ui_BeaconSettings()
        self.settings_window.setupUi(self)
        self.beacon = beacon
        self.settings_window.periodLineEdit.setText(str(self.beacon.check_period))
        if self.beacon.test_devices:
            self.settings_window.tDevicesLineEdit.setText(str(self.beacon.test_devices).strip('][').replace("'", ''))
            # str(self.beacon.test_devices).strip('][').replace("'", '').strip()
        else:
            self.settings_window.tDevicesLineEdit.setText()

    def accept(self):
        self.beacon.check_period = int(self.settings_window.periodLineEdit.text())
        str_list = self.settings_window.tDevicesLineEdit.text()
        self.beacon.test_devices = str_list.strip('][').replace(" ", "").split(',')
        print(self.beacon.test_devices, type(self.beacon.test_devices))
        if self.beacon.running:
            self.hide()
            self.beacon.timer.cancel()
            self.beacon.timer.start()
        self.done(1)

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    aplc = Application()
    sys.exit(app.exec_())
