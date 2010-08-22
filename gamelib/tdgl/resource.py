"""
 Find files somewhere in a resource path

 Copyright Sep 2007 Peter Harris
 Release under GNU GPL v3 or later.
"""

__all__ = ('path','find','append_dir')

path = ["."]

import os

def find(fname):
    for prefix in path:
        f = os.path.join(prefix,fname)
        if os.path.exists(f):
            return f

def append_dir(dirname):
    if dirname not in path and os.path.exists(dirname):
        path.append(dirname)
