import re
import os

'''
The statics-folder should be placed in same folder as the statics_helper.
The secrets-folder is a sub-folder of the statics-folder.
'''
__statics_folder__ = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'statics')
__secrets_folder__ = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'statics/secrets')


def load_statics(name):
    class StaticsObject(object):
        pass

    def get_statics_path(n):
        secrets = False
        s = n.split('.')
        if len(s) > 1:
            if s[1] == 'secret':
                secrets = True
        # load_statics3: Final method for handling statics. Loads name from secrets folder, outputs object
        if secrets:
            return os.path.join(__secrets_folder__, n)
        else:
            return os.path.join(__statics_folder__, n)

    statics = StaticsObject()
    with open(get_statics_path(name), 'r') as f:
        for line in f:
            line = re.sub("[ '\n]", '', line)
            (key, val) = line.split('=')
            setattr(statics, key, val)
    return statics

