import datetime

# Kaltura helpers
from Llab_libs.KalturaExtensions import *

def now():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


if __name__ == '__main__':
    print(now(), 'Running', __file__)
    print()
    
    print(now(), 'Setting up client')
    client = KalturaExtender()
    print()

    print(now(), 'Get existing users')
    path = 'users.csv'
    list = client.getExistingUsers(printResult=False)
    print()
    
    print(now(), 'Write existing users to csv')
    v = vars(list['admin'])
    exportToCsv(list, path, specificVariables=v)
    print()

    print(now(), 'done')
