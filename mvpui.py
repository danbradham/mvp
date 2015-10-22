import maya.cmds as cmds
import mvp
from psforms import *
from psforms.fields import *

class PlayblastForm(Form):

    meta = FormMetaData(
        title='MVP Playblast',
        description='Better playblasting...',
        header=True
    )

    filename = SaveFileField('Filename')
    camera = StringOptionField('Camera')
    resolution = Int2Field(
        'Resolution',
        range1=(0, 1920),
        range2=(0, 1080),
        default=(960, 540)
    )
    preset = StringOptionField('Preset', options=['Current Settings'])

def accepted(dialog):
    def do_accept():
        data = dialog.get_value()
        if data['preset'] == 'Current Settings':
            state = mvp.Viewport.active().get_state()
        mvp.playblast(
            data['filename'],
            data['camera'],
            state=state,
            width=data['resolution'][0],
            height=data['resolution'][1],
        )
    return do_accept

def show():
    pf = PlayblastForm.as_dialog(parent=mvp.get_maya_window())
    pf.setStyleSheet(stylesheet)
    pf.camera.set_options(cmds.ls(cameras=True))
    pf.accepted.connect(accepted(pf))
    pf.show()
