import collections
import re
import traceback

import pywikibot
import pywikibot.pagegenerators

PREV_YEAR = '2019'
CUR_YEAR = '2020'

pywikibot.config.put_throttle = 0

SITE = pywikibot.Site()

prefixes = [
    'Translations:Commons:Picture_of_the_Year/{}/',
    'Translations:Template:POTY{}/',
]

old_pages_data = collections.defaultdict(lambda: collections.defaultdict(dict))

for prefix in prefixes:
    old_pg_gen = pywikibot.pagegenerators.PrefixingPageGenerator(prefix.format(PREV_YEAR), site=SITE)
    old_pg_gen = pywikibot.pagegenerators.PreloadingGenerator(old_pg_gen)

    for old_page in old_pg_gen:
        reobj = re.match(r'^Translations:(.+)/(\d+|Page display title)/([a-z-]+)$', old_page.title())
        if reobj is None:
            raise AssertionError(old_page.title())

        sourcepage, group, lang = reobj.groups()

        old_pages_data[sourcepage][group][lang] = old_page


for prefix in prefixes:
    new_pg_gen = pywikibot.pagegenerators.PrefixingPageGenerator(prefix.format(CUR_YEAR), site=SITE)
    for new_page in new_pg_gen:
        reobj = re.match(r'^Translations:(.+)/(\d+|Page display title)/([a-z-]+)$', new_page.title())

        sourcepage, group, lang = reobj.groups()
        if lang != 'en':
            continue

        year_fix = False
        old_page_groups = old_pages_data[sourcepage.replace(CUR_YEAR, PREV_YEAR)]

        for old_group, langdict in old_page_groups.items():
            if langdict['en'].text == new_page.text:
                break
        else:
            if CUR_YEAR not in new_page.text:
                continue

            for old_group, langdict in old_page_groups.items():
                if langdict['en'].text == new_page.text.replace(CUR_YEAR, PREV_YEAR):
                    year_fix = True
                    break
            else:
                continue

        for lang, translation in langdict.items():
            new_title = 'Translations:{}/{}/{}'.format(sourcepage, group, lang)
            new_page = pywikibot.Page(SITE, new_title)

            if new_page.exists():
                continue

            if year_fix:
                if PREV_YEAR not in translation.text:
                    continue

                new_page.text = translation.text.replace(PREV_YEAR, CUR_YEAR)
            else:
                new_page.text = translation.text

            print(new_page, new_page.text)
            try:
                new_page.save(summary='Copying translations from {}, original was at [[{}]]'.format(PREV_YEAR, translation.title()))
            except pywikibot.Error:
                traceback.print_exc()
