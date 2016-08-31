""" 
From Obfsproxy repo:
https://github.com/david415/obfsproxy/blob/david-bananaphone/obfsproxy/common/rand.py
"""

import os

def random_bytes(n):
    """ Returns n bytes of strong random data. """

    return os.urandom(n)