import smtplib
import re
import os

from Llab_libs.statics_helper import load_statics
from email.message import EmailMessage


class LLabMailHelper:
    __secrets_folder__ = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'secrets')

    def __init__(self):
        # load secrets
        s =  load_statics(os.path.join(self.__secrets_folder__,'llab_mail.secret'))
        self.mailaddr = s['mailaddr']
        self.mailpwd = s['mailpwd']
        self.errormessage_destination = s['errmsgdest']
        smtpaddr = s['smtpaddr']
        smtpport = s['smtpport']

        # setup server connection
        try:
            server = smtplib.SMTP_SSL(smtpaddr, smtpport)
            server.ehlo()
            server.login(self.mailaddr, self.mailpwd)
        except Exception as e:
            print("Couldn't setup connection to server")
            print(e)

    def send_error_mail(self, sender, msg):
        msg = EmailMessage()
        msg['Subject'] = 'Error detected in %s' % sender
        msg['From'] = self.mailaddr
        msg['To'] = self.errormessage_destination
        msg.set_content(msg)

