#! /usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import datetime
import random
import re

from frozendict import frozendict
import pywikibot

from poty.eligibility.candidates import FPCategorizer, VoteTally, TopCriteria
from poty.parsers.candidates import (
    Pattern, CategorizedParser, UncategorizedParser, FPParser)
from poty.round import Round
from poty.sites import COMMONS
from poty.utils.properties import cachedproperty


class POTY(int):
    def __new__(cls, year=None):
        return super(POTY, cls).__new__(
            cls, year or datetime.datetime.now().year - 1)

    def page(self, title):
        return pywikibot.Page(COMMONS, title)

    @cachedproperty
    def basepage(self):
        return self.page('Commons:Picture of the Year/%d' % self)

    def subpage(self, subpage):
        return self.page('Commons:Picture of the Year/%d/%s' % (self, subpage))

    @cachedproperty
    def rounds(self):
        GLOBAL_VOTER_ELIGIBILITY = frozendict({
            'register': frozendict({
                'before': pywikibot.Timestamp(self + 1, 1, 1),
            }),
            'edits': frozendict({
                'before': pywikibot.Timestamp(self + 1, 1, 1),
                'atleast': 75,
                'includedeleted': False
            })
        })

        return [
            Round(
                self, 0,
                candidates=FPParser(
                    pages=[
                        'Commons:Featured pictures/chronological/%s-A' % self,
                        'Commons:Featured pictures/chronological/%s-B' % self,
                    ],
                ),
            ),
            Round(
                self, 1,
                candidates=CategorizedParser(
                    page='Candidates',
                    gallerysortkey=lambda c: tuple(map(
                        int, re.match(r'^(\d+)-(\d+)/(\d+)$', c.id).groups())),
                    gallerypattern=Pattern(
                        r'^(?P<title>[^|]+?)\|(?P<id>\d+-\d+/\d+) *'
                        r'(?:<!--(?P<comment>.+)-->)?$',
                        '{c.nons_title}|{c.id} <!--{c.comment}-->'
                    ),
                    categorypattern=Pattern(
                        r'^== *\[\[Commons:Picture of the Year/\d+/R1/Gallery/'
                        r'([^|]+)\|([^\]]+?)\]\] *==$',
                        '== [[Commons:Picture of the Year/{r.year}/R1/Gallery/'
                        '{c[0]}|{c[1]}]] =='
                    ),
                ),
                candidates_eligible=FPCategorizer(),
            ),
            Round(
                self, 2,
                candidates=UncategorizedParser(
                    page='Candidates/R2',
                    gallerysortkey=lambda c: random.random(),
                    gallerypattern=Pattern(
                        r'^(?P<title>[^|]+?)\|\{\{[^}]+?\}\} *'
                        r'(?:<!--(?P<comment>.+)-->)?$',
                        '{c.nons_title}|{{{{POTY{r.year}/votebutton|'
                        'f={c.nons_title}|base=Commons:Picture_of_the_Year/'
                        '{r.year}/R2}}}} <!--{c.comment}-->'
                    )
                ),
                candidates_eligible=VoteTally(
                    TopCriteria(
                        num=30,
                        key=lambda c: None,
                        cmt='Top #{i} in all categories',
                    ),
                    TopCriteria(
                        num=2,
                        key=lambda c: c.category,
                        cmt='Top #{i} in category "{c.category[1]}"',
                    ),
                    voter_eligible=GLOBAL_VOTER_ELIGIBILITY,
                    maxvotes=None,
                    page='R1/v/{c}',
                    re=r'^# *\[\[User:([^\]\|]+)(?:\|\1)\]\]$',
                ),
            ),
            Round(
                self, 3,
                candidates=UncategorizedParser(
                    gallerysortkey=lambda c: int(
                        re.search(r'#(\d+)', c.comment).group(1)),
                    gallerypattern=Pattern(
                        r'^$',  # should be unused
                        '{c.nons_title}| {c.comment}'
                    )
                ),
                candidates_eligible=VoteTally(
                    TopCriteria(
                        num=None,
                        key=lambda c: None,
                        cmt='#{i}, {n} votes',
                    ),
                    voter_eligible=GLOBAL_VOTER_ELIGIBILITY,
                    maxvotes=3,
                    page='R2/v/{c}',
                    re=r'^# *\[\[User:([^\]\|]+)(?:\|\1)\]\]$'
                ),
            ),
        ]
