# -*- coding: utf-8 -*-

import os
import glob
from collections import OrderedDict
from . import config


POSTRENDER_REGISTRY = OrderedDict()


def register_postrender(name, fn, default=None):
    '''Add postrender function to registry

    :param name: Name of postrender function (used as label in ui)
    :param fn: Postrender function
    '''

    fn.default = default
    POSTRENDER_REGISTRY[name] = fn


def unregister_postrender(name):
    '''Remove postrender function from registry'''

    POSTRENDER_REGISTRY.pop(name, None)


PATHGEN_REGISTRY = OrderedDict()


def register_path(name, fn):
    '''Add a path generator function to registry

    :param name: Name of path generator (used as label in ui)
    :param fn: Path generator function
    '''

    PATHGEN_REGISTRY[name] = fn


def unregister_path(name):
    '''Remove path generator function from registry

    :param name: Name of path generator function
    '''

    PATHGEN_REGISTRY.pop(name, None)


INTEGRATION_REGISTRY = OrderedDict()


def register_integration(name, fn):
    '''Add a path generator function to registry

    :param name: Name of path generator (used as label in ui)
    :param fn: Path generator function
    '''

    INTEGRATION_REGISTRY[name] = fn


def unregister_integration(name):
    '''Remove path generator function from registry

    :param name: Name of path generator function
    '''

    INTEGRATION_REGISTRY.pop(name, None)


def init():
    '''Import all python files in config.PRESETS_PATH'''

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
