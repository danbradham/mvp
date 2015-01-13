# -*- coding: utf-8 -*-

import sys
import mock

MOCK_MODULES = ['maya', 'maya.cmds', 'maya.OpenMaya', 'maya.OpenMayaUI',
                'maya.utils', 'pymel', 'pymel.core', 'PySide', 'shiboken']
sys.modules.update((mod_name, mock.Mock()) for mod_name in MOCK_MODULES)

import os
sys.path.insert(0, os.path.abspath('..'))
import mvp

extensions = [
    'sphinx.ext.intersphinx',
    'sphinx.ext.autodoc',
]

source_suffix = '.rst'
master_doc = 'index'
project = mvp.__title__
copyright = u'2015, {0}'.format(mvp.__author__)
version = mvp.__version__
release = mvp.__version__
pygments_style = 'sphinx'
intersphinx_mapping = {'http://docs.python.org/': None}
