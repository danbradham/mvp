import os
from functools import partial
import shiboken
from PySide import QtGui, QtCore
import maya.cmds as cmds
import maya.OpenMayaUI as OpenMayaUI
import maya.OpenMaya as OpenMaya

WEIGHTS = {
    'light': QtGui.QFont.Light,
    'normal': QtGui.QFont.Normal,
    'demibold': QtGui.QFont.DemiBold,
    'bold': QtGui.QFont.Bold,
    'black': QtGui.QFont.Black,
}


class ViewportLabel(object):

    def __init__(self, m3dview, label, callback):
        self.m3dview = m3dview
        self.label = label
        self._callback = callback

    def __del__(self):
        self.label.setParent(None)
        del(self.label)

    def callback(self):
        if not self._callback:
            return
        text = self._callback()
        self.label.setText(self._callback())
        self.label.setMinimumSize(self.label.minimumSizeHint())

class Viewport(object):

    identifier_labels = []

    def __init__(self, m3dview):
        self._m3dview = m3dview
        self.text_labels = []
        self._update_callback = None
        self._destroy_callback = None

    def get_widget(self):
        w = shiboken.wrapInstance(long(self._m3dview.widget()), QtGui.QWidget)
        return w

    def get_panel(self):
        panel = OpenMayaUI.MQtUtil.fullName(long(self._m3dview.widget()))
        for p in reversed(panel.split('|')):
            if p:
                return p

    def get_camera(self):
        camera = OpenMaya.MDagPath()
        self._m3dview.getCamera(camera)
        camera.pop()
        return camera.partialPathName()

    def set_camera(self, camera_path):
        sel = OpenMaya.MSelectionList()
        sel.add(camera_path)
        camera = OpenMaya.MDagPath()
        sel.getDagPath(0, camera)

        util = OpenMaya.MScriptUtil(0)
        int_ptr = util.asUintPtr()
        camera.numberOfShapesDirectlyBelow(int_ptr)
        num_shapes = util.getUint(int_ptr)
        if num_shapes:
            camera.extendToShape()

        self._m3dview.setCamera(camera)
        self._m3dview.scheduleRefresh()

    def get_background(self):
        color = self._m3dview.backgroundColor()
        return color[0], color[1], color[2]

    def set_background(self, values):
        cmds.displayRGBColor('background', *values)

    def _draw_text(self, **kwargs):
        '''Draw text in viewportand return a QLabel

        :param text: String to display in viewport
        :param color: Color of text
        :param size: Point Size of text
        :param position: Position of text in viewport
        :param weight: Weight of text (light, normal, demibold, bold, black)
        :param background: Background color (R, G, B)
        :param callback: Text callback
        '''

        text = kwargs.get('text', 'No Text')
        color = kwargs.get('color', (255, 255, 255))
        color = QtGui.QColor(*color)
        font = kwargs.get('font', 'Monospace')
        position = kwargs.get('position', (0, 0))
        weight = WEIGHTS[kwargs.get('weight', 'bold')]
        bgc = kwargs.get('background', self.get_background())
        bgc = bgc[0] * 255, bgc[1] * 255, bgc[2] * 255
        background = QtGui.QColor(*bgc)
        size = kwargs.get('size', 24)
        callback = kwargs.get('callback', None)

        qw = self.get_widget()
        label = QtGui.QLabel(text, parent=qw)
        font = QtGui.QFont(font, size, weight)
        font.setStyleHint(QtGui.QFont.TypeWriter)
        label.setFont(font)
        label.setAutoFillBackground(True)
        label.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft)
        palette = QtGui.QPalette()
        palette.setColor(label.backgroundRole(), background)
        palette.setColor(label.foregroundRole(), color)
        label.setPalette(palette)
        label.show()
        label.setMinimumSize(label.minimumSizeHint())
        label.move(*position)
        return ViewportLabel(self, label, callback)

    def draw_text(self, **kwargs):
        '''Draw text in viewport and install post render callback to update hud

        Signature to _draw_text method PLUS
        '''
        if not self._update_callback:
            self._create_update_callback()
        if not self._destroy_callback:
            self._create_destroy_callback()
        self.text_labels.append(self._draw_text(**kwargs))
        self._update_labels()

    def _preset_kwargs(self, **kwargs):
        kwargs.setdefault('position', (0, len(self.text_labels) * 30))
        kwargs.setdefault('size', 18)
        return kwargs

    def draw_frame(self, **kwargs):
        kwargs = self._preset_kwargs(**kwargs)

        def frame_callback():
            return "Frame {:>20}".format(int(cmds.getAttr('time1.outTime')))

        self.draw_text(callback=frame_callback, **kwargs)

    def draw_scene(self, **kwargs):
        kwargs = self._preset_kwargs(**kwargs)

        def scene_callback():
            scene = cmds.file(q=True, shn=True, sn=True)
            return "Scene {:>20}".format(os.path.splitext(scene)[0])

        self.draw_text(callback=scene_callback, **kwargs)

    def draw_camera(self, **kwargs):
        kwargs = self._preset_kwargs(**kwargs)

        def camera_callback():
            return "Camera {:>20}".format(self.get_camera())

        self.draw_text(callback=camera_callback, **kwargs)

    def draw_focal_length(self, **kwargs):
        kwargs = self._preset_kwargs(**kwargs)

        def focal_callback():
            cam = self.get_camera()
            focal_length = float(cmds.getAttr(cam + ".focalLength"))
            return "Lense {:>20.2f}".format(focal_length)

        self.draw_text(callback=focal_callback, **kwargs)

    def clear_text(self):
        self._destroy_labels()

    def register_callback(self, handler):
        callback = OpenMayaUI.MUiMessage.add3dViewPostRenderMsgCallback(
            self.get_panel(),
            handler)
        return callback

    def register_destroy_callback(self, handler):
        callback = OpenMayaUI.MUiMessage.add3dViewDestroyMsgCallback(
            self.get_panel(),
            handler)
        return callback

    def _create_update_callback(self):
        self._update_callback = self.register_callback(
            self._update_labels)

    def _create_destroy_callback(self):
        self._destroy_callback = self.register_destroy_callback(
            self._destroy_labels)

    def _update_labels(self, *args):
        for label in self.text_labels:
            label.callback()

    def _destroy_labels(self, *args):
        while True:
            try:
                label = self.text_labels.pop()
                del(label)
            except IndexError:
                break
        cb, self._update_callback = self._update_callback, None
        dcb, self._destroy_callback = self._destroy_callback, None
        if cb and dcb:
            OpenMayaUI.MUiMessage.removeCallback(cb)
            del(cb)
            OpenMayaUI.MUiMessage.removeCallback(dcb)
            del(dcb)

    @staticmethod
    def count():
        return OpenMayaUI.M3dView.numberOf3dViews()

    @classmethod
    def get(cls, index):
        m3dview = OpenMayaUI.M3dView()
        OpenMayaUI.M3dView.get3dView(index, m3dview)
        return cls(m3dview)

    @classmethod
    def active(cls):
        m3dview = OpenMayaUI.M3dView.active3dView()
        return cls(m3dview)

    @classmethod
    def show_identifiers(cls):
        for index, viewport in cls.enumerate():
            label = viewport._draw_text(
                text=str(index),
                font='Helvetica',
                size=128,
                position=(0,0),
                weight='bold',
            )
            cls.identifier_labels.append(label)

    @classmethod
    def clear_identifiers(cls):
        while True:
            try:
                label = cls.identifier_labels.pop()
                del(label)
            except IndexError:
                break

    @classmethod
    def enumerate(cls, visible=True):
        for index in xrange(cls.count()):
            m3dview = OpenMayaUI.M3dView()
            OpenMayaUI.M3dView.get3dView(index, m3dview)
            if not visible or (visible and m3dview.isVisible()):
                yield index, cls(m3dview)


def test_show_identifiers():
    Viewport.show_identifiers()
    QtCore.QTimer.singleShot(2000, test_clear_identifiers)


def test_clear_identifiers():
    Viewport.clear_identifiers()


def test_draw_text():
    view = Viewport.active()
    view.draw_scene()
    view.draw_frame()
    view.draw_camera()
    view.draw_focal_length()
    QtCore.QTimer.singleShot(2000, partial(test_clear_text, view))


def test_clear_text(view):
    view.clear_text()


def main():
    '''Temporary Shit, run test suite'''
    test_show_identifiers()
    QtCore.QTimer.singleShot(2050, test_draw_text)

if __name__ == '__main__':
    main()
