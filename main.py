#!/usr/bin/python3

import sys
import socket
import ssl
import select
import parselib
import time
import threading
import binascii
import libscrc
from logger import Logger
from datetime import datetime
from database import Database
from PyQt5 import QtWidgets, QtCore, Qt
from window import Ui_MainWindow
from dbSettings import Ui_dbSettings

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
        self.__change_server_widget_state(self.main_window.horizontalLayout_2)
        self.main_window.pushButtonDisconnect.setEnabled(False)
        self.databaseSettingsWindow = None
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

    def stop_server(self):
        self.server.close()
        if self.main_window.checkBox.isChecked():
            self.main_window.checkBox.setChecked(False)
        self.__change_server_widget_state(self.server_settings_widgets)
        self.__change_server_widget_state(self.main_window.horizontalLayout_2)
        self.__inverse_start_stop_button('start')
        self.main_window.actionSelectCert.setEnabled(True)
        self.append_text_browser(f"{self.trans_prot} server on port {self.port} was closed with all it's connections.")
        self.logger.info(f"{self.trans_prot} server on port {self.port} was closed with all it's connections.")

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
            self.db.settings_changed = True
        self.done(1)


class Server(QtCore.QThread):

    display_info = QtCore.pyqtSignal(str)
    new_conn = QtCore.pyqtSignal(str)
    closed_conn = QtCore.pyqtSignal(str)
    to_db = QtCore.pyqtSignal(object)

    IMEI_MSG_HEADER = 4
    TCP_MSG_HEADER = 16
    UDP_END_PACKET = bytes(b'\x00\x00\x00\x00')

    def __init__(self):
        super().__init__()
        self.clients = 0
        self.clientmap = {} # clientmap[imei] = conn_entity (socket or tuple of addr and port)
        self.conn_threads = []
        self.time_format = '%Y.%m.%d %H:%M:%S.%f'
        self.running = False
        self.use_ssl = None
        self.certfile = None
        self.keyfile = None
        self.automatic = None
        self.automatic_period = None
        self.automatic_imei = None
        self.auto_thread = None
        self.beacon = None
        self.lock = threading.Lock()
        self.logger = Logger('Server')
        self.raw_logger = Logger('RAW', 'raw.log')
        self.logger.info(f'Server is created.')

    def create_socket(self, port, trans_prot, use_ssl):
        self.host = '0.0.0.0'
        self.port = int(port)
        self.username = "SERVER"
        self.trans_prot = trans_prot
        self.use_ssl = use_ssl
        if self.trans_prot == 'TCP':
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        elif self.trans_prot == 'UDP':
            self.server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((self.host, self.port))
        if self.use_ssl:
            self.ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            self.ssl_context.load_cert_chain(certfile=self.certfile, keyfile=self.keyfile)
        self.logger.info(f'{self.trans_prot} socket created and binded to {self.port} port.')

    def receive(self, channel, imei=False):
        full_msg = ''
        new_msg = True
        receive = True
        while receive:
            # Receiving has to be done like this on Windows,
            # otherwise it crashes when disconnecting from client.
            msg = ''
            try:
                msg = channel.recv(64)
                msg = str(binascii.hexlify(msg))[2:-1]
            except OSError:
                pass
            if not msg:
                self.logger.warning(f"Received nothing!!!")
                return msg
            if new_msg:
                if imei:
                    #msg = msg[:-1] # Temporary. For debugging. Using netcat.
                    header_len = self.IMEI_MSG_HEADER
                    msglen = (int(msg[:header_len], 16) * 2) + 4
                    new_msg = False
                else:
                    header_len = self.TCP_MSG_HEADER
                    msglen = (int(msg[:header_len], 16) * 2) + 24
                    new_msg = False
            full_msg += msg
            if len(full_msg) >= msglen:
                receive = False
                # if not imei:
                #     #full_msg = full_msg[:-1]
            # Temporary. For debugging. Using netcat.
        # print(f"FULL MSG: {full_msg}")
        self.raw_logger.info(f'<< {full_msg}')
        return full_msg

    def send(self, channel, msg):
        if isinstance(msg, str): msg = binascii.unhexlify(msg)
        channel.send(msg)
        self.raw_logger.info(f'>> {binascii.hexlify(msg)}')

    def send_cmd(self, cmd, imei):
        conn = self.clientmap.get(imei)
        if conn:
            packet = parselib.build_gprs_cmd(cmd)
            try:
                if self.trans_prot == 'TCP':
                    self.send(conn, packet)
                elif self.trans_prot == 'UDP':
                    self.server.sendto(binascii.unhexlify(packet), conn)
                    conn = None
            except BrokenPipeError as e:
                conn = None
                self.display_info.emit(f"Could not send GPRS CMD - {e}.")
                self.logger.error(f"Could not send GPRS CMD - {e}.")
            self.display_info.emit(f"Sending GPRS CMD to {imei} - {cmd}")
            self.logger.info(f"Sending GPRS CMD to {imei} - {cmd}")
        if self.automatic:
            self.display_info.emit(f"Scheduling GPRS CMD SENDING in {self.automatic_period} seconds.")
            self.logger.info(f"Scheduling GPRS CMD SENDING in {self.automatic_period} seconds.")
            self.auto_thread = threading.Timer(self.automatic_period, self.send_cmd, [cmd, imei])
            self.auto_thread.start()
    
    def stop_auto_sending(self):
        if self.auto_thread: 
            self.auto_thread.cancel()
            self.auto_thread = None
            self.automatic_imei = None
            self.display_info.emit(f"Automatic GPRS CMD SENDING stopped.")
            self.logger.info(f"Automatic GPRS CMD SENDING stopped.")

    def accept_new_connection(self, imei, conn_entity):
        if not self.clientmap.get(imei):
            # Add IMEI and conn_entity to clientmap.
            with self.lock:
                self.clientmap[imei] = conn_entity
            self.clients += 1
            self.new_conn.emit(imei)
        else:
            # Update clientmap with received conn_entity (UDP entity might change).
            if self.clientmap[imei] != conn_entity:
                self.clientmap[imei] = conn_entity
                self.logger.warning(f'{imei} is in the list of clients but its address and port are different.')
                if self.trans_prot == 'TCP':
                    conn_entity = conn_entity.getsockname()
                self.logger.info(f'Updating {imei} address and port to {conn_entity}')

    def close(self):
        if self.trans_prot == 'TCP':
            # For some reason, Windows doesn't play nice with shutdown here. Needs further investigation.
            # self.server.shutdown(socket.SHUT_RDWR)
            self.server.close()
        elif self.trans_prot == 'UDP':
            self.server.sendto(self.UDP_END_PACKET, ('127.0.0.1', self.port))
            self.clients = 0
            for imei in self.clientmap:
                self.closed_conn.emit(imei)
            with self.lock:
                self.clientmap = {}
        self.running = False

    def disconnect_client(self, imei):
        conn = self.clientmap.get(imei)
        if self.trans_prot == 'TCP':
            conn.shutdown(socket.SHUT_RDWR)
            conn.close()
            # Everything else is handled automatically in self.communicate().
        elif self.trans_prot == 'UDP':
            with self.lock:
                del self.clientmap[imei]
            self.clients -= 1
            self.closed_conn.emit(imei)
        if self.automatic_imei == imei:
            self.stop_auto_sending()
        self.display_info.emit(f"Connection with {imei} closed by user input.")

    def beacon_test(self, recs):
        bec_data = []
        for rec in recs:
            for avl_id, value in rec.items():
                if avl_id == '0181':
                    bec_data += parselib.parse_beacon_avl_id_simple(value, rec['timestamp'])
                elif avl_id == '0224':
                    bec_data += parselib.parse_beacon_avl_id_advanced(value, rec['timestamp'])
        printable_data = ''
        for bec in bec_data:
            printable_data += parselib.pretty_beacon_data(bec)
        return printable_data, bec_data

    def communicate(self, conn, addr):
        connected = True
        imei = None
        self.logger.info('TCP Server-Client communication thread created.')
        while connected:
            if not imei:
                self.logger.info(f"Waiting for IMEI...")
                imei = self.receive(conn, True)
                imei = parselib.parse_imei(imei)
                #imei = '000F383634363036303432333339333234'
                self.logger.info(f'IMEI received from the client - {imei}')
                if not imei:
                    connected = False
                    self.display_info.emit(f"Couldn't establish connection with {addr}")
                    self.logger.error(f"Couldn't establish connection with {addr}")
                else:
                    self.send(conn, '01')
                    self.logger.info(f'Sending IMEI reply...')
                    self.accept_new_connection(imei, conn)
                    self.display_info.emit(f"Connected from: {addr}. IMEI: {imei}")
                    self.logger.info(f"Connected from: {addr}. IMEI: {imei}")
            else:
                data = self.receive(conn)
                if data:
                    packet = (datetime.now(), data)
                    pinfo, reply = parselib.parse_packet(packet)
                    rpayload = pinfo['records']
                    data_no = pinfo['no_of_data_1']
                    codec = pinfo['codec']
                    if codec == '08' or codec == '8e':
                        recs = parselib.parse_record_payload(rpayload, data_no, codec)
                        # If beacon testing mode is enabled, parse and print beacon AVL data.
                        if self.beacon:
                            printable_data, bec_data = self.beacon_test(recs)
                            if bec_data: 
                                data = printable_data
                                self.to_db.emit((imei, bec_data))
                        self.display_info.emit(f"IMEI: {imei} - {data}")
                        self.display_info.emit(f"Sending record reply: {reply}")
                        self.logger.info(f"IMEI: {imei} - {data}")
                        self.logger.info(f"Sending record reply: {reply}")
                        self.send(conn, reply)
                    elif codec == '0c':
                        response = parselib.parse_gprs_cmd_response(rpayload)
                        self.display_info.emit(f"{imei} - {response}")
                        self.logger.info(f"{imei} - {response}")
                else:
                    connected = False
                    self.clients -= 1
                    self.display_info.emit(f"Connection with {imei} - {addr} closed.")
                    self.logger.info(f"Connection with {imei} - {addr} closed.")
                    self.closed_conn.emit(imei)
                    with self.lock:
                        del self.clientmap[imei]

    def run_tcp_server(self):
        self.server.listen()
        self.running = True
        while self.running:
            try:
                conn, addr = self.server.accept()
                self.logger.info(f"Connected from {addr}")
                if self.use_ssl:
                    self.logger.info(f"Attempting to establish SSL connection with {addr}...")
                    self.display_info.emit(f"Attempting to establish SSL connection with {addr}...")
                    conn =  self.ssl_context.wrap_socket(conn, server_side=True)
                t = threading.Thread(target=self.communicate, args=[conn, addr])
                self.conn_threads.append(t)
                t.start()
            except ssl.SSLError as e:
                self.logger.error(f"SSL connection with {addr} couldn't be established. Reason: {e}")
                self.display_info.emit(f"SSL connection with {addr} couldn't be established. Reason: {e}")
            except OSError as e:
                self.running = False
                # OSError can be raised if user tries to STOP the server.
                self.logger.info(f"{e} - Server thread is closing")
                # Change .items() with .values() maybe?
                for _, conn in self.clientmap.items():
                    conn.shutdown(socket.SHUT_RDWR)
                    conn.close()

    def run_udp_server(self):
        self.running = True
        while self.running:
            data, addr = self.server.recvfrom(1500)
            if data:
                if addr[0] != ('127.0.0.1'): self.display_info.emit(f"Received UDP packet from {addr}.")
                data = str(binascii.hexlify(data))[2:-1]
                if data == '00000000':
                    self.running = False # For some reason, server doesn't close greacfully on Windows without this line.
                    self.server.close()
                else:
                    packet = (datetime.now(), data)
                    pinfo, reply = parselib.parse_packet(packet)
                    rpayload = pinfo['records']
                    data_no = pinfo['no_of_data_1']
                    codec = pinfo['codec']
                    recs = parselib.parse_record_payload(rpayload, data_no, codec)
                    if codec != '0c':
                        imei = parselib.parse_imei(pinfo['imei'], False)
                        self.accept_new_connection(imei, addr)
                        if self.beacon:
                            printable_data, bec_data = self.beacon_test(recs)
                            if bec_data: 
                                data = printable_data
                                self.to_db.emit((imei, bec_data))
                        self.display_info.emit(f"IMEI: {imei} - {data}")
                        self.display_info.emit(f"Sending record reply: {reply}")
                        self.logger.info(f"IMEI: {imei} - {data}")
                        self.logger.info(f"Sending record reply: {reply}")
                        self.server.sendto(binascii.unhexlify(reply), addr)
                    else:
                        response = parselib.parse_gprs_cmd_response(rpayload)
                        self.display_info.emit(f"{response}")
                        self.logger.info(f"{response}")

    def run(self):
        if self.trans_prot == 'TCP':
            self.run_tcp_server()
        elif self.trans_prot == 'UDP':
            self.run_udp_server()
            

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    aplc = Application()
    sys.exit(app.exec_())