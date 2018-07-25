#! /usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import pywikibot

from poty.sites import META, COMMONS


def get_voter(username):
    # TODO: Eligibility, Rename
    return pywikibot.User(COMMONS, username)
