from datetime import datetime
from termcolor import colored
from sys import _getframe as gf
import sys


class SimpleLogger(object):
    """
    SimpleLogger is inspired from https://github.com/mtayler/simplelogger
    However small edits are made for the usage needed in this particular project
    """
    logfile = None
    ll = {'log': -1,
          'all': 0,
          'debug': 1,
          'info': 2,
          'warning': 3,
          'error': 4,
          'critical': 5}

    def __init__(self, logfile=None):
        if logfile is not None:
            self.logfile = open(logfile, 'a')
        self.pendingLog = []
        self.level = 'all'

    # Emulated private function
    def _log(self, string, sender=None, date_color="cyan", sender_color="white", color="white", on_color=None, p=False):
        """Internal logger function, should only be called be SimplerLogger-class methods.

        :param string:          String to print
        :param sender:          Current function the logger logs from
        :param date_color:      Specifying color of the date-stamp
        :param sender_color:    Specifying color of the sender
        :param color:           Specifying color of the string
        :param on_color:        Specifyinh on-color of the message
        :param p:               If True, the logger prints the log-message
        """
        if self.ll[self.level] > self.ll[str(gf().f_back.f_code.co_name)]:
            return

        now = datetime.now()
        date = str(now)[:19]
        message = str(string)
        if sender is None:
            sender = gf().f_back.f_back.f_code.co_name
        log_string = "[{d}][{s}] {m}".format(d=colored(date, date_color),
                                             m=colored(message, color, on_color),
                                             s=colored(sender, sender_color))
        if p:
            print(log_string)
        if self.logfile is not None:
            self.logfile.write(log_string + "\n")
            self.logfile.flush()

    def log(self, string, sender=None, color="white", on_color=None, print=False):
        self._log(string=string, sender=sender, color=color, on_color=on_color, p=print)

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

    def set_level(self, log_level):
        if log_level in self.ll:
            self.level = log_level
        else:
            raise RuntimeError('Invalid log-level.')
