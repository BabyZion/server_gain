#!usr/bin/python3

import logging


class Logger:
    def __init__(self, logger_name, log_file='application_events.log'):
        """
        Initializes Logger object used to log various events happening during the execution of the application.
        """
        self.logger_name = logger_name
        self.log_file = log_file
        self.file_handler = logging.FileHandler(self.log_file)
        self.logger = logging.getLogger(self.logger_name)
        if self.logger_name == 'RAW':
            self.formatter = logging.Formatter('%(asctime)s - %(name)s: %(message)s')
            self.file_handler.setFormatter(self.formatter)
            self.logger.addHandler(self.file_handler)
        else:
            self.formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s: %(message)s')
            self.stream_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s: %(message)s')
            self.stream_handler = logging.StreamHandler()
            self.file_handler.setFormatter(self.formatter)
            self.stream_handler.setFormatter(self.stream_formatter)
            self.logger.addHandler(self.stream_handler)
            self.logger.addHandler(self.file_handler)
        self.logger.setLevel(logging.INFO)

    def info(self, msg):
        """
        """
        self.logger.info(msg)

    def warning(self, msg):
        """
        """
        self.logger.warning(msg)

    def error(self, msg):
        """
        """
        self.logger.error(msg)

    def exception(self, msg):
        """
        """
        self.logger.exception(msg)