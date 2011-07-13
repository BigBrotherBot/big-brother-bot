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
# 2011-04-17 - 1.0 - Courgette
# * add logging of sent commands

"""
dummy rcon module for Frontline to satisfy B3 parser. 

Ideally, B3 parser should be changed to allow games such as homefront to 
not require a separated socket connection for rcon commands

To use that Rcon class, instanciate and use the set_homefront_client() method. 
Then you can expect this class to work like the other Rcon classes
"""

__author__  = 'Courgette'
__version__ = '1.0'


#--------------------------------------------------------------------------------------------------
class Rcon:
    def __init__(self, console, *args):
        self.console = console
        self.frontline_client = None
        
    def set_frontline_client(self, frontline_client):
        self.frontline_client = frontline_client
    
    def writelines(self, lines):
        for line in lines:
            self.write(line)

    def write(self, cmd, *args, **kwargs):
        if not self.frontline_client:
            return
        self.console.verbose(u'RCON :\t %s' % cmd)
        self.frontline_client.command(cmd)
        
    def flush(self):
        pass

    def close(self):
        pass
            
            
if __name__ == '__main__':
    """
    To run tests : 
    cd c:\whereever\is\b3
    c:\python26\python.exe b3/parsers/homefront/rcon.py <rcon_ip> <rcon_port> <rcon_password>
    """
    import sys, time, asyncore, thread, threading
    from b3.fake import fakeConsole
    from protocol import Client as FrontlineClient

#    if len(sys.argv) != 5:
#        host = raw_input('Enter game server host IP/name: ')
#        port = int(raw_input('Enter host port: '))
#        user = raw_input('Enter username: ')
#        pw = raw_input('Enter password: ')
#    else:
#        host = sys.argv[1]
#        port = int(sys.argv[2])
#        user = sys.argv[3]
#        pw = sys.argv[4]
   
    host = '127.0.0.1'
    port = 14507
    user = 'admin'
    pw = 'pass'
    
    
    def packetListener(packet):
        print(">>> received : %s" % packet)
    
    
    frontline_client = FrontlineClient(fakeConsole, host, port, user, pw, keepalive=True)
    frontline_client.add_listener(packetListener)
    working = True
    
    def run_hf_client(frontline_client):
        print('start client')
        try:
            while working and (frontline_client.connected or not frontline_client.authed):
                asyncore.loop(timeout=3, count=1)
        except EOFError, KeyboardInterrupt:
            frontline_client.close()
        print('end client')
    
    thread.start_new_thread(run_hf_client, (frontline_client,))
    
    time.sleep(3)
    
    r = Rcon(fakeConsole, ("what", 1337), "ever")
    r.set_frontline_client(frontline_client)
    
    def close_hf_connection():
        try:
            frontline_client.close()
        except:
            pass
    t = threading.Timer(10.0, frontline_client.close)
    t.start()
    
    for cmd in ('PLAYERLIST',
                'KICK',
                'PLAYERSAY',
                'SAY hello everybody',
                'CHATLOGGING TRUE',
                'MAPLIST',
                'GetCurrentMap',
                'GetNextMap',
                ):
        print('-----------------------------> test command : %r' % cmd)
        r.write(cmd) 
        time.sleep(1)
    
    for i in range(30):
        frontline_client.ping()
        time.sleep(.5)
    
    working = False
    
    print(".")
