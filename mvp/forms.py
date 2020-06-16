# -*- coding: utf-8 -*-

# Standard library imports
import os

# Third party imports
from psforms import *
from psforms.validators import required
from psforms.fields import *


class PostRenderForm(Form):

    meta = FormMetaData(
        title='Post Render',
        description='Post Render Callbacks',
        header=False,
        labels_on_top=False,
        columns=2
    )


class PlayblastForm(Form):

    meta = FormMetaData(
        title='Review',
        description='Playblast for review',
        header=False,
        subforms_as_groups=True
    )
    preset = StringOptionField('Preset', options=['Current Settings'])
    capture_mode = ButtonOptionField(
        'Capture Mode',
        options=['sequence', 'snapshot'],
        label_on_top=False
    )
    filename = SaveFileField('Filename')
    camera = StringOptionField('Camera')
    resolution = Int2Field(
        'Resolution',
        range1=(0, 8192),
        range2=(0, 8192),
        default=(960, 540)
    )
    postrender = PostRenderForm()


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
