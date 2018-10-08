import re


def load_statics(path):
    s = {}
    with open(path, 'r') as f:
        for line in f:
            line = re.sub("[ '\n]", '', line)
            (key, val) = line.split('=')
            s[key] = val
    return s
