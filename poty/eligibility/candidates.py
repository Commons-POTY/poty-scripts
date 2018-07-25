#! /usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import collections

TopCriteria = collections.namedtuple('TopCriteria', 'num key cmt')


class FPCategorizer(object):
    def process_candidates(self, round, candidates):
        for candidate in candidates:
            candidate.category = ('dummy', 'dummy')
            candidate.comment = ''

        return candidates


class VoteTally(object):
    def __init__(self, criteria):
        self.criteria = criteria

    def process_candidates(self, round, candidates):
        raise NotImplementedError
