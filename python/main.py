import time

# Kaltura helpers
from Llab_libs.KalturaExtensions import *

if __name__ == '__main__':
    client = KalturaExtender()
    client.merge_dualstreams(verbose=False, mailerror=True)
    # print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 'Running dualstreamMerge')
