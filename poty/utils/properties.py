#! /usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import functools

from poty.utils.misc import no_recurse


# ndd = non-data descriptor
class _base_ndd_property(object):
    def __init__(self, func):
        self.__func__ = func
        functools.update_wrapper(self, func)

    def __get__(self, obj, objtype):
        # Bind it before calling, like how Python itself does
        return self.__func__.__get__(obj, objtype)()


class classproperty(_base_ndd_property):
    def __init__(self, func):
        super(classproperty, self).__init__(classmethod(func))
        functools.update_wrapper(self, func)


class ndd_property(_base_ndd_property):
    def __get__(self, obj, objtype):
        if obj is None:
            return self
        return super(ndd_property, self).__get__(obj, objtype)


class _cachedproperty_mixin(object):
    @no_recurse()
    def __get__(self, obj, objtype):
        accessed = objtype if obj is None else obj
        setattr(accessed, self.__name__,
                super(_cachedproperty_mixin, self).__get__(obj, objtype))
        return accessed.__dict__[self.__name__]


cachedproperty = type(str('cachedproperty'),
                      (_cachedproperty_mixin, ndd_property), {})
cachedclassproperty = type(str('cachedclassproperty'),
                           (_cachedproperty_mixin, classproperty), {})


def _test():
    def show(func):
        print(__import__('inspect').getsource(func).strip())
        try:
            print(repr(func()))
        except Exception:
            __import__('traceback').print_exc()

    def testfunc(wrapper):
        print('-'*32)
        print(wrapper.__name__)

        class testclass(object):
            @wrapper
            def blah(self):
                print(self)
                return 'value'
        instance = testclass()
        show(lambda: testclass.blah)
        show(lambda: testclass.blah)
        show(lambda: instance.blah)
        show(lambda: instance.blah)

    testfunc(classproperty)
    testfunc(cachedclassproperty)
    testfunc(ndd_property)
    testfunc(cachedproperty)


if __name__ == '__main__':
    _test()
