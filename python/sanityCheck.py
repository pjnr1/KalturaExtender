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
    
    print(now(), 'Get dualstream channels')
    res = client.getDualStreamChannels()
    for x, y in res.items():
        printKalturaObject(y, specificVariables=['id', 'name'])

    print()

    #print(now(), 'Get dualstream entries')
    #res = client.getDualStreamEntryPairs()
    #for x in res:
    #    print(x)
#
    #print()

    print(now(), 'Get existing users')
    client.getExistingUsers(specificVariables=['id', 'fullName', 'screenName', 'email', 'createdAt'])
    print()

    
