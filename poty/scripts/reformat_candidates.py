#! /usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import argparse

from poty.poty import POTY


def main(*args):
    parser = argparse.ArgumentParser(
        description='Re-format POTY candidates page.')
    parser.add_argument('year', type=int,
                        help='the year of POTY')
    parser.add_argument('round', type=int,
                        help='the round number')
    args = parser.parse_args(args=args or None)

    poty = POTY(args.year)
    round = poty.rounds[args.round]
    candidates = round.candidates.parse(round)
    print(round.candidates.format(round, candidates))


if __name__ == '__main__':
    main()
