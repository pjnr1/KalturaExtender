import time

# Kaltura helpers
from Llab_libs.KalturaExtensions import *

if __name__ == '__main__':
    client = KalturaExtender(log=True, errormail=True)
    client.merge_dualstreams(verbose=False)
    client.update_dual_user_list()
    client.update_dual_user_ownerships()
    # print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 'Running dualstreamMerge')
