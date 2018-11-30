#!/usr/bin/python3

from setuptools import setup

setup(name='ggkbdd',
      version='1',
      description='A Gaming Keyboard emulation daemon',
      long_description=open('README.md', 'r').read(),
      url='http://gitlab.freedesktop.org/whot/ggkbdd',
      packages=['ggkbdd'],
      author='Peter Hutterer',
      author_email='peter.hutterer@who-t.net',
      license='GPL',
      entry_points={
          "console_scripts": [
              'ggkbdd = ggkbdd.daemon:main',
              ]
      },
      classifiers=[
          'Development Status :: 3 - Alpha',
          'License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.6'
      ],
      python_requires='>=3.6',
      include_package_data=True,
      )
