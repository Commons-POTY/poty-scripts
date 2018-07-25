#! /usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import collections

from poty.utils.misc import kwargs_setattr


class Round(collections.namedtuple('_Round', 'year num')):
    def __new__(cls, year, num, **kwargs):
        assert num > 0
        return super(Round, cls).__new__(cls, year, num)

    def __init__(self, year, num, **kwargs):
        kwargs_setattr(self, kwargs)
