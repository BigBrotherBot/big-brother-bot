#
# BigBrotherBot(B3) (www.bigbrotherbot.net)
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
#
# 2011-03-30 : 0.1
# * first alpha test
# 2011-09-28 : 0.2
# * First commit to repo
# 2011-09-29 : 0.3
# * Added !maps, found !map functionality broken in Web Admin 

#
from b3 import functions
from b3.clients import Client
from b3.lib.sourcelib import SourceQuery
from b3.parser import Parser
from ftplib import FTP
import asyncore
import b3
import b3.cron
import ftplib
import os
import rcon
import re
import string
import sys
import time
import urllib
import urllib2
import httplib
import cookielib
import hashlib


__author__  = 'Courgette, xlr8or, Freelander, 82ndab-Bravo17'
__version__ = '0.3'


class Ro2Parser(b3.parser.Parser):
    '''
    The Ref Orchestra 2 B3 parser class
    '''
    gameName = "redorchestra2"
    OutputClass = rcon.Rcon
    PunkBuster = None 
    # RO2 engine does not support color code, so we need this property
    # in order to get stripColors working
    _reColor = re.compile(r'(\^[0-9])')
    _reSteamId64 = re.compile(r'^[0-9]{17}$')
    _playerlistInterval = 30
    _server_banlist = {}
    _read_write_delay=1
    _write_queue=[]
    _read_queue=[]
    url=''
    login_page=''
    site=''
    user_agent=''
    password=''
    password_hash=''
    cj=None
    opener=None
    map_rotation = {}
    map_cycles = {}
    map_cycle_no = 0
    active_map_cycle = 0

    _commands = {}
    _commands['message'] = '%(prefix)s %(message)s'
    _commands['say'] = ('%(prefix)s %(message)s')
    _commands['kick'] = ('adminkick+%(playerid)s')
    _commands['ban'] = ('adminkickban+%(playerid)s')
    _commands['tempban'] = ('adminkick+%(playerid)s')
    
    _settings = {'line_length': 90, 
                 'min_wrap_length': 100}
    
    prefix = '%s: '
    
    def startup(self):
        self.debug("startup()")
        
        # create the 'Admin' client
        self.clients.newClient('Admin', guid='Server', name='Admin', hide=True, pbid='Server', team=b3.TEAM_UNKNOWN)
        
        if self.config.has_option('server','inifile'):
            # open ini file
            ini_file = self.config.get('server','inifile')
            if ini_file[0:6] == 'ftp://':
                    self.ftpconfig = functions.splitDSN(ini_file)
                    self._ini_file = 'ftp'
                    self.bot('ftp supported')
            elif ini_file[0:7] == 'sftp://':
                self.bot('sftp currently not supported')
            else:
                self.bot('Getting configs from %s', ini_file)
                f = self.config.getpath('server', 'inifile')
                if os.path.isfile(f):
                    self.input  = file(f, 'r')
                    self._ini_file = f

        if not self._ini_file:
            self.debug('Incorrect ini file or no ini file specified, map commands other than nextmap not available')
        
        
        self.cron + b3.cron.CronTab(self.retrievePlayerList, second='*/%s' % self._playerlistInterval)
    
        self.user_agent = 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'
        self.site=self._publicIp + ':' + str(self._rconPort)
        #self.debug(self.site)
        self.login_page="ServerAdmin"
        self.username="Admin"
        self.password=self._rconPassword
        
        self.password_hash = "$sha1$%s" % hashlib.sha1("%s%s" % (self.password, self.username)).hexdigest()

        self.url = "http://%s/%s" % (self.site, self.login_page)
        
    def webconnect(self):
        
        remember=-1        
        password=''
        login_url = self.url + '/'
        headers = {'Content-type' : 'application/x-www-form-urlencoded', 'User-Agent' : self.user_agent}
        self.cj = cookielib.LWPCookieJar()
        self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cj))
        urllib2.install_opener(self.opener)
        request = urllib2.Request(login_url, None, headers)
        page = urllib2.urlopen(request)
        response=page.read()
        
        #<input type="hidden" name="token" value="3309899D" />
        token_start = response.partition('<input type="hidden" name="token" value="')
        token = token_start[2]
        token_value = token[0:8]

        referer = login_url
        params = urllib.urlencode({ 'token' : token_value, 'password_hash' : self.password_hash, 'username' : self.username, 'password' : password, 'remember' : remember })
        headers = {'User-Agent' : self.user_agent, "Accept": "ext/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8", "Accept-Language" : "en-us,en;q =0.5", "Content-type": "application/x-www-form-urlencoded", "Accept-Charset" : "ISO-8859-1,utf-8;q=0.7,*;q=0.7", "Referer" : referer} 

        request = urllib2.Request(login_url, params, headers)

        try:
            main_page = self.opener.open(request)
            response = main_page.read()
            return True
   
        except:
            print "Failed open URL\n"
            raise
            return False
        
    def handle_chat(self, data):
        if string.capitalize(data['div_class']) == 'Chatnotice':
            return
        func = 'onChat_type%s' % (string.capitalize(data['div_class']))

        if hasattr(self, func):
            self.debug('routing ----> %s' % func)
            func = getattr(self, func)
            event = func(data)
            if event:
                self.queueEvent(event)
            else:
                self.warning('TODO handle: %s(%s)' % (func, data))
        else:
            self.warning('TODO handle packet : %s' % packet)
            self.queueEvent(self.getEvent('EVT_UNKNOWN', packet))
                    
        
    def run(self):
        """Main worker thread for B3"""
        self.bot('Start listening ...')
        self.screen.write('Startup Complete : B3 is running! Let\'s get to work!\n\n')
        self.screen.write('(If you run into problems, check %s for detailed log info)\n' % self.config.getpath('b3', 'logfile'))

        self.updateDocumentation()
        
        #Connect to RO2 web server
        
        web_auth = self.webconnect()
        if web_auth:
            self.bot('Authenticated on Web Server')
            
        self.working=True

        while self.working:
            """
            While we are working, connect to the RO2 server
            """
            self._paused=False
            if self._paused:
                if self._pauseNotice == False:
                    self.bot('PAUSED - Not parsing any lines, B3 will be out of sync.')
                    self._pauseNotice = True
            else:
                counter = 0
                while len(self._write_queue) == 0 and counter < 5:
                    time.sleep(.2)
                    counter +=1
                
                if len(self._write_queue) == 0:
                    self.readwriteajax()
                else:
                    self.debug('Go to ajax')
                    message = self._write_queue.pop(0)
                    self.debug(self._write_queue)
                    self.readwriteajax(message)
                    
                while len(self._read_queue) != 0:
                    chat_data = self._read_queue.pop(0)
                    self.handle_chat(chat_data)
                
                counter = 0
                time.sleep(.2)
        self.bot('Stop listening.')

        if self.exiting.acquire(1):
            self._serverConnection.close()
            if self.exitcode:
                sys.exit(self.exitcode)


    def readwriteajax(self, message = None):
        if message:
            message_text = self.addplus(message)
        else:
            message_text=''
    
        #<div class="chatmessage">
        #<span class="teamcolor" style="background: #8FB9B0;">&#160;</span>
        #<span class="username">&lt;82ndAB&gt;1LT.Bravo17 </span>:
        #<span class="message">test message from game</span>
        #</div>
        
        chatdata_url = self.url + '/current/chat/data'
        #data = 'ajax=1&message=message+from+b3&teamsay=-1'
        data = 'ajax=1' + message_text
        referer = self.url + '/current/chat'
        headers = {'User-Agent' : self.user_agent, "Accept": "ext/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8","Accept-encoding" : "gzip, deflate", "Accept-Language" : "en-us,en;q =0.5", "Content-type": "application/x-www-form-urlencoded", "Accept-Charset" : "ISO-8859-1,utf-8;q=0.7,*;q=0.7", "Referer" : referer}
        request_chat = urllib2.Request(chatdata_url, data, headers)
        chat_read = self.opener.open(request_chat)
        chat_data = chat_read.read()
        #'<div class="chatnotice">\r\n<span class="noticesymbol">***</span> [<span class="username"></span>]\r\n<span class="message">82ndAB ADMIN: No offensive names.</span>\r\n</div>\r\n\r\n'
        if len(chat_data) > 0:
            self.decode_chat_data(chat_data)
 
        return
        
    def addplus(self, message):
        #ajax=1&message=test+chat&teamsay=-1
        message.replace(' ', '+')
        message = '&message=' + message + '&teamsay=-1'
        return message
        
    def decode_chat_data(self, data):
        
        data = data.partition('div class="')[2]
        while data != '':
            chat_decoded = {}
            data_split = data.partition('">')
            chat_decoded['div_class'] = data_split[0]
            data = data_split[2]
            while data.partition('<span class="')[2] != '':
                data = data.partition('<span class="')[2]
                data_split = data.partition('"')
                span_class = data_split[0]
                data_split = data.partition('">')
                data = data_split[2]
                data_split = data.partition('</span>')
                chat_decoded[span_class] = data_split[0]
                data = data_split[2]
                
            data = data.partition('div class="')[2]
            chat_decoded['username'] = self.getUsername(chat_decoded['username'])
            self._read_queue.append(chat_decoded)
        
    def onChat_typeChatnotice(self,data):
        #Admin Chat ignore
        return None
        
        
        #<div class="chatmessage">
        #<span class="teamcolor" style="background: #8FB9B0;">&#160;</span>
        #<span class="username">&lt;82ndAB&gt;1LT.Bravo17 </span>:
        #<span class="message">test message from game</span>
        #</div>     
        
    def onChat_typeChatmessage(self, data):
        name = self.getUsername(data['username'])
        text = data['message']

        client = self.clients.getByName(name)
        if client is None:
            self.debug("Could not find client")
            return

        return self.getEvent('EVT_CLIENT_SAY', text, client)
        
    def getUsername(self, name):
        name = '%r' % name
        name = name.replace("\'", "")
        name = name.strip()

        if name.find('&') != -1:
            name = name.replace('&lt;', '<')
            name = name.replace('&gt;', '>')
            
        return name
 
    def decodeplayers(self, data):
        players = {}
        data = data.partition('<table id="players" class="grid">')[2]
        data = data.partition('<tbody>')[2]
        data = data.partition('</tbody>')[0]
        while data.find('<tr class=') != -1:
            players_data = data.partition('</tr>')
            data = players_data[2]
            next_player = players_data[0]
            next_player_decoded = self.decode_nextplayer(next_player)
            players[str(next_player_decoded['playerid'])] = next_player_decoded

        return players
        
    def decode_nextplayer(self, data):
        player={}
        data = data.partition('<td style=')[2]
        data = data.partition('>')[2]
        #left most character 0 axis 1 allies
        color = data.partition('</td>')[0]
        data = data.partition('<td>')[2]
        player['name'] = self.getUsername(data.partition('</td>')[0])
        data = data.partition('<td class="right">')[2]
        player['ping'] = data.partition('</td>')[0]
        data = data.partition('<td>')[2]
        player['ip'] = data.partition('</td>')[0]
        data = data.partition('<td>')[2]
        player['guid'] = data.partition('</td>')[0]
        data = data.partition('<td>')[2]
        player['steam_id'] = data.partition('</td>')[0]
        data = data.partition('<td class="center">')[2]
        player['admin'] = data.partition('</td>')[0]
        data = data.partition('<td class="center">')[2]
        spec = data.partition('</td>')[0]
        data = data.partition('<input type="hidden" name="playerid" value="')[2]
        player['playerid'] = data.partition('"')[0]
        data = data.partition('<input type="hidden" name="playerkey" value="')[2]
        player['playerkey'] = data.partition('"')[0]
        self.debug(player)
        if spec.lower() == 'yes':
            player['team'] = self.getTeam('2')
        else:
            player['team'] = self.getTeam(color[0])
        
        return player
        
        
    def decodeBans(self, data):
        ban_list = {}
        if data.find('<!--<td><%ban.playername%></td>-->') == -1:
            self.debug('No bans in list')
            return ban_list

        while data.find('<!--<td><%ban.playername%></td>-->') != -1:
            data = data.partition('<!--<td><%ban.playername%></td>-->')[2]
            data = data.partition('<td>')[2]
            banid = data.partition('</td>')[0]
            data = data.partition('<input type="hidden" name="banid" value="')[2]
            ban_no = data.partition('"')[0]
            ban_list[str(banid)] = ban_no
            
        return ban_list
            
            
    # =======================================
    # implement parser interface
    # =======================================
    

    def write(self, msg, maxRetries=None):
        """Write a message to Console via Ajax"""
        if self.replay:
            self.bot('Sent rcon message: %s' % msg)
        elif self.output == None:
            pass
        else:
            msg = self.stripColors(msg)
            self._write_queue.append(msg)
            self.debug(self._write_queue)
            return

    def writelines(self, msg):
        """Write a sequence of messages to Console via Ajax."""
        if self.replay:
            self.bot('Sent rcon message: %s' % msg)
        elif self.output == None:
            pass
        else:
            for line in lines:
                self.write(line)
                time.sleep(0.1)
            return
            
    def writeAdminCommand(self, cmd):

        consoledata_url = self.url + '/console'
        data = 'command=' + cmd
        self.debug('Admin Command data %s' % data)
        headers = {'User-Agent' : self.user_agent, "Accept": "ext/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8", "Accept-Language" : "en-us,en;q =0.5", "Content-type": "application/x-www-form-urlencoded", "Accept-Charset" : "ISO-8859-1,utf-8;q=0.7,*;q=0.7", "Referer" : consoledata_url}
        request_console = urllib2.Request(consoledata_url, data, headers)
        adminconsole_read = self.opener.open(request_console)
        console_data = adminconsole_read.read()
    
    
    def getPlayerList(self):
        """\
        Returns a list of client objects
        """
        self.verbose2('Retrieving Playerlist')
        playerlist_url = self.url + '/current/players'
        referer = self.url + '/current'
        headers = {'User-Agent' : self.user_agent, "Accept": "ext/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8", "Accept-Language" : "en-us,en;q =0.5", "Content-type": "application/x-www-form-urlencoded", "Accept-Charset" : "ISO-8859-1,utf-8;q=0.7,*;q=0.7", "Referer" : referer}
        request_playerlist = urllib2.Request(playerlist_url, None, headers)
        playerlist_read = self.opener.open(request_playerlist)
        playerlist_data = playerlist_read.read()
        if playerlist_data.find('<em>There are no players</em>') != -1:
            self.debug('No players on server')
            clients = {}
        else:
            clients = self.decodeplayers(playerlist_data)
            self.debug (clients)
        
        return clients
            
    def authorizeClients(self):
        """\
        For all connected players, fill the client object with properties allowing to find 
        the user in the database (usualy guid, or punkbuster id, ip) and call the 
        Client.auth() method 
        """
        pass
    
    def findNewPlayers(self, c_client_list):

        for c in c_client_list:
            cl = c_client_list[c]
            uid = cl['guid']
            if len(uid) != 18:
                self.warning(u"weird UID : [%s]" % uid)
            
            # try to get the client by guid
            client = self.clients.getByGUID(uid)
            if not client:
                self.debug('adding client')
                client = self.clients.newClient(cl['playerid'], guid=uid, name=cl['name'], team=b3.TEAM_UNKNOWN)
            # update client data
            client.name = cl['name']
            client.team = cl['team']
            client.cid = cl['playerid']
            self.verbose2('onServerPlayer: name: %s, team: %s' %( client.name, client.team ))

            
    def sync(self, c_client_list):
        """\
        Check Clients list against all connected players returned by self.getPlayerList() and 
        if required call the client.disconnect() method to remove a client from self.clients.
        """

        self.debug("synchronizing clients")
        client_cid_list = []
        for c in c_client_list:
            cl = c_client_list[c]
            client_cid_list.append(cl['playerid'])
        
        for client in self.clients.getList():
            
            if (client_cid_list.count(client.cid) == 0):
                self.debug( 'Removing %s from list' % client.name)
                self.debug(client)
                client.disconnect()

                
    def say(self, msg):
        """\
        broadcast a message to all players
        """
        msg = self.stripColors(msg)
        for line in self.getWrap(msg, self._settings['line_length'], self._settings['min_wrap_length']):
            line = self.stripColors(line)
            self.write(self.getCommand('say',  prefix=self.msgPrefix, message=line))

    def message(self, client, text):
        """\
        display a message to a given player
        """
        # actually send private messages
        text = self.stripColors(text)
        for line in self.getWrap(text, self._settings['line_length'], self._settings['min_wrap_length']):
            line = self.stripColors(line)
            self.write(self.getCommand('message', uid=client.guid, prefix=self.msgPrefix, message=line))

    def kick(self, client, reason='', admin=None, silent=False, *kwargs):
        """\
        kick a given player
        """
        self.debug('KICK : client: %s, reason: %s', client.cid, reason)
        if admin:
            fullreason = self.getMessage('kicked_by', self.getMessageVariables(client=client, reason=reason, admin=admin))
        else:
            fullreason = self.getMessage('kicked', self.getMessageVariables(client=client, reason=reason))
        fullreason = self.stripColors(fullreason)
        reason = self.stripColors(reason)

        if not silent and fullreason != '':
            self.say(fullreason)


        self.writeAdminCommand(self.getCommand('kick', playerid=client.cid))
        self.queueEvent(self.getEvent('EVT_CLIENT_KICK', reason, client))
        client.disconnect()

    def ban(self, client, reason='', admin=None, silent=False, *kwargs):
        """\
        ban a given player
        """
        self.debug('BAN : client: %s, reason: %s', client.cid, reason)
        if admin:
            fullreason = self.getMessage('banned_by', self.getMessageVariables(client=client, reason=reason, admin=admin))
        else:
            fullreason = self.getMessage('banned', self.getMessageVariables(client=client, reason=reason))
        fullreason = self.stripColors(fullreason)
        reason = self.stripColors(reason)

        if not silent and fullreason != '':
            self.say(fullreason)
        
        banid = client.guid

        
        
        bandata_url = self.url + '/policy/bans'
        data = 'action=add&uniqueid=' + banid
        self.debug('Ban data %s' % data)
        headers = {'User-Agent' : self.user_agent, "Accept": "ext/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8", "Accept-Language" : "en-us,en;q =0.5", "Content-type": "application/x-www-form-urlencoded", "Accept-Charset" : "ISO-8859-1,utf-8;q=0.7,*;q=0.7", "Referer" : bandata_url}
        request_console = urllib2.Request(bandata_url, data, headers)
        banconsole_read = self.opener.open(request_console)
        console_data = banconsole_read.read()
        
        self.queueEvent(self.getEvent('EVT_CLIENT_BAN', {'reason': reason, 'admin': admin}, client))
        client.disconnect()

    def unban(self, client, reason='', admin=None, silent=False, *kwargs):
        """\
        unban a given player
        """
        ban_list = self.retrieveBanlist()


        self.debug('using guid to unban')
        banid = client.guid
        self.debug (banid)
        ban_no = None
        try:
            ban_no = ban_list[banid]
        except:
            if admin:
                admin.message(' %s not in server banlist' %client.name)

        if ban_no:
            ban_no = str(ban_no[8:])
        
            banlist_url = self.url + '/policy/bans'
            referer = self.url + '/policy/bans'
            data = 'banid=plainid%3A' + ban_no + '&action=delete'
            self.debug(data)
            headers = {'User-Agent' : self.user_agent, "Accept": "ext/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8", "Accept-Language" : "en-us,en;q =0.5", "Content-type": "application/x-www-form-urlencoded", "Accept-Charset" : "ISO-8859-1,utf-8;q=0.7,*;q=0.7", "Referer" : referer}
            request_banlist = urllib2.Request(banlist_url, data, headers)
            banlist_read = self.opener.open(request_banlist)
            banlist_data = banlist_read.read()
            if admin:
                admin.message('Removed %s from Server banlist' %client.name)
        
        if admin:
            admin.message('Removed %s from B3 banlist' %client.name)
            
        self.queueEvent(self.getEvent('EVT_CLIENT_UNBAN', reason, client))

    def tempban(self, client, reason='', duration=2, admin=None, silent=False, *kwargs):
        """\
        tempban a given player
        """
        self.debug('TEMPBAN : client: %s, reason: %s', client.cid, reason)
        if admin:
            fullreason = self.getMessage('temp_banned_by', self.getMessageVariables(client=client, reason=reason, admin=admin, banduration=b3.functions.minutesStr(duration)))
        else:
            fullreason = self.getMessage('temp_banned', self.getMessageVariables(client=client, reason=reason, banduration=b3.functions.minutesStr(duration)))
        fullreason = self.stripColors(fullreason)
        reason = self.stripColors(reason)

        if not silent and fullreason != '':
            self.say(fullreason)

        self.writeAdminCommand(self.getCommand('kick', playerid=client.cid))
        self.queueEvent(self.getEvent('EVT_CLIENT_BAN_TEMP', {'reason': reason, 
                                                              'duration': duration, 
                                                              'admin': admin}
                                      , client))
        client.disconnect()

        
    def getMaps(self):
        """\
        return the available maps/levels name
        """
        self.map_rotation = []
        self.map_cycles = {}
        self.map_cycle_no = 0
        if self._ini_file:
            if self._ini_file == 'ftp':
                self.getftpini()
            else:
                input = open(self._ini_file, 'r')
                for line in input:
                    if line[0:15] == 'ActiveMapCycle=':
                        self.active_map_cycle = int(line.partition('ActiveMapCycle=')[2])
                    if line[0:14] == 'GameMapCycles=':
                        self.map_cycles[str(self.map_cycle_no)] = line
                        self.map_cycle_no += 1

                input.close()
                
            map_line = self.map_cycles[str(self.active_map_cycle)]
            map_line = map_line.partition('Maps=("')[2]
            map_line = map_line.partition('"),RoundLimits=')[0]
            self.map_rotation.append(map_line.partition('","')[0])
            while map_line.find('","') != -1:
                map_line= map_line.partition('","')[2]
                self.map_rotation.append(map_line.partition('","')[0])

        self.debug(self.map_rotation)
        return self.map_rotation

    def rotateMap(self):
        """\
        load the next map/level
        """
        raise NotImplementedError
        
    def changeMap(self, map):
        """\
        load a given map/level
        return a list of suggested map names in cases it fails to recognize the map that was provided
        """
        raise NotImplementedError
        map.replace('-', '&2d')
        cmd = 'AdminChangeMap&20' + map
        self.writeAdminCommand(cmd)
        

    def getPlayerPings(self):
        """\
        returns a dict having players' id for keys and players' ping for values
        """
        pings = {}
        clients = self.clients.getList()
        for c in clients:
            try:
                pings[c.name] = int(c.ping)
            except AttributeError:
                pass
        return pings

    def getTeam(self, team):
        team = str(team).lower()
        if team == '0':
            result = b3.TEAM_RED
        elif team == '1':
            result = b3.TEAM_BLUE
        elif team == '2':
            result = b3.TEAM_SPEC
        elif team == '3':
            result = b3.TEAM_UNKNOWN
        else:
            result = b3.TEAM_UNKNOWN
        return result
    
    # =======================================
    # convenience methods
    # =======================================

    def getClient(self, name):
        """return a already connected client by searching the 
        clients cid index.

        This method can return None
        """
        client = self.clients.getByName(name)
        if client:
            return client
        return None
    
    def getClientByUidOrCreate(self, uid, name):
        """return a already connected client by searching the 
        clients guid index or create a new client
        
        This method can return None
        """
        client = self.clients.getByGUID(uid)
        if client is None and name:
            client = self.clients.newClient(name, guid=uid, name=name, team=b3.TEAM_UNKNOWN)
            client.last_update_time = time.time()
        return client
    
    def retrievePlayerList(self):
        """\
        Send RETRIEVE PLAYERLIST to the server to trigger onServerPlayer return events
        """
        client_list = self.getPlayerList()
        self.findNewPlayers(client_list)
        if len(client_list) != 0:
            self.sync(client_list)

    def retrieveBanlist(self):
        """\
        Returns a list of banned player from the server
        """
        self.verbose2('Retrieving Banlist')
        banlist_url = self.url + '/policy/bans'
        referer = self.url + '/policy/bans'
        headers = {'User-Agent' : self.user_agent, "Accept": "ext/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8", "Accept-Language" : "en-us,en;q =0.5", "Content-type": "application/x-www-form-urlencoded", "Accept-Charset" : "ISO-8859-1,utf-8;q=0.7,*;q=0.7", "Referer" : referer}
        request_banlist = urllib2.Request(banlist_url, None, headers)
        banlist_read = self.opener.open(request_banlist)
        banlist_data = banlist_read.read()
        ban_list = self.decodeBans(banlist_data)

        
        return ban_list
        
    

    def getftpini(self):
        def handleDownload(line):
            if line[0:15] == 'ActiveMapCycle=':
                self.active_map_cycle = int(line.partition('ActiveMapCycle=')[2])
            if line[0:14] == 'GameMapCycles=':
                self.map_cycles[str(self.map_cycle_no)] = line
                self.map_cycle_no += 1


        ftp = None
        try:
            ftp = self.ftpconnect()
            self._nbConsecutiveConnFailure = 0
            remoteSize = ftp.size(os.path.basename(self.ftpconfig['path']))
            self.verbose("Connection successful. Remote file size is %s" % remoteSize)
            ftp.retrlines('RETR ' + os.path.basename(self.ftpconfig['path']), handleDownload)          

        except ftplib.all_errors, e:
            self.debug(str(e))
            try:
                ftp.close()
                self.debug('FTP Connection Closed')
            except:
                pass
            ftp = None

        try:
            ftp.close()
        except:
            pass


    def ftpconnect(self):
        #self.debug('Python Version %s.%s, so setting timeout of 10 seconds' % (versionsearch.group(2), versionsearch.group(3)))
        self.verbose('Connecting to %s:%s ...' % (self.ftpconfig["host"], self.ftpconfig["port"]))
        ftp = FTP()
        ftp.set_debuglevel(self._ftplib_debug_level)
        ftp.connect(self.ftpconfig['host'], self.ftpconfig['port'], self._connectionTimeout)
        ftp.login(self.ftpconfig['user'], self.ftpconfig['password'])
        ftp.voidcmd('TYPE I')
        dir = os.path.dirname(self.ftpconfig['path'])
        self.debug('trying to cwd to [%s]' % dir)
        ftp.cwd(dir)
        return ftp
    
