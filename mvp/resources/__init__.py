from os.path import abspath, dirname, join
from ..vendor.Qt import QtCore, QtGui


res_package = dirname(__file__)


def get_path(*parts):
    return abspath(join(res_package, *parts)).replace('\\', '/')


def get_qicon(resource, size=None):
    if size:
        pixmap = QtGui.QPixmap(get_path(resource))
        icon = QtGui.QIcon(pixmap.scaled(
            size,
            QtCore.Qt.IgnoreAspectRatio,
            QtCore.Qt.SmoothTransformation,
        ))
    else:
        icon = QtGui.QIcon(get_path(resource))
    return icon


def get_style():
    with open(get_path('style.css'), 'r') as f:
        style = f.read()
    return style
