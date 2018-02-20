#!/usr/bin/env python

from setuptools import setup
from bobcat_feeder import __version__

setup(
    name='bobcat_feeder',
    version=__version__,
    description='Bobcat Feeder',
    author='Sogeti AB',
    author_email='supportwebb@sogeti.se',
    classifiers=['License :: Other/Proprietary License'],
    url='https://github.com/elinfs/bobcat-validator-ul',
    packages=[
        'bobcat_feeder',
    ],
    package_data={'bobcat_feeder': [
       
    ]},
    install_requires=[
        'aiodns',
        'aiohttp',
        'hbmqtt',
        'pynmea2',
        'setuptools',
        'tzlocal'
    ],
    data_files=[
    
    ],
    entry_points={
        "console_scripts": [
            "bobcat_feeder = bobcat_feeder.main:main"
        ]
    }
)
