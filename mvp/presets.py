import json
import glob
import os
import sys

presets_path = os.environ.get('MVP_PRESETS', os.path.expanduser('~/.mvp'))

if not os.path.exists(presets_path):
    os.makedirs(presets_path)

sys.path.insert(1, presets_path)


def get_presets():
    for f in glob.glob(os.path.join(presets_path, '*.json')):

        base = os.path.basename(f)
        name = os.path.splitext(base)[0]

        with open(f, 'r') as f:
            data = json.loads(f.read())

        yield name, data


def new_preset(name, data):

    with open(os.path.join(presets_path, f + '.json'), 'w') as f:
        f.write(json.dumps(data))


def del_preset(name):

    preset_path = os.path.join(presets_path, name + '.json')
    if os.path.exists(preset_path):
        os.remove(preset_path)


pathgen_registry = {}

def register(name, fn):
    pathgen_registry[name] = fn


def unregister(name):
    pathgen_registry.pop(name, None)


def load_preset_pymodules():
    for f in glob.glob(os.path.join(presets_path, '*.py')):

        base = os.path.basename(f)
        name = os.path.splitext(base)[0]
        __import__(base)
