"""
Persistent Sets
"""

import sets
import shelve

class PersistentSet(sets.Set):
    def __init__(self, file, iterable=None):
        self._data = shelve.open(file)
        if iterable is not None:
            self._update(iterable)

    def __iand__(self, other):
        """Update a set with the intersection of itself and another."""
        self._binary_sanity_check(other)
        ia = (self & other)._data
        self._data.clear()
        self._data.update(ia)
        return self

