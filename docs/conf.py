# -*- coding: utf-8 -*-

import sys
import mock # Mock for maya specific modules
for mod in ['maya.cmds', 'maya.OpenMaya', 'maya.OpenMayaUI',
            'pymel.core', 'PySide', 'shiboken']:
    sys.modules[mod] = mock.MagicMock()

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
