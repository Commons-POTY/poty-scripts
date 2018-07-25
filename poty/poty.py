#! /usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import datetime

import pywikibot

from poty.sites import COMMONS
from poty.utils.properties import cachedproperty


class POTY(int):
    def __new__(cls, year=datetime.datetime.now().year - 1):
        return super(POTY, cls).__new__(cls, year)

    @cachedproperty
    def basepage(self):
        return pywikibot.Page(COMMONS, 'Commons:Picture of the Year/%d' % self)

    def subpage(self, subpage):
        return pywikibot.Page(
            COMMONS, 'Commons:Picture of the Year/%d/%s' % (self, subpage))

    @cachedproperty
    def rounds(self):
        rounds = [None]
        rounds.append()
