import json
import glob
import os
import sys

PRESETS_PATH = os.environ.get('MVP_PRESETS', os.path.expanduser('~/.mvp'))

if not os.path.exists(PRESETS_PATH):
    os.makedirs(PRESETS_PATH)

sys.path.insert(1, PRESETS_PATH)


def get_presets():
    for f in glob.glob(os.path.join(PRESETS_PATH, '*.json')):

        base = os.path.basename(f)
        name = os.path.splitext(base)[0]

        with open(f, 'r') as f:
            data = json.loads(f.read())

        yield name, data


def get_preset(name):

    for n, s in get_presets():
        if name == n:
            return s


def new_preset(name, data):

    preset_path = os.path.join(PRESETS_PATH, name + '.json')
    with open(preset_path, 'w') as f:
        f.write(json.dumps(data))


def del_preset(name):

    preset_path = os.path.join(PRESETS_PATH, name + '.json')
    if os.path.exists(preset_path):
        os.remove(preset_path)


PATHGEN_REGISTRY = {}

def register(name, fn):
    PATHGEN_REGISTRY[name] = fn


def unregister(name):
    PATHGEN_REGISTRY.pop(name, None)


def init():
    for f in glob.glob(os.path.join(PRESETS_PATH, '*.py')):

        base = os.path.basename(f)
        name = os.path.splitext(base)[0]
        __import__(name)
