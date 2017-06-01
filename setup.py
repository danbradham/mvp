#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from setuptools import setup, find_packages
from subprocess import check_call
import shutil
import sys


if sys.argv[-1] == 'cheeseit!':
    check_call('nosetests -v')
    check_call('python setup.py sdist bdist_wheel')
    check_call('twine upload dist/*')
    shutil.rmtree('dist')
    sys.exit()
elif sys.argv[-1] == 'testit!':
    check_call('nosetests -v')
    check_call('python setup.py sdist bdist_wheel upload -r pypitest')
    sys.exit()


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
        '': ['LICENSE', 'README.rst', '*.css'],
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
