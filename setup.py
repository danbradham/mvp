#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup
import os
import sys

__title__ = 'mvp'
__author__ = 'Dan Bradham'
__email__ = 'danielbradham@gmail.com'
__url__ = 'http://github.com/danbradham/mvp.git'
__version__ = '0.1.0'
__license__ = 'MIT'
__description__ = 'Manipulate Maya 3D Viewports.'

if sys.argv[-1] == 'cheeseit!':
    os.system('python setup.py sdist upload')
    sys.exit()

elif sys.argv[-1] == 'testit!':
    os.system('python setup.py sdist upload -r test')
    sys.exit()


package_data = {
    '': ['LICENSE', 'README.rst']
}

with open("README.rst") as f:
    readme = f.read()

setup(
    name="mvp",
    version=__version__,
    description=__description__,
    long_description=readme,
    author=__author__,
    author_email=__email__,
    url=__url__,
    license=__version__,
    package_data=package_data,
    py_modules=['mvp'],
    include_package_data=True,
    classifiers=(
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        'Programming Language :: Python :: 2',
    ),
)
