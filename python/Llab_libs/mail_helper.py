import smtplib

from Llab_libs.statics_helper import load_statics


class LLabMailHelper:
    server = None

    def __init__(self):
        # load secrets
        self.s = load_statics('llab_mail.secret')

        # setup server connection
        try:
            self.server = smtplib.SMTP_SSL(self.s.smtpaddr + ':' + self.s.smtpport)
            self.server.ehlo()
            self.server.login(self.s.mailaddr, self.s.mailpwd)
        except Exception as e:
            print("Couldn't setup connection to server")
            print(e)

    def send_error_mail(self, msg, sender=None):
        m = ""
        if sender is not None:
            m += sender.__str__() + '\n'
        m += msg
        if self.server:
            try:
                self.server.sendmail(self.s.mailaddr, self.s.errmsgdest, m.__str__())
            except Exception as e:
                print("Couldn't send message")
                print(e)
            finally:
                self.server.quit()
