import datetime

# Kaltura helpers
from Llab_libs.KalturaExtensions import *

def now():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


if __name__ == '__main__':
    print(now(), 'Running', __file__)
    print()

    client = KalturaExtender()
    print(client.getDualStreamChannels())
    print()

    print(client.getDualStreamEntryPairs())
    print()

