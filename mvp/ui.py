from PySide import QtGui, QtCore
from psforms import stylesheet, controls
import maya.cmds as cmds
from functools import partial
from .viewport import playblast, Viewport
from .forms import PlayblastForm, NewPresetForm, DelPresetForm
from .utils import wait, get_maya_window
from .presets import *


def new_dialog(parent_dialog):

    dialog = NewPresetForm.as_dialog(parent=parent_dialog)
    dialog.panel.set_options([v.panel for v in Viewport.iter()])

    def on_accept():
        name = dialog.name.get_value()
        panel = dialog.panel.get_value()
        v = Viewport.from_panel(panel)
        state = v.get_state()
        new_preset(name, state)
        parent_dialog.update_presets

    def identify_clicked():
        panel = dialog.panel.get_value()
        v = Viewport.from_panel(panel)
        v.identify()

    identify = QtGui.QPushButton('identify')
    identify.clicked.connect(identify_clicked)

    dialog.panel.grid.addWidget(identify, 1, 2)
    dialog.accepted.connect(on_accept)
    dialog.setStyleSheet(stylesheet)
    dialog.show()


def del_dialog(parent_dialog):

    def on_accept():
        name = parent_dialog.preset.get_value()
        del_preset(name)
        parent_dialog.update_presets()

    dialog = DelPresetForm.as_dialog(parent=parent_dialog)
    dialog.accepted.connect(on_accept)
    dialog.setStyleSheet(stylesheet)
    dialog.show()


def update_presets(dialog):

    presets = ['Current Settings'] + [n for n, s in get_presets()]
    dialog.preset.set_options(presets)


def show():

    dialog = PlayblastForm.as_dialog(parent=get_maya_window())
    dialog.camera.set_options(cmds.ls(cameras=True))

    def on_accept():
        data = dialog.get_value()

        if data['preset'] == 'Current Settings':
            state = Viewport.active().get_state()
        else:
            state = get_preset(data['preset'])

        playblast(
            data['filename'],
            data['camera'],
            state=state,
            width=data['resolution'][0],
            height=data['resolution'][1],
        )

    dialog.accepted.connect(on_accept)

    new_button = QtGui.QPushButton('New')
    new_button.clicked.connect(partial(new_dialog, dialog))
    del_button = QtGui.QPushButton('Delete')
    del_button.clicked.connect(partial(del_dialog, dialog))
    dialog.preset.grid.addWidget(new_button, 1, 2)
    dialog.preset.grid.addWidget(del_button, 1, 3)

    def update_presets():
        presets = ['Current Settings'] + [n for n, s in get_presets()]
        dialog.preset.set_options(presets)

    dialog.update_presets = update_presets
    dialog.update_presets()

    path_options = ['Custom']
    path_options.extend(PATHGEN_REGISTRY.keys())
    path_option = controls.StringOptionControl('Path Option', labeled=False)
    path_option.set_options(path_options)
    dialog.filename.grid.addWidget(path_option.widget, 1, 2)

    def on_path_option_change():
        path_fn = PATHGEN_REGISTRY.get(path_option.get_value(), None)

        if not path_fn:
            return

        dialog.filename.set_value(path_fn())

    path_option.changed.connect(on_path_option_change)

    def on_filename_change():
        path_option.set_value('Custom')

    dialog.filename.changed.connect(on_filename_change)

    dialog.setStyleSheet(stylesheet)
    dialog.show()
