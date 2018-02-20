#!/usr/bin/env python

from setuptools import setup
from cron_conf import __version__

setup(
    name='cron_conf',
    version=__version__,
    description='Cronf conf',
    author='Sogeti AB',
    author_email='supportwebb@sogeti.se',
    classifiers=['License :: Other/Proprietary License'],
    url='https://github.com/elinfs/bobcat-validator-ul',
    packages=[
        'cron_conf',
    ],
    package_data={'cron_conf': [
       
    ]},
    install_requires=[                
        'azure-storage-blob',
        'setuptools'
    ],
    data_files=[
    
    ],
    entry_points={
        "console_scripts": [
            "cron_conf = cron_conf.main:main"
        ]
    }
)
