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

__author__ = 'xlr8or & courgette'
__version__ = '0.2'

import threading
from b3.plugins.censor import CensorPlugin


class CensorurtPlugin(CensorPlugin):

    _mute = False
    _slap = False
    _muteduration1 = 0
    _muteduration2 = 0
    _muteduration3 = 0
    _warnafter = 0

    requiresParsers = ['iourt41', 'iourt42', 'iourt43']
    loadAfterPlugins = ['chatlogger']

    _default_messages = {
        'mute_announcement': 'Muting $playername for $duration minutes',
        'pm_unmuted': '^7unmuted. watch your mouth'
    }

    ####################################################################################################################
    #                                                                                                                  #
    #    STARTUP                                                                                                       #
    #                                                                                                                  #
    ####################################################################################################################
  
    def onLoadConfig(self):
        CensorPlugin.onLoadConfig(self)
        try:
            self._mute = self.config.getboolean('urbanterror', 'mute')
        except:
            pass
        try:
            self._slap = self.config.getboolean('urbanterror', 'slap')
        except:
            pass
        try:
            self._muteduration1 = self.config.getfloat('urbanterror', 'muteduration1')
        except:
            pass
        try:
            self._muteduration2 = self.config.getfloat('urbanterror', 'muteduration2')
        except:
            pass
        try:
            self._muteduration3 = self.config.getfloat('urbanterror', 'muteduration3')
        except:
            pass
        try:
            self._warnafter = self.config.getint('urbanterror', 'warn_after')
        except:
            pass

    ####################################################################################################################
    #                                                                                                                  #
    #    OTHER METHODS                                                                                                 #
    #                                                                                                                  #
    ####################################################################################################################
      
    def penalizeClient(self, penalty, client, data=''):
        # addition to mute players in Urban Terror
        if self._slap:
            self.console.write('slap %s' % client.cid)
        if not self._mute:
            CensorPlugin.penalizeClient(self, penalty, client, data='')
        else:
            if hasattr(client, 'langMuted') and client.langMuted:
                self.debug('%s is already muted' % client.name)
            else:
                if not hasattr(client, 'langWarnings'):
                    client.langWarnings = 1
                else:
                    client.langWarnings += 1
                if client.langWarnings == 1:
                    if self._muteduration1 != 0:
                        self.debug('Muting %s for %s minutes.' % (client.name, self._muteduration1))
                        self.console.say(self.getMessage('mute_announcement',
                                                         {'playername': client.name, 'duration': self._muteduration1}))
                        self.console.write('mute %s' % client.cid)
                        client.langMuted = True
                        t = threading.Timer(self._muteduration1 * 60, self.unmutePlayer, (client,))
                        t.start()
                elif client.langWarnings == 2:
                    if self._muteduration2 != 0:
                        self.debug('Muting %s for %s minutes.' % (client.name, self._muteduration2))
                        self.console.say(self.getMessage('mute_announcement',
                                                         {'playername': client.name, 'duration': self._muteduration2}))
                        self.console.write('mute %s' % client.cid)
                        client.langMuted = True
                        t = threading.Timer(self._muteduration2 * 60, self.unmutePlayer, (client,))
                        t.start()
                else:
                    self.debug('Muting %s for %s minutes.' % (client.name, self._muteduration3))
                    self.console.say(self.getMessage('mute_announcement',
                                                     {'playername': client.name, 'duration': self._muteduration3}))
                    self.console.write('mute %s' % client.cid)
                    client.langMuted = True
                    t = threading.Timer(self._muteduration3 * 60, self.unmutePlayer, (client,))
                    t.start()

                if client.langWarnings > self._warnafter:
                    self._adminPlugin.penalizeClient(penalty.type, client, penalty.reason, penalty.keyword, penalty.duration, None, data)

    def unmutePlayer(self, client):
        if client.langMuted:
          client.langMuted = False
          # note: "/rcon mute <player> 0" ensures unmuting
          self.console.write('mute %s 0' % client.cid)
          client.message(self.getMessage('pm_unmuted'))