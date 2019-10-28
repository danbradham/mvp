# -*- coding: utf-8 -*-

from Qt import QtWidgets
import time
from contextlib import contextmanager


def get_maya_window(cache=[]):
    '''Get Maya MainWindow as a QWidget.'''

    if cache:
        return cache[0]

    for widget in QtWidgets.QApplication.instance().topLevelWidgets():
        if widget.objectName() == 'MayaWindow':
            cache.append(widget)
            return widget

    raise RuntimeError('Could not locate MayaWindow...')


def wait(delay=1):
    '''Delay python execution for a specified amount of time'''

    app = QtWidgets.QApplication.instance()

    s = time.clock()
    while True:
        if time.clock() - s >= delay:
            return

        app.processEvents()


@contextmanager
def viewport_state(viewport, state):
    '''Sets a viewports state options for the duration of the context.

    Example:

        # Turn off the display of nurbsCurves
        viewport = Viewport.active()
        state = viewport.state()
        state['nurbsCurves'] = False

        with viewport_state(viewport, state):
            # Do something with nurbsCurves off
    '''

    previous_state = viewport.get_state()
    try:
        viewport.set_state(state)
        yield
    finally:
        viewport.set_state(previous_state)
