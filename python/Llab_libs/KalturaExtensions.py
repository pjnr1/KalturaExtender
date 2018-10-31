import csv
import re
import os
import collections
import json
from functools import partial
import traceback
from datetime import datetime

# LearningLab libraries
from Llab_libs import FuncDecorators
from Llab_libs.statics_helper import load_statics
from Llab_libs.mail_helper import LLabMailHelper
from Llab_libs.Logger import SimpleLogger

# Kaltura imports
from Kaltura.KalturaClient import *
from Kaltura.KalturaClient.Base import *
from Kaltura.KalturaClient.Plugins.Core import *

__basepath__ = os.path.dirname(os.path.realpath(__file__))
__dual_user_list__ = os.path.join(__basepath__, '../dual_user_list.json')

listOfUnixTimeStampVariables = ['createdAt', 'updatedAt', 'lastLoginTime',
                                'statusUpdatedAt', 'deletedAt', 'mediaDate',
                                'firstBroadcast', 'lastBroadcast']


def _now():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def kalturaObjectValueToString(a, v):
    if v is None or v is NotImplemented:
        return ""
    elif 'Kaltura' in type(v).__name__:
        if type(v).__name__ == 'KalturaLiveStreamConfiguration':
            return 'KalturaLiveStreamConfiguration'
        elif type(v).__name__ == 'KalturaLiveStreamBitrate':
            return 'KalturaLiveStreamBitrate'
        else:
            return v.getValue().__str__()
    elif any(x in a for x in listOfUnixTimeStampVariables):
        return datetime.fromtimestamp(v).strftime("%Y-%m-%d %H:%M:%S")
    else:
        return v.__str__()


def printKalturaObject(object, specificVariables=None, counter=None, levelOfIndent=0):
    indent = '\t' * levelOfIndent

    def printOut(a, values):
        print('{:s}{:s}:\n{:s}\t{:s}'.format(indent, a, indent, kalturaObjectValueToString(a, values)))

    if counter is not None:
        print('{:d}\t{}'.format(counter, object.id))
    else:
        if specificVariables and 'id' not in specificVariables:
            print('id: {:s}'.format(object.id))

    print('-' * 80)
    for p in vars(object).items():
        if specificVariables and p[0] not in specificVariables:
            continue

        if p[1]:
            if type(p[1]) is list:
                for a in p[1]:
                    printOut(p[0], a)
            else:
                printOut(p[0], p[1])
    print('')


class KalturaExtender:
    TIMESTAMP_RANGE = 30

    client = NotImplemented
    errorMailer = NotImplemented
    logger = NotImplemented
    ks = NotImplemented
    categoryIds = NotImplemented

    def __init__(self, log=False, errormail=False):
        s = load_statics('kaltura.secret')
        self.categoryIds = load_statics('kaltura_categoryIds')
        # Initial API client setup
        cfg = KalturaConfiguration(s.partnerId)
        cfg.serviceUrl = s.serviceUrl
        self.client = KalturaClient(cfg)
        # Start session
        self.ks = self.client.session.start(s.adminSecret, None, KalturaSessionType.ADMIN, s.partnerId)
        self.client.setKs(self.ks)

        if errormail:
            self.errorMailer = LLabMailHelper()

        if log:
            self.logger = SimpleLogger(logfile='../kaltura.log')

    @staticmethod
    def apply_filter(filter, filters):
        if filters is not None:
            for f in filters:
                if hasattr(filter, f):
                    setattr(filter, f, filters[f])
                else:
                    print('Warning:', filters[f], 'is not a valid KalturaMediaEntryFilter() attribute')

    @staticmethod
    def comp_timestamps(t1, t2, r=0):
        t0 = t1 - t2
        t0 = abs(t0)
        return not t0 > r

    def get_client(self):
        if self.client is NotImplemented:
            raise RuntimeError('KalturaExtender::client not loaded!')
        return self.client

    def get_entries(self, filters=None, entryType='media', printResult=False, specificVariables=None):
        entryFilter = KalturaMediaEntryFilter()
        self.apply_filter(entryFilter, filters)

        res = getattr(self.get_client(), entryType).list(entryFilter)
        i = 0
        output = {}
        for entry in res.objects:
            output[entry.id] = entry

            if printResult:
                printKalturaObject(entry, specificVariables=specificVariables, counter=i)

            i += 1

        return output

    def get_live_entries(self, printResult=True, specificVariables=None):
        f = KalturaLiveEntryFilter()
        res = self.get_client().liveStream.list(f)

        i = 0
        output = {}
        for stream in res.objects:
            output[stream.id] = stream

            if printResult:
                printKalturaObject(stream, counter=i, specificVariables=specificVariables)

            i += 1

        return output

    def get_users(self, printResult=True, onlyAdmins=False, specificVariables=None):
        f = KalturaUserFilter()
        p = KalturaFilterPager()
        p.pageSize = 500
        res = self.get_client().user.list(f, p)
        i = 0
        output = {}
        for user in res.objects:
            if onlyAdmins and not user.isAdmin:
                continue

            output[user.id] = user

            if printResult:
                printKalturaObject(user, specificVariables=specificVariables, counter=i)

            i += 1

        return output

    def get_entries_by_user(self, username, filters=None, printResult=False, specificVariables=None):
        mediaFilter = KalturaMediaEntryFilter()
        mediaFilter.userIdEqual = username
        self.apply_filter(mediaFilter, filters)

        res = self.get_client().media.list(mediaFilter)

        i = 0
        output = {}
        for media in res.objects:
            output[media.id] = media

            if printResult:
                printKalturaObject(media, specificVariables=specificVariables, counter=i)

            i += 1

        return output

    def set_parent(self, parent, child, entryType='media'):
        modifierEntry = KalturaMediaEntry()
        modifierEntry.parentEntryId = parent

        return getattr(self.get_client(), entryType).update(child, modifierEntry)

    def update_entry(self, entryId, updates, entryType='media', modifierEntry=KalturaMediaEntry()):
        if self.logger is not NotImplemented:
            log_str = "Updating entry {0}: {1}".format(entryId, updates)
            self.logger.info(log_str)
        if updates is not None:
            for u in updates:
                if hasattr(modifierEntry, u):
                    setattr(modifierEntry, u, updates[u])

        return getattr(self.get_client(), entryType).update(entryId, modifierEntry)

    def delete_entry(self, entryId, entryType):
        if self.logger is not NotImplemented:
            log_str = "Deleting entry {0}".format(entryId)
            self.logger.info(log_str)
        return getattr(self.get_client(), entryType).delete(entryId)

    def get_categories(self, filters=None):
        f = KalturaCategoryFilter()
        self.apply_filter(f, filters)

        res = self.get_client().category.list(f)

        i = 0
        output = {}
        for cats in res.objects:
            output[cats.id] = cats

            i += 1

        return output

    def get_dualstream_channels(self):
        return self.get_entries(filters={'categoriesIdsMatchAnd': self.categoryIds.Streams,
                                         'mediaTypeEqual': 201},
                                entryType='liveStream')

    def get_dualstream_pairs(self):
        streamEntries = self.get_dualstream_channels()

        readyEntries = {}
        for streams in streamEntries.items():
            listOfEntries = self.get_entries(filters={'rootEntryIdEqual': streams[0],
                                                      'categoriesIdsNotContains': self.categoryIds.Recordings,
                                                      'mediaTypeEqual': 1,
                                                      'statusEqual': KalturaEntryStatus.READY})

            for entry in listOfEntries.items():
                readyEntries[entry[0]] = entry[1]

        contentEntries = []
        cameraEntries = []
        pairedEntries = []
        for entry in readyEntries.items():
            if 'Content' in entry[1].name:
                contentEntries.append(entry)
            if 'Camera' in entry[1].name:
                cameraEntries.append(entry)

        for cont in contentEntries:
            str1 = re.sub(r' [0-9]+', '', cont[1].name)
            str1 = str1.replace('Content', '').replace(' ', '')
            for cam in cameraEntries:
                str2 = cam[1].name.replace('Camera', '').replace(' ', '')
                if str1 in str2:
                    if self.comp_timestamps(cont[1].createdAt, cam[1].createdAt, self.TIMESTAMP_RANGE):
                        cameraEntries.remove(cam)
                        pairedEntries.append((cont, cam))

        return pairedEntries

    def merge_dualstreams(self, verbose=True):
        if verbose:
            print(str(_now()),
                  'Searching for DualStream entries')

        client = KalturaExtender()

        pairedEntries = client.get_dualstream_pairs()

        updateErrorCount = 0
        errorList = []
        for parent, child in pairedEntries:
            try:
                client.set_parent(parent=parent[1].id, child=child[1].id)
                client.update_entry(entryId=parent[1].id, updates={'categoriesIds': self.categoryIds.Recordings})
                if self.logger is not NotImplemented:
                    self.logger.info('{0} Updated:'.format(str(_now())))
                    self.logger.info('\tparent: {0} | {1}'.format(parent[0], parent[1].name))
                    self.logger.info('\tchild: {0} | {1}'.format(child[0], child[1].name))
            except Exception as e:
                updateErrorCount += 1
                tb = traceback.format_exc()
                errEnd = '\n\n' + ('-' * 50) + '\n\n'
                errorList.append('{0} {1} {2}'.format(str(_now()),
                                                      str(e), errEnd))
                errorList.append(tb)

        if errorList:
            errorHeader = '{0} Encountered following errors:'.format(str(_now()))
            if self.logger is not NotImplemented:
                self.logger.critical(errorHeader)
            if verbose:
                print(errorHeader)

            for e in errorList:
                if self.logger:
                    self.logger.error(e)
                if verbose:
                    print('-' * 80)
                    print(e)
            if self.errorMailer is not NotImplemented:
                self.errorMailer.send_error_mail(__file__, errorList)

        updatedCount = len(pairedEntries) - updateErrorCount
        totalCount = len(pairedEntries)
        finalInfo = '{0} Updated {1} out of {2} entries'.format(str(_now()),
                                                               str(updatedCount), str(totalCount))

        if self.logger is not NotImplemented:
            if updatedCount != totalCount:
                self.logger.warning(finalInfo)
            else:
                self.logger.info(finalInfo)
        if verbose:
            print(finalInfo)

    def get_dual_users(self):
        def list_duplicates_of(seq, item):
            start_at = -1
            locs = []
            while True:
                try:
                    loc = seq.index(item, start_at + 1)
                except ValueError:
                    break
                else:
                    locs.append(loc)
                    start_at = loc
            return locs

        userList = self.get_users(printResult=False)
        userUsersList = []
        userIndexList = []
        for user in userList:
            userUsersList.append(user)
            userIndexList.append(user.split('@')[0])

        duplicates = [item for item, count in collections.Counter(userIndexList).items() if count > 1]
        duplicates_indexes = partial(list_duplicates_of, userIndexList)

        dual_users = []
        for d_idx in duplicates:
            indexes = duplicates_indexes(d_idx)

            kms_user = None
            lms_user = None
            if len(indexes) == 2:
                for idx in indexes:
                    userId = userUsersList[idx]
                    if '@' in userId:
                        kms_user = userId
                    else:
                        lms_user = userId
            if kms_user is not None and lms_user is not None:
                dual_users.append({'kms_user': kms_user, 'lms_user': lms_user})

        return dual_users

    def set_entry_ownership(self, entryId, userId):
        return self.update_entry(entryId=entryId, updates={'userId': userId})

    def set_entry_coeditors(self, entryId, userIdList):
        return self.update_entry(entryId=entryId, updates={'entitledUsersEdit': userIdList})

    def set_dual_user_ownerships(self, kms_userId, lms_userId):
        c = 0
        for lms_owned_entryId in self.get_entries_by_user(lms_userId):
            self.set_entry_ownership(lms_owned_entryId, kms_userId)
            c = c + 1
        for kms_owned_entryId in self.get_entries_by_user(kms_userId):
            self.set_entry_coeditors(kms_owned_entryId, lms_userId)
            c = c + 1
        return c

    def update_dual_user_list(self):
        user_list = None
        if os.path.isfile(__dual_user_list__):
            with open(__dual_user_list__, 'r') as f:
                user_list = json.load(f)

        dual_users = self.get_dual_users()

        c = 0
        if user_list is not None:
            c = c + len(user_list)
            poplist = []
            for i, dual_user in enumerate(dual_users):
                if dual_user in user_list:
                    poplist.append(i)
            for i in reversed(poplist):
                dual_users.pop(i)
            user_list = user_list + dual_users
        else:
            user_list = dual_users

        if os.path.isfile(__dual_user_list__):
            os.remove(__dual_user_list__)
        with open(__dual_user_list__, 'w') as f:
            json.dump(user_list, f)

        addedCount = len(user_list) - c

        if self.logger is not NotImplemented:
            log_str = "Added {0} new dual users to list".format(addedCount)
            self.logger.info(log_str)
        return addedCount

    def update_dual_user_ownerships(self):
        user_list = None
        if os.path.isfile(__dual_user_list__):
            with open(__dual_user_list__, 'r') as f:
                user_list = json.load(f)

        if user_list is not None:
            for user in user_list:
                if user['lms_user'] == 'jeslar':
                    self.set_dual_user_ownerships(user['kms_user'], user['lms_user'])


def exportToCsv(list, path, specificVariables=None):
    if len(list) is 0:
        return

    if specificVariables is None:
        specificVariables = vars(list.values().__iter__().__next__()).keys()

    with open(path, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=specificVariables)
        writer.writeheader()
        for x, o in sorted(list.items()):
            row = {}
            for p in vars(o).items():
                if p[0] not in specificVariables:
                    row[p[0]] = None
                    continue

                if p[1]:
                    row[p[0]] = kalturaObjectValueToString(p[0], p[1])
                else:
                    row[p[0]] = None

            writer.writerow(row)
