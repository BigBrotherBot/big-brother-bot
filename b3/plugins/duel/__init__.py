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

__author__  = 'Courgette'
__version__ = '1.2'


import b3
import b3.clients
import b3.events
import b3.plugin


class DuelPlugin(b3.plugin.Plugin):

    adminPlugin = None
    requiresConfigFile = False

    ####################################################################################################################
    #                                                                                                                  #
    #   PLUGIN STARTUP                                                                                                 #
    #                                                                                                                  #
    ####################################################################################################################

    def onStartup(self):
        """
        Initialize the plugin.
        """
        self.adminPlugin = self.console.getPlugin('admin')
        if not self.adminPlugin:
            raise AttributeError('could not get admin plugin')

        # register the events needed
        self.registerEvent('EVT_CLIENT_KILL', self.onKill)
        self.registerEvent('EVT_CLIENT_DISCONNECT', self.onDisconnect)
        self.registerEvent('EVT_GAME_ROUND_END', self.onRoundEnd)

        # register our commands
        self.adminPlugin.registerCommand(self, 'duel', 1, self.cmd_duel)
        self.adminPlugin.registerCommand(self, 'duelreset', 1, self.cmd_duelreset)
        self.adminPlugin.registerCommand(self, 'duelcancel', 1, self.cmd_duelcancel)

    ####################################################################################################################
    #                                                                                                                  #
    #   HANLE EVENTS                                                                                                   #
    #                                                                                                                  #
    ####################################################################################################################

    def onKill(self, event):
        """
        Executed when EVT_CLIENT_KILL is received.
        """
        if event.client and event.client.isvar(self, 'duelling'):
            duels = event.client.var(self, 'duelling', {}).value
            for duel in duels.values():
                if (duel.clientA == event.client and duel.clientB == event.target) or \
                    (duel.clientB == event.client and duel.clientA == event.target):
                    duel.registerKillEvent(event)

    def onDisconnect(self, event):
        """
        Executed when EVT_CLIENT_DISCONNECT is received.
        """
        if event.client.isvar(self, 'duelling'):
            self.debug('client disconnecting : %r' % event.client)
            for c in self.console.clients.getList():
                duels = c.var(self, 'duelling', {}).value
                for duel in duels.values():
                    if duel.clientA == event.client or duel.clientB == event.client:
                        duel.announceScoreTo(duel.clientA)
                        duel.announceScoreTo(duel.clientB)
                        self.cancelDuel(duel)
    
    def onRoundEnd(self, _):
        """
        Executed when EVT_GAME_ROUND_END is received.
        """
        for c in self.console.clients.getList():
            if c.isvar(self, 'duelling'):
                self.showDuelsScoresTo(c)

    ####################################################################################################################
    #                                                                                                                  #
    #   OTHER METHODS                                                                                                  #
    #                                                                                                                  #
    ####################################################################################################################

    def cancelDuel(self, duel):
        """
        Will remove references to this duel in both players instances.
        :param duel: Duel instance
        """
        self.debug('canceling duel: %r' % duel)
        clientA = duel.clientA
        clientB = duel.clientB
        if clientA:
            try:
                duelsA = clientA.var(self, 'duelling', {}).value
                del duelsA[clientB]
                self.debug('removed ref to duel %s from player %s' % (id(duel), clientA.name))
                clientA.message('^7Duel with %s ^7canceled' % clientB.exactName)
            except KeyError:
                pass
        if clientB:
            try:
                duelsB = clientB.var(self, 'duelling', {}).value
                del duelsB[clientA]
                self.debug('removed ref to duel %s from player %s' % (id(duel), clientB.name))
                clientB.message('^7Duel with %s ^7canceled' % clientA.exactName)
            except KeyError:
                pass

    def showDuelsScoresTo(self, client):
        """
        Announce duel scores to the given client.
        :param client: the client we want to notice Duel scores.
        """
        duels = client.var(self, 'duelling', {}).value
        for duel in duels.values():
            duel.announceScoreTo(client)

    ####################################################################################################################
    #                                                                                                                  #
    #   COMMANDS                                                                                                       #
    #                                                                                                                  #
    ####################################################################################################################

    def cmd_duelcancel(self, data, client, _):
        """
        [<name>] - cancel a duel you started
        """
        duels = client.var(self, 'duelling', {}).value
        if len(duels) == 0:
            client.message('You have no duel in progress: nothing to cancel!')
            return

        x = self.adminPlugin.parseUserCmd(data)
        if not x:
            if len(duels) == 1:
                self.cancelDuel(duels.values()[0])
            else:
                client.message('^7You have ^3%s ^7duels running, type ^3!^7duelcancel <name>' % len(duels))
        else:
            # x[0] is the player you challenge
            opponent = self.adminPlugin.findClientPrompt(x[0], client)
            if not opponent:
                # a player matching the name was not found, a list of closest matches will be displayed
                # we can exit here and the user will retry with a more specific player
                return

            if opponent not in duels:
                client.message('^7You have no duel with %s^7: cannot cancel!' % opponent.exactName)
            else:
                self.cancelDuel(duels[opponent])
                
    def cmd_duelreset(self, data, client, _):
        """
        [<name>] - reset scores for a duel you started
        """
        duels = client.var(self, 'duelling', {}).value
        if len(duels) == 0:
            client.message('You have no duel in progress: nothing to reset!')
            return

        x = self.adminPlugin.parseUserCmd(data)
        if not x:
            if len(duels) == 1:
                duels.values()[0].resetScores()
            else:
                client.message('^7You have ^3%s ^7duels running, type ^3!^7duelreset <name>' % len(duels))
        else:
            # x[0] is the player you challenge
            opponent = self.adminPlugin.findClientPrompt(x[0], client)
            if not opponent:
                # a player matching the name was not found, a list of closest matches will be displayed
                # we can exit here and the user will retry with a more specific player
                return

            if opponent not in duels:
                client.message('^7You have no duel with %s^7: cannot reset!' % opponent.exactName)
            else:
                duels[opponent].resetScores()

    def cmd_duel(self, data, client, _):
        """
        <name> - challenge a player for a duel or accept a duel
        """
        x = self.adminPlugin.parseUserCmd(data)
        if not x:
            client.message('^7Invalid data, try ^3!^7help duel')
            return

        # x[0] is the player you challenge
        opponent = self.adminPlugin.findClientPrompt(x[0], client)
        if not opponent:
            # a player matching the name was not found, a list of closest matches will be displayed
            # we can exit here and the user will retry with a more specific player
            return

        if client == opponent:
            client.message('^7You cannot duel yourself!')
            return

        client_duels = client.var(self, 'duelling', {}).value
        opponent_duels = opponent.var(self, 'duelling', {}).value
        if client not in opponent_duels and opponent not in client_duels:
            # no duel exists between those two: creating duel
            client_duels[opponent] = Duel(client, opponent)
            client.message('Duel proposed to %s' % opponent.exactName)
        elif client in opponent_duels:
            # we are accepting a duel
            duel = opponent_duels[client]
            duel.acceptDuel()
            client_duels[opponent] = duel
        elif opponent in client_duels:
            # duel already exists but only on our side
            client.message('^You suggested a duel to %s' % opponent.exactName)
            opponent.message('%s ^7is challenging you in a duel: '
                             'type ^3!^7duel %s to start duelling' % (client.exactName, client.name))


########################################################################################################################
#                                                                                                                      #
#   DUEL DEDICATED CODE                                                                                                #
#                                                                                                                      #
########################################################################################################################


class DuelError(Exception):
    """raised whenever an error occurs in a Duel"""
    pass


class Duel(object):
    """
    How does it work ?
    
    - player A challenges player B
        * player B is notified
    - player B accept challenge from player A
        * players A and B get notified that the duel stated
        
    - on each kill of player A or B
        * players A and B get notified of the current duel score
        
    - on round end
        * players A and B get notified of the duel score
        * players A and B get reminded to type duelreset to set scores back to 0
    
    - on player A or B disconnection
        * the other player get notified of the duel score
    """

    STATUS_WAITING_AGREEMENT = 0         # challenge proposed, waiting for agreement
    STATUS_STARTED = 1                   # both players agreed to duel
    clientA = None                       # the player who propose the duel
    clientB = None                       # the player who accept the duel
    scores = {}                          # duel scores
    status = STATUS_WAITING_AGREEMENT    # current duel status
    
    def __init__(self, clientA, clientB):
        """
        Initialize the Duel instance
        :param clientA: the client who proposed the duel
        :param clientB: the client who accepted the duel
        """
        if not isinstance(clientA, b3.clients.Client):
            raise DuelError('clientA is not a client')
        if not isinstance(clientB, b3.clients.Client):
            raise DuelError('opponent is not a client')
        if not clientA.connected:
            raise DuelError('clientA is not connected')
        if not clientB.connected:
            raise DuelError('opponent is not connected')
        if clientA == clientB:
            raise DuelError('you cannot challenge yourself')
        self.clientA = clientA
        self.clientB = clientB
        self.scores = {clientA: 0, clientB: 0}
        self.clientB.message('%s ^7proposes a duel: '
                             'to accept type ^3!^7duel %s' % (self.clientA.exactName, self.clientA.name.lower()))
    
    def acceptDuel(self):
        """
        Accept a proposed duel.
        """
        self.status = Duel.STATUS_STARTED
        self.clientA.message('%s^7 is now duelling with you' % self.clientB.exactName)
        self.clientB.message('^7You accepted %s^7\'s duel' % self.clientA.exactName)
        self.resetScores()
    
    def resetScores(self):
        """
        Reset current duel scores and announce them.
        """
        self.scores = {self.clientA: 0, self.clientB: 0}
        self.announceScoreTo(self.clientA)
        self.announceScoreTo(self.clientB)
        
    def registerKillEvent(self, event):
        """
        Handle a kill event.
        """
        if self.status == Duel.STATUS_STARTED:

            if not isinstance(event, b3.events.Event) or \
                (event.client != self.clientA and event.client != self.clientB) or \
                    (event.target != self.clientA and event.target != self.clientB):
                raise DuelError('invalid kill event supplied')

            self.scores[event.client] += 1
            self.announceScoreTo(event.client)
            self.announceScoreTo(event.target)
            
    def announceScoreTo(self, client):
        """
        Announce duel score to the given client.
        :param client: b3.client.Client instance
        """
        if self.status == Duel.STATUS_STARTED:

            pattern = "^7[^5Duel^7]: ^7%(player)s %(playerScore)s^5:%(opponentScore)s ^7%(opponent)s"
            opponent = client == self.clientA and self.clientB or self.clientA
            scoreClient = self.scores[client]
            scoreOpponent = self.scores[opponent]

            # neutral color: assume they are tied
            colorClient = colorOpponent = '^5'
            if scoreClient > scoreOpponent:
                colorClient, colorOpponent = '^2', '^1'
            elif scoreOpponent > scoreClient:
                colorClient, colorOpponent = '^1', '^2'

            # send the message to the client
            client.message(pattern % {'player': client.exactName, 'opponent': opponent.exactName,
                                      'playerScore': '%s%s' % (colorClient, scoreClient),
                                      'opponentScore': '%s%s' % (colorOpponent, scoreOpponent)})

    def __repr__(self):
        """
        Object representation.
        """
        return 'Duel<%s:%s> ' % (self.clientA.name, self.clientB.name)