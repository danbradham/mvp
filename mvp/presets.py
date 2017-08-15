import json
import glob
import os
from . import config


def get_presets():
    '''Get a generator yielding preset name, data pairs'''

    for f in glob.glob(os.path.join(config.PRESETS_PATH, '*.json')):

        base = os.path.basename(f)
        name = os.path.splitext(base)[0]

        with open(f, 'r') as f:
            data = json.loads(f.read())

        yield name, data


def get_preset(name):
    '''Get a preset by name'''

    for n, s in get_presets():
        if name == n:
            return s


def new_preset(name, data):
    '''Create a new preset from viewport state data

    :param name: Name of the preset
    :param data: Viewport state dict

    usage::

        import mvp
        active = mvp.Viewport.active()
        mvp.new_preset('NewPreset1', active.get_state())
    '''

    preset_path = os.path.join(config.PRESETS_PATH, name + '.json')
    with open(preset_path, 'w') as f:
        f.write(json.dumps(data))


def del_preset(name):

    preset_path = os.path.join(config.PRESETS_PATH, name + '.json')
    if os.path.exists(preset_path):
        os.remove(preset_path)
