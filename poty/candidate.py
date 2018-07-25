#! /usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import pywikibot

from poty.sites import COMMONS
from poty.utils.misc import kwargs_setattr


class Candidate(pywikibot.FilePage):
    def __init__(self, title, **kwargs):
        super(Candidate, self).__init__(COMMONS, title)
        kwargs_setattr(self, kwargs)

    @property
    def ns_title(self):
        return self.title()

    @property
    def nons_title(self):
        return self.title(withNamespace=False)
