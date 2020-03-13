#!/usr/bin/env python

from os.path import exists
try:
    # Use setup() from setuptools(/distribute) if available
    from setuptools import setup
except ImportError:
    from distutils.core import setup


setup(name='zouk',
      version='0.0.1',
      author='Angel ILIEV, John Jacobsen',
      author_email='a.v.iliev13@gmail.com',
      packages=['zouk'],
      scripts=[],
      url='https://github.com/AngelVI13/zouk',
      license='MIT',
      description='Simple continuous task execution tool',
      long_description=open('README.md').read() if exists("README.md") else "",
      entry_points=dict(console_scripts=['zouk=zouk.zouk:main']),
      install_requires=[])
