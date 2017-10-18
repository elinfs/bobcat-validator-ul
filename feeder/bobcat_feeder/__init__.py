
"""Bobcat Feeder"""

import os

__version__ = '1.0.1a1'

SCHEMADIR = os.path.dirname(__file__) + '/schema'


def MSG(msgid: str) -> str:
        return msgid
