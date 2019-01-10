#! /usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import os

import pywikibot

if 'POTY_USERNAME' in os.environ:
    COMMONS = pywikibot.Site('commons', 'commons', os.environ['POTY_USERNAME'])
else:
    COMMONS = pywikibot.Site('commons', 'commons')
META = pywikibot.Site('meta', 'meta')
