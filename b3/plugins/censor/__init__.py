# -*- coding: utf-8 -*-

# ################################################################### #
#                                                                     #
#  BigBrotherBot(B3) (www.bigbrotherbot.net)                          #
#  Copyright (C) 2005 Michael "ThorN" Thornton                        #
#                                                                     #
#  This program is free software; you can redistribute it and/or      #
#  modify it under the terms of the GNU General Public License        #
#  as published by the Free Software Foundation; either version 2     #
#  of the License, or (at your option) any later version.             #
#                                                                     #
#  This program is distributed in the hope that it will be useful,    #
#  but WITHOUT ANY WARRANTY; without even the implied warranty of     #
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the       #
#  GNU General Public License for more details.                       #
#                                                                     #
#  You should have received a copy of the GNU General Public License  #
#  along with this program; if not, write to the Free Software        #
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA      #
#  02110-1301, USA.                                                   #
#                                                                     #
# ################################################################### #

__author__ = 'ThorN, xlr8or, Bravo17, Courgette'
__version__ = '3.3'

import b3
import re
import traceback
import sys
import threading
import b3.events
import b3.plugin

from b3.config import XmlConfigParser
from b3 import functions
from ConfigParser import NoOptionError


class PenaltyData:

    type = None
    reason = None
    keyword = None
    duration = 0

    def __init__(self, **kwargs):
        for k, v in kwargs.iteritems():
            setattr(self, k, v)

    def __repr__(self):
        return """Penalty(type=%r, reason=%r, keyword=%r, duration=%r)""" % (self.type, self.reason,
                                                                             self.keyword, self.duration)

    def __str__(self):
        data = {"type": self.type, "reason": self.reason, "reasonkeyword": self.keyword, "duration": self.duration}
        return "<penalty " + ' '.join(['%s="%s"' % (k, v) for k, v in data.items() if v]) + " />"


class CensorData:

    name = None
    penalty = None
    regexp = None

    def __init__(self, **kwargs):
        for k, v in kwargs.iteritems():
            setattr(self, k, v)

    def __repr__(self):
        return """CensorData(name=%r, penalty=%r, regexp=%r)""" % (self.name, self.penalty, self.regexp)


class CensorPlugin(b3.plugin.Plugin):

    _adminPlugin = None
    _reClean = re.compile(r'[^0-9a-z ]+', re.I)
    _defaultBadWordPenalty = PenaltyData(type="warning", keyword="cuss")
    _defaultBadNamePenalty = PenaltyData(type="warning", keyword="badname")
    _maxLevel = 0
    _ignoreLength = 3
    _badWords = None
    _badNames = None

    loadAfterPlugins = ['chatlogger']

    ####################################################################################################################
    #                                                                                                                  #
    #    STARTUP                                                                                                       #
    #                                                                                                                  #
    ####################################################################################################################

    def onStartup(self):
        """
        Initialize plugin
        """
        self._adminPlugin = self.console.getPlugin('admin')

        self.registerEvent('EVT_CLIENT_SAY')
        self.registerEvent('EVT_CLIENT_TEAM_SAY')
        self.registerEvent('EVT_CLIENT_NAME_CHANGE')
        self.registerEvent('EVT_CLIENT_AUTH')

    def onLoadConfig(self):
        """
        Load plugin configuration.
        """
        assert isinstance(self.config, XmlConfigParser)

        try:
            self._maxLevel = self.config.getint('settings', 'max_level')
            self.debug('loaded settings/max_level: %s' % self._maxLevel)
        except NoOptionError:
            self.warning('could not find settings/max_level in config file, '
                         'using default: %s' % self._maxLevel)
        except ValueError, e:
            self.error('could not load settings/max_level config value: %s' % e)
            self.debug('using default value (%s) for settings/max_level' % self._maxLevel)

        try:
            self._ignoreLength = self.config.getint('settings', 'ignore_length')
            self.debug('loaded settings/ignore_length: %s' % self._ignoreLength)
        except NoOptionError:
            self.warning('could not find settings/ignore_length in config file, '
                         'using default: %s' % self._ignoreLength)
        except ValueError, e:
            self.error('could not load settings/ignore_length config value: %s' % e)
            self.debug('using default value (%s) for settings/ignore_length' % self._ignoreLength)

        default_badwords_penalty_nodes = self.config.get('badwords/penalty')
        if len(default_badwords_penalty_nodes):
            penalty = default_badwords_penalty_nodes[0]
            self._defaultBadWordPenalty = PenaltyData(type=penalty.get('type'),
                                                      reason=penalty.get('reason'),
                                                      keyword=penalty.get('reasonkeyword'),
                                                      duration=functions.time2minutes(penalty.get('duration')))
        else:
            self.warning('no default badwords penalty found in configuration file: '
                         'using default (%s)' % self._defaultBadNamePenalty)

        default_badnames_penalty_nodes = self.config.get('badnames/penalty')
        if len(default_badnames_penalty_nodes):
            penalty = default_badnames_penalty_nodes[0]
            self._defaultBadNamePenalty = PenaltyData(type=penalty.get('type'),
                                                      reason=penalty.get('reason'),
                                                      keyword=penalty.get('reasonkeyword'),
                                                      duration=functions.time2minutes(penalty.get('duration')))
        else:
            self.warning('no default badnames penalty found in configuration file: '
                         'using default (%s)' % self._defaultBadNamePenalty)

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
        """
        Add a badword to be rule.
        :param rulename: The name of the badword
        :param penalty: The penalty to apply
        :param word: The word to match
        :param regexp: The regex to match
        """
        if word is None and regexp is None:
            self.warning("badword rule [%s] has no word and no regular expression to search for" % rulename)
        elif word is not None and regexp is not None:
            self.warning("badword rule [%s] cannot have both a word and regular expression to search for" % rulename)
        elif regexp is not None:
            # has a regular expression
            self._badWords.append(self._get_censor_data(rulename, regexp.strip(), penalty, self._defaultBadWordPenalty))
            self.debug("badword rule '%s' loaded" % rulename)
        elif word is not None:
            # has a plain word
            self._badWords.append(self._get_censor_data(rulename, '\\s' + word.strip() + '\\s',
                                                        penalty, self._defaultBadWordPenalty))
            self.debug("badword rule '%s' loaded" % rulename)

    def _add_bad_name(self, rulename, penalty=None, word=None, regexp=None):
        """
        Add a badname to be censored.
        :param rulename: The name of the rule
        :param penalty: The penalty to apply
        :param word: The word to match
        :param regexp: The regex to match
        """
        if word is None and regexp is None:
            self.warning("badname rule [%s] has no word and no regular expression to search for" % rulename)
        elif word is not None and regexp is not None:
            self.warning("badname rule [%s] cannot have both a word and regular expression to search for" % rulename)
        elif regexp is not None:
            # has a regular expression
            self._badNames.append(self._get_censor_data(rulename, regexp.strip(), penalty, self._defaultBadNamePenalty))
            self.debug("badname rule '%s' loaded" % rulename)
        elif word is not None:
            # has a plain word
            self._badNames.append(self._get_censor_data(rulename, '\\s' + word.strip() + '\\s',
                                                        penalty, self._defaultBadNamePenalty))
            self.debug("badname rule '%s' loaded" % rulename)

    def _get_censor_data(self, name, regexp, penalty, default):
        try:
            regexp = re.compile(regexp, re.IGNORECASE)
        except re.error:
            self.error('invalid regular expression: %s - %s' % (name, regexp))
            raise

        if penalty is not None:
            pd = PenaltyData(type=penalty.get('type'),
                             reason=penalty.get('reason'),
                             keyword=penalty.get('reasonkeyword'),
                             duration=functions.time2minutes(penalty.get('duration')))
        else:
            pd = default

        return CensorData(name=name, penalty=pd, regexp=regexp)

    ####################################################################################################################
    #                                                                                                                  #
    #    OTHER METHODS                                                                                                 #
    #                                                                                                                  #
    ####################################################################################################################

    def onEvent(self, event):
        """
        Handle intercepted events
        """
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

            if event.type == self.console.getEventID('EVT_CLIENT_AUTH') or \
               event.type == self.console.getEventID('EVT_CLIENT_NAME_CHANGE'):
                self.checkBadName(event.client)

            elif len(event.data) > self._ignoreLength:
                if event.type == self.console.getEventID('EVT_CLIENT_SAY') or \
                   event.type == self.console.getEventID('EVT_CLIENT_TEAM_SAY'):
                    self.checkBadWord(event.data, event.client)

        except b3.events.VetoEvent:
            raise
        except Exception, msg:
            self.error('censor plugin error: %s - %s', msg, traceback.extract_tb(sys.exc_info()[2]))

    def penalizeClient(self, penalty, client, data=''):
        """
        This is the default penalization for using bad language in say and teamsay
        """
        # fix for reason keyword not working
        if penalty.keyword is None:
            penalty.keyword = penalty.reason
        self._adminPlugin.penalizeClient(penalty.type, client, penalty.reason,
                                         penalty.keyword, penalty.duration, None, data)

    def penalizeClientBadname(self, penalty, client, data=''):
        """
        This is the penalization for bad names
        """
        # self.debug("%s"%((penalty.type, penalty.reason, penalty.keyword, penalty.duration),))
        self._adminPlugin.penalizeClient(penalty.type, client, penalty.reason,
                                         penalty.keyword, penalty.duration, None, data)

    def checkBadName(self, client):
        """
        Check a client for a badname
        :param client: The client to check
        """
        if not client.connected:
            self.debug('client not connected')
            return

        cleaned_name = ' ' + self.clean(client.exactName) + ' '
        self.info("checking '%s'=>'%s' for badname" % (client.exactName, cleaned_name))

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
        """
        Check a if a client said a badword
        :param text: The said message
        :param client: The client to check
        """
        cleaned = ' ' + self.clean(text) + ' '
        text = ' ' + text + ' '
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