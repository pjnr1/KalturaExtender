from datetime import datetime
from termcolor import colored
import sys


class SimpleLogger(object):
    logfile = NotImplemented

    def __init__(self, logfile=None):
        if logfile is not None:
            self.logfile = open(logfile, 'a')
        self.pendingLog = []

    # Emulated private function
    def __log(self, string, sender=None, color="white", on_color=None, p=False):
        now = datetime.now()
        date = str(now)[:19]
        message = str(string)
        if sender is None:
            sender = sys._getframe().f_back.f_back.f_code.co_name
        log_string = "[{d}][ {s} ] {m}".format(d=colored(date, 'cyan'),
                                               m=colored(message, color, on_color),
                                               s=sender)
        if p:
            print(log_string)
        if self.logfile:
            self.logfile.write(log_string + "\n")
            self.logfile.flush()

    def log(self, string, sender=None, color="white", on_color=None, p=False):
        self.__log(string, sender, color, on_color, p)

    def debug(self, string, sender=None):
        self.__log(string, sender, color="magneta")

    def info(self, string, sender=None):
        self.__log(string, sender)

    def warning(self, string, sender=None):
        self.__log(string, sender, color="yellow")

    def error(self, string, sender=None):
        self.__log(string, sender, color="red")

    def critical(self, string, sender=None):
        self.__log(string, sender, on_color="on_red")
