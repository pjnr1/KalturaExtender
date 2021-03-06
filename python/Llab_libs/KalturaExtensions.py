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
from Llab_libs.meta_helper import *
from Llab_libs.mail_helper import LLabMailHelper
from Llab_libs.Logger import SimpleLogger

# Kaltura imports
from Kaltura.KalturaClient import *
from Kaltura.KalturaClient.Base import *
from Kaltura.KalturaClient.Plugins.Core import *

__basepath__ = os.path.dirname(os.path.realpath(__file__))
__dual_user_list__ = os.path.join(__basepath__, 'json/dual_user_list.json')

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


def export_to_csv(list_to_export, path, specificVariables=None):
    if len(list_to_export) is 0:
        return

    if specificVariables is None:
        specificVariables = vars(list_to_export.values().__iter__().__next__()).keys()

    with open(path, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=specificVariables)
        writer.writeheader()
        for x, o in sorted(list_to_export.items()):
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


class KalturaExtender:
    TIMESTAMP_RANGE = 30

    client = NotImplemented
    errorMailer = NotImplemented
    logger = NotImplemented
    ks = NotImplemented
    categoryIds = NotImplemented

    def __init__(self, log=True, log_level=None, errormail=False):
        # Load secrets
        s = load_statics('kaltura.secret')
        # Load categoryIds
        self.categoryIds = load_statics('kaltura_categoryIds')
        # Load class meta
        self.meta = load_json('meta.json')
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
            if log_level is not None:
                self.logger.set_level(log_level)

    @staticmethod
    def apply_filter(filter_, filters):
        if filters is not None:
            for f in filters:
                if hasattr(filter_, f):
                    setattr(filter_, f, filters[f])
                else:
                    print('Warning:', filters[f], 'is not a valid attribute')

    @staticmethod
    def comp_timestamps(t1, t2, r=0):
        return abs(t1 - t2) <= r

    def get_client(self):
        if self.client is NotImplemented:
            raise RuntimeError('KalturaExtender::client not loaded!')
        return self.client

    def get_entry(self, entryId, entryType='media'):
        """
        Get entry by it's entryId. Default entry-type is 'media', however any KalturaApi supported entry types can be
        used.

        :param entryId:     id of entry
        :param entryType:   type of entry
        :return: entryType.Object
        """
        try:
            res = getattr(self.get_client(), entryType).get(entryId)
            if self.logger is not NotImplemented:
                log_str = "Fetching entry {0}".format(entryId)
                self.logger.info(log_str)
        except Exception as e:
            if self.logger is not NotImplemented:
                self.logger.error(e)
            return e
        return res

    def update_entry(self, entryId, updates, entryType='media', modifierEntry=None):
        """

        :param entryId:
        :param updates:
        :param entryType:
        :param modifierEntry:
        :return:
        """
        if modifierEntry is None:
            modifierEntry = KalturaMediaEntry()
        if updates is not None:
            for u in updates:
                if hasattr(modifierEntry, u):
                    setattr(modifierEntry, u, updates[u])
        try:
            res = getattr(self.get_client(), entryType).update(entryId, modifierEntry)
            if self.logger is not NotImplemented:
                log_str = "Updating entry {0}: {1}".format(entryId, updates)
                self.logger.warning(log_str)
        except Exception as e:
            if self.logger is not NotImplemented:
                self.logger.error(e)
            return e
        return res

    def delete_entry(self, entryId, entryType):
        """
        Delete entry by it's entryId and entryType

        :param entryId:     id of entry
        :param entryType:   type of entry
        :return:
        """
        try:
            res = getattr(self.get_client(), entryType).delete(entryId)
            if self.logger is not NotImplemented:
                log_str = "Deleting entry {0}".format(entryId)
                self.logger.warning(log_str)
        except Exception as e:
            if self.logger is not NotImplemented:
                self.logger.error(e)
            return e
        return res

    def get_entries(self, filters=None, entryType='media', printResult=False, specificVariables=None, pager=None):
        """
        Get list of entries based on filters. This also implements a print method for fast debugging.

        :param filters:
        :param entryType:
        :param printResult:
        :param specificVariables:
        :param pager:
        :return:
        """
        if entryType == 'media':
            entryFilter = KalturaMediaEntryFilter()
        elif entryType == 'category':
            entryFilter = KalturaCategoryFilter()
        elif entryType == 'liveStream':
            entryFilter = KalturaLiveStreamEntryFilter()
        elif entryType == 'user':
            assert pager is not None
            entryFilter = KalturaUserFilter()
        else:
            entryFilter = KalturaBaseEntryBaseFilter()

        self.apply_filter(entryFilter, filters)

        if pager is None:
            pager = KalturaFilterPager(pageSize=500)

        res = getattr(self.get_client(), entryType).list(entryFilter, pager)

        i = 0
        output = {}
        for entry in res.objects:
            output[entry.id] = entry

            if printResult:
                printKalturaObject(entry, specificVariables=specificVariables, counter=i)

            i += 1

        if filters is not None:
            log_str = "Found {0} {1}-entries with: {2}".format(i, entryType, filters)
        else:
            log_str = "Found {0} {1}-entries".format(i, entryType)
        self.logger.info(log_str)

        return output

    def get_users(self, printResult=True, onlyAdmins=False, specificVariables=None):
        p = KalturaFilterPager()
        p.pageSize = 500

        res = self.get_entries(entryType='user', pager=p)

        i = 0
        output = {}
        for userId, user in res.items():
            if onlyAdmins and not user.isAdmin:
                continue

            output[userId] = user

            if printResult:
                printKalturaObject(user, specificVariables=specificVariables, counter=i)

            i += 1

        if onlyAdmins:
            log_str = "Found {0} admin users".format(i)
        else:
            log_str = "Found {0} users".format(i)
        if self.logger is not NotImplemented:
            self.logger.info(log_str)

        return output

    def get_entries_by_user(self, userId, filters=None):
        if filters is not None:
            filters['userIdEqual'] = userId
        else:
            filters = {'userIdEqual': userId}

        res = self.get_entries(entryType='media', filters=filters)

        if self.logger is not NotImplemented:
            log_str = "Found {0} entries by {1}".format(len(res), userId)
            self.logger.info(log_str)

        return res

    def set_parent(self, parentId, childId):
        return self.update_entry(childId, {'parentEntryId': parentId})

    def get_categories(self, filters=None):
        return self.get_entries(filters=filters, entryType='category')

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

    def merge_dualstreams(self, verbose=False):
        if verbose:
            print(str(_now()),
                  'Searching for DualStream entries')

        pairedEntries = self.get_dualstream_pairs()

        updateErrorCount = 0
        errorList = []
        for parent, child in pairedEntries:
            try:
                self.set_parent(parentId=parent[1].id, childId=child[1].id)
                self.update_entry(entryId=parent[1].id, updates={'categoriesIds': self.categoryIds.Recordings})
                if self.logger is not NotImplemented:
                    self.logger.log('Updated (parent: {0}) and (child: {0})'.format(parent[0], child[0]),
                                    color="yellow")
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
        if totalCount == 0:
            finalInfo = 'No new dualstream recordings detected.'
        else:
            finalInfo = 'Updated {0} out of {1} entries'.format(str(updatedCount), str(totalCount))

        if self.logger is not NotImplemented:
            if updatedCount != totalCount:
                self.logger.warning(finalInfo)
            else:
                self.logger.info(finalInfo)
        if verbose:
            print(_now(), finalInfo)

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
        try:
            return self.update_entry(entryId=entryId, updates={'userId': userId})
        except Exception as e:
            return e

    def set_entry_coowners(self, entry, userIdList):
        # Insert method to test
        newEntitledUsersEdit = list()
        newEntitledUsersPublish = list()

        for uid in userIdList:
            newEntitledUsersEdit.append(uid)
            newEntitledUsersPublish.append(uid)

        eue = entry.entitledUsersEdit.split(',')
        eup = entry.entitledUsersPublish.split(',')

        for uid in eue:
            newEntitledUsersEdit.append(uid)
        for uid in eup:
            newEntitledUsersPublish.append(uid)

        return self.update_entry(entryId=entry.id, updates={'entitledUsersEdit': ','.join(newEntitledUsersEdit),
                                                            'entitledUsersPublish': ','.join(newEntitledUsersPublish)})

    # todo: rewrite to grab all entry-lists with a multiRequest
    def set_dual_user_ownerships(self, kms_userId, lms_userId):
        c = 0
        f = {'typeEqual': KalturaEntryType.MEDIA_CLIP,
             'userIdEqual': lms_userId}
        for lms_owned_entryId, entry in self.get_entries(filters=f).items():
            try:
                self.set_entry_ownership(lms_owned_entryId, kms_userId)
            except Exception:
                pass
            else:
                c = c + 1

        f = {'typeEqual': KalturaEntryType.MEDIA_CLIP,
             'userIdEqual': kms_userId}
        for kms_owned_entryId, entry in self.get_entries(filters=f).items():
            if lms_userId not in entry.entitledUsersEdit.split(',') or \
               lms_userId not in entry.entitledUsersPublish.split(','):
                try:
                    self.set_entry_coowners(entry, [kms_userId, lms_userId])
                except Exception:
                    pass
                else:
                    c = c + 1

        f = {'typeEqual': KalturaEntryType.MEDIA_CLIP,
             'entitledUsersEditMatchOr': ','.join([kms_userId, lms_userId])}
        for entryId, entry in self.get_entries(filters=f).items():
            if kms_userId not in entry.entitledUsersEdit.split(',') or \
               lms_userId not in entry.entitledUsersEdit.split(','):
                try:
                    self.add_entry_coeditor(entry, [kms_userId, lms_userId])
                except Exception:
                    pass
                else:
                    c = c + 1

        f = {'typeEqual': KalturaEntryType.MEDIA_CLIP,
             'entitledUsersPublishMatchOr': ','.join([kms_userId, lms_userId])}
        for entryId, entry in self.get_entries(filters=f).items():
            if kms_userId not in entry.entitledUsersPublish.split(',') or \
               lms_userId not in entry.entitledUsersPublish.split(','):
                try:
                    self.add_entry_copublisher(entry, [kms_userId, lms_userId])
                except:
                    pass
                else:
                    c = c + 1

        return c

    def add_entry_coeditor(self, entry, userId):
        coEditors = entry.entitledUsersEdit.split(',')
        c = 0
        for uId in userId:
            if uId not in coEditors:
                coEditors.append(uId)
                c = c + 1
        if c is 0:
            return
        coEditors = ','.join(coEditors)
        return self.update_entry(entryId=entry.id, updates={'entitledUsersEdit': coEditors})

    def add_entry_copublisher(self, entry, userId):
        coPublishers = entry.entitledUsersPublish.split(',')
        c = 0
        for uId in userId:
            if uId not in coPublishers:
                coPublishers.append(uId)
                c = c + 1
        if c is 0:
            return
        coPublishers = ','.join(coPublishers)
        return self.update_entry(entryId=entry.id, updates={'entitledUsersPublish': coPublishers})

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

        addedCount = len(user_list) - c

        if addedCount is 0:
            log_str = "No new dual users detected"
        else:
            log_str = "Found {0} new dual users to local list {1} ".format(addedCount, __dual_user_list__)
            try:
                if os.path.isfile(__dual_user_list__):
                    os.remove(__dual_user_list__)
                with open(__dual_user_list__, 'w') as f:
                    json.dump(user_list, f)
            except Exception as e:
                self.logger.error("Error removing and rewriting user-list: {0}".format(__dual_user_list__))
                if self.errorMailer is not NotImplemented:
                    self.errorMailer.send_error_mail(msg=e)

        if self.logger is not NotImplemented:
            self.logger.info(log_str)

        return addedCount

    def update_dual_user_ownerships(self):
        user_list = None
        if os.path.isfile(__dual_user_list__):
            with open(__dual_user_list__, 'r') as f:
                user_list = json.load(f)
        c = 0
        if user_list is not None:
            for user in user_list:
                d = self.set_dual_user_ownerships(user['kms_user'], user['lms_user'])
                c = c + d

        if self.logger is not NotImplemented:
            if c > 0:
                log_str = "Updated {0} dual user entries".format(c)
            else:
                log_str = "No new dual user entries detected"
            self.logger.info(log_str)

    def init_request_queue(self):
        self.get_client().startMultiRequest()

    def send_request_queue(self):
        return self.get_client().doMultiRequest()

    def get_updated_entries(self, since):
        f = {'typeEqual': KalturaEntryType.MEDIA_CLIP,
             'updatedAtGreaterThanOrEqual': since}
        return self.get_entries(filters=f)

    def get_updated_since_last_run(self):
        meta = load_json('meta')
        update_json('meta', {'lastRun': int(datetime.timestamp(datetime.now()))})
        return self.get_updated_entries(meta['lastRun'])

    def create_mix_entry(self, name):
        mixEntry = KalturaMixEntry()
        mixEntry.name = name
        mixEntry.userId = 'jectli@llab.dtu.dk'
        mixEntry.editorType = KalturaEditorType.ADVANCED
        return self.get_client().mixing.add(mixEntry)

    def append_mix_entry(self, mixEntryId, mediaEntryId):
        return self.get_client().mixing.appendMediaEntry(mixEntryId, mediaEntryId)
