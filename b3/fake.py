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

__version__ = '1.1'


import thread
import re
from b3.plugins.admin import AdminPlugin
import b3.parser
import b3.events
from sys import stdout
import Queue


class FakeConsole(b3.parser.Parser):
    Events = b3.events.eventManager
    screen = stdout
    noVerbose = False
    
    def __init__(self, configFile):
        b3.console = self
        self._timeStart = self.time()
        self.config = b3.config.load(configFile)
        self.storage = FakeStorage()
        self.clients  = b3.clients.Clients(self)
        self.queue = Queue.Queue(15)
        self.working = True
        thread.start_new_thread(self.handleEvents, ())
    
    def run(self):
        pass
    
    def getPlugin(self, name):
        if name == 'admin':
            return fakeAdminPlugin
        else:
            return None
    
    def getNextMap(self):
        return "ut4_theNextMap"
    
    def stripColors(self, text):
        return re.sub(self._reColor, '', text).strip()
    
    def say(self, msg):
        """send text to the server"""
        print "\t sending to gameserver >>> %s" % msg
    
    def tempban(self, client, reason, duration, admin, silent):
        """tempban a client"""
        self.info('tempbanning %s for %s (%s)' % (client.name, reason, duration))
    
    
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
        
class FakeAdminPlugin(AdminPlugin):
    def startup(self):
        self.registerEvent(b3.events.EVT_CLIENT_SAY)
        self.registerEvent(b3.events.EVT_CLIENT_PRIVATE_SAY)
    def warnClient(self, client, keyword, admin=None, timer=True, data='', duration=None):
        self.console.console(" give warning to %s (%s)" % (client.name, keyword))
        
class FakeStorage(object):
    _clients = {}
    _groups = []
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
        G.level = 20
        self._groups.append(G)
        
    def getClient(self, client):
        return client
    def setClient(self, client):
        return None
    def getGroups(self):
        return self._groups
    
class FakeClient(b3.clients.Client):
    console = None
    def __init__(self, **kwargs):
        self.console = fakeConsole
        b3.clients.Client.__init__(self, **kwargs)
    def message(self, msg):
        self.console.console("sending msg to client: %s" % msg)
    def says(self, msg):
        print "%s says \"%s\"" % (self.name, msg)
        b3.fake.fakeConsole.queueEvent(b3.events.Event(b3.events.EVT_CLIENT_SAY, msg, self))
    def says2team(self, msg):
        print "%s says to team \"%s\"" % (self.name, msg)
        b3.fake.fakeConsole.queueEvent(b3.events.Event(b3.events.EVT_CLIENT_TEAM_SAY, msg, self))
        

print "creating fakeConsole with @b3/conf/b3.xml"
fakeConsole = FakeConsole('@b3/conf/b3.xml')
print "creating fakeAdminPlugin with @b3/conf/plugin_admin.xml"
fakeAdminPlugin = FakeAdminPlugin(fakeConsole, '@b3/conf/plugin_admin.xml')
fakeAdminPlugin.startup()

joe = FakeClient(cid=1, name="Joe", guid="1")

