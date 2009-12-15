""" 
    This module make plugin testing simple. It provides you
    with fakeConsole and joe which can be used to say commands
    as if it where a player.
"""
""" Example with the spamcontrol plugin :
    
if __name__ == '__main__':
    from b3.fake import fakeConsole
    from b3.fake import joe
    
    p = SpamcontrolPlugin(fakeConsole, '@b3/conf/plugin_spamcontrol.xml')
    p.onStartup()
    
    p.info("---------- start spamming")
    joe.says("i'm spammmmmmmmmming")
    time.sleep(1)
    joe.says("i'm spammmmmmmmmming")
    time.sleep(1)
    joe.says("i'm spammmmmmmmmming")
    time.sleep(1)
    joe.says("i'm spammmmmmmmmming")
    time.sleep(1)
    joe.says("i'm spammmmmmmmmming")
    time.sleep(1)
    joe.says("i'm spammmmmmmmmming")
"""
""" Example with the adv plugin

if __name__ == '__main__':
    from b3.fake import fakeConsole
    from b3.fake import joe
    
    p = AdvPlugin(fakeConsole, '@b3/conf/plugin_adv.xml')
    p.onStartup()
    
    p.adv()
    print "-----------------------------"
    time.sleep(2)
    
    joe._maxLevel = 100
    joe.authed = True
    joe.says('!advlist')
    time.sleep(2)
    joe.says('!advrem 0')
    time.sleep(2)
    joe.says('!advrate 1')
    while True: pass # so we can see cron events 
"""
""" Example with the censor plugin :
    
if __name__ == '__main__':
    import time
    from b3.fake import fakeConsole
    from b3.fake import joe
    
    p = CensorPlugin(fakeConsole, '@b3/conf/plugin_censor.xml')
    p.onStartup()

    fakeConsole.noVerbose = True
    joe._maxLevel = 0
    joe.connected = True
    
    #p.onEvent(b3.events.Event(b3.events.EVT_CLIENT_SAY, "fuck", joe))
    joe.says('hello')
    joe.says('fuck')
    joe.says('nothing wrong')
    joe.says('ass')
    joe.says('shit')
    
    time.sleep(2)
"""

__version__ = '1.2'


import thread
import re
import time
from b3.plugins.admin import AdminPlugin
import b3.parsers.punkbuster
import b3.parser
import b3.events
from sys import stdout
import Queue
import StringIO


class FakeConsole(b3.parser.Parser):
    Events = b3.events.eventManager
    screen = stdout
    noVerbose = False
    input = None
    
    def __init__(self, config):
        b3.console = self
        self._timeStart = self.time()
        
        if isinstance(config, b3.config.XmlConfigParser) \
            or isinstance(config, b3.config.CfgConfigParser):
            self.config = config
        else:
            self.config = b3.config.load(config)
        
        self.storage = FakeStorage()
        self.clients  = b3.clients.Clients(self)
        self.game = b3.game.Game(self, "fakeGame")
        
        if not self.config.has_option('server', 'punkbuster') or self.config.getboolean('server', 'punkbuster'):
            self.PunkBuster = b3.parsers.punkbuster.PunkBuster(self)
        
        self.input = StringIO.StringIO()
        
        self.queue = Queue.Queue(15)
        self.working = True
        thread.start_new_thread(self.handleEvents, ())
    
    def run(self):
        pass
    
    def getPlugin(self, name):
        if name == 'admin':
            return fakeAdminPlugin
        else:
            return b3.parser.Parser.getPlugin(self, name)
    
    def sync(self):
        return {}
    
    def getNextMap(self):
        return "ut4_theNextMap"
    
    def getPlayerScores(self):
        return {0:5,1:4}
    
    def say(self, msg):
        """send text to the server"""
        print ">>> %s" % re.sub(re.compile('\^[0-9]'), '', msg).strip()
    
    def write(self, msg):
        """send text to the console"""
        print "### %s" % re.sub(re.compile('\^[0-9]'), '', msg).strip()
    
    def tempban(self, client, reason, duration, admin, silent):
        """tempban a client"""
        print '>>>tempbanning %s for %s (%s)' % (client.name, reason, duration)
    
    def kick(self, client, reason='', admin=None, silent=False, *kwargs):
        if isinstance(client, str) and re.match('^[0-9]+$', client):
            self.write(self.getCommand('kick', cid=client, reason=reason))
            return
        elif admin:
            reason = self.getMessage('kicked_by', client.exactName, admin.exactName, reason)
        else:
            reason = self.getMessage('kicked', client.exactName, reason)

        if self.PunkBuster:
            self.PunkBuster.kick(client, 0.5, reason)
        else:
            self.write(self.getCommand('kick', cid=client.cid, reason=reason))

        if not silent:
            self.say(reason)

        self.queueEvent(b3.events.Event(b3.events.EVT_CLIENT_KICK, reason, client))
        client.disconnect()
    
    def message(self, client, text):
        if client == None:
            self.say(text)
        elif client.cid == None:
            pass
        else:
            print "sending msg to %s: %s" % (client.name, re.sub(re.compile('\^[0-9]'), '', text).strip())
    
    ##############################
    
    def error(self, msg, *args, **kwargs):
        """Log an error"""
        print 'ERROR    : ' + msg % args

    def debug(self, msg, *args, **kwargs):
        """Log a debug message"""
        print 'DEBUG    : ' + msg % args

    def bot(self, msg, *args, **kwargs):
        """Log a bot message"""
        print 'BOT      : ' + msg % args

    def verbose(self, msg, *args, **kwargs):
        """Log a verbose message"""
        if self.noVerbose: return
        print 'VERBOSE  : ' + msg % args

    def verbose2(self, msg, *args, **kwargs):
        """Log an extra verbose message"""
        print 'VERBOSE2 : ' + msg % args

    def console(self, msg, *args, **kwargs):
        """Log a message from the console"""
        print 'CONSOLE  : ' + msg % args

    def warning(self, msg, *args, **kwargs):
        """Log a message from the console"""
        print 'WARNING  : ' + msg % args

    def info(self, msg, *args, **kwargs):
        """Log a message from the console"""
        print 'INFO     : ' + msg % args

    def exception(self, msg, *args, **kwargs):
        """Log a message from the console"""
        print 'EXCEPTION: ' + msg % args

    def critical(self, msg, *args, **kwargs):
        """Log a message from the console"""
        print 'CRITICAL : ' + msg % args
        
class FakeColoredConsole(FakeConsole):
    
    def printColor (self, string):
        colors = {"default":0, "black":30, "red":31, "green":32, "yellow":33,
                    "blue":34,"magenta":35, "cyan":36, "white":37, "black":38,
                    "black":39} #33[%colors%m
        
        for color in colors:
            color_string = "\033[%dm\033[1m" % colors[color]
            string = string.replace("<%s>" % color, color_string).replace("</%s>" % color, "\033[0m")
        
        print string
        
    def error(self, msg, *args, **kwargs):
        """Log an error"""
        self.printColor('<red>ERROR</red>    : ' + msg % args)

    def debug(self, msg, *args, **kwargs):
        """Log a debug message"""
        self.printColor( '<cyan>DEBUG</cyan>    : ' + msg % args)

    def bot(self, msg, *args, **kwargs):
        """Log a bot message"""
        self.printColor( 'BOT      : ' + msg % args)

    def verbose(self, msg, *args, **kwargs):
        """Log a verbose message"""
        self.printColor( '<green>VERBOSE</green>  : ' + msg % args)

    def verbose2(self, msg, *args, **kwargs):
        """Log an extra verbose message"""
        self.printColor( '<green>VERBOSE2</green> : ' + msg % args)

    def console(self, msg, *args, **kwargs):
        """Log a message from the console"""
        self.printColor( 'CONSOLE  : ' + msg % args)

    def warning(self, msg, *args, **kwargs):
        """Log a message from the console"""
        self.printColor( '<yellow>WARNING</yellow>  : ' + msg % args)

    def info(self, msg, *args, **kwargs):
        """Log a message from the console"""
        self.printColor( 'INFO     : ' + msg % args)

    def exception(self, msg, *args, **kwargs):
        """Log a message from the console"""
        self.printColor( '<red>EXCEPTION</red>: ' + msg % args)

    def critical(self, msg, *args, **kwargs):
        """Log a message from the console"""
        self.printColor( '<red>CRITICAL</red> : ' + msg % args)
        
class FakeStorage(object):
    _clients = {}
    _groups = []
    db = None
    def __init__(self):
        G = b3.clients.Group()
        G.id = 1
        G.name = 'User'
        G.keyword = 'user'
        G.level = 1
        self._groups.append(G)
        
        G = b3.clients.Group()
        G.id = 2
        G.name = 'Regular'
        G.keyword = 'regular'
        G.level = 2
        self._groups.append(G)
        
        G = b3.clients.Group()
        G.id = 8
        G.name = 'Moderator'
        G.keyword = 'moderator'
        G.level = 20
        self._groups.append(G)
        
        G = b3.clients.Group()
        G.id = 16
        G.name = 'Admin'
        G.keyword = 'admin'
        G.level = 40
        self._groups.append(G)
        
        G = b3.clients.Group()
        G.id = 128
        G.name = 'Super Admin'
        G.keyword = 'superadmin'
        G.level = 100
        self._groups.append(G)
        
    def getClient(self, client):
        return client
    def setClient(self, client):
        return None
    def getGroups(self):
        return self._groups
    def shutdown(self):
        pass
    
class FakeClient(b3.clients.Client):
    console = None
    
    def __init__(self, console, **kwargs):
        self.console = console
        b3.clients.Client.__init__(self, **kwargs)
                
    def pushEvent(self, event):
        self.console.queueEvent(event)
        time.sleep(0.3)
    
    def message(self, msg):
        print "sending msg to %s: %s" % (self.name, re.sub(re.compile('\^[0-9]'), '', msg).strip())
        
    def connects(self, cid):
        print "\n%s connects to the game on slot #%s" % (self.name, cid)
        self.cid = cid
        self.timeAdd = self.console.time()
        #self.console.clients.newClient(cid)
        clients = self.console.clients
        clients[self.cid] = self
        clients.resetIndex()

        self.console.debug('Client Connected: [%s] %s - %s (%s)', clients[self.cid].cid, clients[self.cid].name, clients[self.cid].guid, clients[self.cid].data)

        self.pushEvent(b3.events.Event(b3.events.EVT_CLIENT_CONNECT, self, self))
    
        if self.guid:
            self.auth()
        elif not self.authed:
            clients.authorizeClients()
         
    def disconnects(self):
        print "\n%s disconnects from slot #%s" % (self.name, self.cid)
        self.console.clients.disconnect(self)
        self.cid = None
        self.authed = False
        self._pluginData = {}
        self.state = b3.STATE_UNKNOWN
    
    def says(self, msg):
        print "\n%s says \"%s\"" % (self.name, msg)
        self.pushEvent(b3.events.Event(b3.events.EVT_CLIENT_SAY, msg, self))
        
    def says2team(self, msg):
        print "\n%s says to team \"%s\"" % (self.name, msg)
        self.pushEvent(b3.events.Event(b3.events.EVT_CLIENT_TEAM_SAY, msg, self))
        
    def damages(self, victim, points=34.0):
        print "\n%s damages %s for %s points" % (self.name, victim.name, points)
        if self == victim:
            e = b3.events.EVT_CLIENT_DAMAGE_SELF
        elif self.team != b3.TEAM_UNKNOWN and self.team == victim.team:
            e = b3.events.EVT_CLIENT_DAMAGE_TEAM
        else:
            e = b3.events.EVT_CLIENT_DAMAGE
        self.pushEvent( b3.events.Event(e, (points, 1, 1, 1), self, victim))
        
    def kills(self, victim):
        print "\n%s kills %s" % (self.name, victim.name)
        if self == victim:
            self.suicides()
            return
        elif self.team != b3.TEAM_UNKNOWN and self.team == victim.team:
            e = b3.events.EVT_CLIENT_KILL_TEAM
        else:
            e = b3.events.EVT_CLIENT_KILL
        self.pushEvent(b3.events.Event(e, (100, 1, 1, 1), self, victim))
        
    def suicides(self):
        print "\n%s kills himself" % self.name
        self.pushEvent(b3.events.Event(b3.events.EVT_CLIENT_SUICIDE, 
                                                       (100, 1, 1, 1), 
                                                       self, victim))
        
    def doAction(self, actiontype):
        self.console.queueEvent((b3.events.Event(b3.events.EVT_CLIENT_ACTION, actiontype, self)))

    def triggerEvent(self, type, data, target=None):
        print "\n%s trigger event %s" % (self.name, type)
        self.pushEvent(b3.events.Event(type, data, self, target))


#####################################################################################

print "creating fakeConsole with @b3/conf/b3.xml"
fakeConsole = FakeConsole('@b3/conf/b3.xml')

print "creating fakeAdminPlugin with @b3/conf/plugin_admin.xml"
fakeAdminPlugin = AdminPlugin(fakeConsole, '@b3/conf/plugin_admin.xml')
fakeAdminPlugin.onStartup()

joe = FakeClient(fakeConsole, name="Joe", exactName="Joe", guid="zaerezarezar", groupBits=1, team=b3.TEAM_UNKNOWN)
simon = FakeClient(fakeConsole, name="Simon", exactName="Simon", guid="qsdfdsqfdsqf", groupBits=0, team=b3.TEAM_UNKNOWN)
moderator = FakeClient(fakeConsole, name="Moderator", exactName="Moderator", guid="sdf455ezr", groupBits=8, team=b3.TEAM_UNKNOWN)
superadmin = FakeClient(fakeConsole, name="God", exactName="God", guid="f4qfer654r", groupBits=128, team=b3.TEAM_UNKNOWN)
