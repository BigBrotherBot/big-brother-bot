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

# CHANGELOG
# 1.3
#    * add FakeConsole.saybig(msg)
#    * FakeConsole.write() do not fail when arg is not a string
# 1.4 - 2010/11/01
#    * improve FakeStorage implementation
# 1.5 - 2010/11/21
#    * FakeConsole event mechanism does not involve a Queue anymore as this
#      class is meant to test one plugin at a time there is no need for 
#      producer/consumer pattern. This speeds up tests and simplifies the use
#      of a debugger. Also tests do not neet time.sleep() to make sure the events
#      were handled before checking results and moving on (unittest friendly)
# 1.6 - 2010/11/21
# * remove more time.sleep()
# * add message_history for FakeClient which allow to test if a client was sent a message afterward (unittest)
# 1.7 - 2011/06/04
# * replace FakeStorage with DatabaseStorage("sqlite://:memory:")
# 1.8 - 2011/06/06
# * add ban()
# * change data format for EVT_CLIENT_BAN_TEMP and EVT_CLIENT_BAN events
# 1.9 - 2011/06/09
# * FakeConsole now uses the logging module
# 1.10 - 2011/12/29
# * fix issue with plugins' registered events when importing fakeConsole in different TestSuites
__version__ = '1.10'


from b3.cvar import Cvar
from b3.plugins.admin import AdminPlugin
from b3.storage.database import DatabaseStorage
from sys import stdout
import StringIO
import b3.events
import b3.output
import b3.parser
import b3.parsers.punkbuster
import logging
from logging import handlers
import re
import time
import traceback
import sys

class FakeConsole(b3.parser.Parser):
    Events = b3.events.eventManager
    screen = stdout
    noVerbose = False
    input = None
    
    def __init__(self, config):
        b3.console = self
        self._timeStart = self.time()
        
        logging.basicConfig(level=b3.output.VERBOSE2, format='%(asctime)s\t%(levelname)s\t%(message)s')
        self.log = logging.getLogger('output')
        
        
        if isinstance(config, b3.config.XmlConfigParser) \
            or isinstance(config, b3.config.CfgConfigParser):
            self.config = config
        else:
            self.config = b3.config.load(config)
        
        self.storage =  DatabaseStorage("sqlite://:memory:", self)
        self.clients  = b3.clients.Clients(self)
        self.game = b3.game.Game(self, "fakeGame")
        self.game.mapName = 'ut4_turnpike'
        self.cvars = {}
        self._handlers = {}
        
        if not self.config.has_option('server', 'punkbuster') or self.config.getboolean('server', 'punkbuster'):
            self.PunkBuster = b3.parsers.punkbuster.PunkBuster(self)
        
        self.input = StringIO.StringIO()
        self.working = True
    
    def run(self):
        pass
    def queueEvent(self, event, expire=10):
        """Queue an event for processing. NO QUEUE, NO THREAD for faking speed up"""
        if not hasattr(event, 'type'):
            return False
        elif self._handlers.has_key(event.type):    # queue only if there are handlers to listen for this event
            self.verbose('Queueing event %s %s', self.Events.getName(event.type), event.data)
            self._handleEvent(event)
            return True
        return False
    
    def _handleEvent(self, event):
        """NO QUEUE, NO THREAD for faking speed up"""
        if event.type == b3.events.EVT_EXIT or event.type == b3.events.EVT_STOP:
            self.working = False

        nomore = False
        for hfunc in self._handlers[event.type]:
            if not hfunc.isEnabled():
                continue
            elif nomore:
                break

            self.verbose('Parsing Event: %s: %s', self.Events.getName(event.type), hfunc.__class__.__name__)
            try:
                hfunc.parseEvent(event)
                time.sleep(0.001)
            except b3.events.VetoEvent:
                # plugin called for event hault, do not continue processing
                self.bot('Event %s vetoed by %s', self.Events.getName(event.type), str(hfunc))
                nomore = True
            except SystemExit, e:
                self.exitcode = e.code
            except Exception, msg:
                self.error('handler %s could not handle event %s: %s: %s %s', hfunc.__class__.__name__, self.Events.getName(event.type), msg.__class__.__name__, msg, traceback.extract_tb(sys.exc_info()[2]))

    def shutdown(self):
        """Shutdown B3 - needed to be changed in FakeConsole due to no thread for dispatching events"""
        try:
            if self.working and self.exiting.acquire():
                self.bot('Shutting down...')
                self.working = False
                self._handleEvent(b3.events.Event(b3.events.EVT_STOP, ''))
                if self._cron:
                    self._cron.stop()
                self.bot('Shutting down database connections...')
                self.storage.shutdown()
        except Exception, e:
            self.error(e)

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
    
    def saybig(self, msg):
        """send bigtext to the server"""
        print "+++ %s" % re.sub(re.compile('\^[0-9]'), '', msg).strip()
    
    def write(self, msg, maxRetries=0):
        """send text to the console"""
        if type(msg) == str:
            print "### %s" % re.sub(re.compile('\^[0-9]'), '', msg).strip()
        else:
            # which happens for BFBC2
            print "### %s" % msg
    
    def writelines(self, lines):
        for line in lines:
            self.write(line)

    def authorizeClients(self):
        pass

    def ban(self, client, reason, admin, silent):
        """permban a client"""
        print '>>>permbanning %s (%s)' % (client.name, reason)
        self.queueEvent(self.getEvent('EVT_CLIENT_BAN', {'reason': reason, 'admin': admin}, client))
        client.disconnect()
    
    def tempban(self, client, reason, duration, admin, silent):
        """tempban a client"""
        print '>>>tempbanning %s for %s (%s)' % (client.name, reason, duration)
        self.queueEvent(self.getEvent('EVT_CLIENT_BAN_TEMP', {'reason': reason, 
                                                              'duration': duration, 
                                                              'admin': admin}
                                      , client))
        client.disconnect()
    
    def unban(self, client, reason='', admin=None, silent=False, *kwargs):
        """unban a client"""
        print '>>>unbanning %s (%s)' % (client.name, reason)
        self.queueEvent(self.getEvent('EVT_CLIENT_UNBAN', reason, client))
    
    def kick(self, client, reason='', admin=None, silent=False, *kwargs):
        if isinstance(client, str) and re.match('^[0-9]+$', client):
            self.write(self.getCommand('kick', cid=client, reason=reason))
            return
        elif admin:
            reason = self.getMessage('kicked_by', self.getMessageVariables(client=client, reason=reason, admin=admin))
        else:
            reason = self.getMessage('kicked', self.getMessageVariables(client=client, reason=reason))

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
    
    def getCvar(self, key):
        print "get cvar %s" % key
        return self.cvars.get(key)

    def setCvar(self, key, value):
        print "set cvar %s" % key
        c = Cvar(name=key,value=value)
        self.cvars[key] = c



class FakeClient(b3.clients.Client):
    console = None
    message_history = [] # this allows unittests to check if a message was sent to the client
    
    def __init__(self, console, **kwargs):
        self.console = console
        b3.clients.Client.__init__(self, **kwargs)
                
    def clearMessageHistory(self):
        self.message_history = []
    def getMessageHistoryLike(self, needle):
        clean_needle = re.sub(re.compile('\^[0-9]'), '', needle).strip()
        for m in self.message_history:
            if clean_needle in m:
                return m
        return None
    def getAllMessageHistoryLike(self, needle):
        result = []
        clean_needle = re.sub(re.compile('\^[0-9]'), '', needle).strip()
        for m in self.message_history:
            if clean_needle in m:
                result.append(m)
        return result
    
    def message(self, msg):
        cleanmsg = re.sub(re.compile('\^[0-9]'), '', msg).strip()
        self.message_history.append(cleanmsg)
        print "sending msg to %s: %s" % (self.name, cleanmsg)
    def warn(self, duration, warning, keyword=None, admin=None, data=''):
        w = b3.clients.Client.warn(self, duration, warning, keyword=None, admin=None, data='')
        print(">>>>%s gets a warning : %s" % (self, w))
    def connects(self, cid):
        print "\n%s connects to the game on slot #%s" % (self.name, cid)
        self.cid = cid
        self.timeAdd = self.console.time()
        #self.console.clients.newClient(cid)
        clients = self.console.clients
        clients[self.cid] = self
        clients.resetIndex()

        self.console.debug('Client Connected: [%s] %s - %s (%s)', clients[self.cid].cid, clients[self.cid].name, clients[self.cid].guid, clients[self.cid].data)

        self.console.queueEvent(b3.events.Event(b3.events.EVT_CLIENT_CONNECT, self, self))
    
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
        self.console.queueEvent(b3.events.Event(b3.events.EVT_CLIENT_SAY, msg, self))
        
    def says2team(self, msg):
        print "\n%s says to team \"%s\"" % (self.name, msg)
        self.console.queueEvent(b3.events.Event(b3.events.EVT_CLIENT_TEAM_SAY, msg, self))
        
    def damages(self, victim, points=34.0):
        print "\n%s damages %s for %s points" % (self.name, victim.name, points)
        if self == victim:
            e = b3.events.EVT_CLIENT_DAMAGE_SELF
        elif self.team != b3.TEAM_UNKNOWN and self.team == victim.team:
            e = b3.events.EVT_CLIENT_DAMAGE_TEAM
        else:
            e = b3.events.EVT_CLIENT_DAMAGE
        self.console.queueEvent( b3.events.Event(e, (points, 1, 1, 1), self, victim))
        
    def kills(self, victim):
        print "\n%s kills %s" % (self.name, victim.name)
        if self == victim:
            self.suicides()
            return
        elif self.team != b3.TEAM_UNKNOWN and self.team == victim.team:
            e = b3.events.EVT_CLIENT_KILL_TEAM
        else:
            e = b3.events.EVT_CLIENT_KILL
        self.console.queueEvent(b3.events.Event(e, (100, 1, 1, 1), self, victim))
        
    def suicides(self):
        print "\n%s kills himself" % self.name
        self.console.queueEvent(b3.events.Event(b3.events.EVT_CLIENT_SUICIDE, 
                                                       (100, 1, 1, 1), 
                                                       self, victim))
        
    def doAction(self, actiontype):
        self.console.queueEvent((b3.events.Event(b3.events.EVT_CLIENT_ACTION, actiontype, self)))

    def triggerEvent(self, type, data, target=None):
        print "\n%s trigger event %s" % (self.name, type)
        self.console.queueEvent(b3.events.Event(type, data, self, target))


#####################################################################################

print "creating fakeConsole with @b3/conf/b3.distribution.xml"
fakeConsole = FakeConsole('@b3/conf/b3.distribution.xml')

print "creating fakeAdminPlugin with @b3/conf/plugin_admin.xml"
fakeAdminPlugin = AdminPlugin(fakeConsole, '@b3/conf/plugin_admin.xml')
fakeAdminPlugin.onStartup()

joe = FakeClient(fakeConsole, name="Joe", exactName="Joe", guid="zaerezarezar", groupBits=1, team=b3.TEAM_UNKNOWN)
simon = FakeClient(fakeConsole, name="Simon", exactName="Simon", guid="qsdfdsqfdsqf", groupBits=0, team=b3.TEAM_UNKNOWN)
reg = FakeClient(fakeConsole, name="Reg", exactName="Reg", guid="qsdfdsqfdsqf33", groupBits=4, team=b3.TEAM_UNKNOWN)
moderator = FakeClient(fakeConsole, name="Moderator", exactName="Moderator", guid="sdf455ezr", groupBits=8, team=b3.TEAM_UNKNOWN)
admin = FakeClient(fakeConsole, name="Level-40-Admin", exactName="Level-40-Admin", guid="875sasda", groupBits=16, team=b3.TEAM_UNKNOWN)
superadmin = FakeClient(fakeConsole, name="God", exactName="God", guid="f4qfer654r", groupBits=128, team=b3.TEAM_UNKNOWN)
