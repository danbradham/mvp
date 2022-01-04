# -*- coding: utf-8 -*-

import os
import json
from functools import partial

from maya import cmds, mel

from .forms import PlayblastForm, NewPresetForm, DelPresetForm
from .. import hooks, resources
from ..renderlayers import enabled_render_layers
from ..viewport import playblast, Viewport
from ..utils import get_maya_window
from ..presets import *
from ..vendor.psforms import controls
from ..vendor.psforms.widgets import FormGroup, FormWidget, IconButton
from ..vendor.psforms.form import generate_form
from ..vendor.Qt import QtCore, QtGui, QtWidgets


MISSING = object()
DIALOG_STATE = None
SNAPSHOT_EXT_OPTIONS = {
    'png': '.png',
}
SCENE_STATE_NODE = 'time1'
SCENE_STATE_ATTR = 'mvp_dialog_state'
SCENE_STATE_PATH = SCENE_STATE_NODE + '.' + SCENE_STATE_ATTR
RESOLUTION_OPTIONS = ['Render Settings', '2048x2048', '1920x1080']


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


class IntegrationUI(object):
    '''Lazily generated UI Group for an Integration class.'''

    def __init__(self, integration, parent=None):
        self.integration = integration
        self.parent = parent
        self._group = None
        self._form = None

    def try_to_toggle(self, value):
        enabled = self.integration.set_enabled(value)

        if enabled and self.group.widget is not self.form:
            self.group.set_widget(self.form)

        self.group.set_enabled(enabled)

    @property
    def group(self):
        if not self._group:
            self._group = FormGroup(
                self.integration.name,
                FormWidget(self.integration.name),  # Stub widget
                parent=self.parent,
            )
            self._group.title.setIcon(QtGui.QIcon(self.integration.icon))
            self._group.toggled.connect(self.try_to_toggle)
            self.try_to_toggle(self.integration.enabled)
        return self._group

    @property
    def form(self):
        if not self._form:
            form = generate_form(
                name=self.integration.name,
                fields=self.integration.fields(),
                title=self.integration.name.title(),
                description=self.integration.description or 'No description',
                icon=self.integration.icon,
                header=False,
                columns=self.integration.columns,
                labels_on_top=False,
            )
            self._form = form.as_widget()

            # Attach controls to integration methods
            for control_name, control in self._form.controls.items():
                if isinstance(control.widget, QtWidgets.QTextEdit):
                    control.widget.setFixedHeight(48)
                method = getattr(
                    self.integration,
                    'on_' + control_name + '_changed',
                    None,
                )

                def slot_method(form, method, control):
                    def slot():
                        method(form, control.get_value())
                    return slot

                if method:
                    control.changed.connect(
                        slot_method(self._form, method, control)
                    )
        return self._form


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
    dialog.setStyleSheet(resources.get_style())
    dialog.show()


def del_preset_dialog(parent_dialog):

    def on_accept():
        name = parent_dialog.preset.get_value()
        del_preset(name)
        update_presets(parent_dialog)

    dialog = DelPresetForm.as_dialog(parent=parent_dialog)
    dialog.accepted.connect(on_accept)
    dialog.setStyleSheet(resources.get_style())
    dialog.show()


def update_presets(dialog, name=None):

    presets = ['Current Settings'] + sorted([n for n, s in get_presets()])
    dialog.preset.set_options(presets)
    if name:
        dialog.preset.set_value(name)


class PlayblastDialog(object):

    def __init__(self):
        self.form = PlayblastForm.as_dialog(
            frameless=False,
            parent=get_maya_window(),
        )
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

        # Update integration ui states
        for name, inst in self.integrations.items():
            if not inst.enabled:
                # Only store integration state for enabled integrations
                DIALOG_STATE.pop(name, None)

        set_scene_dialog_state(DIALOG_STATE)

    def restore_form_state(self):
        '''Restore form state from scene'''
        dialog_state = get_scene_dialog_state(DIALOG_STATE)
        if dialog_state:
            # Update integration ui states
            for name, inst in self.integrations.items():
                state = dialog_state.pop(name, None)
                if state:
                    inst.ui.try_to_toggle(True)
                    inst.ui.group.set_value(**state)
                else:
                    inst.ui.try_to_toggle(False)

            # Update base dialog state
            self.form.set_value(strict=False, **dialog_state)

            if dialog_state['path_option'] != 'Custom':
                self.update_path()

        else:
            # Defaults when no dialog state is present
            self.form.resolution.set_value((
                cmds.getAttr('defaultResolution.width'),
                cmds.getAttr('defaultResolution.height'),
            ))

    def setup_controls(self):
        '''Setup controls and options - Add additional widgets'''

        # Camera options
        cameras = cmds.ls(cameras=True)
        for c in ['frontShape', 'sideShape', 'topShape']:
            if c in cameras:
                cameras.remove(c)
        self.form.camera.set_options(cameras)

        # Viewport Presets
        self.form.preset.grid.setColumnStretch(1, 1)
        presets_menu_button = IconButton(
            icon=resources.get_path('dots-vertical.png'),
            tip='Resolution Presets.',
            name='resolution_menu',
        )
        presets_menu = QtWidgets.QMenu(parent=presets_menu_button)
        presets_menu.addAction('New Preset', partial(new_preset_dialog, self.form))
        presets_menu.addAction('Delete Preset', partial(del_preset_dialog, self.form))
        presets_menu_button.setMenu(presets_menu)
        self.form.preset.grid.addWidget(presets_menu_button, 1, 2)
        update_presets(self.form)

        # Extension options
        ext_option = controls.StringOptionControl(
            'Ext Option',
            labeled=False,
        )
        ext_option.set_options(list(hooks.extension.keys()))
        self.form.controls['ext_option'] = ext_option
        self.form.ext_option = ext_option
        self.form.filename.grid.addWidget(ext_option.widget, 1, 2)

        # Add path option control
        path_options = ['Custom']
        path_options.extend(hooks.pathgen.keys())
        path_option = controls.StringOptionControl(
            'Path Option',
            labeled=False,
        )
        path_option.set_options(path_options)
        self.form.controls['path_option'] = path_option
        self.form.path_option = path_option
        self.form.filename.grid.addWidget(path_option.widget, 1, 3)

        # Identify button
        identify_button = QtWidgets.QPushButton('highlight viewport')
        identify_button.clicked.connect(self.on_identify)
        self.form.button_layout.insertWidget(0, identify_button)

        # Resolution Options
        res_menu_button = IconButton(
            icon=resources.get_path('dots-vertical.png'),
            tip='Resolution Presets.',
            name='resolution_menu',
        )
        res_menu = QtWidgets.QMenu(parent=res_menu_button)
        for option in RESOLUTION_OPTIONS:
            res_menu.addAction(
                option,
                partial(self.apply_resolution_preset, option)
            )
        res_menu_button.setMenu(res_menu)
        self.form.resolution.grid.addWidget(res_menu_button, 1, 2)

        half_res = controls.ToggleControl(
            name='Half Res',
            icon=resources.get_path('half.png'),
            tip='Render half resolution.',
            labeled=False,
        )
        self.form.controls['half_res'] = half_res
        self.form.half_res = half_res
        self.form.resolution.grid.addWidget(half_res.widget, 1, 3)

        # Add postrender hook checkboxes
        self.form.postrender.after_toggled.connect(self.auto_resize)
        self.form.postrender.toggle()
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
        self.integrations = {}
        for name, integration in hooks.integration.items():
            inst = integration()
            inst.ui = IntegrationUI(inst, self.form)
            inst.ui.group.after_toggled.connect(self.auto_resize)
            inst.form = inst.ui.group
            self.form.add_form(
                name,
                inst.ui.group,
            )
            self.integrations[name] = inst

    def auto_resize(self):
        QtCore.QTimer.singleShot(20, self.form.adjustSize)

    def setup_connections(self):
        '''Connect form controls to callbacks'''

        self.form.capture_mode.changed.connect(self.on_capture_mode_changed)
        self.form.ext_option.changed.connect(self.on_ext_changed)
        self.form.path_option.changed.connect(self.update_path)
        self.form.filename.changed.connect(self.on_filename_changed)
        self.form.accepted.connect(self.on_accept)

    def apply_resolution_preset(self, preset):
        if preset == 'Render Settings':
            self.form.resolution.set_value((
                cmds.getAttr('defaultResolution.width'),
                cmds.getAttr('defaultResolution.height'),
            ))
        else:
            self.form.resolution.set_value([int(num) for num in preset.split('x')])

    def apply_stylesheet(self):
        '''Apply mvp stylesheet'''

        self.form.setStyleSheet(resources.get_style())

    def on_ext_changed(self):
        '''Called when the extension changes.'''
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
        for integration in self.integrations.values():
            if integration.enabled:
                integration.on_filename_changed(self.form, path)

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

        for ext in hooks.extension.values():
            if name.endswith(ext.ext):
                self.form.ext_option.set_value(ext.name)
                return

    def on_identify(self):
        '''Highlight the active viewport.'''

        Viewport.active().identify()

    def on_accept(self):
        '''When form is accepted - parse options and capture'''

        self.store_form_state()
        data = self.form.get_value()

        # Prepare to render
        if data['preset'] == 'Current Settings':
            state = Viewport.active().get_state()
        else:
            state = get_preset(data['preset'])
            state.pop('camera')

        output_dir = os.path.dirname(data['filename'])
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        renders = []
        if data['render_layers'] == 'current':
            renders.append(self._render(state, data))
        else:
            with enabled_render_layers() as layers:
                for layer in layers:
                    # Copy data and add layer name to filename
                    render_data = data.copy()
                    base, ext = render_data['filename'].rsplit('.', 1)
                    layer_name = '{}_{}.{}'.format(base, layer.name(), ext)
                    render_data['filename'] = layer_name

                    layer.switchToLayer()
                    renders.append(self._render(state, render_data))

        # Finalize
        for name, integration in self.integrations.items():
            if integration.enabled:
                integration.finalize(integration.form, renders)

    def _render(self, state, data):

        # Execute integration before_playblast
        for name, integration in self.integrations.items():
            if integration.enabled:
                integration.before_playblast(integration.form, data)

        # Prepare resolution
        if data.pop('half_res', False):
            data['resolution'] = (
                round_to_even(data['resolution'][0] * 0.5),
                round_to_even(data['resolution'][1] * 0.5),
            )

        if data['capture_mode'] == 'snapshot':
            # Render snapshot
            data['start_frame'] = cmds.currentTime(q=True)
            data['end_frame'] = data['start_frame']
            out_file = playblast(
                camera=data['camera'],
                state=state,
                format='image',
                compression='png',
                completeFilename=data['filename'],
                frame=[data['start_frame']],
                width=data['resolution'][0],
                height=data['resolution'][1],
            )
        else:
            # Call extension handler
            extension = hooks.extension.get(data['ext_option'])
            framerange = get_framerange()
            data['start_frame'] = framerange[0]
            data['end_frame'] = framerange[1]
            data['fps'] = get_fps()
            data['sound'] = get_sound_track()
            out_file = extension.handler(
                data=dict(
                    state=state,
                    camera=data['camera'],
                    filename=data['filename'],
                    width=data['resolution'][0],
                    height=data['resolution'][1],
                    sound=data['sound'],
                    fps=data['fps'],
                    start_frame=data['start_frame'],
                    end_frame=data['end_frame'],
                ),
                options=extension.options or {},
            )

        # Execute postrender callbacks
        if 'postrender' in data:
            for name, enabled in data['postrender'].items():
                if enabled:
                    postrender = hooks.postrender.get(name)
                    postrender.handler(data['filename'])

        # Update filename from playblast command
        data['filename'] = out_file

        # Execute integration after_playblast
        for name, integration in self.integrations.items():
            if integration.enabled:
                integration.after_playblast(integration.form, data)

        return data


def round_to_even(value):
    return value if value % 2 == 0 else value + 1


def show():
    '''Main playblast form.'''

    PlayblastDialog._instance = PlayblastDialog()
    PlayblastDialog._instance.show()
    return PlayblastDialog._instance
