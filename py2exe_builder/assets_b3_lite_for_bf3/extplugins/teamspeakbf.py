# -*- coding: utf-8 -*-
#
# TeamSpeak Plugin for BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2011 Courgette (courgette@bigbrotherbot.net)
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
#
# CHANGELOG :
# 2010/04/13 - 1.0 - Courgette
# * first version
# 2010/04/14 - 1.1 - Courgette
# * add command !tsauto [off|team|squad] to give player the choice of disabling
#   auto channel switching or to activate it only for teams or squads
# 2011/12/08 - 2.0
# * rename plugin from teamspeakbfbc2 to teamspeakbf
# * can recognize players on teamspeak based on their IP address
# * handle BF3 SQDM game mode (4 teams of 1 squad each)
# 2011/12/14 - 2.1
# * fix crash when trying to delete TS channels having users
# * ServerQuery is now more reactive when receiving a error as response
# 2011/12/16 - 2.2
# * fixes issue #1 : 'player aren't moved at round start' (requires b3 >= 1.8.0dev15)
#
__version__ = '2.2'
__author__ = 'Courgette'

import b3
import b3.events
import b3.plugin

#--------------------------------------------------------------------------------------------------
class TeamspeakbfPlugin(b3.plugin.Plugin):

    connected = False

    _adminPlugin = None
    
    TS3ServerIP = None
    TS3QueryPort = 10011
    TS3ServerID = None
    TS3Login = None
    TS3Password = None
    TS3ChannelB3 = 'B3 autoswitched channels'
    TS3ChannelTeam1 = 'Team A'
    TS3ChannelTeam2 = 'Team B'

    
    tsconnection = None
    tsServerPort = 'unknown'
    
    
    squadNames = {
        0: 'no squad',
        1: 'Alpha',
        2: 'Bravo',
        3: 'Charlie',
        4: 'Delta',
        5: 'Echo',
        6: 'Foxtrot',
        7: 'Golf',
        8: 'Hotel',
    }
    
    autoswitchDefault = True
    autoswitchDefaultTarget = 'squad'

    tsChannelIdB3 = None
    tsChannelIdTeam1 = None
    tsChannelIdTeam2 = None

    tsChannelIdSquadsTeam1 = {
        0: None,
        1: None,
        2: None,
        3: None,
        4: None,
        5: None,
        6: None,
        7: None,
        8: None,
    }
    tsChannelIdSquadsTeam2 = {
        0: None,
        1: None,
        2: None,
        3: None,
        4: None,
        5: None,
        6: None,
        7: None,
        8: None,
    }

    def startup(self):
        """\
        Initialize plugin settings
        """
        
        if self.console.gameName not in ('bfbc2', 'bf3'):
            raise SystemExit('The Teamspeakbf plugin requires BFBC2 or BF3 games')

        # get the admin plugin so we can register commands
        self._adminPlugin = self.console.getPlugin('admin')
        if not self._adminPlugin:
            # something is wrong, can't start without admin plugin
            self.error('Could not find admin plugin')
            return False
    
        # register our commands
        if 'commands' in self.config.sections():
            for cmd in self.config.options('commands'):
                level = self.config.get('commands', cmd)
                sp = cmd.split('-')
                alias = None
                if len(sp) == 2:
                    cmd, alias = sp
            
                func = self.getCmd(cmd)
                if func:
                    self._adminPlugin.registerCommand(self, cmd, level, func, alias)

        # Register our events
        self.verbose('Registering events')
        self.registerEvent(b3.events.EVT_CLIENT_TEAM_CHANGE)
        self.registerEvent(b3.events.EVT_CLIENT_SQUAD_CHANGE)
        self.registerEvent(b3.events.EVT_CLIENT_AUTH)
    
        self.debug('Started')


    def getCmd(self, cmd):
        cmd = 'cmd_%s' % cmd
        if hasattr(self, cmd):
            func = getattr(self, cmd)
            return func
    
        return None


    def onLoadConfig(self):
        self.connected = False
        self.readConfig()
        
        try:
            self.tsconnection = ServerQuery(self.TS3ServerIP, self.TS3QueryPort)
            self.tsConnect()
            self.tsInitChannels()
            for c in self.console.clients.getList():
                self.moveClient(c)
        except TS3Error, err:
            self.error(str(err))
    
    def readConfig(self):
        try:
            self.TS3ServerIP = self.config.get('teamspeakServer', 'host')
        except:
            self.error('Cannot get teamspeak server host from config file')
            raise SystemExit('invalid teamspeak configuration')
      
        try:
            self.TS3QueryPort = self.config.getint('teamspeakServer', 'queryport')
        except:
            self.error('Cannot get teamspeak server queryport from config file, using default : %s' % self.TS3QueryPort)
      
        try:
            self.TS3ServerID = self.config.getint('teamspeakServer', 'id')
        except:
            self.error('Cannot get teamspeak server Id from config file')
            raise SystemExit('invalid teamspeak configuration')

        try:
            self.TS3Login = self.config.get('teamspeakServer', 'login')
        except:
            self.error('Cannot get teamspeak login from config file')
            raise SystemExit('invalid teamspeak configuration')
      
        try:
            self.TS3Password = self.config.get('teamspeakServer', 'password')
        except:
            self.error('Cannot get teamspeak password from config file')
            raise SystemExit('invalid teamspeak configuration')
      
        
        try:
            self.TS3ChannelB3 = self.config.get('teamspeakChannels', 'B3')
            self.info('teamspeakChannels::B3 : \'%s\'' % self.TS3ChannelB3)
        except:
            self.info('Cannot get teamspeakChannels::B3 from config file, using default : %s' % self.TS3ChannelB3)
      
        try:
            self.TS3ChannelTeam1 = self.config.get('teamspeakChannels', 'team1')
            self.info('teamspeakChannels::team1 : \'%s\'' % self.TS3ChannelTeam1)
        except:
            self.info('Cannot get teamspeakChannels::team1 from config file, using default : %s' % self.TS3ChannelTeam1)
      
        try:
            self.TS3ChannelTeam2 = self.config.get('teamspeakChannels', 'team2')
            self.info('teamspeakChannels::team2 : \'%s\'' % self.TS3ChannelTeam2)
        except:
            self.info('Cannot get teamspeakChannels::team2 from config file, using default : %s' % self.TS3ChannelTeam2)
      
      

    def onEvent(self, event):
        """\
        Handle intercepted events
        """
        client = event.client
        if event.type == b3.events.EVT_STOP:
            try:
                self.tsDeleteChannels()
            except TS3Error, err:
                self.error(err)
            self.tsconnection.disconnect()
            self.connected = False
        elif self.connected is False:
            return
        elif event.type in (b3.events.EVT_CLIENT_SQUAD_CHANGE, b3.events.EVT_CLIENT_TEAM_CHANGE):
            try:
                self.moveClient(client)
            except TS3Error, err:
                self.error(str(err))
        elif event.type == b3.events.EVT_CLIENT_AUTH and client:
            try:
                tsclient = self.tsGetClient(client)
                if not tsclient:
                    self.debug('cannot find %s client info from TS' % client.name)
                else:
                    if not self.tsIsClientInB3Channel(tsclient):
                        teamspeak_cmd =  self._adminPlugin._commands['teamspeak']
                        command_name = teamspeak_cmd.alias if teamspeak_cmd.alias else 'teamspeak'
                        if self.tsIsClientInB3Channel(tsclient):
                            self.tsTellClient(tsclient['clid'], "Hi, %s found you on our \"%s\" gameserver. Type !%s in game to unlink B3 and TS3" % (self.console.name, self.console.game.sv_hostname, command_name))
                        else:
                            self.tsTellClient(tsclient['clid'], "Hi, %s found you on our \"%s\" gameserver. Type !%s in game to link B3 and TS3" % (self.console.name, self.console.game.sv_hostname, command_name))
                        self.tsTellClient(tsclient['clid'], "Join the \"%s\" channel" % self.TS3ChannelB3)
            except TS3Error, err:
                self.error(str(err))


    #===============================================================================
    #
    #    B3 Commands implementations
    #
    #===============================================================================

    def cmd_tsreconnect(self ,data , client, cmd=None):
        """\
        Reconnect B3 to the Teamspeak server
        """
        if client:
            client.message('Reconnecting to TS on %s:%s ...' % (self.TS3ServerIP, self.TS3QueryPort))
            try:
                self.tsConnect()
            except TS3Error, err:
                client.message('Failed to connect : %s' % err.msg)
                self.error(str(err))


    def cmd_tsdisconnect(self ,data , client, cmd=None):
        """\
        Disconnect B3 from the Teamspeak server
        """
        if client:
            client.message('Disconnecting from TS on %s:%s ...' % (self.TS3ServerIP, self.TS3QueryPort))
            try:
                self.tsconnection.disconnect()
                self.connected = False
            except TS3Error, err:
                client.message('Failed to disconnect : %s' % err.msg)
                self.error(str(err))


    def cmd_teamspeak(self ,data , client, cmd=None):
        """\
        Teamspeak server info
        """
        if client:
            if self.connected:
                tsclient = self.tsGetClient(client)
                if tsclient is None:
                    client.message('Join our Teamspeak server on %s:%s' % (self.TS3ServerIP, self.tsServerPort))
                    if not hasattr(client, 'ip') or not client.ip:
                        client.message('Use the same name on Teamspeak as in game to be auto switch to the right channel')
                else:
                    client.message('You are connected on our Teamspeak server')
                    if data == 'join':
                        client.setvar(self, 'original_ts_channel', tsclient['cid'])
                        self.tsMoveTsclientToChannelId(tsclient, self.tsChannelIdB3)
                        tsclient['cid'] = self.tsChannelIdB3
                    elif data == 'disjoin':
                        original_channel = client.var(self, 'original_ts_channel', 1).value
                        self.tsMoveTsclientToChannelId(tsclient, original_channel)
                        tsclient['cid'] = original_channel
                    if not self.tsIsClientInB3Channel(tsclient):
                        client.message('If you want to be switched automatically to your team/squad channel, enter the %s channel or type !teamspeak join' % self.TS3ChannelB3)
                    else:
                        client.message('If you want to be leave the "%s" TS channel, !teamspeak disjoin' % self.TS3ChannelB3)
                        autoswitch = client.var(self, 'autoswitch', self.autoswitchDefault).value
                        if autoswitch is False:
                            client.message('You are not in auto-switch mode. To be automatically switched to your team channel, type !tsauto on')
                        else:
                            switchtarget = client.var(self, 'switchtarget', self.autoswitchDefaultTarget).value
                            self.debug('switchtarget: %s' % switchtarget)
                            if switchtarget == 'squad':
                                client.message('You are in auto-switch squad mode')
                                client.message('type: "!tsauto team" to get switched to your team channel instead')
                                client.message('type: "!tsauto off" to disable TeamSpeak autoswitch')
                            else:
                                client.message('You are in auto-switch team mode')
                                client.message('type: "!tsauto squad" to get switched to your squad channel instead')
                                client.message('type: "!tsauto off" to disable TeamSpeak autoswitch')
            else:
                client.message('Teamspeak server not available')

    def cmd_tsauto(self, data, client, cmd=None):
        """\
        Change the way you are moved to the different TeamSpeak channels
        """
        if client:
            autoswitch = client.var(self, 'autoswitch', self.autoswitchDefault).value
            switchtarget = client.var(self, 'switchtarget', self.autoswitchDefaultTarget).value
            if not data:
                infotxt = 'TS autoswitch is '
                if autoswitch:
                    infotxt += 'enabled in %s mode' % switchtarget
                else:
                    infotxt += 'disabled'
                client.message(infotxt)
            else:
                if data not in ('off', 'team', 'squad'):
                    client.message("Invalid parameter. Expecting one of : 'off', 'team', 'squad'")
                elif data == 'off':
                    client.setvar(self, 'autoswitch', False)
                    client.message('You will not be automatically switched on teamspeak')
                elif data == 'team':
                    client.setvar(self, 'autoswitch', True)
                    client.setvar(self, 'switchtarget', 'team')
                    client.message('You will be automatically switched on your team channel')
                    self.moveClient(client)
                elif data == 'squad':
                    client.setvar(self, 'autoswitch', True)
                    client.setvar(self, 'switchtarget', 'squad')
                    client.message('You will be automatically switched on your squad channel')
                    self.moveClient(client)


    #===============================================================================
    #
    #    Others
    #
    #===============================================================================

    def moveClient(self, client):
        """Move the client to its team or squad depending on his settings"""
        if client:
            autoswitch = client.var(self, 'autoswitch', self.autoswitchDefault).value
            switchtarget = client.var(self, 'switchtarget', self.autoswitchDefaultTarget).value
            if not autoswitch:
                self.debug('%s is not in autoswitch mode' % client.cid)
                return
            tsclient = self.tsGetClient(client)
            if not tsclient:
                self.debug('cannot find %s client info from TS' % client.cid)
            else:
                if not self.tsIsClientInB3Channel(tsclient):
                    ## we only act on players found on within the B3 channel
                    self.debug('%s is not in the autoswitched B3 channel' % client.cid)
                    return
                def is_squad_death_match():
                    if self.console.gameName == 'bf3' and self.console.game.gameType == 'SquadDeathMatch0':
                        # in this game mode there are only 4 squads fighting each others which are in fact
                        # 4 teams. Players are always in squad 1 and teamID can be 1, 2, 3 or 4
                        if client.teamId not in (1, 2, 3 , 4):
                            self.debug('moving %s to B3 channel (unable to find team %s/%s)' % (client.cid, client.teamId, client.squad))
                            self.tsMoveTsclientToChannelId(tsclient, self.tsChannelIdB3)
                        else:
                            self.debug('moving %s to team%s channel' % (client.cid, client.teamId))
                            self.tsMoveTsclientToChannelId(tsclient, self.tsChannelIdSquadsTeam1[int(client.teamId)])
                        return True
                    else:
                        return False
                if switchtarget == 'team':
                    if not is_squad_death_match():
                        if client.team == b3.TEAM_BLUE:
                            self.debug('moving %s to team1 channel' % client.cid)
                            self.tsMoveTsclientToChannelId(tsclient, self.tsChannelIdTeam1)
                        elif client.team == b3.TEAM_RED:
                            self.debug('moving %s to team2 channel' % client.cid)
                            self.tsMoveTsclientToChannelId(tsclient, self.tsChannelIdTeam2)
                        else:
                            self.debug('moving %s to B3 channel' % client.cid)
                            self.tsMoveTsclientToChannelId(tsclient, self.tsChannelIdB3)
                elif switchtarget == 'squad':
                    if not is_squad_death_match():
                        if client.team == b3.TEAM_BLUE:
                            self.debug('moving %s to his Team1 squad channel' % client.cid)
                            cid = self.tsChannelIdSquadsTeam1[int(client.squad)]
                            self.tsMoveTsclientToChannelId(tsclient, cid)
                        elif client.team == b3.TEAM_RED:
                            self.debug('moving %s to his Team2 squad channel' % client.cid)
                            cid = self.tsChannelIdSquadsTeam2[int(client.squad)]
                            self.tsMoveTsclientToChannelId(tsclient, cid)
                        else:
                            self.debug('moving %s to B3 channel (unable to find team %s/%s)' % (client.cid, client.team, client.squad))
                            self.tsMoveTsclientToChannelId(tsclient, self.tsChannelIdB3)


    #===========================================================================
    #
    # TeamSpeak related methods
    #
    #===========================================================================

    def tsSendCommand(self, cmd, parameter={}, option=[]):
        if self.connected:
            return self._tsSendCommand(cmd, parameter, option)

    def _tsSendCommand(self, cmd, parameter, option, numtries=1):
        if numtries > 3:
            self.error("Too many tries. Could not send TS3 command %s(%s) " % (cmd, repr(parameter)))
            return
        try:
            self.debug('TS command %s(%s) [#%s]' % (cmd, repr(parameter), numtries))
            return self.tsconnection.command(cmd, parameter, option)
        except TS3Error, err:
            # Try to automatically recover from some frequent errors
            self.error("TS3 error : %s" % str(err))
            if err.code == 1024:
                ## invalid serverID
                self.tsconnection.command('use', {'sid': self.TS3ServerID})
                return self._tsSendCommand(cmd, parameter, option, numtries+1)
            elif err.code == 12:
                ## Bad TS3 response
                self.tsConnect()
                return self._tsSendCommand(cmd, parameter, option, numtries+1)
            elif err.code == 3331:
                ## Flood ban
                self.error("The teamspeak server banned B3 for flooding commands. Add B3 ip to the teamspeak server whitelist file called query_ip_whitelist.txt")
                return
            else:
                raise
        except telnetlib.socket.error, err:
            self.tsConnect()
            return self._tsSendCommand(cmd, parameter, option, numtries+1)
    
    def tsConnect(self):
        if self.tsconnection is not None:
            try:
                self.tsconnection.disconnect()
            except Exception:
                pass
            del self.tsconnection

        self.connected = False
        self.tsconnection = ServerQuery(self.TS3ServerIP, self.TS3QueryPort)
        
        self.info('connecting to teamspeak server %s:%s' % (self.TS3ServerIP, self.TS3QueryPort))
        self.tsconnection.connect()
        
        try:
            versiondata = self.tsconnection.command('version')
        except TS3Error, err:
            if err.code == 3329:
                ## give a bit a guidance to the user in such case
                self.warning("B3 is banned from the TS3 server. Make sure you add the B3 ip to your TS3 server white list (query_ip_whitelist.txt)")
            raise
        self.info('TS version : %s' % versiondata)
        if not versiondata['version'].startswith('3.'):
            self.warning("This plugin is meant to work with a TeamSpeak 3 server")
        
        self.info('Loging to TS server with login name \'%s\'' % self.TS3Login)
        self.tsconnection.command('login', {'client_login_name': self.TS3Login, 'client_login_password': self.TS3Password})
        
        self.connected = True
        
        self.info('Joining server ID : %s' % self.TS3ServerID)
        self.tsconnection.command('use', {'sid': self.TS3ServerID})
        
        self.info('Get server port')
        serverinfo = self.tsconnection.command('serverinfo')
        self.debug(serverinfo)
        self.tsServerPort = serverinfo['virtualserver_port']
        self.info('TS server port is %s', self.tsServerPort)
    
    
    def tsInitChannels(self):
        channellist = self.tsSendCommand('channellist')
        self.debug('channellist : %s' % channellist)
        
        self.tsChannelIdB3 = self.tsGetChannelIdByName(self.TS3ChannelB3, channellist)
        if self.tsChannelIdB3 is None:
            self.info('creating channel [%s]' % self.TS3ChannelB3)
            response = self.tsSendCommand('channelcreate',
                                                              {'channel_name': self.TS3ChannelB3
                                                               , 'channel_flag_semi_permanent': 1})
            self.debug(response)
            self.tsChannelIdB3 = response['cid']
            
            
        self.tsChannelIdTeam1 = self.tsGetChannelIdByName(self.TS3ChannelTeam1, channellist, self.tsChannelIdB3)
        if self.tsChannelIdTeam1 is None:
            self.info('creating sub-channel [%s]' % self.TS3ChannelTeam1)
            response = self.tsSendCommand('channelcreate',
                                                              {'channel_name': self.TS3ChannelTeam1,
                                                               'cpid': self.tsChannelIdB3
                                                               , 'channel_flag_semi_permanent': 1})
            self.debug(response)
            self.tsChannelIdTeam1 = response['cid']
        self.tsChannelIdSquadsTeam1[0] = self.tsChannelIdTeam1
        
        self.tsChannelIdTeam2 = self.tsGetChannelIdByName(self.TS3ChannelTeam2, channellist, self.tsChannelIdB3)
        if self.tsChannelIdTeam2 is None:
            self.info('creating sub-channel [%s]' % self.TS3ChannelTeam2)
            response = self.tsSendCommand('channelcreate',
                                                              {'channel_name': self.TS3ChannelTeam2,
                                                               'cpid': self.tsChannelIdB3
                                                               , 'channel_flag_semi_permanent': 1})
            self.debug(response)
            self.tsChannelIdTeam2 = response['cid']
        self.tsChannelIdSquadsTeam2[0] = self.tsChannelIdTeam2
        
        for i in range(1, 9):
            self.tsChannelIdSquadsTeam1[i] = self.tsGetChannelIdByName(self.squadNames[i], channellist, self.tsChannelIdTeam1)
            if self.tsChannelIdSquadsTeam1[i] is None:
                self.info('creating squad-channel [%s] for team1' % self.squadNames[i])
                self.tsChannelIdSquadsTeam1[i] = self.tsCreateSubChannel(self.squadNames[i], self.tsChannelIdTeam1)
        
            self.tsChannelIdSquadsTeam2[i] = self.tsGetChannelIdByName(self.squadNames[i], channellist, self.tsChannelIdTeam2)
            if self.tsChannelIdSquadsTeam2[i] is None:
                self.info('creating squad-channel [%s] for team2' % self.squadNames[i])
                self.tsChannelIdSquadsTeam2[i] = self.tsCreateSubChannel(self.squadNames[i], self.tsChannelIdTeam2)
            
    def tsDeleteChannels(self):
        if self.connected:
            self.tsSendCommand('channeldelete', {'cid': self.tsChannelIdB3, 'force': 1})
            self.tsChannelIdB3 = None
            self.tsChannelIdTeam1 = None
            self.tsChannelIdTeam2 = None
            self.tsChannelIdSquadsTeam1 = {
                1: None,
                2: None,
                3: None,
                4: None,
                5: None,
                6: None,
                7: None,
                8: None,
            }
            self.tsChannelIdSquadsTeam2 = {
                1: None,
                2: None,
                3: None,
                4: None,
                5: None,
                6: None,
                7: None,
                8: None,
            }
        
    def tsCreateSubChannel(self, channelName, parentChannelId):
        response = self.tsSendCommand('channelcreate',
                                  {'channel_name': channelName,
                                   'cpid': parentChannelId
                                   , 'channel_flag_semi_permanent': 1})
        return response['cid']

            
    def tsGetChannelIdByName(self, channelName, channellist=[], parentChannel=None):
        cid = None
        for c in channellist:
            if c['channel_name'] == channelName and (parentChannel is None or c['pid'] == parentChannel):
                cid = c['cid']
        return cid

    
    def tsGetClient(self, client):
        """Return a dict with all TS client properties as returned by the 
        clientinfo command
        """
        if not client:
            return None
        clientlist = self.tsSendCommand('clientlist')
        self.debug('clientlist: %s' % clientlist)
        if client.ip is not None:
            clients_info = {}
            matches_by_ip = []
            matches_by_name = []

            for c in clientlist:
                clid = c['clid']
                clients_info[clid] = info = self.tsSendCommand('clientinfo', {'clid': clid})
                if client.ip and 'connection_client_ip' in info and info['connection_client_ip'] == client.ip:
                    matches_by_ip.append(clid)
                nick = info['client_nickname'].lower()
                if nick in (client.name.lower()):
                    matches_by_name.append(clid)

            found_client_data = None
            if len(matches_by_ip) == 1:
                self.verbose("found teamspeak client by ip (%s)" % client.ip)
                found_client_data = clients_info[matches_by_ip[0]]
                found_client_data['clid'] = matches_by_ip[0]
            else:
                if len(matches_by_name) > 0:
                    found_client_data = clients_info[matches_by_name[0]]
                    found_client_data['clid'] = matches_by_name[0]
            return found_client_data
        return None
    
        
    def tsMoveTsclientToChannelId(self, tsclient, tsChannelId):
        if tsclient and self.connected:
            if tsclient['cid'] != tsChannelId:
                try:
                    self.tsSendCommand('clientmove', {'clid': tsclient['clid'], 'cid': tsChannelId})
                except TS3Error, err:
                    if not err.code == 770: ## client already in channel
                        raise
 
    def tsIsClientInB3Channel(self, tsclient):
        """Return True if the client is found in the B3 channel or one of
        its sub-channels"""
        if not tsclient:
            return False
        if tsclient['cid'] == self.tsChannelIdB3:
            return True
        return self.tsIsClientInChannelTeam1(tsclient) or self.tsIsClientInChannelTeam2(tsclient)
    
    def tsIsClientInChannelTeam1(self, tsclient):
        """Return True if the client is found in the team1 channel or one of
        its sub-channels"""
        if not tsclient:
            return False
        if tsclient['cid'] == self.tsChannelIdTeam1:
            return True
        for channelId in self.tsChannelIdSquadsTeam1.values():
            if tsclient['cid'] == channelId:
                return True
        return False
    
    def tsIsClientInChannelTeam2(self, tsclient):
        """Return True if the client is found in the team2 channel or one of
        its sub-channels"""
        if not tsclient:
            return False
        if tsclient['cid'] == self.tsChannelIdTeam2:
            return True
        for channelId in self.tsChannelIdSquadsTeam2.values():
            if tsclient['cid'] == channelId:
                return True
        return False
    

    def tsTellClient(self, clid, msg):
        """Send a private message to a TS3 client"""
        self.tsSendCommand('sendtextmessage', {'targetmode': 3, 'target': clid, 'msg': "[%s] %s" % (self.console.name, msg)})

    
##################################################################################################
# Copyright (c) 2009 Christoph Heer (Christoph.Heer@googlemail.com)
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the \"Software\"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED \"AS IS\", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

import telnetlib
import re
import thread
import time


class TS3Error(Exception):
    def __init__(self, code, msg, msg2):
        Exception.__init__(self)
        self.code = code
        self.msg = msg
        self.msg2 = msg2

    def __str__(self):
        return "ID %s (%s) %s" % (self.code, self.msg, self.msg2)


class ServerQuery():
    TSRegex = re.compile(r"(\w+)=(.*?)(\s|$|\|)")

    def __init__(self, ip='127.0.0.1', query=10011):
        """
        This class contains functions to connecting a TS3 Query Port and send
        command.
        @param ip: IP adress of the TS3 Server
        @type ip: str
        @param query: Query Port of the TS3 Server. Default 10011
        @type query: int
        """
        self.IP = ip
        self.Query = int(query)
        self.Timeout = 5.0
        self.lock = thread.allocate_lock()

    def connect(self):
        """
        Open a link to the Teamspeak 3 query port
        @return: A tulpe with a error code. Example: ('error', 0, 'ok')
        """
        try:
            self.telnet = telnetlib.Telnet(self.IP, self.Query)
        except telnetlib.socket.error, err:
            raise TS3Error(10, 'Can not open a link on the port or IP', err)
        output = self.telnet.read_until('TS3', self.Timeout)
        if not output.endswith('TS3'):
            raise TS3Error(20, 'This is not a Teamspeak 3 Server')
        else:
            return True

    def disconnect(self):
        """
        Close the link to the Teamspeak 3 query port
        @return: ('error', 0, 'ok')
        """
        self.telnet.write('quit \n')
        self.telnet.close()
        return True

    def escaping2string(self, string):
        """
        Convert the escaping string form the TS3 Query to a human string.
        @param string: A string form the TS3 Query with ecaping.
        @type string: str
        @return: A human string with out escaping.
        """
        string = str(string)
        string = string.replace('\/', '/')
        string = string.replace('\s', ' ')
        string = string.replace('\p', '|')
        string = string.replace('\n', '')
        string = string.replace('\r', '')
        try:
            string = int(string)
            return string
        except ValueError:
            ustring = unicode(string, "utf-8")
            return ustring

    def string2escaping(self, string):
        """
        Convert a human string to a TS3 Query Escaping String.
        @param string: A normal/human string.
        @type string: str
        @return: A string with escaping of TS3 Query.
        """
        if string is None:
            return ""
        elif type(string) == type(int()):
            string = str(string)
        else:
            string = string.encode("utf-8")
            string = string.replace('/', '\\/')
            string = string.replace(' ', '\\s')
            string = string.replace('|', '\\p')
        return string

    def command(self, cmd, parameter={}, option=[]):
        """
        Send a command with paramters and options to the TS3 Query.
        @param cmd: The command who wants to send.
        @type cmd: str
        @param parameter: A dict with paramters and value.
        Example: sid=2 --> {'sid':'2'}
        @type cmd: dict
        @param option: A list with options. Example: �uid --> ['uid']
        @type option: list
        @return: The answer of the server as tulpe with error code and message.
        """
        telnetCMD = cmd
        for key in parameter:
            telnetCMD += " %s=%s" % (key, self.string2escaping(parameter[key]))
        for i in option:
            telnetCMD += " -%s" % (i)
        telnetCMD += '\n'

        with self.lock:
            self.telnet.write(telnetCMD)
            regexp_index, match, telnetResponse = self.telnet.expect([r"(?m)error id=0 msg=ok$", r"(?m)error id=(?P<errorcode>\d+) msg=(?P<msg>.*)$"], self.Timeout)
        telnetResponse = telnetResponse.split(r'error id=')
        notParsedCMDStatus = "id=" + telnetResponse[1]
        notParsedInfo = telnetResponse[0].split('|')

        if (cmd.endswith("list") == True) or (len(notParsedInfo) > 1):
            returnInfo = []
            for notParsedInfoLine in notParsedInfo:
                ParsedInfo = self.TSRegex.findall(notParsedInfoLine)
                ParsedInfoDict = {}
                for ParsedInfoKey in ParsedInfo:
                    ParsedInfoDict[ParsedInfoKey[0]] = self.escaping2string(
                        ParsedInfoKey[1])
                returnInfo.append(ParsedInfoDict)

        else:
            returnInfo = {}
            ParsedInfo = self.TSRegex.findall(notParsedInfo[0])
            for ParsedInfoKey in ParsedInfo:
                returnInfo[ParsedInfoKey[0]] = self.escaping2string(
                    ParsedInfoKey[1])

        ReturnCMDStatus = {}
        ParsedCMDStatus = self.TSRegex.findall(notParsedCMDStatus)
        for ParsedCMDStatusLine in ParsedCMDStatus:
            ReturnCMDStatus[ParsedCMDStatusLine[0]] = self.escaping2string(
                ParsedCMDStatusLine[1])
        if ReturnCMDStatus['id'] != 0:
            raise TS3Error(ReturnCMDStatus['id'], ReturnCMDStatus['msg'], ReturnCMDStatus)

        return returnInfo


class ServerNotification(ServerQuery):
    def __init__(self, ip='127.0.0.1', query=10011):
        """
        This class contains functions to work with the
        ServerNotification of TS3.
        @param ip: IP adress of the TS3 Server
        @type ip: str
        @param query: Query Port of the TS3 Server. Default 10011
        @type query: int
        """
        ServerQuery.__init__(self, ip, query)
        self.LastCommand = 0

        self.Lock = thread.allocate_lock()
        self.RegistedNotifys = []
        self.RegistedEvents = []
        thread.start_new_thread(self.worker, ())

    def worker(self):
        while True:
            self.Lock.acquire()
            RegistedNotifys = self.RegistedNotifys
            LastCommand = self.LastCommand
            self.Lock.release()
            if len(RegistedNotifys) == 0:
                continue
            if LastCommand < time.time() - 180:
                self.command('version')
                self.Lock.acquire()
                self.LastCommand = time.time()
                self.Lock.release()
            telnetResponse = self.telnet.read_until("\n", 0.1)
            if telnetResponse.startswith('notify'):
                notifyName = telnetResponse.split(' ')[0]
                ParsedInfo = self.TSRegex.findall(telnetResponse)
                notifyData = {}
                for ParsedInfoKey in ParsedInfo:
                    notifyData[ParsedInfoKey[0]] = self.escaping2string(
                        ParsedInfoKey[1])
                for RegistedNotify in RegistedNotifys:
                    if RegistedNotify['notify'] == notifyName:
                        RegistedNotify['func'](notifyName, notifyData)
            time.sleep(0.2)

    def registerNotify(self, notify, func):
        notify2func = {'notify': notify, 'func': func}

        self.Lock.acquire()
        self.RegistedNotifys.append(notify2func)
        self.LastCommand = time.time()
        self.Lock.release()

    def unregisterNotify(self, notify, func):
        notify2func = {'notify': notify, 'func': func}

        self.Lock.acquire()
        self.RegistedNotifys.remove(notify2func)
        self.LastCommand = time.time()
        self.Lock.release()

    def registerEvent(self, eventName, parameter={}, option=[]):
        parameter['event'] = eventName
        self.RegistedEvents.append(eventName)
        self.command('servernotifyregister', parameter, option)
        self.Lock.acquire()
        self.LastCommand = time.time()
        self.Lock.release()

    def unregisterEvent(self):
        self.command('servernotifyunregister')
        
