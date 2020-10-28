#!/usr/bin/python3

import sys
import socket
import select
import parselib
import time
import threading
import binascii
import libscrc
from datetime import datetime
from PyQt5 import QtWidgets, QtCore, Qt
from window import Ui_MainWindow


class Application(QtWidgets.QMainWindow):

    def __init__(self):
        super().__init__()
        self.main_window = Ui_MainWindow()
        self.main_window.setupUi(self)
        self.main_window.pushButtonSend.pressed.connect(self.send_gprs_cmd)
        self.main_window.lineEdit.returnPressed.connect(self.send_gprs_cmd)
        self.main_window.pushButtonStart.pressed.connect(self.start_server)
        self.show()
        self.time_format = '%Y.%m.%d %H:%M:%S.%f'
        self.server = Server()
        self.server.received_data.connect(self.append_text_browser)
        self.server.new_conn.connect(self.add_conn)
        self.server.closed_conn.connect(self.del_conn)
        
    def append_text_browser(self, data):
        time_recv = datetime.strftime(datetime.now(), self.time_format)
        self.main_window.textBrowser.append(f'[{time_recv}] - {data}')

    def add_conn(self, imei):
        self.main_window.comboBox.addItem(imei)
        self.main_window.labelCount.setText(str(self.server.clients))
    
    def del_conn(self, imei):
        index = self.main_window.comboBox.findText(imei)
        self.main_window.comboBox.removeItem(index)
        self.main_window.labelCount.setText(str(self.server.clients))

    def send_gprs_cmd(self):
        cmd = self.main_window.lineEdit.text() + '\r\n'
        imei = self.main_window.comboBox.currentText()
        self.server.send_cmd(cmd, imei)
        self.append_text_browser(f"Sending GPRS CMD to {imei} - {cmd}")

    def change_server_type(self):
        ser_type = self.sender().text()
        self.trans_prot = ser_type
        self.server.server.shutdown(socket.SHUT_RDWR)
        self.server.server.close()

    def start_server(self):
        self.trans_prot = self.main_window.buttonGroup.checkedButton().text()
        self.port = self.main_window.spinBox.value()
        self.__change_server_widget_state(self.main_window.horizontalLayout_3)
        self.__inverse_start_stop_button('stop')
        self.server.create_socket(self.port, self.trans_prot)
        self.server.start()
        self.append_text_browser(f"{self.trans_prot} server started on port {self.port}.")

    def stop_server(self):
        self.server.server.shutdown(socket.SHUT_RDWR)
        self.server.server.close()
        self.__change_server_widget_state(self.main_window.horizontalLayout_3)
        self.__inverse_start_stop_button('start')
        self.append_text_browser(f"{self.trans_prot} server on port {self.port} was closed with all it's connections.")

    def __change_server_widget_state(self, layout):
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

class Server(QtCore.QThread):

    received_data = QtCore.pyqtSignal(str)
    new_conn = QtCore.pyqtSignal(str)
    closed_conn = QtCore.pyqtSignal(str)

    IMEI_MSG_HEADER = 4
    TCP_MSG_HEADER = 16

    def __init__(self):
        super().__init__()
        self.clients = 0
        self.clientmap = {} # clientmap[imei] = conn_entity (socket or tuple of addr and port)
        self.conn_threads = []
        self.time_format = '%Y.%m.%d %H:%M:%S.%f'

    def create_socket(self, port, trans_prot):
        self.host = '0.0.0.0'
        self.port = int(port)
        self.username = "SERVER"
        self.trans_prot = trans_prot
        if self.trans_prot == 'TCP':
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        elif self.trans_prot == 'UDP':
            self.server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((self.host, self.port))

    def receive(self, channel, imei=False):
        full_msg = ''
        new_msg = True
        receive = True
        while receive:
            msg = channel.recv(64)
            msg = str(binascii.hexlify(msg))[2:-1]
            if not msg:
                return
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
        return full_msg

    def send(self, channel, msg):
        if isinstance(msg, str): msg = binascii.unhexlify(msg)
        channel.send(msg)

    def send_cmd(self, cmd, imei):
        for conn_imei, soc in self.clientmap.items():
            if conn_imei == imei:
                conn = soc
        packet = parselib.build_gprs_cmd(cmd)
        self.send(conn, packet)

    def accept_new_connection(self, imei, conn_entity):
        if not self.clientmap.get(imei):
            # Add IMEI and conn_entity to clientmap.
            self.clientmap[imei] = conn_entity
            self.clients += 1
            self.new_conn.emit(imei)
        else:
            # Update clientmap with received conn_entity (UDP entity might change).
            self.clientmap[imei] = conn_entity

    def communicate(self, conn, addr):
        connected = True
        imei = None
        while connected:
            if not imei:
                print("Waiting for IMEI...")
                imei = self.receive(conn, True)
                imei = parselib.parse_imei(imei)
                #imei = '000F383634363036303432333339333234'
                print(imei)
                if not imei:
                    connected = False
                    self.clients -= 1
                    self.received_data.emit(f"Couldn't establish connection with {addr}")
                else:
                    self.send(conn, '01')
                
                    self.accept_new_connection(imei, conn)
                    self.received_data.emit(f"Connected from: {addr}. IMEI: {imei}\n")
            else:
                data = self.receive(conn)
                print(data)
                if data:
                    packet = (datetime.now(), data)
                    pinfo, reply = parselib.parse_packet(packet)
                    rpayload = pinfo['records']
                    data_no = pinfo['no_of_data_1']
                    codec = pinfo['codec']
                    if codec != '0c':
                        recs = parselib.parse_record_payload(rpayload, data_no, codec)
                        self.received_data.emit(f"{data}")
                        self.received_data.emit(f"Sending record reply: {reply}")
                        self.send(conn, reply)
                    else:
                        response = parselib.parse_gprs_cmd_response(rpayload)
                        self.received_data.emit(f"{response}")
                else:
                    connected = False
                    self.clients -= 1
                    self.received_data.emit(f"Connection with {imei} - {addr} closed.")
                    self.closed_conn.emit(imei)

    def run_tcp_server(self):
        self.server.listen()
        running = True
        while running:
            try:
                print(self.trans_prot)
                conn, addr = self.server.accept()
                print(f"Connected from {addr}")
                t = threading.Thread(target=self.communicate, args=[conn, addr])
                self.conn_threads.append(t)
                t.start()
            except OSError as e:
                # OSError can be raised if user tries to STOP the server.
                print(f"{e} - Server thread is closing")
                for _, conn in self.clientmap.items():
                    conn.shutdown(socket.SHUT_RDWR)
                    conn.close()
                self.clientmap = {}
                running = False

    def run_udp_server(self):
        while True:
            data, addr = self.server.recvfrom(1500)
            if data:
                self.received_data.emit(f"Received UDP packet from {addr}.")
                data = str(binascii.hexlify(data))[2:-1]
                packet = (datetime.now(), data)
                pinfo, reply = parselib.parse_packet(packet)
                imei = parselib.parse_imei(pinfo['imei'], False)
                self.accept_new_connection(imei, addr)
                self.received_data.emit(f"IMEI: {imei} - {data}")
                self.received_data.emit(f"Sending record reply: {reply}")
                self.server.sendto(binascii.unhexlify(reply), addr)

    def run(self):
        if self.trans_prot == 'TCP':
            self.run_tcp_server()
        elif self.trans_prot == 'UDP':
            self.run_udp_server()
            

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    aplc = Application()
    sys.exit(app.exec_())