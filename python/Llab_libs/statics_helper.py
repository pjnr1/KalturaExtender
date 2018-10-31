import re
import os


__statics_folder__ = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'statics')
__secrets_folder__ = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'statics/secrets')


class StaticsObject(object):
    pass


def get_statics_path(name):
    secrets = False
    s = name.split('.')
    if len(s) > 1:
        if s[1] == 'secret':
            secrets = True
    # load_statics3: Final method for handling statics. Loads name from secrets folder, outputs object
    if secrets:
        return os.path.join(__secrets_folder__, name)
    else:
        return os.path.join(__statics_folder__, name)


def load_statics(name):
    s = StaticsObject()
    with open(get_statics_path(name), 'r') as f:
        for line in f:
            line = re.sub("[ '\n]", '', line)
            (key, val) = line.split('=')
            setattr(s, key, val)
    return s

