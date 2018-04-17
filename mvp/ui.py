from Qt import QtGui, QtCore, QtWidgets
from psforms import controls, Form
import maya.cmds as cmds
import os
from functools import partial
from .viewport import playblast, Viewport
from .forms import PlayblastForm, NewPresetForm, DelPresetForm
from .utils import get_maya_window
from .presets import *
from .hooks import *


DIALOG_STATE = None
EXT_OPTIONS = {
    'h.264': '.mov',
    'png': '.png',
    'Custom': ''
}


def stylesheet():
    path = os.path.join(os.path.dirname(__file__), 'style.css')
    with open(path, 'r') as f:
        style = f.read()
    return style


def new_dialog(parent_dialog):

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


def del_dialog(parent_dialog):

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


def show():

    dialog = PlayblastForm.as_dialog(parent=get_maya_window())
    cameras = cmds.ls(cameras=True)
    for c in ['frontShape', 'sideShape', 'topShape']:
        cameras.remove(c)
    dialog.camera.set_options(cameras)

    new_button = QtWidgets.QPushButton('New')
    new_button.clicked.connect(partial(new_dialog, dialog))
    del_button = QtWidgets.QPushButton('Delete')
    del_button.clicked.connect(partial(del_dialog, dialog))
    dialog.preset.grid.addWidget(new_button, 1, 2)
    dialog.preset.grid.addWidget(del_button, 1, 3)
    update_presets(dialog)

    ext_option = controls.StringOptionControl('Ext Option', labeled=False)
    ext_option.set_options(list(EXT_OPTIONS.keys()))
    dialog.controls['ext_option'] = ext_option
    dialog.filename.grid.addWidget(ext_option.widget, 1, 2)

    # Add path generator functions
    path_options = ['Custom']
    path_options.extend(PATHGEN_REGISTRY.keys())
    path_option = controls.StringOptionControl('Path Option', labeled=False)
    path_option.set_options(path_options)

    def capture_mode_changed():
        mode = dialog.capture_mode.get_value()
        if mode == 'sequence':
            ext_option.set_options(list(EXT_OPTIONS.keys()))
        else:
            ext_option.set_options(list(EXT_OPTIONS.keys())[1:])
        get_path()

    dialog.capture_mode.changed.connect(capture_mode_changed)
    dialog.capture_mode.label.hide()
    dialog.capture_mode.grid.addWidget(QtWidgets.QLabel('Capture Mode'), 1, 0)

    dialog.controls['path_option'] = path_option
    dialog.filename.grid.addWidget(path_option.widget, 1, 3)

    def get_path():
        path_fn = PATHGEN_REGISTRY.get(path_option.get_value(), None)

        if not path_fn:
            return

        ext = EXT_OPTIONS[ext_option.get_value()]
        if dialog.capture_mode.get_value() == 'sequence' and ext == '.png':
            scene = os.path.splitext(cmds.file(q=True, shn=True, sn=True))[0]
            path = os.path.join(path_fn(), scene)
        else:
            path = path_fn()

        path += ext
        dialog.filename.set_value(path)

    ext_option.changed.connect(get_path)
    path_option.changed.connect(get_path)

    def on_filename_change():
        path_option.set_value('Custom')
        name = dialog.filename.get_value()

        if (dialog.capture_mode.get_value() == 'sequence' and
            name.endswith('.mov')):
            ext_option.set_value('h.264')
        elif name.endswith('.png'):
            ext_option.set_value('png')
        else:
            ext_option.set_value('Custom')

    dialog.filename.changed.connect(on_filename_change)

    def on_accept():
        data = dialog.get_value()

        if data['preset'] == 'Current Settings':
            state = Viewport.active().get_state()
        else:
            state = get_preset(data['preset'])

        path, ext = os.path.splitext(data['filename'])
        is_snapshot = data['capture_mode'] == 'snapshot'
        is_png_sequence = False

        if is_snapshot:
            ext = '.png'
            path += ext
            output_path = path
        else:
            if ext in ['.png', '.tif', '.iff', '.jpeg', '.jpg']:
                ext = '.png'
                output_path = path
                path += ext
            else:
                ext = '.mov'
                path += ext
                output_path = path

        global DIALOG_STATE
        DIALOG_STATE = dialog.get_value()

        playblast_kwargs = dict(
            camera=data['camera'],
            state=state,
            width=data['resolution'][0],
            height=data['resolution'][1],
            format='qt' if ext == '.mov' else 'image',
            compression='H.264' if ext == '.mov' else 'png',
            viewer=False
        )
        output_dir = os.path.dirname(output_path)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        if data['capture_mode'] == 'snapshot':
            playblast(
                completeFilename=output_path,
                frame=[cmds.currentTime(q=True)],
                **playblast_kwargs
            )
        else:
            playblast(
                filename=output_path,
                **playblast_kwargs
            )

        # post render
        if 'postrender' in data:
            for name, enabled in data['postrender'].items():
                if enabled:
                    fn = POSTRENDER_REGISTRY[name]
                    fn(path)

    def on_identify():
        Viewport.active().identify()

    identify_button = QtWidgets.QPushButton('Identify')
    dialog.button_layout.addWidget(identify_button)
    identify_button.clicked.connect(on_identify)

    # Add postrender hook checkboxes
    if POSTRENDER_REGISTRY.keys():
        for name, fn in POSTRENDER_REGISTRY.iteritems():
            c = controls.BoolControl(
                name,
                label_on_top=False,
                default=fn.default
            )
            dialog.postrender.add_control(
                name,
                controls.BoolControl(
                    name,
                    label_on_top=False,
                    default=fn.default
                )
            )

    dialog.accepted.connect(on_accept)
    dialog.setStyleSheet(stylesheet())

    # Restore state
    global DIALOG_STATE
    if DIALOG_STATE:
        dialog.set_value(strict=False, **DIALOG_STATE)
        if DIALOG_STATE['path_option'] != 'Custom':
            get_path()  # Refresh path if it is not custom

    dialog.show()
    return dialog
