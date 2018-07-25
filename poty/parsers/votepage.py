#! /usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals, print_function

import logging
import re

from poty.eligibility.voter import get_voter
from poty.utils.misc import warn_lineignore


logger = logging.getLogger('poty.parsers.candidates')


def get_voters(votetally, year, candidate):
    votepage = year.subpage(votetally.page.format(c=candidate.nons_title))
    voters = set()

    for line in votepage.text.split('\n'):
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
