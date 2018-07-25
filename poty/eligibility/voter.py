#! /usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import collections
import logging

import pywikibot

from poty.sites import COMMONS

logger = logging.getLogger('poty.eligibility.voter')


def _get_voter(username, eligibility_dict):
    voter = pywikibot.User(COMMONS, username)
    sul = COMMONS._simple_request(
        action='query',
        meta='globaluserinfo',
        guiprop='merged',
        guiuser=voter.username
    ).submit()
    try:
        sul = sul['query']['globaluserinfo']['merged']
    except KeyError:
        newusername = eligibility_dict['possiblerenames'][voter.username]
        logger.warn('Following rename "%s" -> "%s"' % (username, newusername))
        return get_voter(newusername, eligibility_dict)

    sul = sorted(sul, key=lambda item: item['editcount'], reverse=True)

    eligible_register = eligible_edits = False
    for sulentry in sul:
        eligible_register = eligible_register or (
            min(
                pywikibot.Timestamp.fromISOformat(sulentry['registration']),
                pywikibot.Timestamp.fromISOformat(sulentry['timestamp'])
            ) < eligibility_dict['register']['before'])
        if not eligible_edits:
            # Being lazy
            if sulentry['editcount'] >= eligibility_dict['edits']['atleast']:
                try:
                    sul_site = COMMONS.fromDBName(sulentry['wiki'])
                except pywikibot.exceptions.UnknownFamily:
                    pywikibot.exception(
                        'Failed to get Site object for {}, skipping'.format(
                            sulentry['wiki']))
                    continue
                if eligibility_dict['edits']['includedeleted']:
                    raise NotImplementedError(
                        'counting deleted edits is not implemented')
                else:
                    contribs = sul_site.usercontribs(
                        voter.username,
                        start=eligibility_dict['edits']['before'],
                        total=eligibility_dict['edits']['atleast']
                    )
                    eligible_edits = (len(list(contribs)) >=
                                      eligibility_dict['edits']['atleast'])

        if eligible_register and eligible_edits:
            # logger.warn('[[User:{}]]: eligible'.format(voter.username))
            return voter

    return None


_cache = collections.defaultdict(dict)


def get_voter(username, eligibility_dict):
    if username in _cache[eligibility_dict]:
        return _cache[eligibility_dict][username]

    voter = _get_voter(username, eligibility_dict)
    _cache[eligibility_dict][username] = voter

    logger.warn('[[User:{s}]]: {cond}eligible'.format(
        s=username,
        cond='' if voter else 'in'
    ))

    return voter
