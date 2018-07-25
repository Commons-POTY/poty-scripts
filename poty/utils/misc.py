#! /usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import functools

try:
    from _thread import get_ident
except ImportError:
    from _dummy_thread import get_ident

from six import with_metaclass


# modified from reprlib.recursive_repr
def no_recurse(identity=lambda *args, **kwargs: (
    tuple(map(id, args)),
    tuple(kwargs.keys()),
    tuple(map(id, kwargs.values()))
)):
    def decorating_function(func):
        repr_running = set()

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            key = identity(*args, **kwargs), get_ident()
            if key in repr_running:
                raise RecursionError
            repr_running.add(key)
            try:
                result = func(*args, **kwargs)
            finally:
                repr_running.discard(key)
            return result

        return wrapper

    return decorating_function


from poty.utils.properties import cachedproperty  # noqa: E302


class _SingletonMeta(type):
    def __call__(self):
        return self.instance

    @cachedproperty
    def instance(self):
        return super(_SingletonMeta, self).__new__(self)


class Singleton(with_metaclass(_SingletonMeta)):
    pass


def kwargs_setattr(obj, kwargs):
    for key, val in kwargs.items():
        setattr(obj, key, val)
