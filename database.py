#!/usr/bin/python3

import os
import psycopg2
import socket
import threading
import traceback
from logger import Logger
from PyQt5 import QtCore
from queue import SimpleQueue


class Database(QtCore.QThread):

    display_info = QtCore.pyqtSignal(str) # Used to display information in GUI text browser.

    def __init__(self):
        """
        Initializes database object and creates backup file.
        """
        super().__init__()
        self.dbname = None
        self.user = None
        self.host = None
        self.password = None
        self.port = None
        self.connection = None
        self.cursor = None
        self.running = False
        self.connected = False
        open('backup.sql', 'a').close()
        # Queue used to enter data received from the server.
        self.queue = SimpleQueue()
        self.logger = Logger('Database')

    def connect(self):
        """
        Connects to database. If connection couldn't be established - starts threading timer
        to periodically ( every 10 s. - hardcoded ) try to establish connection.
        """
        self.logger.info(f"Trying to connect to {self.host}")
        self.display_info.emit(f"Trying to connect to {self.host}")
        args = f"dbname='{self.dbname}' user='{self.user}' host='{self.host}' password='{self.password}' port={self.port}"
        "'connect_timeout'=3 'keepalives'=1 'keepalives_idle'=5 'keepalives_interval'=2 'keepalives_count'=2"
        try:
            self.connection = psycopg2.connect(args)
            # This allows connection to raise psycopg2.OperationalError when database becomes unavailable
            # during transaction. Othervise, transaction hangs on cursor operations. 
            # FOR UNIX LIKE MACHINES ONLY
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
            # If connection is successfully established, enter data from backup file to database.
            self.__insert_backup_to_db()
        except psycopg2.OperationalError as e:
            self.connected = False
            # Periodically try to reconnect.
            if self.running:
                threading.Timer(10, self.connect).start()
            self.logger.error(f"Unable to connect to database - {e}")
            self.display_info.emit(f"Unable to connect to database - {e}")     

    def disconnect(self):
        """
        Disconnects from database.
        """
        if self.connected:
            self.cursor.close()
            self.connection.close()
            self.logger.warning(f"Disconnected from database - {self.dbname}")
            self.display_info.emit(f"Disconnected from database - {self.dbname}")

    def insert_into(self, table, data):
        """
        Inserts information from Python dictionary to the database.

        Parameters:
            table (str): name of the table to insert data to.
            data (dict): dictionary of data to be inserted.
        """
        columns = data.keys()
        values = data.values()
        insert_que = f"INSERT INTO {table} (%s) VALUES %s RETURNING id"
        # print(self.cursor.mogrify(insert_que, (psycopg2.extensions.AsIs(','.join(columns)), tuple(values))))
        try:
            self.cursor.execute(insert_que, (psycopg2.extensions.AsIs(','.join(columns)), tuple(values)))
            ent_id = self.cursor.fetchone()[0]
            self.connection.commit()
            return ent_id
        except (psycopg2.OperationalError, TypeError) as e:
            self.connected = False
            threading.Timer(10, self.connect).start()
            self.logger.error(f"Unable to add data to database - {e}")
            self.display_info.emit(f"Unable to add data to database - {e}")
        except psycopg2.errors.NumericValueOutOfRange:
            self.logger.error(traceback.format_exc())
            self.disconnect()
            self.connect()

    def request(self, req):
        """
        Executes SQL request.

        Parameters:
            req (str): SQL request to be executed.
        """
        self.logger.info(f'Request: {req}')
        if self.connected:
            try:
                self.cursor.execute(req)
                data = self.cursor.fetchall()
                return data
            except psycopg2.OperationalError as e:
                self.connected = False
            except psycopg2.ProgrammingError as e:
                self.logger.error(f"Unable to execute the request - {e}")
                self.display_info.emit(f"Unable to execute the request - {e}")

    def __insert_beacons_to_db(self, data):
        """
        Spaghetti code that does various nonesense with beacon data to be inserted to database and
        than actually inserts it into database.

        Parameters:
            data (list): beacon data to be inserted to database.
        """
        imei = data[0]
        curr_ts = None
        prev_ts = None
        i = None
        succsess = True
        backup = {'rec':'', 'beacons':[]}
        for d in data[1]:
            curr_ts = d['timestamp']
            if curr_ts != prev_ts:
                # Write backup to file if backup is present.
                if backup['rec'] or backup['beacons']:
                    self.__to_backup(backup)
                    backup = {'rec':'', 'beacons':[]}
                if self.connected:
                    i = self.insert_into('beacon_records', {'data':d['data'], 'timestamp':d['timestamp'], 'imei':imei})
                if not self.connected:
                    # Insert to sql backup file.
                    backup['rec'] = f"INSERT INTO beacon_records (data) VALUES ('{d['data']}') RETURNING id INTO beacid;"
                    succsess = False
            if d.get('uuid'):
                del d['data'], d['timestamp']
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
                    succsess = False
            prev_ts = curr_ts
        return succsess
        
    def __to_backup(self, backup):
        """
        Creates SQL request and stores it to the backup file.
        """
        insert_que = backup['rec'] + '\n' + '\n'.join(backup['beacons'])
        sql_cmd = f"DO $$DECLARE beacid integer; BEGIN {insert_que} END $$;"
        with open('backup.sql', 'a') as f:
            f.write(sql_cmd + '\n')

    def __insert_backup_to_db(self):
        """
        Executes SQL queries from backup file.
        """
        if self.connected and os.stat('backup.sql').st_size > 0:
            self.logger.info(f"Backup file is not empty. Entering backup data to database - {self.dbname}")
            self.display_info.emit(f"Backup file is not empty. Entering backup data to database - {self.dbname}")
            try:
                self.cursor.execute(open("backup.sql", "r").read())
                open('backup.sql', 'w').close() # Clears backup file.
                self.logger.info(f"Successfully entered backup data to database - {self.dbname}")
                self.display_info.emit(f"Successfully entered backup data to database - {self.dbname}")
            except psycopg2.OperationalError as e:
                self.logger.error(f"Unable to add BACKUP to database - {e}")
                self.display_info.emit(f"Unable to add BACKUP to database - {e}")
            except psycopg2.errors.SyntaxError as e:
                # If somehow backup file got corrupted, clears the backup file and
                # places corrupted data in another file.
                self.logger.error(f"Pasibly corrupted backup file - {e}.")
                self.display_info.emit(f"Pasibly corrupted backup file - {e}.")
                with open('backup_err.sql', 'a') as f:
                    f.write(open("backup.sql", "r").read())
                open('backup.sql', 'w').close()

    def stop(self):
        """
        Closes connection with database and stops database main thread.
        """
        # Look for alternative way to wait for queue to become empty.
        while not self.queue.empty():
            pass
        self.queue.put(None)
        self.running = False
        self.disconnect()

    def run(self):
        """
        Main database thread method.
        """
        self.logger.info(f"Main database settings: dbname='{self.dbname}' user='{self.user}'"
        f" host='{self.host}' password='{self.password}'")
        self.display_info.emit(f"Main database settings: dbname='{self.dbname}' user='{self.user}'"
        f" host='{self.host}' password='{self.password}'")
        self.running = True
        self.connect()
        while self.running:
            data = self.queue.get()
            if data:
                result = self.__insert_beacons_to_db(data)
                if result:
                    self.logger.info(f"Successfully entered data into database - {self.dbname}")
                    self.display_info.emit(f"Successfully entered data into database - {self.dbname}")
                else:
                    self.logger.warning(f"Data saved to backup file - backup.sql")
                    self.display_info.emit(f"Data saved to backup file - backup.sql")
        self.logger.warning("Database was stopped...")
        self.display_info.emit("Database was stopped...")        
