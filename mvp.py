# -*- coding: utf-8 -*-
'''
=======================
MVP - Maya Viewport API
=======================

I really needed this...
'''

import os
from functools import partial
import shiboken
from PySide import QtGui, QtCore
import maya.cmds as cmds
import maya.OpenMayaUI as OpenMayaUI
import maya.OpenMaya as OpenMaya

__title__ = 'mvp'
__author__ = 'Dan Bradham'
__email__ = 'danielbradham@gmail.com'
__url__ = 'http://github.com/danbradham/mvp.git'
__version__ = '0.1.0'
__license__ = 'MIT'
__description__ = 'Manipulate Maya 3D Viewports.'


class Viewport(object):
    '''A convenient api for manipulating Maya 3D Viewports. While you can
    manually construct a Viewport from an OpenMayaUI.M3dView instance, it is
    much easier to use the convenience methods Viewport.enumerate,
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


    :param m3dview: OpenMayaUI.M3dView instance.
    '''

    _identifier_labels = []
    _editor_properties = [
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
    _unique_properties = ['depthOfField']
    _plugin_objects = ['gpuCacheDisplayFilter']

    def __init__(self, m3dview):
        self._m3dview = m3dview
        self.identify = self._identify

    def __eq__(self, other):
        return self.panel == other.panel

    def __getattr__(self, name):

        if name in self._unique_properties:
            return getattr(self, name)

        if name in self._editor_properties:
            return self._get_property(name)

        super(Viewport, self).__getattr__(name)

    def __setattr__(self, name, value):

        if name in self._unique_properties:
            return setattr(self, name, value)

        if name in self._editor_properties:
            return self._set_property(name, value)

        super(Viewport, self).__setattr__(name, value)

    def _get_property(self, name):
        '''Gets a model editor property.'''

        try:
            val = cmds.modelEditor(self.panel, **{'query': True, name: True})
        except TypeError:
            val = cmds.modelEditor(self.panel, **{'query': True, 'qpo': name})

        return val

    def _set_property(self, name, value):
        '''Sets a model editor property.'''

        try:
            cmds.modelEditor(self.panel, **{'edit': True, name: value})
        except TypeError:
            cmds.modelEditor(self.panel, **{'edit': True, 'po': [name, value]})

    @property
    def properties(self):
        '''A list including all editor property names.'''

        return self._editor_properties

    def get_state(self):
        '''Get a state dictionary of all modelEditor properties.'''

        active_state = {}
        for ep in self._editor_properties:

            if ep in self._unique_properties:
                active_state[ep] = getattr(self, ep)
                continue

            if ep == 'smallObjectThreshold':
                # We need to add an exception here because this query returns
                # a list but when setting the property we have to use a string
                # Hooray for weird maya behavior
                active_state[ep] = self._get_property(ep)[0]
                continue

            active_state[ep] = self._get_property(ep)

        active_state['RenderGlobals'] = RenderGlobals.get_state()

        return active_state

    def set_state(self, state):
        '''Sets a dictionary of properties all at once.

        :param state: Dictionary including property, value pairs'''

        cstate = dict(state)

        for up in self._unique_properties:
            try:
                setattr(self, up, cstate.pop(up))
            except KeyError:
                pass

        rg_state = cstate.pop('RenderGlobals')
        RenderGlobals.set_state(rg_state)

        for k, v in cstate.iteritems():
            try:
                self._set_property(k, v)
            except TypeError:
                pass

    @property
    def widget(self):
        '''Returns a QWidget object for the viewport.'''

        w = shiboken.wrapInstance(long(self._m3dview.widget()), QtGui.QWidget)
        return w

    @property
    def panel(self):
        '''Returns a panel name for the Viewport.'''

        panel = OpenMayaUI.MQtUtil.fullName(long(self._m3dview.widget()))
        for p in reversed(panel.split('|')):
            if p:
                return p

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

    def copy(self):
        '''Tear off a copy of the viewport.

        :returns: A new torn off copy of Viewport'''

        panel = cmds.modelPanel(tearOffCopy=self.panel)
        view = self.from_panel(panel)
        view.focus = True
        return view

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

        c = self.camera
        return cmds.getAttr(c + '.depthOfField')

    @depthOfField.setter
    def depthOfField(self, value):
        '''Set active camera depthOfField attribute'''

        c = self.camera
        cmds.setAttr(c + '.depthOfField', value)

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

    def _identify(self, time=2000):
        '''Shows identifier only in this Viewport. Replaces classmethod
        identify on __init__ of a Viewport instance::

            v = Viewport.active()
            v.identify()

        :param time: Length of time in ms to leave up identifier
        '''

        self.draw_identifier(self.index)
        QtCore.QTimer.singleShot(time, self.clear_identifiers)

    @classmethod
    def identify(cls, time=2000):
        '''Shows identifiers in all Viewports::

            Viewport.identify()

        :param time: Length of time in ms to leave up identifier
        '''

        cls.show_identifiers()
        QtCore.QTimer.singleShot(time, cls.clear_identifiers)

    @classmethod
    def show_identifiers(cls):
        '''Draws QLabels indexing each Viewport. These indices can be used to
        with :method:`get` to return a corresponding Viewport object.

        :param time: Lenght of time to leave up identifying labels.'''

        for index, viewport in cls.enumerate():
            viewport.draw_identifier(index)

    def draw_identifier(self, index):
        '''Draws an identifier in a Viewport.'''

        label = self._draw_label(
            text=str(index),
            font='Helvetica',
            size=128,
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
    def clear_identifiers(cls):
        '''Remove all the QLabels drawn by show_identifiers.'''
        while True:
            try:
                label = cls._identifier_labels.pop()
                label.setParent(None)
                del(label)
            except IndexError:
                break

    @classmethod
    def enumerate(cls, visible=True):
        '''Enumerate all Viewports.
        :returns: Tuple including index and Viewport objects.'''

        for index in xrange(cls.count()):
            m3dview = OpenMayaUI.M3dView()
            OpenMayaUI.M3dView.get3dView(index, m3dview)
            if not visible or (visible and m3dview.isVisible()):
                yield index, cls(m3dview)


class RenderGlobals(object):
    '''Get and set hardwareRenderingGlobals.'''

    _relevant_attributes = [
        'multiSampleEnable', 'multiSampleCount', 'colorBakeResolution',
        'bumpBakeResolution', 'motionBlurEnable', 'motionBlurSampleCount',
        'ssaoEnable', 'ssaoAmount', 'ssaoRadius', 'ssaoFilterRadius'
    ]

    @classmethod
    def get(cls, name):
        return cmds.getAttr('hardwareRenderingGlobals.' + name)

    @classmethod
    def set(cls, name, value):
        cmds.setAttr('hardwareRenderingGlobals.' + name, value)

    @classmethod
    def get_state(cls):
        '''Collect hardwareRenderingGlobals attributes that effect
        Viewports.'''

        active_state = {}
        for p in cls._relevant_attributes:
            active_state[p] = cls.get(p)

        return active_state

    @classmethod
    def set_state(cls, state):
        '''Set a bunch of hardwareRenderingGlobals all at once.

        :param state: Dict containing attr, value pairs'''

        for k, v in state.iteritems():
            cls.set(k, v)
