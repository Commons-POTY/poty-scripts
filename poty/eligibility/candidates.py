#! /usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import collections
import functools
import logging

import pywikibot
from pywikibot.data import api

from poty.candidate import Candidate
from poty.parsers.votepage import get_voters
from poty.sites import COMMONS
from poty.utils.concurrent import concurrent_map
from poty.utils.misc import kwargs_setattr, get_tops

logger = logging.getLogger('poty.eligibility.candidates')

TopCriteria = collections.namedtuple('TopCriteria', 'num key cmt')


class FPCategorizer(object):
    def process_candidates(self, year, candidates):
        for candidate in candidates:
            candidate.category = ('dummy', 'dummy')
            candidate.comment = ''

        # TODO

        return candidates


class VoteTally(object):
    def __init__(self, *criteria, **kwargs):
        self.criteria = criteria
        kwargs_setattr(self, kwargs)

    def process_candidates(self, year, candidates):
        candidates = list(candidates)
        voters = concurrent_map(functools.partial(get_voters, self, year),
                                candidates)

        # not using MultiDicts here because we can neither remove a pair easily
        # nor reverse dicts
        def do_remove(dct, key, val):
            s = dct[key]
            s.remove(val)
            if not s:
                del dct[key]

        candidate_voters = dict(zip(candidates, voters))
        voter_candidates = collections.defaultdict(set)
        for candidate, voters in zip(candidates, voters):
            for voter in voters:
                voter_candidates[voter].add(candidate)

        # Process max votes per voter
        if self.maxvotes is not None:
            for voter, candidates in voter_candidates.copy().items():
                if len(candidates) > self.maxvotes:
                    logger.warn('[[User:{u}]]: voted too many '
                                '({n}) times'.format(
                                    u=voter.username,
                                    n=len(candidates),
                                ))
                    for candidate in self.fixup_toomanyvotes(
                            year, voter, candidates):
                        do_remove(candidate_voters, candidate, voter)
                        do_remove(voter_candidates, voter, candidate)
                    assert len(candidates) == self.maxvotes

        for candidate, voters in candidate_voters.items():
            logger.warn('[[{c}]]: {n} votes'.format(
                c=candidate.ns_title,
                n=len(voters),
            ))

        tops = set()
        for criteria in self.criteria:
            cat_can_num = collections.defaultdict(dict)
            for candidate, voters in candidate_voters.items():
                cat_can_num[criteria.key(candidate)][candidate] = len(voters)
            for cat, can_num in cat_can_num.items():
                for i, candidate in get_tops(can_num, criteria.num):
                    if candidate not in tops:
                        candidate.comment = criteria.cmt.format(
                            c=candidate,
                            i=i,
                            n=can_num[candidate],
                        )
                        tops.add(candidate)

        return tops

    def fixup_toomanyvotes(self, year, voter, candidates):
        # XXX: No guarentees that this thing is a 'prefix'
        votepage_prefix = year.subpage(self.page.format(c='')).title()
        ucgen = COMMONS._generator(api.ListGenerator,
                                   type_arg="usercontribs",
                                   ucprop="title|sizediff",
                                   ucuser=voter,
                                   ucnamespace=4,
                                   ucend=str(pywikibot.Timestamp(
                                       year + 1, 1, 1)))

        last_votes = set()
        for contrib in ucgen:
            if contrib['sizediff'] < 0 or not contrib['title'].startswith(
                    votepage_prefix):
                continue

            # Make sure candidate constructed here cannot leak outside this
            # module, they can have different attrs.
            candidate = Candidate(contrib['title'][len(votepage_prefix):])
            if candidate in candidates:
                logger.warn(
                    '[[{c}]]: Keep vote from [[User:{u}]]'.format(
                        c=candidate.ns_title,
                        u=voter.username,
                    ))
                last_votes.add(candidate)

                if len(last_votes) == self.maxvotes:
                    break

        drops = candidates - last_votes
        for candidate in drops:
            logger.warn(
                '[[{c}]]: Drop vote from [[User:{u}]]'.format(
                    c=candidate.ns_title,
                    u=voter.username,
                ))
        return drops
