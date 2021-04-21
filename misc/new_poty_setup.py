#! /usr/bin/python
# -*- coding: utf-8 -*-
# LICENSE: WTFPL <http://www.wtfpl.net/txt/copying/>
# Script is really ugly and hacky; please don't [[:zh:吐槽]] ;)

from __future__ import absolute_import, unicode_literals

import datetime
import traceback

import pywikibot
from pywikibot.comms import http
from pywikibot.pagegenerators import PrefixingPageGenerator

try:
    input = raw_input
except NameError:
    pass

YEAR = datetime.datetime.now().year - 1
LAST = YEAR - 1

SITE = pywikibot.Site()


def is_translation(page):
    url = "%s/index.php?title=%s" % (SITE.scriptpath(), page.title(asUrl=True))
    return '"wgTranslatePageTranslation":"translation"' in http.request(
        SITE, url)


def setup(src):
    # print(src)
    target = pywikibot.Page(
        SITE,
        src.title().replace(str(YEAR), str(YEAR+1)).replace(str(LAST), str(YEAR))
    )
    # if target.exists(): return
    if is_translation(src):
        return
    text_o = target.text
    target.text = src.text.replace(str(YEAR), str(YEAR+1)).replace(str(LAST), str(YEAR))
    if target.text == text_o:
        return

    pywikibot.output('>>> %s <<<' % target.title())
    pywikibot.showDiff(text_o, target.text)

    while True:
        r = input('Save? [y/n] ').lower().strip()
        if r == 'n':
            return
        elif r == 'y':
            try:
                target.save('POTY %d' % YEAR)
            except Exception:
                traceback.print_exc()

            return


prefixes = [
    'Template:POTY',
    'Module:POTY',
    'Commons:Picture of the Year',
    'Commons talk:Picture of the Year',
    'Commons:POTY',
    'Category:POTY',
    'Category:Pictures of the Year',
]
forcepages = [
    'MediaWiki:Gadget-EnhancedPOTY.js',
    'MediaWiki:Gadget-POTYEnhancements.js',
    'MediaWiki:Gadget-POTYEnhancements.core.css'
    'Help:Picture of the Year',
    'MediaWiki:Abusefilter-warning-potycontact'
    # 'MediaWiki:Titleblacklist',
    # 'Special:AbuseFilter/77',
    # 'Special:AbuseFilter/96',
    # 'Special:AbuseFilter/129',
]


for prefix in prefixes:
    for page in PrefixingPageGenerator(
            prefix, includeredirects=True, site=SITE):
        if not str(LAST) in page.title():
            continue
        # 'candidates'
        if any(kw in page.title().lower()
               for kw in ['results', 'transparency', '/v/']):
            continue
        setup(page)

for page in forcepages:
    page = pywikibot.Page(SITE, page)
    setup(page)

# FIXME:
# Template:POTY%d/state to 'weAreWorking'
# Commons:Picture_of_the_Year/%s ordinal (first/second/third/etc.) & comments
# Commons:POTY/%d/VOTE
# Commons:Picture of the Year/%d/Galleries
# Commons:Picture of the Year/%d/Rules/Time/data
# Commons talk:Picture of the Year/%d
# MediaWiki:Gadget-POTYEnhancements.core.js
# Commons:Picture of the Year/%d/Candidates/Sets
# Template:POTY%d/eligibilityLink
# Commons:Picture_of_the_Year/%s/Share ordinal (first/second/third/etc.)

# FIXME: Translation setup
