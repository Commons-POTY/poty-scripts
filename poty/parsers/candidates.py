#! /usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import collections
import logging
import re

from poty.candidate import Candidate
from poty.utils.misc import kwargs_setattr

logger = logging.getLogger('poty.parsers.candidates')

Pattern = collections.namedtuple('Pattern', 're fmt')


class CandidatesParser(object):
    def __init__(self, **kwargs):
        kwargs_setattr(self, kwargs)

    def parse(self, round):
        page = round.year.subpage(round.candidatespage)
        candidates = set()
        self._parse(round, page.text, candidates)
        return candidates


# XXX: Python needs monads. I can't think of a way to DRY this without monads.

class CategorizedParser(CandidatesParser):
    def _parse(self, round, text, container):
        ingallery = False
        curcat = None
        for line in text.split('\n'):
            line = line.strip()

            if not line:
                continue

            elif line.startswith('<gallery'):
                assert not ingallery
                ingallery = True
            elif line == '</gallery>':
                assert ingallery
                ingallery = False
            else:
                if ingallery:
                    reobj = re.match(self.gallerypattern.re, line)
                    container.add(Candidate(**reobj.groupdict()))
                else:
                    reobj = re.match(self.categorypattern.re, line)
                    if not curcat and not reobj:
                        logger.warn('Ignoring line: ' + line)
                        continue
                    curcat = reobj.group(1)


class UncategorizedParser(CandidatesParser):
    def _parse(self, round, text, container):
        ingallery = False
        for line in text.split('\n'):
            line = line.strip()

            if not line:
                continue

            elif line.startswith('<gallery'):
                assert not ingallery
                ingallery = True
            elif line == '</gallery>':
                assert ingallery
                ingallery = False
            else:
                if ingallery:
                    reobj = re.match(self.gallerypattern.re, line)
                    container.add(Candidate(**reobj.groupdict()))
                else:
                    logger.warn('Ignoring line: ' + line)
