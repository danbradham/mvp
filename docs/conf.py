# -*- coding: utf-8 -*-

import os
import sys
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
