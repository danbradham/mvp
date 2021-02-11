# -*- coding: utf-8 -*-


class Integration(object):

    name = None
    description = None
    icon = None
    banner = None
    requires_confirmation = False
    enabled_by_default = False
    columns = 1

    def __init__(self):
        self.set_enabled(self.enabled_by_default)

    def fields(self):
        '''Return a list of fields.

        Example:
            return [
                {
                    'name': 'StringField',
                    'type': 'str',
                    'default': None,
                    'options': [...],
                    'required': False,
                },
                ...
            ]
        '''
        return NotImplemented

    def on_filename_changed(self, form, value):
        return NotImplemented

    def set_enabled(self, value):
        '''Returns True if the integration was successfully enabled'''

        if value:
            return self._on_enable()
        else:
            return self._on_disable()

    def _on_enable(self):
        self.enabled = self.on_enable()
        return self.enabled

    def on_enable(self):
        '''Return True to enable integration and False to disable'''

        return True

    def _on_disable(self):
        self.enabled = not self.on_disable()
        return self.enabled

    def on_disable(self):
        '''Return True to disable integration and False to enable'''

        return True

    def before_playblast(self, form, data):
        '''Runs before playblasting.'''

        return NotImplemented

    def after_playblast(self, form, data):
        '''Runs after playblasting.'''

        return NotImplemented

    def finalize(self, form, data):
        '''Runs after entire playblast process is finished.

        Unlike after_playblast, this method will only run ONCE after all
        playblasting is finished. So, when playblasting multiple render layers
        you can use this to execute after all of those render layers have
        completed rendering.

        Arguments:
            form: The Form object including render options
            data: List of renders that were output
        '''

        return NotImplemented
