import binascii
import libscrc
import parselib
import socket
import ssl
import threading
from PyQt5 import QtCore
from logger import Logger

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
        self.trans_prot = None
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
            