import time

# Kaltura helpers
from Llab_libs.KalturaExtensions import *

if __name__ == '__main__':
    client = KalturaExtender(log=True, log_level=1, errormail=True)
    client.merge_dualstreams(verbose=False)
    client.update_dual_user_list()
    client.update_dual_user_ownerships()
