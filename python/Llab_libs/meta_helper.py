import re
import os
import json

__json_folder__ = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'json')


def load_json(name):
    res = None
    n = os.path.join(__json_folder__, name + '.json')
    if os.path.isfile(n):
        with open(n, 'r') as f:
            try:
                res = json.load(f)
            except json.decoder.JSONDecodeError:
                pass
    return res


def save_json(name, o):
    n = os.path.join(__json_folder__, name + '.json')
    if os.path.isfile(n):
        with open(n, 'w') as f:
            json.dump(o, f)


def update_json(name, update):
    json_old = load_json(name)

    if isinstance(json_old, type(None)):
        save_json(name, update)
    elif isinstance(json_old, dict):
        for key, u in update.items():
            json_old[key] = u
    save_json(name, json_old)

