# coding: utf-8
#
# Translator Plugin for BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2013 Daniele Pantaleone <fenix@bigbrotherbot.net>
# 
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.

__author__ = 'Fenix'
__version__ = '2.10'

import b3
import b3.plugin
import b3.events
import json
import re

from b3.functions import getCmd
from urllib import urlencode
from urllib2 import urlopen
from urllib2 import Request
from urllib2 import URLError


class TranslatorPlugin(b3.plugin.Plugin):
    
    adminPlugin = None
    cmdPrefix = None

    # configuration values
    settings = {
        'default_source_language': 'auto',
        'default_target_language': 'en',
        'display_translator_name': True,
        'translator_name': '^7[^1T^7]',
        'min_sentence_length': 6,
        'microsoft_client_id': None,
        'microsoft_client_secret': None
    }

    last_message_said = ''

    # available languages
    languages = {
        'ca': 'Catalan', 'cs': 'Czech', 'da': 'Danish', 'nl': 'Dutch', 'en': 'English', 'et': 'Estonian',
        'fi': 'Finnish', 'fr': 'French', 'de': 'German', 'el': 'Greek', 'ht': 'Haitian Creole', 'he': 'Hebrew',
        'hi': 'Hindi', 'hu': 'Hungarian', 'id': 'Indonesian', 'it': 'Italian', 'lv': 'Latvian', 'lt': 'Lithuanian',
        'no': 'Norwegian', 'pl': 'Polish', 'pt': 'Portuguese', 'ro': 'Romanian', 'sl': 'Slovenian', 'es': 'Spanish',
        'sv': 'Swedish', 'th': 'Thai', 'tr': 'Turkish', 'uk': 'Ukrainian'
    }

    def onLoadConfig(self):
        """
        Load the configuration file
        """
        def validate_source(x):
            """helper used to validate the source language"""
            acceptable = self.languages.keys()
            acceptable.append('auto')
            if x not in acceptable and x != 'auto':
                raise ValueError('value must be one of [%s]' % ', '.join(acceptable))
            return x

        def validate_target(x):
            """helper used to validate the target language"""
            acceptable = self.languages.keys()
            if x not in acceptable and x != 'auto':
                raise ValueError('value must be one of [%s]' % ', '.join(acceptable))
            return x

        self.settings['default_source_language'] = self.getSetting('settings', 'default_source_language', b3.STR, 'auto', validate_source)
        self.settings['default_target_language'] = self.getSetting('settings', 'default_target_language', b3.STR, 'en', validate_target)
        self.settings['display_translator_name'] = self.getSetting('settings', 'display_translator_name', b3.BOOL, True)
        self.settings['translator_name'] = self.getSetting('settings', 'translator_name', b3.STR, '^7[^1T^7]')
        self.settings['min_sentence_length'] = self.getSetting('settings', 'min_sentence_length', b3.INT, 6)
        self.settings['microsoft_client_id'] = self.getSetting('settings', 'microsoft_client_id', b3.STR)
        self.settings['microsoft_client_secret'] = self.getSetting('settings', 'microsoft_client_secret', b3.STR)

        if not self.settings['microsoft_client_id'] or not self.settings['microsoft_client_secret']:
            self.error('microsoft translator is not configured properly: disabling the plugin...')
            self.disable()

    def onStartup(self):
        """
        Initialize plugin settings
        """
        self.adminPlugin = self.console.getPlugin('admin')
        
        # register our commands
        if 'commands' in self.config.sections():
            for cmd in self.config.options('commands'):
                level = self.config.get('commands', cmd)
                sp = cmd.split('-')
                alias = None
                if len(sp) == 2: 
                    cmd, alias = sp

                func = getCmd(self, cmd)
                if func: 
                    self.adminPlugin.registerCommand(self, cmd, level, func, alias)

        self.registerEvent('EVT_CLIENT_SAY', self.onSay)
        self.registerEvent('EVT_CLIENT_TEAM_SAY', self.onSay)

        self.cmdPrefix = (self.adminPlugin.cmdPrefix, self.adminPlugin.cmdPrefixLoud,
                          self.adminPlugin.cmdPrefixBig, self.adminPlugin.cmdPrefixPrivate)

        # notice plugin startup
        self.debug('plugin started')
        
    ####################################################################################################################
    #                                                                                                                  #
    #   HANDLE EVENTS                                                                                                  #
    #                                                                                                                  #
    ####################################################################################################################

    def onEnable(self):
        """
        Executed when the plugin is enabled
        """
        if not self.settings['microsoft_client_id'] or not self.settings['microsoft_client_secret']:
            self.warning('could not enable plugin translator: microsoft translator is not configured properly')
            self.console.say('Plugin ^3Translator ^7is now ^1OFF')
            self.disable()

    def onSay(self, event):
        """
        Handle EVT_CLIENT_SAY and EVT_CLIENT_SAY_TEAM
        """
        client = event.client
        message = event.data.strip()

        # if not enough length
        if len(message) < self.settings['min_sentence_length']:
            return

        # if it's not a B3 command
        if message[0] not in self.cmdPrefix:

            # save for future use
            self.last_message_said = message

            # we have now to send a translation to all the
            # clients that enabled the automatic translation
            collection = []
            for c in self.console.clients.getList():
                if c != client and c.isvar(self, 'transauto'):
                    collection.append(c)

            if not collection:
                # no one has transauto enabled
                return

            translation = self.translate('', self.settings['default_target_language'], message)
            if not translation:
                # we didn't managed to get a valid translation
                # no need to spam the chat of everyone with a silly message
                return

            for c in collection:
                # send the translation to all the clients
                self.send_translation(c, translation)

    ####################################################################################################################
    #                                                                                                                  #
    #   OTHER METHODS                                                                                                  #
    #                                                                                                                  #
    ####################################################################################################################

    @staticmethod
    def to_byte_string(s):
        """
        Convert the given unicode string to a bytestring, using utf-8 encoding.
        If it is already a bytestring, just return the string given.
        """
        return s if isinstance(s, str) else s.encode('utf-8')

    @staticmethod
    def str_sanitize(s):
        """
        Sanitize the given string.
        Will remove color codes, XML tags and substitute unprintable characters with their alphabetical representation.
        """
        return re.sub('\^[0-9]', '', re.sub(r'<[^>]*>', '', s)).replace('ß', 'ss').replace('ü', 'ue').\
               replace('ö', 'oe').replace('ä', 'ae').replace('à', 'a').replace('è', 'e').replace('é', 'e').\
               replace('ì', 'i').replace('ò', 'o').replace('ù', 'u').replace('ç', 'c').replace('€', 'euro').\
               replace('$', 'dollar').replace('£', 'pound').replace('%', 'pc').replace('"', "''").strip()

    ####################################################################################################################
    #                                                                                                                  #
    #   TRANSLATION METHODS                                                                                            #
    #                                                                                                                  #
    ####################################################################################################################

    def get_access_token(self, client_id, client_secret):
        """
        Make an HTTP POST request to the token service, and return the access_token
        See description here: http://msdn.microsoft.com/en-us/library/hh454949.aspx
        """
        data = urlencode({
            'client_id': client_id,
            'client_secret': client_secret,
            'grant_type': 'client_credentials',
            'scope': 'http://api.microsofttranslator.com'
        })
    
        try:
            self.debug('requesting microsoft translator access token.....')
            req = Request('https://datamarket.accesscontrol.windows.net/v2/OAuth2-13')
            req.add_data(data)
            res = urlopen(req)
            rtn = json.loads(res.read())
            if 'access_token' in rtn.keys():
                return rtn['access_token']

        except (URLError, TypeError), e:
            # just print error in log and let the method return false
            # this was split into several exceptions catches but it makes no
            # sense since without the access token we are not able to translate
            self.error('could not request microsoft translator access token: %s' % e)

        return False

    def translate(self, source, target, message):
        """
        Translate the given sentence in the specified target language
        """
        try:

            self.debug('attempting to translate message -> %s : %s' % (target, message))
            token = self.get_access_token(self.settings['microsoft_client_id'],
                                          self.settings['microsoft_client_secret'])
        
            if not token:
                return None
            
            data = {'text': self.to_byte_string(message), 'to': target}
            
            if source != 'auto' and source != '':
                data['from'] = source

            # getting the translation
            req = Request('http://api.microsofttranslator.com/v2/Http.svc/Translate?' + urlencode(data))
            req.add_header('Authorization', 'Bearer ' + token)
            res = urlopen(req)
            rtn = res.read()
            
            # formatting the string
            msg = self.str_sanitize(rtn)
            if not msg:
                self.debug('could not translate message (%s): empty string returned' % message)
                return None

            # print as verbose not to spam too many log lines in debug configuration
            self.verbose('message translated [ source <%s> : %s | result <%s> : %s ]' % (source, message, target, msg))
            return msg

        except (URLError, TypeError), e:
            self.error('could not translate message (%s): %s' % e)
            return None

    def send_translation(self, client, message, cmd=None):
        """
        Send a translated message to a client
        """
        # prepend translator name if specified
        if self.settings['display_translator_name']:
            message = '%s %s' % (self.settings['translator_name'], message)

        if not cmd:
            client.message(message)
            return

        cmd.sayLoudOrPM(client, message)

    ####################################################################################################################
    #                                                                                                                  #
    #   COMMANDS                                                                                                       #
    #                                                                                                                  #
    ####################################################################################################################

    def cmd_translate(self, data, client, cmd=None):
        """
        [<source>]*[<target>] <message> - translate a message
        """
        if not data: 
            client.message('^7missing data, try ^3!^7help translate')
            return

        src = self.settings['default_source_language']
        tar = self.settings['default_target_language']

        if '*' in data:

            # language codes specified for this translation
            r = re.compile(r'''^(?P<source>\w*)[*]?(?P<target>\w*)\s*(?P<message>.+)$''')
            m = r.match(data)
            if not m:
                client.message('^7invalid data, try ^3!^7help translate')
                return

            source = m.group('source').strip()
            target = m.group('target').strip()

            if source and source != 'auto':
                if source not in self.languages:
                    self.verbose('invalid source language (%s) specified in !translate command: unable to translate' % source)
                    client.message('^7invalid ^1source ^7language specified, try ^3!^7translang')
                    return
                # use the given source language code
                src = source

            if target:
                if target not in self.languages:
                    self.verbose('invalid target language (%s) specified in !translate command: unable to translate' % target)
                    client.message('^7invalid ^1target ^7language specified, try ^3!^7translang')
                    return
                # use the given target language code
                tar = target

            # get the real message to be translated
            data = m.group('message')

        translation = self.translate(src, tar, data)
        if not translation:
            client.message('^7unable to translate')
            return

        # send the translation to the given client
        self.send_translation(client, translation, cmd)

    def cmd_translast(self, data, client, cmd=None):
        """
        [<target>] - translate the last available sentence from the chat
        """
        if not self.last_message_said:
            client.message('^7unable to translate')
            return

        # set default target language
        tar = self.settings['default_target_language']

        if data:
            if data not in self.languages:
                self.verbose('invalid target language (%s) specified in !translast command: unable to translate' % data)
                client.message('^7Invalid ^1target ^7language specified, try ^3!^7translang')
                return

            # use the provided language code
            tar = data

        message = self.translate('', tar, self.last_message_said)
        if not message:
            client.message('^7unable to translate')
            return

        # send the translation to the given client
        self.send_translation(client, message, cmd)
    
    def cmd_transauto(self, data, client, cmd=None):
        """
        <on|off> - turn on/off the automatic translation
        """
        if not data: 
            client.message('^7missing data, try ^3!^7help transauto')
            return

        data = data.lower()
        if data not in ('on', 'off'):
            client.message('invalid data, try ^3!^7help transauto')
            return

        if data == 'on':
            client.setvar(self, 'transauto', True)
            client.message('^7Transauto: ^2ON')
        elif data == 'off':
            client.delvar(self, 'transauto')
            client.message('^7Transauto: ^1OFF')

    def cmd_translang(self, data, client, cmd=None):
        """
        Display the list of available language codes
        """
        codes = []
        for k, v in self.languages.items():
            codes.append('^2%s^7:%s' % (k, v))

        cmd.sayLoudOrPM(client, '^7Languages: %s' % ', '.join(codes))