import os
import logging
import traceback
from logging import FileHandler, Formatter
class Module_Logger(object):
    def __init__(self, logger):
        self.logger = logger
        self.log_folder = './log/'
        self.log_file = f'{self.logger.name.lower()}_log.txt'
        if not os.path.exists(self.log_folder):
            os.mkdir(self.log_folder)
        self.logger.setLevel(logging.INFO)
        self.logger_handler = FileHandler(self.log_folder + self.log_file)
        self.logger_formater = Formatter('%(asctime)s : [%(levelname)s] : %(message)s')
        self.logger_handler.setFormatter(self.logger_formater)
        self.logger.addHandler(self.logger_handler)

    def error_log(self, line_no):
        err_formater = logging.Formatter('%(asctime)s : [%(levelname)s][LINE ' + line_no + '] : %(message)s')
        self.logger_handler.setFormatter(err_formater)
        self.logger.addHandler(self.logger_handler)
        self.logger.error(traceback.format_exc())
        self.logger_handler.setFormatter(self.logger_formater)
        self.logger.addHandler(self.logger_handler)
