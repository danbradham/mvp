'''
General purpose classes and functions.
'''


def itemattrgetter(index, attr):
    '''Returns a function which gets an object in a sequence, then looks up
    an attribute on that object and returns its value.'''

    def get_it(obj):
        return getattr(obj[index], attr)

    return get_it


class Ordered(object):
    '''Maintains the order of creation for all instances/subclasses'''

    _count = 0

    def __init__(self):
        Ordered._count += 1
        self._order = self._count
