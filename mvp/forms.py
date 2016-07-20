from psforms import *
from psforms.validators import required
from psforms.fields import *


class PlayblastForm(Form):

    meta = FormMetaData(
        title='MVP Playblast',
        description='Better playblasting? lol',
        header=True
    )

    preset = StringOptionField('Preset', options=['Current Settings'])
    filename = SaveFileField('Filename')
    camera = StringOptionField('Camera')
    resolution = Int2Field(
        'Resolution',
        range1=(0, 1920),
        range2=(0, 1080),
        default=(960, 540)
    )


class NewPresetForm(Form):

    meta = FormMetaData(
        title='New Preset',
        description='Create a new preset from the selected panel',
        header=True,
    )

    panel = StringOptionField('Panel')
    name = StringField('Preset Name', validators=(required,))


class DelPresetForm(Form):

    meta = FormMetaData(
        title='Delete Preset',
        description='Are you sure you want to delete this preset?',
        header=True,
    )
