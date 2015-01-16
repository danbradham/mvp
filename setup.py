#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup
import os
import sys

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
    version='0.1.2',
    description='Manipulate Maya 3D Viewports.',
    long_description=readme,
    author='Dan Bradham',
    author_email='danielbradham@gmail.com',
    url='http://github.com/danbradham/mvp.git',
    license='MIT',
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
