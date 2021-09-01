# -*- coding: utf-8 -*-

# Standard library imports
import os

# Third party imports
from .vendor.psforms import *
from .vendor.psforms.exc import ValidationError
from .vendor.psforms.validators import required
from .vendor.psforms.fields import *


def check_resolution(value):
    if (value[0] % 2) != 0 or (value[1] % 2) != 0:
        raise ValidationError('Resolution must use even numbers.')
    return True


class PostRenderForm(Form):

    meta = FormMetaData(
        title='Post Render',
        description='Post Render Callbacks',
        header=False,
        labels_on_top=False,
        columns=2,
    )


class PlayblastForm(Form):

    meta = FormMetaData(
        header=False,
        icon=os.path.join(os.path.dirname(__file__), 'icon.png'),
        title='Review',
        subforms_as_groups=True,
        labels_on_top=False
    )

    filename = SaveFileField(
        'Filename',
        validators=(required,),
    )
    preset = StringOptionField(
        'Viewport Preset',
        options=['Current Settings'],
    )
    capture_mode = StringOptionField(
        'Capture Mode',
        options=['sequence', 'snapshot'],
    )
    render_layers = StringOptionField(
        'Render Layers',
        options=['current', 'all enabled'],
    )
    camera = StringOptionField(
        'Camera',
    )
    resolution = Int2Field(
        'Resolution',
        range1=(0, 8192),
        range2=(0, 8192),
        default=(960, 540),
        validators=(check_resolution,),
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
