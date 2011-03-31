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
#

"""
dummy rcon module for Homefront to satisfy B3 parser. 

Ideally, B3 parser should be change to allow games such as homefront to not require 
a separated socket connection for rcon commands

To use that Rcon class, instanciate and use the set_homefront_client() method. 
Then you can expect this class to work like the other Rcon classes
"""

__author__  = 'Courgette'
__version__ = '0.1'


#--------------------------------------------------------------------------------------------------
class Rcon:
    def __init__(self, console, *args):
        self.console = console
        self.hfclient = None
        
    def set_homefront_client(self, hfclient):
        self.hfclient = hfclient
    
    def writelines(self, lines):
        for line in lines:
            self.write(line)

    def write(self, cmd, *args, **kwargs):
        if not self.hfclient:
            return
        self.hfclient.command(cmd)
        
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
    from protocol import Client as HomefrontClient

    if len(sys.argv) != 4:
        host = raw_input('Enter game server host IP/name: ')
        port = int(raw_input('Enter host port: '))
        pw = raw_input('Enter password: ')
    else:
        host = sys.argv[1]
        port = int(sys.argv[2])
        pw = sys.argv[3]
    
    
    def packetListener(packet):
        print(">>> received : %s" % packet)
    
    
    hfclient = HomefrontClient(fakeConsole, host, port, pw, keepalive=True)
    hfclient.add_listener(packetListener)
    working = True
    
    def run_hf_client(hfclient):
        print('start client')
        try:
            while working and (hfclient.connected or not hfclient.authed):
                #print("\t%s" % (time.time() - hfclient.last_pong_time))
                if time.time() - hfclient.last_pong_time > 6 and hfclient.last_ping_time < hfclient.last_pong_time:
                    hfclient.ping()
                asyncore.loop(timeout=3, count=1)
        except EOFError, KeyboardInterrupt:
            hfclient.close()
        print('end client')
    
    thread.start_new_thread(run_hf_client, (hfclient,))
    
    time.sleep(3)
    
    r = Rcon(fakeConsole, ("what", 1337), "ever")
    r.set_homefront_client(hfclient)
    
    def close_hf_connection():
        try:
            hfclient.close()
        except:
            pass
    t = threading.Timer(10.0, hfclient.close)
    t.start()
    
    print('-----------------------------> test command : say "B3 test"')
    r.write('say "B3 test"')  
    
    for i in range(30):
        hfclient.ping()
        time.sleep(.5)
    
    working = False
    
    print(".")
