#! /usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals, print_function

import logging
import re

import pywikibot

from poty.eligibility.voter import get_voter
from poty.utils.misc import warn_lineignore


logger = logging.getLogger('poty.parsers.candidates')


def get_voters(votetally, year, candidate):
    votepage = year.subpage(votetally.page.format(c=candidate.nons_title))
    voters = set()

    for rev in votepage.revisions():
        if rev.timestamp < pywikibot.Timestamp(2020, 3, 23, 0, 0, 0):
            break
    else:
        assert False

    text = votepage.getOldVersion(rev.revid)
    if votepage.text != text:
        votepage.text = text
        votepage.save(f'Revert to old revision before R1 end, [[Special:Permalink/{rev.revid}]]')

    return voters

    for line in votepage.getOldVersion(rev.revid).split('\n'):
        line = line.strip()

        if not line:
            continue

        reobj = re.match(votetally.re, line)
        if not reobj:
            warn_lineignore('poty.parsers.candidates', line)
            continue

        voter = get_voter(reobj.group(1), votetally.voter_eligible)
        if voter is None:
            logger.warn(
                '[[{c}]]: Drop ineligible vote from [[User:{s}]]'.format(
                    c=candidate.ns_title,
                    s=reobj.group(1),
                ))
            continue

        if voter in voters:
            logger.warn(
                '[[{c}]]: Drop duplicate vote from [[User:{u}]]'
                ' (src=[[User:{us}]])'.format(
                    c=candidate.ns_title,
                    u=voter.username,
                    s=reobj.group(1),
                ))

        voters.add(voter)

    return voters
