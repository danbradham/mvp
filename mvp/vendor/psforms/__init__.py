# -*- coding: utf-8 -*-

__title__ = 'psforms'
__author__ = 'Dan Bradham'
__email__ = 'danielbradham@gmail.com'
__url__ = 'http://github.com/danbradham/psforms.git'
__version__ = '0.7.0'
__license__ = 'MIT'
__description__ = 'Hassle free PySide forms.'

import os

from . import (controls, exc, fields, resource, widgets)
from .form import Form, FormMetaData
from .validators import *

with open(os.path.join(os.path.dirname(__file__), 'style.css')) as f:
    stylesheet = f.read()
