from PySide import QtGui, QtCore
from psforms import stylesheet
import maya.cmds as cmds
from .viewport import playblast, Viewport
from .forms import PlayblastForm, NewPresetForm, DelPresetForm
from .utils import wait, get_maya_window


def new_dialog():

    dialog = NewPresetForm.as_dialog(parent=get_maya_window())
    dialog.panel.set_options([v.panel for v in Viewport.iter()])

    def preset_accepted():
        name = dialog.name.get_value()
        panel = dialog.panel.get_value()
        v = Viewport.from_panel(panel)
        state = v.get_state()
        print state

    def show_identifier():
        panel = dialog.panel.get_value()
        v = Viewport.from_panel(panel)
        v.identify()

    identify = QtGui.QPushButton('identify')
    identify.clicked.connect(show_identifier)

    dialog.panel.grid.addWidget(identify, 1, 2)
    dialog.accepted.connect(preset_accepted)
    dialog.setStyleSheet(stylesheet)
    dialog.show()


def del_dialog():
    dialog = DelPresetForm.as_dialog(parent=get_maya_window())

    def delete_accepted():
        print 'Deleting preset'

    dialog.accepted.connect(delete_accepted)
    dialog.setStyleSheet(stylesheet)
    dialog.show()


def show():

    dialog = PlayblastForm.as_dialog(parent=get_maya_window())
    dialog.camera.set_options(cmds.ls(cameras=True))

    newpreset = QtGui.QPushButton('New')
    newpreset.clicked.connect(new_dialog)
    delpreset = QtGui.QPushButton('Delete')
    delpreset.clicked.connect(del_dialog)
    dialog.preset.grid.addWidget(newpreset, 1, 2)
    dialog.preset.grid.addWidget(delpreset, 1, 3)

    def accepted(dialog):
        def do_accept():
            data = dialog.get_value()
            if data['preset'] == 'Current Settings':
                state = Viewport.active().get_state()
            playblast(
                data['filename'],
                data['camera'],
                state=state,
                width=data['resolution'][0],
                height=data['resolution'][1],
            )
        return do_accept

    dialog.accepted.connect(accepted(dialog))

    dialog.setStyleSheet(stylesheet)
    dialog.show()
