import maya.cmds as cmds

RENDER_GLOBALS = [
    'multiSampleEnable', 'multiSampleCount', 'colorBakeResolution',
    'bumpBakeResolution', 'motionBlurEnable', 'motionBlurSampleCount',
    'ssaoEnable', 'ssaoAmount', 'ssaoRadius', 'ssaoFilterRadius',
    'ssaoSamples'
]


class RenderGlobals(object):
    '''Get and set hardwareRenderingGlobals attributes::

        RenderGlobals.multiSampleEnable = True
        RenderGlobals.ssaoEnable = True
    '''

    def __getattr__(self, name):
        return cmds.getAttr('hardwareRenderingGlobals.' + name)

    def __setattr__(self, name, value):
        cmds.setAttr('hardwareRenderingGlobals.' + name, value)

    @property
    def properties(self):
        '''A list of valid render global attributes'''
        return RENDER_GLOBALS

    def get_state(self):
        '''Collect hardwareRenderingGlobals attributes that effect
        Viewports.'''

        active_state = {}
        for attr in RENDER_GLOBALS:
            active_state[attr] = getattr(self, attr)

        return active_state

    def set_state(self, state):
        '''Set a bunch of hardwareRenderingGlobals all at once.

        :param state: Dict containing attr, value pairs'''

        for k, v in state.iteritems():
            setattr(self, k, v)


RenderGlobals = RenderGlobals()
