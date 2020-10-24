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
        self.main_window.pushButton.pressed.connect(self.send_gprs_cmd)
        self.main_window.lineEdit.returnPressed.connect(self.send_gprs_cmd)
        self.show()
        self.time_format = '%Y.%m.%d %H:%M:%S.%f'
        self.server = Server(6969)
        self.server.received_data.connect(self.append_text_browser)
        self.server.new_conn.connect(self.add_conn)
        self.server.closed_conn.connect(self.del_conn)
        self.server.start()

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


class Server(QtCore.QThread):

    received_data = QtCore.pyqtSignal(str)
    new_conn = QtCore.pyqtSignal(str)
    closed_conn = QtCore.pyqtSignal(str)

    IMEI_MSG_HEADER = 4
    TCP_MSG_HEADER = 16

    def __init__(self, port):
        super().__init__()
        self.host = '0.0.0.0'
        self.port = int(port)
        self.username = "SERVER"
        self.clients = 0
        self.clientmap = {}
        self.conn_threads = []
        self.time_format = '%Y.%m.%d %H:%M:%S.%f'

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
        for soc, conn_imei in self.clientmap.items():
            if conn_imei == imei:
                conn = soc
        packet = parselib.build_gprs_cmd(cmd)
        self.send(conn, packet)

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
                
                    self.clientmap[conn] = imei
                    self.new_conn.emit(imei)
                    self.received_data.emit(f"Connected from: {addr}. IMEI: {imei}\n")
            else:
                data = self.receive(conn)
                print(data)
                if data:
                    packet = (datetime.now(), data)
                    pinfo = parselib.parse_packet(packet)
                    rpayload = pinfo['records']
                    data_no = pinfo['no_of_data_1']
                    codec = pinfo['codec']
                    if codec != '0c':
                        recs, reply = parselib.parse_record_payload(rpayload, data_no, codec)
                        self.received_data.emit(f"{data}")
                        self.received_data.emit(f"Sending record reply: {reply}")
                        self.send(conn, reply)
                    else:
                        self.received_data.emit(f"{binascii.unhexlify(rpayload[10:]).decode('utf-8')}")
                else:
                    connected = False
                    self.clients -= 1
                    self.received_data.emit(f"Connection with {imei} - {addr} closed.")
                    self.closed_conn.emit(imei)

    def run(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((self.host, self.port))
        self.socket_list = [self.server]
        self.server.listen(5)
        running = True
        while running:
            conn, addr = self.server.accept()
            print(f"Connected from {addr}")
            t = threading.Thread(target=self.communicate, args=[conn, addr])
            self.conn_threads.append(t)
            t.start()
            self.clients += 1
            

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    aplc = Application()
    sys.exit(app.exec_())