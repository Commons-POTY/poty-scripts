#! /usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals, print_function

import calendar
import collections
import re

try:
    from io import StringIO
except ImportError:  # PY2
    from StringIO import StringIO

from werkzeug.datastructures import MultiDict

from poty.candidate import Candidate
from poty.utils.concurrent import concurrent_map
from poty.utils.misc import (
    kwargs_setattr, warn_lineignore, if_redirct_get_target)

Pattern = collections.namedtuple('Pattern', 're fmt')


class CandidatesParser(object):
    def __init__(self, **kwargs):
        kwargs_setattr(self, kwargs)

    def _gettext(self, round):
        return round.year.subpage(self.page).text

    def parse(self, round):
        candidates = set()
        self._parse(round, self._gettext(round), candidates)
        return candidates

    def format(self, round, candidates):
        text = StringIO()
        self._format(round, candidates, text)
        return text.getvalue()


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
                    if not reobj:
                        warn_lineignore('poty.parsers.candidates', line)
                        continue
                    container.add(Candidate(
                        category=curcat,
                        **reobj.groupdict('')))
                else:
                    reobj = re.match(self.categorypattern.re, line)
                    if not curcat and not reobj:
                        warn_lineignore('poty.parsers.candidates', line)
                        continue
                    curcat = reobj.groups()

    def _format(self, round, candidates, text):
        category_dict = MultiDict((c.category, c) for c in candidates)
        categories = round.candidates_eligible.categories[:]
        categories += list(sorted(set(category_dict) - set(categories)))

        for category in categories:
            print(self.categorypattern.fmt.format(r=round, c=category),
                  file=text)
            print('<gallery>', file=text)
            for candidate in sorted(category_dict.getlist(category),
                                    key=self.gallerysortkey):
                print(self.gallerypattern.fmt.format(r=round, c=candidate),
                      file=text)
            print('</gallery>', file=text)


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
                    if not reobj:
                        warn_lineignore('poty.parsers.candidates', line)
                        continue
                    container.add(Candidate(**reobj.groupdict('')))
                else:
                    warn_lineignore('poty.parsers.candidates', line)

    def _format(self, round, candidates, text):
        print('<gallery>', file=text)
        for candidate in sorted(candidates, key=self.gallerysortkey):
            print(self.gallerypattern.fmt.format(r=round, c=candidate),
                  file=text)
        print('</gallery>', file=text)


class FPParser(CandidatesParser):
    MONTHS = calendar.month_name[:]

    def _gettext(self, round):
        return '\n\n'.join(round.year.page(page).text for page in self.pages)

    def _parse(self, round, text, container):
        _container = set()

        ingallery = False
        curmonth = None
        for line in text.split('\n'):
            line = line.strip()

            if not line:
                continue

            if re.match(r'^{{Fp-log-chron-header\|[^{}]+}}$', line):
                assert not ingallery
            elif line == '<gallery>':
                assert not ingallery
                ingallery = True
            elif line == '</gallery>':
                assert ingallery
                ingallery = False
            else:
                if ingallery:
                    reobj = re.match(r'([^|]*?)\|(\d+) .+', line)
                    if not reobj or any(kw in line.lower()
                                        for kw in ['demote', 'delist']):
                        warn_lineignore('poty.parsers.candidates', line)
                        continue
                    if not reobj.group(1):
                        # Delinker... please remove the whole line when it's in
                        # a gallery
                        warn_lineignore('poty.parsers.candidates', line)
                        continue
                    _container.add((
                        reobj.group(1),
                        '%s-%02d/%s' % (
                            round.year, curmonth, reobj.group(2))))
                else:
                    reobj = re.match(
                        r'^== +(%s) %s +==$' % (
                            '|'.join(filter(None, self.MONTHS)), round.year),
                        line)
                    curmonth = self.MONTHS.index(reobj.group(1))

        def mapfunc(item):
            title, idstr = item
            candidate = if_redirct_get_target(
                Candidate(title))
            container.add(Candidate(
                title=candidate.title(),
                id=idstr))

        concurrent_map(mapfunc, _container)
