'''
Configure mvp presets and hooks
'''

import os
import sys

PRESETS_PATH = os.environ.get('MVP_PRESETS', os.path.expanduser('~/.mvp'))

if not os.path.exists(PRESETS_PATH):
    os.makedirs(PRESETS_PATH)

sys.path.insert(1, PRESETS_PATH)
