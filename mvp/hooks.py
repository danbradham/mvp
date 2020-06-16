# -*- coding: utf-8 -*-

import os
import glob
from collections import OrderedDict, namedtuple
from . import config


postrender = OrderedDict()
pathgen = OrderedDict()
integration = OrderedDict()
extension = OrderedDict()

PathGenerator = namedtuple('PathGenerator', ['name', 'handler'])
PostRender = namedtuple('PostRender', ['name', 'handler', 'default'])
Extension = namedtuple('Extension', ['name', 'ext', 'handler', 'options'])


def register_postrender(name, handler, default=None):
    '''Add postrender function to registry

    :param name: Name of postrender function (used as label in ui)
    :param handler: Postrender function
    '''

    postrender[name] = PostRender(name, handler, default)


def unregister_postrender(name):
    '''Remove postrender function from registry'''

    postrender.pop(name, None)


def register_path(name, handler):
    '''Add a path generator function to registry

    :param name: Name of path generator (used as label in ui)
    :param handler: Path generator function
    '''

    pathgen[name] = PathGenerator(name, handler)


def unregister_path(name):
    '''Remove path generator function from registry

    :param name: Name of path generator function
    '''

    pathgen.pop(name, None)


def register_integration(name, obj):
    '''Add a path generator function to registry

    :param name: Name of Integration
    :param obj: Integration obj
    '''

    integration[name] = obj


def unregister_integration(name):
    '''Remove path generator function from registry

    :param name: Name of integration to remove
    '''

    integration.pop(name, None)


def register_extension(name, ext, handler, options=None):
    '''Register a function to handle playblasting a specific file extension

    :param name: Nice name of the extension
    :param ext: File extension
    :param handler: Handler function that performs the playblasting
    '''

    extension[name] = Extension(name, ext, handler, options)


def unregister_extension(name):
    '''Register a function to handle playblasting a specific file extension

    :param name: Nice name of the extension to unregister
    '''

    extension.pop(name, None)


def init():
    '''Discover presets'''

    postrender.clear()
    pathgen.clear()
    integration.clear()
    extension.clear()

    # Find registered presets in MVP_PRESETS path
    for path in config.PRESETS_PATH:

        # Import all python files on MVP_PRESETS path
        for f in glob.glob(os.path.join(path, '*.py')):
            base = os.path.basename(f)
            name = os.path.splitext(base)[0]
            __import__(name)

        # Import all packages on MVP_PRESETS path
        for f in glob.glob(os.path.join(path, '*', '__init__.py')):
            name = os.path.basename(os.path.dirname(f))
            __import__(name)

    # Import builtin extensions
    from . import extensions
