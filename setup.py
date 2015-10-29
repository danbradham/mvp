#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from setuptools import setup, find_packages
import os
import sys


def get_info(pyfile):
    '''Retrieve dunder values from a pyfile'''

    info = {}
    info_re = re.compile(r"^__(\w+)__ = ['\"](.*)['\"]")
    with open(pyfile, 'r') as f:
        for line in f.readlines():
            match = info_re.search(line)
            if match:
                info[match.group(1)] = match.group(2)

    return info

info = get_info('mvp/__init__.py')


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
    name=info['title'],
    version=info['version'],
    description=info['description'],
    long_description=readme,
    author=info['author'],
    author_email=info['email'],
    url=info['url'],
    license=info['license'],
    packages=find_packages(),
    package_data={
        '': ['LICENSE', 'README.rst']
    },
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
