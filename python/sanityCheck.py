import datetime
import sys

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
    
    if 'dualstream' in sys.argv:
        print(now(), 'Get dualstream channels')
        res1 = client.getDualStreamChannels()
        for x1, y1 in res1.items():
            printKalturaObject(y1, specificVariables=['id', 'name'])
            res2 = client.get_entries(filters={'rootEntryIdEqual': x1,
                                              'mediaTypeEqual': 1})
            for x2, y2 in res2.items():       
                printKalturaObject(y2, levelOfIndent=1, specificVariables=['id', 'name', 'createdAt'])                          
                res3 = client.get_entries(filters={'parentEntryIdEqual': x2,
                                                  'mediaTypeEqual': 1})
                for x3, y3 in res3.items():       
                    printKalturaObject(y3, levelOfIndent=2, specificVariables=['id', 'name', 'parentEntryId', 'createdAt', 'status', 'duration', 'durationType', 'mediaType'])  
                    
                    print()


    if 'users' in sys.argv:
        print(now(), 'Get existing users')
        client.get_users(specificVariables=['id', 'fullName', 'screenName', 'email', 'createdAt'])
        print()
