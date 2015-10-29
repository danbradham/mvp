# -*- coding: utf-8 -*-
import maya.cmds as cmds
import maya.api.OpenMayaUI as OpenMayaUI
import maya.api.OpenMaya as OpenMaya
import re
import os
import sys
import tempfile
from datetime import datetime
from collections import OrderedDict
import mvp.presets


CTX_PATTERNS = [
    r"sequences[/\\](?P<root>.*?)[/\\](?P<name>.*?)[/\\]",
    r"assets[/\\](?P<root>.*?)[/\\](?P<name>.*?)[/\\]"
]


def relative(*paths):
    '''Returns paths relative to the modules directory.'''

    return unipath(os.path.dirname(__file__), *paths)


def unipath(*paths):
    return os.path.abspath(os.path.join(*paths)).replace('\\', '/')


def get_context(path):
    '''Retrieve context from filepath.

    :returns: {'root': asset type or sequence, 'name': shot or asset name}'''

    for pattern in CTX_PATTERNS:
        ctx = re.search(pattern, path, re.IGNORECASE)
        if ctx:
            return ctx.groupdict()

    return {}


def get_renders_path():
    '''Retrieve a playblast path within the context of the current workspace'''

    project_root = cmds.workspace(q=True, rd=True)
    renders_dir = cmds.workspace('images', q=True, fileRuleEntry=True)
    scene = os.path.splitext(cmds.file(q=True, shn=True, sn=True))[0]
    ctx = get_context(project_root)

    return unipath(project_root, renders_dir, 'PLAYBLASTS',
                   ctx['root'], ctx['name'], scene)


def get_desktop_path():
    '''Desktop playblast path'''

    scene = os.path.splitext(cmds.file(q=True, shn=True, sn=True))[0]
    desktop = os.path.expanduser("~/Desktop")
    return unipath(desktop, scene)


def get_dailies_path():
    '''Dailies playblast path'''

    project_root = cmds.workspace(q=True, rd=True)
    dailies_dir = cmds.workspace('DAILIES', q=True, fileRuleEntry=True)
    today = datetime.now().strftime('%m%d%y')
    scene = os.path.splitext(cmds.file(q=True, shn=True, sn=True))[0]
    return unipath(project_root, dailies_dir, today, scene)


def get_temp_path():
    '''Temporary playblast path'''

    tf = tempfile.NamedTemporaryFile(prefix='tempblast_')
    temp_path = tf.name
    tf.close()
    return temp_path


mvp.presets.register('Renders', get_renders_path)
mvp.presets.register('Dailies', get_dailies_path)
mvp.presets.register('Desktop', get_desktop_path)
