#
# BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2005 Michael "ThorN" Thornton
# 
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
# CHANGELOG
#    2011/12/26 - 3.0 - Courgette
#       Refactor and make the checks on raw text before checks on cleaned text. Add tests
#    2/12/2011 - 2.2.2 - Bravo17
#       Fix for reason keyword not working
#    1/16/2010 - 2.2.1 - xlr8or
#       Plugin can now be disabled with !disable censor
#    1/16/2010 - 2.2.0 - xlr8or
#       Added ignore_length as an optional configurable option
#       Started debugging the badname checker
#    8/13/2005 - 2.0.0 - ThorN
#       Converted to use XML config
#       Allow custom penalties for words and names
#    7/23/2005 - 1.1.0 - ThorN
#       Added data column to penalties table
#       Put censored message/name in the warning data

__author__  = 'ThorN'
__version__ = '3.0'

import b3, re, traceback, sys, threading
import b3.events
import b3.plugin
from b3 import functions

class PenaltyData:
    def __init__(self, **kwargs):
        for k, v in kwargs.iteritems():
            setattr(self, k, v)

    type = None
    reason = None
    keyword = None
    duration = 0

class CensorData:
    def __init__(self, **kwargs):
        for k, v in kwargs.iteritems():
            setattr(self, k, v)

    name = None
    penalty = None
    regexp = None

#--------------------------------------------------------------------------------------------------
class CensorPlugin(b3.plugin.Plugin):
    _adminPlugin = None
    _reClean = re.compile(r'[^0-9a-z ]+', re.I)
    _defaultBadWordPenalty = None
    _defaultBadNamePenalty = None
    _maxLevel = 0
    _ignoreLength = 3

    def onStartup(self):
        self._adminPlugin = self.console.getPlugin('admin')
        if not self._adminPlugin:
            return False

        self.registerEvent(b3.events.EVT_CLIENT_SAY)
        self.registerEvent(b3.events.EVT_CLIENT_TEAM_SAY)
        self.registerEvent(b3.events.EVT_CLIENT_NAME_CHANGE)
        self.registerEvent(b3.events.EVT_CLIENT_AUTH)


    def onLoadConfig(self):
        try:
            self._maxLevel = self.config.getint('settings', 'max_level')
        except:
            self._maxLevel = 0
        try:
            self._ignoreLength = self.config.getint('settings', 'ignore_length')
        except:
            self._ignoreLength = 3

        penalty = self.config.get('badwords/penalty')[0]

        self._defaultBadWordPenalty = PenaltyData(type = penalty.get('type'),
                            reason = penalty.get('reason'),
                            keyword = penalty.get('reasonkeyword'),
                            duration = functions.time2minutes(penalty.get('duration')))

        penalty = self.config.get('badnames/penalty')[0]

        self._defaultBadNamePenalty = PenaltyData(type = penalty.get('type'),
                            reason = penalty.get('reason'),
                            keyword = penalty.get('reasonkeyword'),
                            duration = functions.time2minutes(penalty.get('duration')))

        # load bad words into memory
        self._badWords = []
        for e in self.config.get('badwords/badword'):
            penalty_node = e.find('penalty')
            word_node = e.find('word')
            regexp_node = e.find('regexp')
            self._add_bad_word(rulename=e.get('name'),
                penalty=penalty_node,
                word=word_node.text if word_node is not None else None,
                regexp=regexp_node.text if regexp_node is not None else None)

        # load bad names into memory
        self._badNames = []
        for e in self.config.get('badnames/badname'):
            penalty_node = e.find('penalty')
            word_node = e.find('word')
            regexp_node = e.find('regexp')
            self._add_bad_name(rulename=e.get('name'),
                penalty=penalty_node,
                word=word_node.text if word_node is not None else None,
                regexp=regexp_node.text if regexp_node is not None else None)


    def _add_bad_word(self, rulename, penalty=None, word=None, regexp=None):
        if word is regexp is None:
            self.warning("badword rule [%s] has no word and no regular expression to search for" % rulename)
        elif word is not None and regexp is not None:
            self.warning("badword rule [%s] cannot have both a word and regular expression to search for" % rulename)
        elif regexp is not None:
            # has a regular expression
            self._badWords.append(self._getCensorData(rulename, regexp.strip(), penalty, self._defaultBadWordPenalty))
            self.debug("badword rule '%s' loaded" % rulename)
        elif word is not None:
            # has a plain word
            self._badWords.append(self._getCensorData(rulename, '\\s' + word.strip() + '\\s', penalty, self._defaultBadWordPenalty))
            self.debug("badword rule '%s' loaded" % rulename)

    def _add_bad_name(self, rulename, penalty=None, word=None, regexp=None):
        if word is regexp is None:
            self.warning("badname rule [%s] has no word and no regular expression to search for" % rulename)
        elif word is not None and regexp is not None:
            self.warning("badname rule [%s] cannot have both a word and regular expression to search for" % rulename)
        elif regexp is not None:
            # has a regular expression
            self._badNames.append(self._getCensorData(rulename, regexp.strip(), penalty, self._defaultBadNamePenalty))
            self.debug("badname rule '%s' loaded" % rulename)
        elif word is not None:
            # has a plain word
            self._badNames.append(self._getCensorData(rulename, '\\s' + word.strip() + '\\s', penalty, self._defaultBadNamePenalty))
            self.debug("badname rule '%s' loaded" % rulename)

    def _getCensorData(self, name, regexp, penalty, defaultPenalty):
        try:
            regexp = re.compile(regexp, re.I)
        except re.error, e:
            self.error('Invalid regular expression: %s - %s' % (name, regexp))
            raise

        if penalty is not None:
            pd = PenaltyData(type = penalty.get('type'),
                            reason = penalty.get('reason'),
                            keyword = penalty.get('reasonkeyword'),
                            duration = functions.time2minutes(penalty.get('duration')))
        else:
            pd = defaultPenalty

        return CensorData(name=name, penalty=pd, regexp=regexp)


    def onEvent(self, event):
        try:
            if not self.isEnabled():
                return
            elif not event.client:
                return
            elif event.client.cid is None:
                return
            elif event.client.maxLevel > self._maxLevel:
                return
            elif not event.client.connected:
                return

            if event.type == b3.events.EVT_CLIENT_AUTH or event.type == b3.events.EVT_CLIENT_NAME_CHANGE:
                self.checkBadName(event.client)

            elif len(event.data) > self._ignoreLength:
                if event.type == b3.events.EVT_CLIENT_SAY or \
                   event.type == b3.events.EVT_CLIENT_TEAM_SAY:
                    self.checkBadWord(event.data, event.client)


        except b3.events.VetoEvent:
            raise
        except Exception, msg:
            self.error('Censor plugin error: %s - %s', msg, traceback.extract_tb(sys.exc_info()[2]))

    def penalizeClient(self, penalty, client, data=''):
        """\
        This is the default penalisation for using bad language in say and teamsay
        """
        #self.debug("%s"%((penalty.type, penalty.reason, penalty.keyword, penalty.duration),))
        # fix for reason keyword not working
        if penalty.keyword is None:
            penalty.keyword = penalty.reason
        self._adminPlugin.penalizeClient(penalty.type, client, penalty.reason, penalty.keyword, penalty.duration, None, data)

    def penalizeClientBadname(self, penalty, client, data=''):
        """\
        This is the penalisation for bad names
        """
        #self.debug("%s"%((penalty.type, penalty.reason, penalty.keyword, penalty.duration),))
        self._adminPlugin.penalizeClient(penalty.type, client, penalty.reason, penalty.keyword, penalty.duration, None, data)

    def checkBadName(self, client):
        if not client.connected:
            self.debug('Client not connected?')
            return

        cleaned_name = ' ' + self.clean(client.exactName) + ' '
        self.info("Checking '%s'=>'%s' for badname" % (client.exactName, cleaned_name))

        was_penalized = False

        for w in self._badNames:
            if w.regexp.search(client.exactName):
                self.debug("badname rule [%s] matches '%s'" % (w.name, client.exactName))
                self.penalizeClientBadname(w.penalty, client, '%s (rule %s)' % (client.exactName, w.name))
                was_penalized = True
                break
            if w.regexp.search(cleaned_name):
                self.debug("badname rule [%s] matches cleaned name '%s' for player '%s'" % (w.name, cleaned_name, client.exactName))
                self.penalizeClientBadname(w.penalty, client, '%s (rule %s)' % (client.exactName, w.name))
                was_penalized = True
                break

        if was_penalized:
            # check again in 1 minute
            t = threading.Timer(60, self.checkBadName, (client,))
            t.start()
            return

    def checkBadWord(self, text, client):
        cleaned = ' ' + self.clean(text) + ' '
        self.debug("cleaned text: [%s]" % cleaned)
        for w in self._badWords:
            if w.regexp.search(text):
                self.debug("badword rule [%s] matches '%s'" % (w.name, text))
                self.penalizeClient(w.penalty, client, text)
                raise b3.events.VetoEvent
            if w.regexp.search(cleaned):
                self.debug("badword rule [%s] matches cleaned text '%s'" % (w.name, cleaned))
                self.penalizeClient(w.penalty, client, '%s => %s' % (text, cleaned))
                raise b3.events.VetoEvent


    def clean(self, data):
        return re.sub(self._reClean, ' ', self.console.stripColors(data.lower()))
    

    