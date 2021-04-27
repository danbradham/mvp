# -*- coding: utf-8 -*-

__title__ = 'mvp'
__author__ = 'Dan Bradham'
__email__ = 'danielbradham@gmail.com'
__url__ = 'http://github.com/danbradham/mvp.git'
__version__ = '0.9.0'
__license__ = 'MIT'
__description__ = 'Manipulate Maya 3D Viewports.'

from .viewport import Viewport, playblast
from .renderglobals import RenderGlobals
from . import config, utils, presets, hooks
from .ui import show

hooks.init()
