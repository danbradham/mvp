# -*- coding: utf-8 -*-
'''
=======================
MVP - Maya Viewport API
=======================

I really needed this...
'''

import os
import shiboken
from PySide import QtGui, QtCore
from .renderglobals import RenderGlobals
from .utils import wait
import maya.cmds as cmds
import maya.OpenMayaUI as OpenMayaUI
import maya.OpenMaya as OpenMaya
import maya.utils as utils



EDITOR_PROPERTIES = [
    'activeComponentsXray', 'activeOnly', 'backfaceCulling', 'bufferMode',
    'bumpResolution', 'camera', 'cameras', 'clipGhosts', 'colorResolution',
    'controlVertices', 'cullingOverride', 'deformers', 'dimensions',
    'displayAppearance', 'displayLights', 'displayTextures',
    'dynamicConstraints', 'dynamics', 'fluids', 'fogColor', 'fogDensity',
    'fogEnd', 'fogMode', 'fogSource', 'fogStart', 'fogging', 'follicles',
    'greasePencils', 'grid', 'hairSystems', 'handles', 'headsUpDisplay',
    'hulls', 'ignorePanZoom', 'ikHandles', 'imagePlane',
    'interactiveBackFaceCull', 'interactiveDisableShadows', 'isFiltered',
    'jointXray', 'joints', 'lights', 'lineWidth', 'locators',
    'lowQualityLighting', 'manipulators', 'maxConstantTransparency',
    'maximumNumHardwareLights', 'motionTrails', 'nCloths', 'nParticles',
    'nRigids', 'nurbsCurves', 'nurbsSurfaces', 'objectFilterShowInHUD',
    'occlusionCulling', 'particleInstancers', 'pivots', 'planes',
    'pluginShapes', 'polymeshes', 'rendererName', 'selectionHiliteDisplay',
    'shadingModel', 'shadows', 'smallObjectCulling',
    'smallObjectThreshold', 'smoothWireframe', 'sortTransparent',
    'strokes', 'subdivSurfaces', 'textureAnisotropic',
    'textureCompression', 'textureDisplay', 'textureHilight',
    'textureMaxSize', 'textureSampling', 'textures', 'transpInShadows',
    'transparencyAlgorithm', 'twoSidedLighting', 'useBaseRenderer',
    'useDefaultMaterial', 'useInteractiveMode', 'useReducedRenderer',
    'viewSelected', 'wireframeOnShaded', 'xray', 'depthOfField',
    'gpuCacheDisplayFilter'
]


def deferred_close(view):
    panel = view.panel
    wait(0.1)
    utils.executeDeferred(cmds.deleteUI, panel, panel=True)


def playblast(filename, camera, state=None,
              width=960, height=540, format='qt', compression='H.264'):

    active = Viewport.active()
    pre_state = active.get_state()

    # Setup viewport
    v = Viewport.new()
    v.size = width, height
    v.center()
    wait(0.1)
    if state:
        v.set_state(state)
    v.camera = camera
    v.playblast(
        filename,
        width=width,
        height=height,
        format=format,
        compression=compression)

    # wait(1)
    # Restore previous state
    active.set_state(pre_state)
    v.close()


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

    for p in EDITOR_PROPERTIES: # Initialize all editor properties
        locals()[p] = EditorProperty(p)

    _identifier_labels = []

    def __init__(self, m3dview):
        self._m3dview = m3dview
        self.identify = self._identify

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

        return EDITOR_PROPERTIES

    def get_state(self):
        '''Get a state dictionary of all modelEditor properties.'''

        active_state = {}
        for ep in EDITOR_PROPERTIES:
            active_state[ep] = getattr(self, ep)
        active_state['RenderGlobals'] = RenderGlobals.get_state()

        return active_state

    def set_state(self, state):
        '''Sets a dictionary of properties all at once.

        :param state: Dictionary including property, value pairs'''

        cstate = state.copy()

        renderglobals_state = cstate.pop('RenderGlobals', None)
        if renderglobals_state:
            RenderGlobals.set_state(renderglobals_state)

        for k, v in cstate.iteritems():
            setattr(self, k, v)

    def playblast(self, filename, **kwargs):
        '''Playblasting with reasonable default arguments. Automatically sets
        this viewport to the active view, ensuring that we playblast the
        correct view.

        :param filename: Absolute path to output file
        :param kwargs: Same kwargs as :func:`maya.cmds.playblast`'''

        playblast_kwargs = {
            'filename': filename,
            'offScreen': False,
            'percent': 100,
            'quality': 100,
            'viewer': True,
            'width': 960,
            'height': 540,
            'framePadding': 4,
            'format': 'qt',
            'compression': 'H.264',
            'forceOverwrite': True,
        }
        playblast_kwargs.update(kwargs)

        if not self.focus:
            self.focus = True
        cmds.playblast(**playblast_kwargs)

    @property
    def screen_geometry(self):
        qapp = QtGui.QApplication.instance()
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

        w = shiboken.wrapInstance(long(self._m3dview.widget()), QtGui.QWidget)
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

        for i, view in Viewport.enumerate():
            if self == view:
                return i
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
    def depthOfField(self):
        '''Get active camera depthOfField attribute'''

        return cmds.getAttr(self.camera + '.depthOfField')

    @depthOfField.setter
    def depthOfField(self, value):
        '''Set active camera depthOfField attribute'''

        cmds.setAttr(self.camera + '.depthOfField', value)

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

    def _draw_label(self, **kwargs):
        '''Draw text in viewport and return a QLabel. Used for identifying
        viewports.

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
        weight = {
            'light': QtGui.QFont.Light,
            'normal': QtGui.QFont.Normal,
            'demibold': QtGui.QFont.DemiBold,
            'bold': QtGui.QFont.Bold,
            'black': QtGui.QFont.Black,
        }[kwargs.get('weight', 'bold')]
        bgc = kwargs.get('background', self.background)
        bgc = bgc[0] * 255, bgc[1] * 255, bgc[2] * 255
        background = QtGui.QColor(*bgc)
        size = kwargs.get('size', 24)

        label = QtGui.QLabel(text, parent=self.widget)
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
        return label

    def _identify(self, delay=2000):
        '''Shows identifier only in this Viewport. Replaces classmethod
        identify on __init__ of a Viewport instance::

            v = Viewport.active()
            v.identify()

        :param delay: Length of time in ms to leave up identifier
        '''

        self.draw_identifier(self.panel)
        QtCore.QTimer.singleShot(delay, self.clear_identifiers)

    @classmethod
    def identify(cls, delay=2000):
        '''Shows identifiers in all Viewports::

            Viewport.identify()

        :param delay: Length of time in ms to leave up identifier
        '''

        cls.show_identifiers()
        QtCore.QTimer.singleShot(delay, cls.clear_identifiers)

    @classmethod
    def show_identifiers(cls):
        '''Draws QLabels indexing each Viewport. These indices can be used to
        with :method:`get` to return a corresponding Viewport object.'''

        for index, viewport in cls.enumerate():
            viewport.draw_identifier(viewport.panel)

    @classmethod
    def clear_identifiers(cls):
        '''Remove all the QLabels drawn by show_identifiers.'''
        while True:
            try:
                label = cls._identifier_labels.pop()
                label.setParent(None)
                del(label)
            except IndexError:
                break

    def draw_identifier(self, text):
        '''Draws an identifier in a Viewport.'''

        label = self._draw_label(
            text=text,
            font='Helvetica',
            size=60,
            position=(0,0),
            weight='bold',
        )
        self._identifier_labels.append(label)

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
                print v.panel
        '''

        for index in xrange(cls.count()):
            m3dview = OpenMayaUI.M3dView()
            OpenMayaUI.M3dView.get3dView(index, m3dview)
            yield cls(m3dview)
