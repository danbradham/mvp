# -*- coding: utf-8 -*-

import json
import glob
import os
from . import config


def get_presets():
    '''Get a generator yielding preset name, data pairs'''

    for path in config.PRESETS_PATH:
        for f in glob.glob(os.path.join(path, '*.json')):

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


def find_preset(name):
    '''Find the path to a given preset...'''

    for path in config.PRESETS_PATH:
        prospect = os.path.join(path, name + '.json')
        if os.path.isfile(prospect):
            return prospect

    raise ValueError('Could not find a preset named %s', name)


def new_preset(name, data):
    '''Create a new preset from viewport state data

    :param name: Name of the preset
    :param data: Viewport state dict

    usage::

        import mvp
        active = mvp.Viewport.active()
        mvp.new_preset('NewPreset1', active.get_state())
    '''

    preset_path = os.path.join(config.PRESETS_PATH[0], name + '.json')
    with open(preset_path, 'w') as f:
        f.write(json.dumps(data))


def del_preset(name):

    preset_path = find_preset(name)
    if os.path.exists(preset_path):
        os.remove(preset_path)
