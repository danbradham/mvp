# -*- coding: utf-8 -*-

from Qt import QtGui, QtCore, QtWidgets
from psforms import controls, Form
from psforms.form import generate_form
from maya import cmds, mel
import os
import json
from functools import partial
from .viewport import playblast, Viewport
from .forms import PlayblastForm, NewPresetForm, DelPresetForm
from .utils import get_maya_window, viewport_state
from .presets import *
from . import hooks


MISSING = object()
DIALOG_STATE = None
SNAPSHOT_EXT_OPTIONS = {
    'png': '.png',
}
SCENE_STATE_NODE = 'time1'
SCENE_STATE_ATTR = 'mvp_dialog_state'
SCENE_STATE_PATH = SCENE_STATE_NODE + '.' + SCENE_STATE_ATTR


def get_sound_track():
    '''Get the current sound track'''

    playback_slider = mel.eval('$tmpVar=$gPlayBackSlider')
    return cmds.timeControl(playback_slider, query=True, sound=True)


def get_fps():
    '''Get the scene fps'''

    # Returns a unit string like game or 5fps
    unit = cmds.currentUnit(query=True, time=True)

    # If unit is not in the following dict - we must have a string like 5fps
    fps = {
        'game': '15fps',
        'film': '24fps',
        'pal': '25fps',
        'ntsc': '30fps',
        'show': '48fps',
        'palf': '50fps',
        'ntscf': '60fps',
    }.get(unit, unit)

    # Convert to a floating point value
    return float(fps.rstrip('fps'))


def get_framerange():
    '''Get the scene framerange'''

    return(
        cmds.playbackOptions(query=True, minTime=True),
        cmds.playbackOptions(query=True, maxTime=True),
    )


def integration_to_group(integration, parent=None):
    '''Create a group for the integration'''

    form = generate_form(
        integration.name,
        integration.fields(),
        title=integration.name.title(),
        description=integration.description or 'No description',
        icon=integration.icon,
        hearer=False,
        columns=integration.columns
    )
    group = form.as_group(parent=parent)
    group.title.setIcon(QtGui.QIcon(integration.icon))
    group.integration = integration
    group.set_enabled(integration.enabled_by_default)

    def try_to_toggle(value):
        enabled = integration.set_enabled(value)
        group.set_enabled(enabled)

    group.toggled.connect(try_to_toggle)

    return group


def get_scene_dialog_state(default=MISSING):
    '''Retrieve dialog state from a maya scene'''

    if cmds.objExists(SCENE_STATE_PATH):
        encoded_state = cmds.getAttr(SCENE_STATE_PATH)
        if encoded_state:
            return json.loads(encoded_state)

    if default is not MISSING:
        return default


def set_scene_dialog_state(state):
    '''Store dialog state in a maya scene'''

    if not cmds.objExists(SCENE_STATE_PATH):
        cmds.addAttr(SCENE_STATE_NODE, ln=SCENE_STATE_ATTR, dataType='string')

    encoded_state = json.dumps(state)
    cmds.setAttr(SCENE_STATE_PATH, encoded_state, type='string')


def stylesheet():
    path = os.path.join(os.path.dirname(__file__), 'style.css')
    with open(path, 'r') as f:
        style = f.read()
    return style


def new_preset_dialog(parent_dialog):

    dialog = NewPresetForm.as_dialog(parent=parent_dialog)
    dialog.panel.set_options([v.panel for v in Viewport.iter()])

    def on_accept():
        name = dialog.name.get_value()
        panel = dialog.panel.get_value()
        v = Viewport.from_panel(panel)
        state = v.get_state()
        new_preset(name, state)
        update_presets(parent_dialog, name)

    def identify_clicked():
        panel = dialog.panel.get_value()
        v = Viewport.from_panel(panel)
        v.identify()

    identify = QtWidgets.QPushButton('identify')
    identify.clicked.connect(identify_clicked)

    dialog.panel.grid.addWidget(identify, 1, 2)
    dialog.accepted.connect(on_accept)
    dialog.setStyleSheet(stylesheet())
    dialog.show()


def del_preset_dialog(parent_dialog):

    def on_accept():
        name = parent_dialog.preset.get_value()
        del_preset(name)
        update_presets(parent_dialog)

    dialog = DelPresetForm.as_dialog(parent=parent_dialog)
    dialog.accepted.connect(on_accept)
    dialog.setStyleSheet(stylesheet())
    dialog.show()


def update_presets(dialog, name=None):

    presets = ['Current Settings'] + sorted([n for n, s in get_presets()])
    dialog.preset.set_options(presets)
    if name:
        dialog.preset.set_value(name)


class PlayblastDialog(object):

    def __init__(self):
        self.form = PlayblastForm.as_dialog(parent=get_maya_window())
        self.setup_controls()
        self.setup_connections()
        self.restore_form_state()
        self.apply_stylesheet()

    def show(self):
        self.form.show()

    def store_form_state(self):
        '''Store form state in scene'''
        global DIALOG_STATE
        DIALOG_STATE = self.form.get_value()
        set_scene_dialog_state(DIALOG_STATE)

    def restore_form_state(self):
        '''Restore form state from scene'''
        dialog_state = get_scene_dialog_state(DIALOG_STATE)
        if dialog_state:
            self.form.set_value(strict=False, **dialog_state)
            if dialog_state['path_option'] != 'Custom':
                self.update_path()

    def setup_controls(self):
        '''Setup controls and options - Add additional widgets'''

        # Camera options
        cameras = cmds.ls(cameras=True)
        for c in ['frontShape', 'sideShape', 'topShape']:
            cameras.remove(c)
        self.form.camera.set_options(cameras)

        # Viewport Presets
        new_button = QtWidgets.QPushButton('New')
        new_button.clicked.connect(partial(new_preset_dialog, self.form))
        del_button = QtWidgets.QPushButton('Delete')
        del_button.clicked.connect(partial(del_preset_dialog, self.form))
        self.form.preset.grid.addWidget(new_button, 1, 2)
        self.form.preset.grid.addWidget(del_button, 1, 3)
        update_presets(self.form)

        # Extension options
        ext_option = controls.StringOptionControl(
            'Ext Option',
            labeled=False
        )
        ext_option.set_options(list(hooks.extension.keys()))
        self.form.controls['ext_option'] = ext_option
        self.form.ext_option = ext_option
        self.form.filename.grid.addWidget(ext_option.widget, 1, 2)

        # Add capture mode label
        self.form.capture_mode.label.hide()
        self.form.capture_mode.grid.addWidget(
            QtWidgets.QLabel('Capture Mode'), 1, 0
        )

        # Add path option control
        path_options = ['Custom']
        path_options.extend(hooks.pathgen.keys())
        path_option = controls.StringOptionControl(
            'Path Option',
            labeled=False
        )
        path_option.set_options(path_options)
        self.form.controls['path_option'] = path_option
        self.form.path_option = path_option
        self.form.filename.grid.addWidget(path_option.widget, 1, 3)

        # Identify button
        identify_button = QtWidgets.QPushButton('Identify')
        self.form.button_layout.addWidget(identify_button)
        identify_button.clicked.connect(self.on_identify)

        # Add postrender hook checkboxes
        for postrender in hooks.postrender.values():
            self.form.postrender.add_control(
                postrender.name,
                controls.BoolControl(
                    postrender.name,
                    label_on_top=False,
                    default=postrender.default,
                )
            )

        # Add integration groups
        self.form.integrations = {}
        for name, integration in hooks.integration.items():
            inst = integration()
            group = integration_to_group(inst)
            self.form.add_form(name, group)
            self.form.integrations[name] = inst
            for control_name, control in group.controls.items():
                method = getattr(inst, 'on_' + control_name + '_changed', None)
                def slot_method(form, method, control):
                    def slot():
                        method(form, control.get_value())
                    return slot
                if method:
                    control.changed.connect(
                        slot_method(dialog, method, control)
                    )

    def setup_connections(self):
        '''Connect form controls to callbacks'''

        self.form.capture_mode.changed.connect(self.on_capture_mode_changed)
        self.form.ext_option.changed.connect(self.on_ext_changed)
        self.form.path_option.changed.connect(self.update_path)
        self.form.filename.changed.connect(self.on_filename_changed)
        self.form.accepted.connect(self.on_accept)

    def apply_stylesheet(self):
        '''Apply mvp stylesheet'''

        self.form.setStyleSheet(stylesheet())

    def on_ext_changed(self):
        '''Called when the extension changes.'''
        ext_opt = self.form.ext_option.get_value()
        extension = hooks.extension.get(ext_opt)
        self.update_path()

    def update_path(self):
        '''Update the file path based on pathgen, ext, and capture mode'''

        path_opt = self.form.path_option.get_value()
        ext_opt = self.form.ext_option.get_value()
        capture_mode = self.form.capture_mode.get_value()

        path_gen = hooks.pathgen.get(path_opt, None)

        if not path_gen:
            return

        # Compute path using PathGenerator hook
        path = path_gen.handler()

        if capture_mode == 'snapshot':

            # Snapshots are just pngs
            ext = SNAPSHOT_EXT_OPTIONS.get(ext_opt, '.png')

        else:

            # Get ext from Extension hook
            extension = hooks.extension.get(ext_opt, None)
            if extension:
                ext = extension.ext
            else:
                ext = '.mov'

            # Put png sequences in a subdirectory
            if ext == '.png':
                scene_path = cmds.file(q=True, shn=True, sn=True)
                scene = os.path.splitext(scene_path)[0]
                path = os.path.join(path, scene).replace('\\', '/')

        # Add extension to path and set filename
        path += ext
        self.form.filename.set_value(path)

        # Notify integrations of filename change
        for integration in self.form.integrations.values():
            if integration.enabled:
                integration.on_filename_changed(self.form, path)

    def on_accept(self):
        '''When form is accepted - parse options and capture'''

        self.store_form_state()
        data = self.form.get_value()

        # Execute integration before_playblast
        for name, integration in self.form.integrations.items():
            if integration.enabled:
                integration.before_playblast(data)

        # Get viewport state
        if data['preset'] == 'Current Settings':
            state = Viewport.active().get_state()
        else:
            state = get_preset(data['preset'])
            state.pop('camera')

        output_dir = os.path.dirname(data['filename'])
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        if data['capture_mode'] == 'snapshot':
            # Render snapshot
            playblast(
                camera=data['camera'],
                state=state,
                format='image',
                compression='png',
                completeFilename=data['filename'],
                frame=[cmds.currentTime(q=True)],
                width=data['resolution'][0],
                height=data['resolution'][1],
            )
        else:
            # Call extension handler
            extension = hooks.extension.get(data['ext_option'])
            options = extension.options or {}
            framerange = get_framerange()
            extension.handler(
                data=dict(
                    state=state,
                    camera=data['camera'],
                    filename=data['filename'],
                    width=data['resolution'][0],
                    height=data['resolution'][1],
                    sound=get_sound_track(),
                    fps=get_fps(),
                    start_frame=framerange[0],
                    end_frame=framerange[1],
                ),
                options=extension.options,
            )

        # postrender callbacks
        if 'postrender' in data:
            for name, enabled in data['postrender'].items():
                if enabled:
                    postrender = hooks.postrender.get(name)
                    postrender.handler(data['filename'])

        # integrations after_playblast
        for name, integration in self.form.integrations.items():
            if integration.enabled:
                integration.after_playblast(data)

    def on_capture_mode_changed(self):
        '''Update path when capture_mode changes.'''

        mode = self.form.capture_mode.get_value()
        if mode == 'sequence':
            self.form.ext_option.set_options(list(hooks.extension.keys()))
        else:
            self.form.ext_option.set_options(list(SNAPSHOT_EXT_OPTIONS))

        self.update_path()

    def on_filename_changed(self):
        '''Update contol values when filename changes.'''

        self.form.path_option.set_value('Custom')

        name = self.form.filename.get_value()
        capture_mode = self.form.capture_mode.get_value()

        for ext in hooks.extension.values():
            if name.endswith(ext.ext):
                self.form.ext_option.set_value(ext.name)
                return

    def on_identify(self):
        '''Highlight the active viewport.'''

        Viewport.active().identify()


def show():
    '''Main playblast form.'''

    PlayblastDialog._instance = PlayblastDialog()
    PlayblastDialog._instance.show()
