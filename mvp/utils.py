from Qt import QtWidgets
import time


def get_maya_window(cache=[]):
    '''Get Maya MainWindow as a QWidget.'''

    if cache:
        return cache[0]

    for widget in QtWidgets.qApp.topLevelWidgets():
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
