from datetime import datetime

# Kaltura helpers
from Llab_libs.KalturaExtensions import *


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


if __name__ == '__main__':
    print(now(), 'Running', __file__)
    print()
    
    print(now(), 'Setting up client')
    client = KalturaExtender()
    print()

    print(now(), 'Get existing users')
    userList = client.get_users(printResult=False)
    print()

    print(now(), 'Write existing users to csv')
    v = vars(userList['admin'])
    path = '../csv_files/users.csv'
    export_to_csv(userList, path, specificVariables=v)
    print()

    print(now(), 'done')
