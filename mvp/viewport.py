# -*- coding: utf-8 -*-
from __future__ import print_function, absolute_import

import sys

import maya.cmds as cmds
import maya.OpenMayaUI as OpenMayaUI
import maya.OpenMaya as OpenMaya
import maya.utils as utils
from Qt import QtGui, QtCore, QtWidgets

from .renderglobals import RenderGlobals
from .utils import wait, viewport_state, get_maya_window

# Py3 compat
if sys.version_info > (3, 0):
    basestring = str
    long = int


EDITOR_PROPERTIES = [
    'activeComponentsXray',
    'activeOnly',
    'backfaceCulling',
    'bufferMode',
    'bumpResolution',
    'camera',
    'cameras',
    'clipGhosts',
    'colorResolution',
    'controllers',
    'controlVertices',
    'cullingOverride',
    'deformers',
    'depthOfField',
    'dimensions',
    'displayAppearance',
    'displayLights',
    'displayTextures',
    'dynamicConstraints',
    'dynamics',
    'fluids',
    'fogColor',
    'fogDensity',
    'fogEnd',
    'fogging',
    'fogMode',
    'fogSource',
    'fogStart',
    'follicles',
    'gpuCacheDisplayFilter',
    'greasePencils',
    'grid',
    'hairSystems',
    'handles',
    'headsUpDisplay',
    'hulls',
    'ignorePanZoom',
    'ikHandles',
    'imagePlane',
    'interactiveBackFaceCull',
    'interactiveDisableShadows',
    'isFiltered',
    'joints',
    'jointXray',
    'lights',
    'lineWidth',
    'locators',
    'lowQualityLighting',
    'manipulators',
    'maxConstantTransparency',
    'maximumNumHardwareLights',
    'motionTrails',
    'nCloths',
    'nParticles',
    'nRigids',
    'nurbsCurves',
    'nurbsSurfaces',
    'objectFilterShowInHUD',
    'occlusionCulling',
    'particleInstancers',
    'pivots',
    'planes',
    'pluginShapes',
    'polymeshes',
    'rendererName',
    'selectionHiliteDisplay',
    'shadingModel',
    'shadows',
    'smallObjectCulling',
    'smallObjectThreshold',
    'smoothWireframe',
    'sortTransparent',
    'strokes',
    'subdivSurfaces',
    'textureAnisotropic',
    'textureCompression',
    'textureDisplay',
    'textureHilight',
    'textureMaxSize',
    'textures',
    'textureSampling',
    'transparencyAlgorithm',
    'transpInShadows',
    'twoSidedLighting',
    'useBaseRenderer',
    'useDefaultMaterial',
    'useInteractiveMode',
    'useReducedRenderer',
    'viewSelected',
    'wireframeOnShaded',
    'xray',
]

CAMERA_PROPERTIES = [
    'displayFilmGate',
    'displayResolution',
    'displayGateMask',
    'displayFieldChart',
    'displaySafeAction',
    'displaySafeTitle',
    'displayFilmPivot',
    'displayFilmOrigin',
    'overscan',
    'displayGateMaskOpacity',
    'displayGateMaskColor'
]


def deferred_close(view):
    panel = view.panel
    wait(0.1)
    utils.executeDeferred(cmds.deleteUI, panel, panel=True)


def playblast(camera=None, state=None, **kwargs):
    '''Playblast the active viewport.

    Arguments:
        :param camera: Camera to playblast
        :param state: Viewport state

    Playblast Arguments:
        :param width: Resolution width
        :param height: Resolution height
        :param format: Render format like qt or image
        :param compression: Render compression
        :param viewer: Launch the default viewer afterwards
    '''

    playblast_kwargs = {
        'offScreen': False,
        'percent': 100,
        'quality': 100,
        'viewer': False,
        'width': 960,
        'height': 540,
        'framePadding': 4,
        'format': 'qt',
        'compression': 'H.264',
        'forceOverwrite': True,
    }
    playblast_kwargs.update(kwargs)

    active = Viewport.active()
    state = state or active.get_state()

    if camera:
        state['camera'] = camera

    with viewport_state(active, state):
        file = cmds.playblast(**playblast_kwargs)

    return file

class EditorProperty(object):

    def __init__(self, name):
        self.name = name

    def __get__(self, inst, typ=None):
        '''Gets a model editor property.'''

        if not inst:
            return self

        try:
            val = cmds.modelEditor(
                inst.panel,
                **{'query': True, self.name: True}
            )
        except TypeError:
            val = cmds.modelEditor(
                inst.panel,
                **{'query': True, 'qpo': self.name}
            )

        if self.name == 'smallObjectThreshold':
            val = val[0]

        return val

    def __set__(self, inst, value):
        '''Sets a model editor property.'''

        try:
            cmds.modelEditor(
                inst.panel,
                **{'edit': True, self.name: value}
            )
        except TypeError:
            cmds.modelEditor(
                inst.panel,
                **{'edit': True, 'po': [self.name, value]}
            )


class CameraProperty(object):

    def __init__(self, name):
        self.name = name

    def __get__(self, inst, typ=None):
        '''Gets a model panels camera property'''

        if not inst:
            return self

        attr = inst.camera + '.' + self.name
        value = cmds.getAttr(attr)
        if isinstance(value, list):
            if len(value) == 1 and isinstance(value[0], (list, tuple)):
                value = value[0]
        return value

    def __set__(self, inst, value):
        '''Sets a model panels camera property'''

        attr = inst.camera + '.' + self.name

        locked = cmds.getAttr(attr, lock=True)
        if locked:
            return

        has_connections = cmds.listConnections(attr, s=True, d=False)
        if has_connections:
            return

        try:
            if isinstance(value, (int, float)):
                cmds.setAttr(attr, value)
            elif isinstance(value, basestring):
                cmds.setAttr(attr, value, type='string')
            elif isinstance(value, (list, tuple)):
                cmds.setAttr(attr, *value)
            else:
                cmds.setAttr(attr, value)
        except Except as e:
            print('Failed to set state: %s %s' % (attr, value))
            print(e)


class Viewport(object):
    '''A convenient api for manipulating Maya 3D Viewports. While you can
    manually construct a Viewport from an OpenMayaUI.M3dView instance, it is
    much easier to use the convenience methods Viewport.iter,
    Viewport.active and Viewport.get::

        # Get the active view
        v = Viewport.active()
        assert v.focus == True

        # Assuming we have a second modelPanel available
        # Get an inactive view and make it the active view
        v2 = Viewport.get(1)
        v2.focus = True

        assert v.focus == False
        assert v2.focus == True

    Viewport provides standard attribute lookup to all modelEditor properties::

        # Hide nurbsCurves and show polymeshes in the viewport
        v.nurbsCurves = False
        v.polymeshes = True

    :param m3dview: OpenMayaUI.M3dView instance.
    '''

    for p in EDITOR_PROPERTIES:
        locals()[p] = EditorProperty(p)

    for p in CAMERA_PROPERTIES:
        locals()[p] = CameraProperty(p)

    def __init__(self, m3dview):
        self._m3dview = m3dview
        self.highlight = self._highlight
        self.identify = self._highlight

    def __hash__(self):
        return hash(self._m3dview)

    def __eq__(self, other):
        if hasattr(other, '_m3dview'):
            return self._m3dview == other._m3dview
        return self.panel == other

    def copy(self):
        '''Tear off a copy of the viewport.

        :returns: A new torn off copy of Viewport'''

        panel = cmds.modelPanel(tearOffCopy=self.panel)
        view = self.from_panel(panel)
        view.focus = True
        return view

    __copy__ = copy
    __deepcopy__ = copy

    def float(self):
        '''Tear off the panel.'''
        copied_view = self.copy()
        deferred_close(self)
        self._m3dview = copied_view._m3dview

    @classmethod
    def new(cls):
        panel = cmds.modelPanel()
        view = cls.from_panel(panel)
        view.float()
        view.focus = True
        return view

    def close(self):
        '''Close this viewport'''
        deferred_close(self)

    @property
    def properties(self):
        '''A list including all editor property names.'''

        return EDITOR_PROPERTIES + CAMERA_PROPERTIES

    def get_state(self):
        '''Get a state dictionary of all modelEditor properties.'''

        active_state = {}
        active_state['RenderGlobals'] = RenderGlobals.get_state()
        for ep in EDITOR_PROPERTIES + CAMERA_PROPERTIES:
            active_state[ep] = getattr(self, ep)

        return active_state

    def set_state(self, state):
        '''Sets a dictionary of properties all at once.

        :param state: Dictionary including property, value pairs'''

        cstate = state.copy()

        renderglobals_state = cstate.pop('RenderGlobals', None)
        if renderglobals_state:
            RenderGlobals.set_state(renderglobals_state)

        for k, v in cstate.items():
            setattr(self, k, v)

    def playblast(self, camera=None, state=None, **kwargs):
        '''Playblasting with reasonable default arguments. Automatically sets
        this viewport to the active view, ensuring that we playblast the
        correct view.

        :param kwargs: Same kwargs as :func:`maya.cmds.playblast`'''

        if not self.focus:
            self.focus = True

        playblast(camera=None, state=None, **kwargs)

    @property
    def screen_geometry(self):
        qapp = QtWidgets.QApplication.instance()
        desktop = qapp.desktop()
        screen = desktop.screenNumber(self.widget)
        return desktop.screenGeometry(screen)

    def center(self):
        screen_center = self.screen_geometry.center()
        window_center = self.window.rect().center()
        pnt = screen_center - window_center
        self.window.move(pnt)

    @property
    def size(self):
        return self._m3dview.portWidth(), self._m3dview.portHeight()

    @size.setter
    def size(self, wh):
        w1, h1 = self.size
        win_size = self.window.size()
        w2, h2 = win_size.width(), win_size.height()
        w_offset = w2 - w1
        h_offset = h2 - h1
        self.window.resize(wh[0] + w_offset, wh[1] + h_offset)

    @property
    def widget(self):
        '''Returns a QWidget object for the viewport.'''

        try:
            from shiboken import wrapInstance
        except ImportError:  # PySide2 compat
            from shiboken2 import wrapInstance
        w = wrapInstance(long(self._m3dview.widget()), QtWidgets.QWidget)
        return w

    @property
    def window(self):
        '''Returns a QWidget object for the viewports parent window'''

        return self.widget.window()

    @property
    def panel(self):
        '''Returns a panel name for the Viewport.'''
        panel = OpenMayaUI.MQtUtil.fullName(long(self._m3dview.widget()))
        return panel.split('|')[-2]

    @property
    def index(self):
        '''Returns the index of the viewport'''

        i = 0
        for i, view in Viewport.iter():
            if self == view:
                return i
            i += 1
        raise IndexError('Can not find index')

    @property
    def focus(self):
        '''Check if current Viewport is the active Viewport.'''
        return self == self.active()

    @focus.setter
    def focus(self, value):
        '''Set focus to Viewport instance.'''

        if not value:
            try:
                Viewport.get(1).focus = True
            except:
                pass
            return

        cmds.modelEditor(self.panel, edit=True, activeView=True)

    @property
    def camera(self):
        '''Get the short name of the active camera.'''

        camera = OpenMaya.MDagPath()
        self._m3dview.getCamera(camera)
        camera.pop()
        return camera.partialPathName()

    @camera.setter
    def camera(self, camera_path):
        '''Set the active camera for the Viewport.'''

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
        self._m3dview.refresh(False, False)

    @property
    def background(self):
        '''Get the background color of the Viewport'''

        color = self._m3dview.backgroundColor()
        return color[0], color[1], color[2]

    @background.setter
    def background(self, values):
        '''Set the background color of the Viewport.

        :param values: RGB value'''

        cmds.displayRGBColor('background', *values)

    def _highlight(self, msec=2000):
        '''Draws an identifier in a Viewport.'''

        highlight = Highlight(self)
        highlight.display(msec)

    @classmethod
    def identify(cls, delay=2000):
        '''Shows identifiers in all Viewports::

            Viewport.identify()

        :param delay: Length of time in ms to leave up identifier
        '''

        cls.highlight()

    @classmethod
    def highlight(cls, msec=2000):
        '''Draws QLabels indexing each Viewport. These indices can be used to
        with :method:`get` to return a corresponding Viewport object.'''

        for viewport in cls.iter():
            if viewport.widget.isVisible():
                viewport.highlight(msec)

    @staticmethod
    def count():
        '''The number of 3D Viewports.'''

        return OpenMayaUI.M3dView.numberOf3dViews()

    @classmethod
    def from_panel(cls, panel):
        m3dview = OpenMayaUI.M3dView()
        OpenMayaUI.M3dView.getM3dViewFromModelPanel(panel, m3dview)
        return cls(m3dview)

    @classmethod
    def get(cls, index):
        '''Get the Viewport at index.'''

        m3dview = OpenMayaUI.M3dView()
        OpenMayaUI.M3dView.get3dView(index, m3dview)
        return cls(m3dview)

    @classmethod
    def active(cls):
        '''Get the active Viewport.'''

        m3dview = OpenMayaUI.M3dView.active3dView()
        return cls(m3dview)

    @classmethod
    def iter(cls):
        '''Yield all Viewport objects.

        usage::

            for view in Viewport.iter():
                print(v.panel)
        '''

        for index in range(cls.count()):
            m3dview = OpenMayaUI.M3dView()
            OpenMayaUI.M3dView.get3dView(index, m3dview)
            yield cls(m3dview)


class Highlight(QtWidgets.QDialog):
    '''Outline a viewport panel and show the panel name.'''

    def __init__(self, view):
        super(Highlight, self).__init__(parent=get_maya_window())
        self.view = view
        self.widget = self.view.widget

        self.setWindowFlags(
            self.windowFlags()
            | QtCore.Qt.FramelessWindowHint
        )
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)
        wrect = self.widget.geometry()
        rect = QtCore.QRect(
            self.widget.mapToGlobal(
                wrect.topLeft(),
            ),
            wrect.size(),
        )
        self.setGeometry(
            rect
        )

    def display(self, msec):
        w = QtWidgets.QApplication.instance().activeWindow()
        self.show()
        w.raise_()
        QtCore.QTimer.singleShot(msec, self.accept)

    def paintEvent(self, event):

        painter = QtGui.QPainter(self)

        pen = QtGui.QPen(QtCore.Qt.red)
        pen.setWidth(8)
        font = QtGui.QFont()
        font.setPointSize(48)
        painter.setFont(font)
        painter.setPen(pen)
        painter.setBrush(QtCore.Qt.transparent)

        painter.drawRect(self.rect())
        painter.drawText(self.rect(), QtCore.Qt.AlignCenter, self.view.panel)
