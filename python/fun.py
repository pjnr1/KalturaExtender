from Llab_libs.KalturaExtensions import *
import json


if __name__ == '__main__':
    client = KalturaExtender(log=True, log_level=1, errormail=False)
    # client.update_entry(entryId='0_xh7px4xk', updates={'categoriesIds': '186579'})
    client.update_dual_user_list()
    client.update_dual_user_ownerships()
    #printKalturaObject(client.get_client().media.get('0_otrwgrm2'))
