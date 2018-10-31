import csv
import re
import os
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
listOfUnixTimeStampVariables = ['createdAt', 'updatedAt', 'lastLoginTime',
                                'statusUpdatedAt', 'deletedAt', 'mediaDate',
                                'firstBroadcast', 'lastBroadcast']


def _now():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def kalturaObjectValueToString(a, v):
    if v is None or v is NotImplemented:
        return None
    elif 'Kaltura' in type(v).__name__:
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

    def update_entry(self, id, updates, entryType='media', modifierEntry=KalturaMediaEntry()):
        if updates is not None:
            for u in updates:
                if hasattr(modifierEntry, u):
                    setattr(modifierEntry, u, updates[u])

        return getattr(self.get_client(), entryType).update(id, modifierEntry)

    def delete_entry(self, id, entryType):
        return getattr(self.get_client(), entryType).delete(id)

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
                client.update_entry(id=parent[1].id, updates={'categoriesIds': self.categoryIds.Recordings})
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
            if self.logger:
                self.logger.critical(errorHeader)
            if verbose:
                print(errorHeader)

            for e in errorList:
                if self.logger:
                    self.logger.error(e)
                if verbose:
                    print('-' * 80)
                    print(e)
            if self.errorMailer:
                self.errorMailer.send_error_mail(__file__, errorList)

        updatedCount = len(pairedEntries) - updateErrorCount
        totalCount = len(pairedEntries)
        finalInfo = '{0} Updated {1} out of {2}entries'.format(str(_now()),
                                                               str(updatedCount), str(totalCount))

        if self.logger:
            if updatedCount != totalCount:
                self.logger.warning(finalInfo)
            else:
                self.logger.info(finalInfo)
        if verbose:
            print(finalInfo)

    def get_dual_users(self):
        userList = self.get_users(printResult=False)
        for user in userList:
            print(user)


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
