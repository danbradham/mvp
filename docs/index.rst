.. image:: https://readthedocs.org/projects/mvp/badge/?version=latest
    :target: https://readthedocs.org/projects/mvp/?badge=latest
    :alt: Documentation Status

.. image:: https://pypip.in/version/mvp/badge.svg
    :target: https://testpypi.python.org/pypi/mvp/
    :alt: Latest Version

=======================
MVP - Maya Viewport API
=======================

I really needed this...

This module exists to unify and pythonify the various commands and apis necessary to manipulate Maya's 3D Viewports. These include, hardwareRenderGlobal attributes, modelPanel and modelEditor commands, as well as some key features of OpenMayaUI's M3dView class.

::

    from mvp import Viewport

    view = Viewport.active()
    view.camera = 'top'
    view.background = 0.5, 0.5, 0.5
    view.nurbsCurves = False



Features
========

* Unified api for manipulating Maya Viewports

* Get or set every viewport attribute all at once. Making it easy to restore a Viewport to a previous state.

* Easily set focus and playblast Viewports. Much more consistent than using active view.

* Draw text in Viewports using QLabels.

* Show identifiers in viewports, making it easy to grab the correct viewport at a glance.


Get MVP
=======

PyPi
----
MVP is available through the python package index as **mvp**.

::

    pip install mvp

Distutils/Setuptools
--------------------

::

    git clone git@github.com/danbradham/mvp.git
    cd mvp
    python setup.py install


Table of Contents
=================

.. toctree::
    :maxdepth: 2

    guide
    api
