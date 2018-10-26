import re
import os


__secrets_folder__ = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'secrets')


class StaticsObject(object):
    pass


def load_statics_old(path):
    # load_statics_old: Old method for handling statics. Loads path and outputs dict of statics

    s = {}
    with open(path, 'r') as f:
        for line in f:
            line = re.sub("[ '\n]", '', line)
            (key, val) = line.split('=')
            s[key] = val
    return s


def load_statics2(path):
    # load_statics2: Newer method for handling statics. Loads path and outputs object
    s = StaticsObject()
    with open(path, 'r') as f:
        for line in f:
            line = re.sub("[ '\n]", '', line)
            (key, val) = line.split('=')
            setattr(s, key, val)
    return s


def load_statics3(name):
    # load_statics3: Final method for handling statics. Loads name from secrets folder, outputs object
    path = os.path.join(__secrets_folder__, name)
    s = StaticsObject()
    with open(path, 'r') as f:
        for line in f:
            line = re.sub("[ '\n]", '', line)
            (key, val) = line.split('=')
            setattr(s, key, val)
    return s

