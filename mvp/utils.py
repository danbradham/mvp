from PySide import QtGui, QtCore
from maya.OpenMayaUI import MQtUtil
import shiboken
import time



def get_maya_window():
    '''Get Maya MainWindow as a QWidget.'''

    ptr = long(MQtUtil.mainWindow())
    return shiboken.wrapInstance(ptr, QtGui.QMainWindow)


def wait(delay=1):
    '''Delay python execution for a specified amount of time'''

    s = time.clock()

    while True:
        if time.clock() - s >= delay:
            return
        QtGui.qApp.processEvents()
