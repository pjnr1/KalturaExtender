from datetime import datetime
from termcolor import colored
import sys


class SimpleLogger(object):
    logfile = None

    def __init__(self, logfile=None):
        if logfile is not None:
            self.logfile = open(logfile, 'a')
        self.pendingLog = []

    # Emulated private function
    def _log(self, string, sender=None, date_color="cyan", sender_color="white", color="white", on_color=None, p=False):
        now = datetime.now()
        date = str(now)[:19]
        message = str(string)
        if sender is None:
            sender = sys._getframe().f_back.f_back.f_code.co_name
        log_string = "[{d}][{s}] {m}".format(d=colored(date, date_color),
                                             m=colored(message, color, on_color),
                                             s=colored(sender, sender_color))
        if p:
            print(log_string)
        if self.logfile is not None:
            self.logfile.write(log_string + "\n")
            self.logfile.flush()

    def log(self, string, sender=None, color="white", on_color=None, p=False):
        self._log(string, sender, color, on_color, p)

    def debug(self, string, sender=None):
        self._log(string, sender, color="magneta")

    def info(self, string, sender=None):
        self._log(string, sender)

    def warning(self, string, sender=None):
        self._log(string, sender, color="yellow")

    def error(self, string, sender=None):
        self._log(string, sender, color="red", date_color="red", sender_color="red")

    def critical(self, string, sender=None):
        self._log(string, sender, on_color="on_red", date_color="red", sender_color="red")
