#! /usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import collections
import functools
import logging

from pyquery import PyQuery as pq
import pywikibot
from pywikibot.data import api

from poty.candidate import Candidate
from poty.parsers.votepage import get_voters
from poty.sites import COMMONS
from poty.utils.concurrent import concurrent_map
from poty.utils.misc import kwargs_setattr, get_tops, if_redirct_get_target

logger = logging.getLogger('poty.eligibility.candidates')

TopCriteria = collections.namedtuple('TopCriteria', 'num key cmt')


class FPCategorizer(object):
    def __init__(self, **kwargs):
        self.fallback = ('dummy', 'dummy')
        kwargs_setattr(self, kwargs)

    def process_candidates(self, year, candidates):
        for candidate in candidates:
            candidate.category = self.fallback
            candidate.comment = ''

        fpc_res_template = pywikibot.Page(
            COMMONS, 'Template:FPC-results-reviewed')

        def get_category(filepage):
            fpcs = set()

            for fpc_page in filepage.usingPages():
                if not fpc_page.title().startswith(
                        'Commons:Featured picture candidates/'):
                    continue

                for template, params in fpc_page.templatesWithParams():
                    if template == fpc_res_template:
                        if 'featured=yes' in params:
                            fpcs.add(fpc_page)
                        break

            if len(fpcs) == 1:
                fpc_page = fpcs.pop()
            elif len(fpcs) == 0:
                return None  # gotta handle these manually
            else:  # Argh!
                # HACK: HTML scraping the FPC link
                html = filepage.getImagePageHtml()
                d = pq(html)
                e = d('#assessments '
                      'a[title^="Commons:Featured picture candidates/"]')
                assert len(e) == 1

                title = e.attr('title')
                fpc_page = if_redirct_get_target(
                    pywikibot.Page(COMMONS, title))
                assert fpc_page in fpcs

            for template, params in fpc_page.templatesWithParams():
                if template == fpc_res_template:
                    for param in params:
                        if param.startswith('category='):
                            return param[len('category='):].replace('_', ' ')

        def singular(words):
            exceptions = {'glass', 'ous'}

            words = words.split(' ')
            for i, word in enumerate(words):
                if not any(word.endswith(exception)
                           for exception in exceptions):
                    if word.endswith('ies'):
                        words[i] = word[:-3] + 'y'
                    elif word.endswith('s'):
                        words[i] = word[:-1]

            return ' '.join(words)

        token_overrides = {
            'natural': 'nature',
            'animated': 'animation',
        }

        def poty_tokenizer(catstr):
            catstr = catstr.lower()

            cats = [catstr]
            for split_key in [', ', ' and ']:
                cats = [cat.split(split_key) for cat in cats]
                cats = sum(cats, [])

            cats = [singular(cat.strip()) for cat in cats]
            cats = [cat[len('other '):] if cat.startswith('other ') else cat
                    for cat in cats]
            cats = [cat[:-len(' view')] if cat.endswith(' view') else cat
                    for cat in cats]
            cats = [token_overrides[cat] if cat in token_overrides else cat
                    for cat in cats]
            cats = frozenset(filter(None, cats))

            return cats

        poty_tokens = {}
        for category in self.categories:
            for token in poty_tokenizer(', '.join(category)):
                poty_tokens[token] = category

        def fp_tokenizer(catstr):
            catstr = catstr.replace('#', '/')
            return map(poty_tokenizer, catstr.split('/')[::-1])

        def match(catstr):
            if catstr is not None:
                for tokens in fp_tokenizer(catstr):
                    for token in tokens:
                        if token in poty_tokens:
                            return token, poty_tokens[token]
            return None, self.fallback

        def mapfunc(candidate):
            cat = get_category(candidate)
            token, target = match(cat)
            candidate.comment = '%s => %s => %s' % (cat, token, target)
            candidate.category = target

        concurrent_map(mapfunc, candidates)

        return candidates


class VoteTally(object):
    def __init__(self, *criteria, **kwargs):
        self.criteria = criteria
        kwargs_setattr(self, kwargs)

    def process_candidates(self, year, candidates):
        candidates = list(candidates)
        voters = map(functools.partial(get_voters, self, year),
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
