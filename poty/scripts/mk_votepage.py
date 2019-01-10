#! /usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import argparse

from poty.poty import POTY


def main(*args):
    parser = argparse.ArgumentParser(
        description='Graduate POTY candidates. Vote counting, sorting, etc.')
    parser.add_argument('year', type=int,
                        help='the year of POTY')
    parser.add_argument('round', type=int,
                        help='the round number')
    args = parser.parse_args(args=args or None)

    poty = POTY(args.year)
    round, nextround = poty.rounds[args.round:args.round+2]
    candidates = round.candidates.parse(round)

    # TODO: "Modernize" this part
    for candidate in candidates:
        votepage = poty.subpage(nextround.candidates_eligible.page.format(
            c=candidate.nons_title))
        votepage.text = """\
{{autotranslate|base=POTY%d/header}}{{-}}{{POTY%d/Roundheader}}

== {{int:Ratinghistory-table-votes}} ==
""" % (poty, poty)
        votepage.save(
            'Create POTY R%d vote page for %s' % (
                round.num,
                candidate.title(asLink=True)),
            watch='nochange')


if __name__ == '__main__':
    main()
