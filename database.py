#!/usr/bin/python3

import psycopg2
import socket


class Database:

    def __init__(self, dbname, user, host, password):
        self.dbname = dbname
        self.user = user
        self.host = host
        self.password = password
        self.connection = None
        self.cursor = None

    def connect(self):
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

    def insert_into(self, table, data):
        for ent in data:
            columns = ent.keys()
            values = ent.values()
            insert_que = f"INSERT INTO {table} (%s) VALUES %s RETURNING id"
            # print(self.cursor.mogrify(insert_que, (psycopg2.extensions.AsIs(','.join(columns)), tuple(values))))
            self.cursor.execute(insert_que, (psycopg2.extensions.AsIs(','.join(columns)), tuple(values)))
        ent_id = self.cursor.fetchone()[0]
        self.connection.commit()
        return ent_id
