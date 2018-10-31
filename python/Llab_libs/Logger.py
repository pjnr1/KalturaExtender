from datetime import datetime
from termcolor import colored


class SimpleLogger(object):
    logfile = NotImplemented

    def __init__(self, logfile=None):
        if logfile is not None:
            self.logfile = open(logfile, 'a')
        self.pendingLog = []

    def log(self, string, sender=None, color="white", on_color=None):
        now = datetime.now()
        date = str(now)[:19]
        message = str(string)
        logstr = "[{d}][ {s} ] {m}".format(d=colored(date, 'cyan'),
                                           m=colored(message, color, on_color),
                                           s=sender)
        print(logstr)
        if self.logfile:
            self.logfile.write(logstr + "\n")
            self.logfile.flush()

    def debug(self, string, sender=None):
        self.log(string, sender)

    def info(self, string, sender=None):
        self.log(string, sender, color="grey")

    def warning(self, string, sender=None):
        self.log(string, sender, color="yellow")

    def error(self, string, sender=None):
        self.log(string, sender, color="red")

    def critical(self, string, sender=None):
        self.log(string, sender, on_color="on_red")
