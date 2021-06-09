#!/usr/bin/python3

import psycopg2
import socket
from logger import Logger
from PyQt5 import QtCore
from queue import SimpleQueue


class Database(QtCore.QThread):

    display_info = QtCore.pyqtSignal(str)

    def __init__(self, dbname, user, host, password):
        super().__init__()
        self.dbname = dbname
        self.user = user
        self.host = host
        self.password = password
        self.connection = None
        self.cursor = None
        self.running = False
        self.queue = SimpleQueue()
        self.logger = Logger('Database')

    def connect(self):
        self.logger.info(f"Trying to connect to {self.host}")
        self.display_info.emit(f"Trying to connect to {self.host}")
        args = f"dbname='{self.dbname}' user='{self.user}' host='{self.host}' password='{self.password}'"
        self.connection = psycopg2.connect(args)
        # This allows connection to raise psycopg2.OperationalError when database becomes unavailable
        # during transaction. Othervise, transaction hangs on cursor operations.
        s = socket.fromfd(self.connection.fileno(), socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        s.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 6)
        s.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 2)
        s.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 2)
        s.setsockopt(socket.IPPROTO_TCP, socket.TCP_USER_TIMEOUT, 5000)
        self.cursor = self.connection.cursor()
        self.logger.info(f"Successfully connected to database - {self.dbname}")
        self.display_info.emit(f"Successfully connected to database - {self.dbname}")

    def insert_into(self, table, data):
        columns = data.keys()
        values = data.values()
        insert_que = f"INSERT INTO {table} (%s) VALUES %s RETURNING id"
        # print(self.cursor.mogrify(insert_que, (psycopg2.extensions.AsIs(','.join(columns)), tuple(values))))
        self.cursor.execute(insert_que, (psycopg2.extensions.AsIs(','.join(columns)), tuple(values)))
        ent_id = self.cursor.fetchone()[0]
        self.connection.commit()
        return ent_id

    def run(self):
        self.logger.info(f"Main database settings: dbname='{self.dbname}' user='{self.user}'"
        f" host='{self.host}' password='{self.password}'")
        self.display_info.emit(f"Main database settings: dbname='{self.dbname}' user='{self.user}'"
        f" host='{self.host}' password='{self.password}'")
        self.connect()
        self.running = True
        while self.running:
            data = self.queue.get()
            imei = data[0]
            curr_ts = None
            prev_ts = None
            i = None
            for d in data[1]:
                curr_ts = d['timestamp']
                if curr_ts != prev_ts:
                    i = self.insert_into('beacon_records', {'data':d['data']})
                if d.get('uuid'):
                    del d['data']
                    d['record'] = i
                    d['imei'] = imei
                    self.insert_into('beacons', d)
                    prev_ts = curr_ts
            self.logger.info(f"Successfully entered data into database - {self.dbname}")
            self.display_info.emit(f"Successfully entered data into database - {self.dbname}")