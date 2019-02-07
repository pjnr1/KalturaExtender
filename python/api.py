"""
This file is kept for extending the Kaltura API to a public API for indexing and fetching metadata of the site
"""
from Llab_libs.KalturaExtensions import *
import json
import time
import argparse

import collections


class SkipFilter(object):
    def __init__(self, types=None, keys=None, allow_empty=False):
        self.types = tuple(types or [])
        self.keys = set(keys or [])
        self.allow_empty = allow_empty  # if True include empty filtered structures

    def filter(self, data):
        if isinstance(data, collections.Mapping):
            result = {}  # dict-like, use dict as a base
            for k, v in data.items():
                if k in self.keys or isinstance(v, self.types):  # skip key/type
                    continue
                try:
                    result[k] = self.filter(v)
                except ValueError:
                    pass
            if result or self.allow_empty:
                return result
        else:  # we don't know how to traverse this structure...
            return data  # return it as-is, hope for the best...
        raise ValueError('Empty data')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--kaltura', action='store_const', const=True)
    parser.add_argument('--categoryId')
    args = parser.parse_args()
    if args.kaltura is not None:
        client = KalturaExtender(log_level='all')

        if args.categoryId is not None:
            res = client.get_entries(filters={'categoriesIdsMatchAnd': args.categoryId})
            json_prep = dict()
            for key, item in res.items():
                json_prep[key] = item.__dict__
            preprocessor = SkipFilter([], ['status',
                                           'moderationStatus',
                                           'type',
                                           'licenseType',
                                           'replacementStatus',
                                           'operationAttributes',
                                           'displayInSearch',
                                           'mediaType',
                                           'sourceType',
                                           'searchProviderType'],
                                      allow_empty=True)
            print(json.dumps(preprocessor.filter(json_prep)))
