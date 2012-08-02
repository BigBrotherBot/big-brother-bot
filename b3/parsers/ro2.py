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
# 2011-09-30 : 0.4
# * Made webconnect a method and added comments to new methods
# 2011-10-03 : 0.5
# * Seperate out Team and Global chat - squad chat is totally missing from log and web admin
# * Make sure IP's get logged
# * Remove rcon references and rcon.py
# 2011-10-06 : 0.6
# * Kick client if on server when banned
# * Keep running on map change
# * Allow for username in xml file
# 2011-10-8 : 0.7
# * Correct error in ban-kick
# * Rewrite player names logic for extended characters
#   2011-10-16 : 0.8
# * !map working
# * Player with funny accented i character now show in !list
#   2011-11-01 : 1.0
# * Some re-writes and corrections
# * Implement !nextmap
#   2011-11-02 : 1.1
# * Allow use of # instead of @ for client id nos (@ brings up console on some keyboard layouts and cannot go into chat)
#   2011-12-19 : 1.2
#   Don't process B3 messages as chat
#   Auth client if not already authed when chat used
#   2011-12-28 : 1.3
#   Allow Q3 Color Codes in names, since game doesn't filter them out
#   2012-01-27 : 1.4
#   Track team changes for eg teamspeak plugin
#
#
from b3 import functions
from b3.parser import Parser
from ftplib import FTP
import b3
import b3.cron
import ftplib
import os
import re
import string
import sys
import time
import urllib
import urllib2
import cookielib
import hashlib


__author__  = 'Courgette, xlr8or, Freelander, 82ndab-Bravo17'
__version__ = '1.4'


class Ro2Parser(b3.parser.Parser):
    """
    The Ref Orchestra 2 B3 parser class
    """
    gameName = "redorchestra2"
    PunkBuster = None 
    # RO2 engine does not support color code, so we need this property
    # in order to get stripColors working
    _reColor = re.compile(r'(\^[0-9])')
    _reSteamId64 = re.compile(r'^[0-9]{17}$')
    ftpconfig = None
    _ftplib_debug_level = 0 # 0: no debug, 1: normal debug, 2: extended debug
    _ftpconnectionTimeout = 30
    _playerlistInterval = 30
    _server_banlist = {}
    _read_write_delay=1
    _write_queue=[]
    _read_queue=[]
    _ini_file = False
    url=''
    login_page=''
    site=''
    user_agent=''
    username=''
    password=''
    password_hash=''
    cj=None
    headers = {}
    opener=None
    map_cycles = {}
    map_cycle_no = 0
    active_map_cycle = 0
    _gametypes = {"TE" : "ROGame.ROGameInfoTerritories", "CD" : "ROGame.ROGameInfoCountdown", "FF" : "ROGame.ROGameInfoFirefight" }
    _maps = {"TE" : ['TE-Apartments', 'TE-Barracks', 'TE-CommisarsHouse', 'TE-FallenFighters', 'TE-GrainElevator', 'TE-Gumrak', 'TE-PavlovsHouse', 'TE-RedOctoberFactory', 'TE-Spartanovka', 'TE-Station'],
            "CD" : ['CD-Apartments', 'CD-Barracks', 'CD-CommisarsHouse', 'CD-FallenFighters', 'CD-GrainElevator', 'CD-Gumrak', 'CD-PavlovsHouse', 'CD-RedOctoberFactory', 'CD-Spartanovka', 'CD-Station'],
            "FF" : ['FF-Apartments', 'FF-Barracks', 'FF-GrainElevator', 'FF-Station']
            }

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
        if self.config.has_option('server','ro2admin'):
            self.username = self.config.get('server', 'ro2admin')
        else:
            self.username="Admin"
        
        
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
        self.headers = {'User-Agent' : self.user_agent, "Accept": "ext/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8", "Accept-Language" : "en-us,en;q =0.5", "Content-type": "application/x-www-form-urlencoded", "Accept-Charset" : "ISO-8859-1,utf-8;q=0.7,*;q=0.7", "Referer" : ''}
        self.site=self._publicIp + ':' + str(self._rconPort)
        self.login_page="ServerAdmin"
        self.password=self._rconPassword
        
        self.password_hash = "$sha1$%s" % hashlib.sha1("%s%s" % (self.password, self.username)).hexdigest()

        self.url = "http://%s/%s" % (self.site, self.login_page)
        
    def handle_chat(self, data):
        """Handle the chat from players"""
        if string.capitalize(data['div_class']) == 'Chatnotice':
            return
        func = 'onChat_type%s' % (string.capitalize(data['div_class']))

        if hasattr(self, func):
            self.debug('routing ----> %s' % func)
            func = getattr(self, func)
            event = func(data)
            if event:
                if event != 'Unable to Auth client':
                    self.queueEvent(event)
                else:
                    return
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
            #While we are working, connect to the RO2 server
            self._paused=False
            if self._paused:
                if not self._pauseNotice:
                    self.bot('PAUSED - Not parsing any lines, B3 will be out of sync.')
                    self._pauseNotice = True
            else:
                self._pauseNotice = False
                counter = 0
                while len(self._write_queue) == 0 and counter < 5:
                    time.sleep(.2)
                    counter +=1
                
                if not len(self._write_queue):
                    self.readwriteajax()
                else:
                    self.debug('Go to ajax')
                    message = self._write_queue.pop(0)
                    self.debug(self._write_queue)
                    self.readwriteajax(message)
                    
                while len(self._read_queue):
                    chat_data = self._read_queue.pop(0)
                    self.handle_chat(chat_data)
                
                counter = 0
                time.sleep(.5)
        self.bot('Stop listening.')

        if self.exiting.acquire(1) and self.exitcode:
            sys.exit(self.exitcode)
                
    def readwriteweb(self, data= None, referer=None, addurl=None):
        """Handles Reading and Writing to the web interface"""
        data_url = self.url + addurl
        if not referer:
            referer = data_url
        else:
            referer = self.url + referer
            
        self.headers['Referer'] = referer
        
        try:
            request_console = urllib2.Request(data_url, data, self.headers)
            console_read = self.opener.open(request_console)
            console_data = console_read.read()
            return console_data
            
        except Exception:
            self.debug('Failed to open URL')
            self.webconnect()
            return 

    def webconnect(self):
        """Login and make initial connection to the web interface"""
        remember=-1        
        password=''
        login_url = self.url + '/'
        headers = {'Content-type' : 'application/x-www-form-urlencoded', 'User-Agent' : self.user_agent}
        self.cj = cookielib.LWPCookieJar()
        self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cj))
        urllib2.install_opener(self.opener)
        findpage_attempt = 0
        self._paused = True
        response = ""
        while findpage_attempt < 11:
            try:
                request = urllib2.Request(login_url, None, headers)
                page = urllib2.urlopen(request)
                response = page.read()
                break
            except Exception:
                findpage_attempt += 1
                if findpage_attempt > 10:
                    self.debug('Failed to find web page - wait 10 seconds')
                    time.sleep(10)
                    findpage_attempt = 1
                else:
                    time.sleep(1)
                    self.debug('Failed to find Web page %s - Wait 1 second' % findpage_attempt)
                    
        #<input type="hidden" name="token" value="3309899D" />
        token_start = response.partition('<input type="hidden" name="token" value="')
        token = token_start[2]
        token_value = token[0:8]

        login_url = self.url + '/'
        referer = login_url
        data = urllib.urlencode({ 'token' : token_value, 'password_hash' : self.password_hash, 'username' : self.username, 'password' : password, 'remember' : remember })
        self.headers['Referer'] = referer
        
        login_attempt = 1
        while login_attempt < 11:
            try:
                self.debug('Login attempt %s' % login_attempt)
                request_console = urllib2.Request(login_url, data, self.headers)
                console_read = self.opener.open(request_console)
                self._paused = False
                return True
            except Exception:
                self.debug('Failed to login %s' % login_attempt)
                self._paused = True
                login_attempt += 1
                if login_attempt > 11:
                    raise
                time.sleep(1)
        
        
    def readwriteajax(self, message = None):
        """Read and Write to the Ajax interface"""
        if message:
            message_text = self.addplus(message)
        else:
            message_text=''
    
        #<div class="chatmessage">
        #<span class="teamcolor" style="background: #8FB9B0;">&#160;</span>
        #<span class="username">&lt;82ndAB&gt;1LT.Bravo17 </span>:
        #<span class="message">test message from game</span>
        #</div>
        
        #<div class="chatmessage">
        #<span class="teamcolor" style="background: #8FB9B0;">&#160;</span>
        #<span class="teamnotice" style="color: #8FB9B0;">(Team)</span>
        #<span class="username" title="Axis">&lt;82ndAB&gt;1LT.Bravo17 </span>:
        #<span class="message">Team chat</span>
        #</div>
        
        #<div class="chatnotice">
        #<span class="noticesymbol">***</span> [<span class="username"></span>]
        #<span class="message">82ndAB ADMIN: No offensive names.</span>
        #</div>
        
        chatdata_url = '/current/chat/data'
        #data = 'ajax=1&message=message+from+b3&teamsay=-1'
        data = 'ajax=1' + message_text
        referer = '/current/chat'
        chat_data = self.readwriteweb(data, referer, chatdata_url)

        if chat_data:
            if len(chat_data) > 0:
                self.decode_chat_data(chat_data)
 
        return
        

    def addplus(self, message):
        """Replace spaces with plusses ready for sending to the Ajax interface
        also replaces other characters that mess up html"""
        #ajax=1&message=test+chat&teamsay=-1
        message = message.replace(' ', '+')
        message = message.replace('?','%3F')
        message = '&message=' + message + '&teamsay=-1'
        self.debug(message)
        return message
        
    def decode_chat_data(self, data):
        """Decode the data reeived from the web interface and extract the chat data"""
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
            #Ignore what B3 just wrote
            chat_decoded['username'] = self.getUsername(chat_decoded['username'])
            if chat_decoded['username'] == self.username:
                return
            #Ignore new format for server messages 
            if chat_decoded['username'] == '' and chat_decoded['noticesymbol'] == '***':
                return
            self._read_queue.append(chat_decoded)
        
    def onChat_typeChatnotice(self,data):
        """Ignore Admin messages"""
        #Admin Chat ignore
        return None
        
        
        #<div class="chatmessage">
        #<span class="teamcolor" style="background: #8FB9B0;">&#160;</span>
        #<span class="username">&lt;82ndAB&gt;1LT.Bravo17 </span>:
        #<span class="message">test message from game</span>
        #</div>     
        
    def onChat_typeChatmessage(self, data):
        """Handle player chat"""
        name = self.getUsername(data['username'])
        text = data['message']
        # if a command and it contains #no convert to @no
        if text[0] == '!':
            match = re.search(r' #([0-9]+)\b', text)
            if match:
                start = match.start()
                text = (text[0:start+1] + '@' + text[start+2:])
                
        team = False
        if data.has_key('teamnotice'):
            team = True
            
        client = self.clients.getByName(name)
        if client is None:
            self.retrievePlayerList()
            self.debug("Trying to Auth client")
            client = self.clients.getByName(name)
            if client is None:
                self.debug("Unable to Auth client")
                return 'Unable to Auth client'

        if team:
            return self.getEvent('EVT_CLIENT_TEAM_SAY', text, client, client.team)
        else:
            return self.getEvent('EVT_CLIENT_SAY', text, client)

        
    def getUsername(self, name):
        """Retrieve the username and make it 'safe' """
        name = '%r' % name
        self.debug('namebefore = %s' % name)
        name = name.replace("\'", "")
        name = name.replace(r"\\", "\\")
        name = name.strip()

        name = self.stripColors(name)

        if name.find('&') != -1:
            name = name.replace('&lt;', '<')
            name = name.replace('&gt;', '>')
            
        self.debug('nameafter = %s' % name)            
        return name
 
    def decodeplayers(self, data):
        """Get the list of players from the web data"""
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
        """Get the next players details from the web data"""
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
        if spec.lower() == 'yes':
            player['team'] = self.getTeam('2')
        else:
            player['team'] = self.getTeam(color[0])
        
        return player
        
        
    def decodeBans(self, data):
        """Retrieve the list of Bans from the web data"""
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
    
    def getPlayerList(self):
        """\
        Returns a list of client objects
        """
        clients = self.clients.getList()
        return clients

    def write(self, msg, maxRetries=None):
        """Write a message to Console via Ajax"""
        if self.replay:
            self.bot('Sent rcon message: %s' % msg)
        elif self.output is None:
            pass
        else:
            msg = self.stripMsgColors(msg)
            self._write_queue.append(msg)
            return

    def writelines(self, msg):
        """Write a sequence of messages to Console via Ajax."""
        if self.replay:
            self.bot('Sent rcon message: %s' % msg)
        elif self.output is None:
            pass
        else:
            for line in msg:
                self.write(line)
                time.sleep(0.1)
            return
            
    def writeAdminCommand(self, cmd):
        """Write an Admin command via the Web interface console (Limited in what actually works)"""
        consoledata_url = self.url + '/console'
        data = 'command=' + cmd
        headers = {'User-Agent' : self.user_agent, "Accept": "ext/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8", "Accept-Language" : "en-us,en;q =0.5", "Content-type": "application/x-www-form-urlencoded", "Accept-Charset" : "ISO-8859-1,utf-8;q=0.7,*;q=0.7", "Referer" : consoledata_url}
        request_console = urllib2.Request(consoledata_url, data, headers)
        adminconsole_read = self.opener.open(request_console)
        console_data = adminconsole_read.read()
    
    
    def getServerPlayerList(self):
        """\
        Returns a list of client objects
        """
        self.verbose2('Retrieving Playerlist')
        playerlist_url = '/current/players'
        referer = '/current'
        data = None
        playerlist_data = self.readwriteweb(data, referer, playerlist_url)
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
        """Gets a list of non-authed players on the server"""
        for c in c_client_list:
            cl = c_client_list[c]
            uid = cl['guid']
            if len(uid) != 18:
                self.warning(u"weird UID : [%s]" % uid)
            
            # try to get the client by guid
            client = self.clients.getByGUID(uid)
            if not client:

                self.debug('adding client')
                self.debug(cl)
                client = self.clients.newClient(cl['playerid'], guid=uid, name=cl['name'], team=b3.TEAM_UNKNOWN, ip=cl['ip'])
                # update client data
                client.name = cl['name']
                client.team = cl['team']
                client.cid = cl['playerid']
                client.ip = cl['ip']
            else:
                if client.team != cl['team']:
                    self.verbose2('Team change detected for %s' % client.name)
                    client.team = cl['team']
            self.verbose2('onServerPlayer: name: %s, team: %s' %( client.name, client.team ))

            
    def syncDeletions(self, connected_clients):
        """\
        Check Clients list against all connected players returned by self.getServerPlayerList() and 
        if required call the client.disconnect() method to remove a client from self.clients.
        """

        client_cid_list = []

        for cl in connected_clients.values():
            client_cid_list.append(cl['playerid'])

        for client in self.clients.getList():

            if client.cid not in client_cid_list:
                self.debug('Removing %s from list' % client.name)
                client.disconnect()
                

    def sync(self, connected_clients=None):
        """\
        if connected_clients is None :
            get dict of connected players from self.getPlayerList()
        else use connected_clients as the list of connected players 
        For all connected players, get the matching Client
        object from self.clients (with self.clients.getByCID(cid) or similar methods) and
        look for inconsistencies. If required call the client.disconnect() method to remove
        a client from self.clients.
        This is mainly useful for games where clients are identified by the slot number they
        occupy. On map change, a player A on slot 1 can leave making room for player B who
        connects on slot 1.
        """
        if connected_clients is None:
            connected_clients = self.getPlayerList()
            
        self.debug("synchronizing clients")
        mlist = {}

        for client in connected_clients:
            mlist[client.cid] = client

        return mlist

    def say(self, msg):
        """\
        broadcast a message to all players
        """
        msg = self.stripMsgColors(msg)
        for line in self.getWrap(msg, self._settings['line_length'], self._settings['min_wrap_length']):
            line = self.stripMsgColors(line)
            self.write(self.getCommand('say',  prefix=self.msgPrefix, message=line))

    def message(self, client, text):
        """\
        display a message to a given player
        """
        # actually send private messages
        text = self.stripMsgColors(text)
        for line in self.getWrap(text, self._settings['line_length'], self._settings['min_wrap_length']):
            line = self.stripMsgColors(line)
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
        fullreason = self.stripMsgColors(fullreason)
        reason = self.stripMsgColors(reason)

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
        fullreason = self.stripMsgColors(fullreason)
        reason = self.stripMsgColors(reason)

        if not silent and fullreason != '':
            self.say(fullreason)
        
        banid = client.guid
        
        bandata_url = '/policy/bans'
        data = 'action=add&uniqueid=' + banid
        referer = None
        self.debug('Ban data %s' % data)
        console_data = self.readwriteweb(data, referer, bandata_url)
        
        self.queueEvent(self.getEvent('EVT_CLIENT_BAN', {'reason': reason, 'admin': admin}, client))
        
        #If client is on server kick them
        c = self.clients.getByGUID(banid)
        if c:
            self.writeAdminCommand(self.getCommand('kick', playerid=c.cid))
        
        client.disconnect()

    def unban(self, client, reason='', admin=None, silent=False, *kwargs):
        """\
        unban a given player
        """
        ban_list = self.retrieveBanlist()

        self.debug('using guid to unban')
        banid = client.guid
        ban_no = None
        try:
            ban_no = ban_list[banid]
        except Exception:
            if admin:
                admin.message(' %s not in server banlist' %client.name)

        if ban_no:
            ban_no = str(ban_no[8:])
        
            bandata_url = '/policy/bans'
            referer = None
            data = 'banid=plainid%3A' + ban_no + '&action=delete'
            banlist_data = self.readwriteweb(data, referer, bandata_url)
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
        fullreason = self.stripMsgColors(fullreason)
        reason = self.stripMsgColors(reason)

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
        map_rotation = []
        self.map_cycles = {}
        self.map_cycle_no = 0
        self.active_map_cycle = -1
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
                        if self.active_map_cycle >= 0 and self.map_cycle_no > self.active_map_cycle:
                            break

                input.close()
                
            map_line = self.map_cycles[str(self.active_map_cycle)]
            map_line = map_line.partition('Maps=("')[2]
            map_line = map_line.partition('"),RoundLimits=')[0]
            map_rotation.append(map_line.partition('","')[0])
            while map_line.find('","') != -1:
                map_line= map_line.partition('","')[2]
                map_rotation.append(map_line.partition('","')[0])

        return map_rotation

    def changeMap(self, map):
        """\
        load a given map/level
        return a list of suggested map names in cases it fails to recognize the map that was provided
        """
        #gametype=ROGame.ROGameInfoTerritories&map=TE-Barracks&mutatorGroupCount=0&urlextra=&action=change
        gametype = map[0:2]
        if self._gametypes.has_key(gametype) and self._maps[gametype].count(map) > 0:
            mapchange_url = '/current/change'
            data = 'gametype=' + self._gametypes[gametype] + '&map=' + map + '&mutatorGroupCount=0&urlextra=&action=change'
            referer = None
            console_data = self.readwriteweb(data, referer, mapchange_url)
        else:
            self.write(self.getCommand('say',  prefix=self.msgPrefix, message='Incorrect Gametype-Map combination'))

            return
            
    def getMap(self):
        """\
        load the next map/level
        """
        #<dt>Map</dt>
        #<dd><code>mapname</code>
        current_url = '/current'
        referer = None
        data = None
        current_data = self.readwriteweb(data, referer, current_url)
        if current_data.find('<dt>Map</dt>') == -1:
            self.debug('Map error')
            return None
        current_data = current_data.partition('<dt>Map</dt>')[2]
        if current_data.find('<dd><code>') == -1:
            self.debug('Map error')
            return None
        current_data = current_data.partition('<dd><code>')[2]
        mapname = current_data.partition('</code>')[0]
        
        return mapname
    
    def getNextMap(self):
        """\
        load the next map/level
        """
        nextmap=''
        map_rotation = self.getMaps()
        no_maps = len(map_rotation)
        currentmap = self.getMap()
        if map_rotation.count(currentmap) == 1:
            i = map_rotation.index(currentmap)
            if i < no_maps-1:
                nextmap = map_rotation[i+1]
            else:
                nextmap = map_rotation[0]
                
        else:
            nextmap = 'Unknown'
        
        return nextmap
        
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
        
    def getPlayerScores(self):
        """\
        returns a dict having players' id for keys and players' scores for values
        """
        scores = {}
        clients = self.clients.getList()
        for c in clients:
            try:
                scores[c.name] = 0
            except AttributeError:
                pass
        return scores
    
    def getTeam(self, team):
        """Get the players team"""
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
        Retrieve list of players on the server
        """
        if self._paused:
            return
        client_list = self.getServerPlayerList()
        self.findNewPlayers(client_list)
        self.syncDeletions(client_list)

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

    def stripMsgColors(self, text):
        return re.sub(self._reColor, '', text).strip()

    def stripColors(self, text):
        return text.strip()


    def getftpini(self):
        def handleDownload(line):
            if line[0:15] == 'ActiveMapCycle=':
                self.active_map_cycle = int(line.partition('ActiveMapCycle=')[2])
            if line[0:14] == 'GameMapCycles=':
                self.map_cycles[str(self.map_cycle_no)] = line
                self.debug(line)
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
            except Exception:
                pass
            ftp = None

        try:
            ftp.close()
        except Exception:
            pass


    def ftpconnect(self):
        #self.debug('Python Version %s.%s, so setting timeout of 10 seconds' % (versionsearch.group(2), versionsearch.group(3)))
        self.verbose('Connecting to %s:%s ...' % (self.ftpconfig["host"], self.ftpconfig["port"]))
        ftp = FTP()
        ftp.set_debuglevel(self._ftplib_debug_level)
        ftp.connect(self.ftpconfig['host'], self.ftpconfig['port'], self._ftpconnectionTimeout)
        ftp.login(self.ftpconfig['user'], self.ftpconfig['password'])
        ftp.voidcmd('TYPE I')
        dir = os.path.dirname(self.ftpconfig['path'])
        self.debug('trying to cwd to [%s]' % dir)
        ftp.cwd(dir)
        return ftp
    
    # =======================================
    # Not Implemented methods
    # =======================================
    
    def rotateMap(self):
        """\
        load the next map/level
        """
        self.say('Rotate Map not implemented')
    

