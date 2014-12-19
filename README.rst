=======================
MVP - Maya Viewport API
=======================
Because accessing and modifying Maya viewports should be simple.

::

    import mvp

    mvp.Viewport.identify()
    view = mvp.Viewport.get(0)

    view.show_nurbsCurves = 0
    view.show_nurbsSurfaces = 0
    view.show()
    view.hudText(label="Frame", callback=get_frame, align=(-1, -1))
    view.playblast("path/to/playblast.mov")


