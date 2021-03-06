#! /usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import argparse

from poty.poty import POTY


def main(*args):
    parser = argparse.ArgumentParser(
        description='Advance POTY candidates. Vote counting, sorting, etc.')
    parser.add_argument('year', type=int,
                        help='the year of POTY')
    parser.add_argument('round', type=int,
                        help='the round number')
    args = parser.parse_args(args=args or None)

    poty = POTY(args.year)
    round, nextround = poty.rounds[args.round:args.round+2]
    candidates = round.candidates.parse(round)
    candidates = nextround.candidates_eligible.process_candidates(
        poty, candidates)
    print(nextround.candidates.format(nextround, candidates))


if __name__ == '__main__':
    main()
