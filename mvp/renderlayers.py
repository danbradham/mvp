# -*- coding: utf-8 -*-
from contextlib import contextmanager

import maya.app.renderSetup.model.renderSetup as renderSetup
from maya import cmds


@contextmanager
def enabled_render_layers():
    old_layer = cmds.editRenderLayerGlobals(query=True, currentRenderLayer=True)
    try:
        rs = renderSetup.instance()

        def switchToLayer(layer):
            def _switch():
                rs.switchToLayer(layer)
            return _switch

        enabled_layers = []
        for layer in rs.getRenderLayers():

            layer.switchToLayer = switchToLayer(layer)
            if layer.isRenderable():
                enabled_layers.append(layer)

        yield enabled_layers
    finally:
        cmds.editRenderLayerGlobals(currentRenderLayer=old_layer)
