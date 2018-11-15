from datetime import datetime

# Kaltura helpers
from Llab_libs.KalturaExtensions import *


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


if __name__ == '__main__':
    client = KalturaExtender(log=True, log_level=1, errormail=False)
    userList = client.get_users(printResult=False)
    v = vars(userList['admin'])
    path = '../csv_files/users.csv'
    export_to_csv(userList, path, specificVariables=v)
    print(now(), 'done')
