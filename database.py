#!/usr/bin/python3

import os
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
        self.connected = False
        self.settings_changed = False
        self.queue = SimpleQueue()
        self.logger = Logger('Database')

    def connect(self):
        self.logger.info(f"Trying to connect to {self.host}")
        self.display_info.emit(f"Trying to connect to {self.host}")
        args = f"dbname='{self.dbname}' user='{self.user}' host='{self.host}' password='{self.password}'"
        try:
            self.connection = psycopg2.connect(args)
            # This allows connection to raise psycopg2.OperationalError when database becomes unavailable
            # during transaction. Othervise, transaction hangs on cursor operations. 
            # FOR UNIX TYPE MACHINES ONLY
            try:
                s = socket.fromfd(self.connection.fileno(), socket.AF_INET, socket.SOCK_STREAM)
                s.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
                s.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 6)
                s.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 2)
                s.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 2)
                s.setsockopt(socket.IPPROTO_TCP, socket.TCP_USER_TIMEOUT, 5000)
            except AttributeError:
                pass
            self.cursor = self.connection.cursor()
            self.connected = True
            self.logger.info(f"Successfully connected to database - {self.dbname}")
            self.display_info.emit(f"Successfully connected to database - {self.dbname}")
        except psycopg2.OperationalError as e:
            self.connected = False
            self.logger.info(f"Unable to connect to database - {e}")
            self.display_info.emit(f"Unable to connect to database - {e}")

    def disconnect(self):
        self.cursor.close()
        self.connection.close()
        self.logger.info(f"Disconnected from database - {self.dbname}")
        self.display_info.emit(f"Disconnected from database - {self.dbname}")

    def insert_into(self, table, data):
        columns = data.keys()
        values = data.values()
        insert_que = f"INSERT INTO {table} (%s) VALUES %s RETURNING id"
        # print(self.cursor.mogrify(insert_que, (psycopg2.extensions.AsIs(','.join(columns)), tuple(values))))
        try:
            self.cursor.execute(insert_que, (psycopg2.extensions.AsIs(','.join(columns)), tuple(values)))
            ent_id = self.cursor.fetchone()[0]
            self.connection.commit()
            return ent_id
        except psycopg2.OperationalError as e:
            self.connected = False
            self.logger.info(f"Unable to add data to database - {e}")
            self.display_info.emit(f"Unable to add data to database - {e}")

    def __insert_beacons_to_db(self, data):
        imei = data[0]
        curr_ts = None
        prev_ts = None
        i = None
        backup = {'rec':'', 'beacons':[]}
        for d in data[1]:
            curr_ts = d['timestamp']
            if curr_ts != prev_ts:
                # Write backup to file if backup is present.
                if backup['rec'] or backup['beacons']:
                    self.__to_backup(backup)
                    backup = {'rec':'', 'beacons':[]}
                if self.connected:
                    i = self.insert_into('beacon_records', {'data':d['data']})
                if not self.connected:
                    # Insert to sql backup file.
                    backup['rec'] = f"INSERT INTO beacon_records (data) VALUES ('{d['data']}') RETURNING id INTO beacid;"
            if d.get('uuid'):
                del d['data']
                d['imei'] = imei
                if self.connected:
                    d['record'] = i
                    self.insert_into('beacons', d)
                if not self.connected:
                    # Insert to sql backup file.
                    d['record'] = 'beacid' if backup['rec'] else str(i)
                    columns = ''
                    values = ''
                    for k,v in d.items():
                        columns += f"{k}, "
                        if v == "beacid":
                            values += f"{v},"
                        else:
                            values += f"'{v}',"
                    columns = columns.strip()[:-1]
                    values = values.strip()[:-1]
                    # columns = tuple(d.keys())
                    # values = tuple(d.values())
                    insert_que = f"INSERT INTO beacons ({columns}) VALUES ({values});"
                    backup['beacons'].append(insert_que)
            prev_ts = curr_ts
        self.logger.info(f"Successfully entered data into database - {self.dbname}")
        self.display_info.emit(f"Successfully entered data into database - {self.dbname}")

    def __to_backup(self, backup):
        insert_que = backup['rec'] + '\n' + '\n'.join(backup['beacons'])
        sql_cmd = f"DO $$DECLARE beacid integer; BEGIN {insert_que} END $$;"
        with open('backup.sql', 'a') as f:
            f.write(sql_cmd + '\n')

    def run(self):
        self.logger.info(f"Main database settings: dbname='{self.dbname}' user='{self.user}'"
        f" host='{self.host}' password='{self.password}'")
        self.display_info.emit(f"Main database settings: dbname='{self.dbname}' user='{self.user}'"
        f" host='{self.host}' password='{self.password}'")
        self.connect()
        self.running = True
        while self.running:
            data = self.queue.get()
            self.__insert_beacons_to_db(data)
