"""
This file is kept as a playground for all minor non-automatic calls to the Kaltura API
"""
from Llab_libs.KalturaExtensions import *
import json
import time

if __name__ == '__main__':
    client = KalturaExtender(log=True, log_level='info', errormail=False)
    #client.update_entry(entryId='0_sggjsk73', updates={'categoriesIds': '186579'})
    #client.update_entry(entryId='0_07bwdxgs', updates={'parentEntryId': '0_sggjsk73'})
    client.update_dual_user_list()
    client.update_dual_user_ownerships()
    #printKalturaObject(client.get_client().media.get('0_otrwgrm2'))
