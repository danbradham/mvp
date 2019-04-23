# -*- coding: utf-8 -*-
'''
Configure mvp presets and hooks
'''

import os
import sys


USER_PRESETS_PATH = os.path.expanduser('~/.mvp')
PRESETS_PATH = [USER_PRESETS_PATH]

# Add paths from MVP_PRESETS env var
for path in os.environ.get('MVP_PRESETS', '').split(os.pathsep):
    if path:
        PRESETS_PATH.insert(0, path)

for path in PRESETS_PATH:

    if not os.path.exists(path):
        os.makedirs(path)

    sys.path.insert(1, path)
