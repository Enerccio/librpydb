# py23 compatible
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals
from __future__ import absolute_import

class NoneDict(dict):
    """
    None dict is a dict that returns None on key it does not have
    """

    def __init__(self, other):
        for key in other:
            self[key] = other[key]

    def __getitem__(self, key):
        if key not in self:
            return None
        return dict.__getitem__(self, key)
