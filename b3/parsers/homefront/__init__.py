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
# aaaa/mm/dd - who 
#    blablbalb
#

__author__  = 'xx'
__version__ = '0.0'


import b3
import b3.parser
import rcon


class HomefrontParser(b3.parser.Parser):
    '''
    The HomeFront B3 parser class
    '''
    gameName = "homefront"
    OutputClass = rcon.Rcon
    
    def startup(self):
        self.checkVersion()
        
        # add specific events
        #self.Events.createEvent('EVT_CLIENT_SQUAD_CHANGE', 'Client Squad Change')
                
        ## read game server info and store as much of it in self.game wich
        ## is an instance of the b3.game.Game class
        

        
    def getPlayerList(self):
        """\
        Query the game server for connected players.
        return a dict having players' id for keys and players' data as another dict for values
        """
        raise NotImplementedError

    def authorizeClients(self):
        """\
        For all connected players, fill the client object with properties allowing to find 
        the user in the database (usualy guid, or punkbuster id, ip) and call the 
        Client.auth() method 
        """
        raise NotImplementedError
    
    def sync(self):
        """\
        For all connected players returned by self.getPlayerList(), get the matching Client
        object from self.clients (with self.clients.getByCID(cid) or similar methods) and
        look for inconsistencies. If required call the client.disconnect() method to remove
        a client from self.clients.
        This is mainly useful for games where clients are identified by the slot number they
        occupy. On map change, a player A on slot 1 can leave making room for player B who
        connects on slot 1.
        """
        raise NotImplementedError
    
    def say(self, msg):
        """\
        broadcast a message to all players
        """
        raise NotImplementedError

    def saybig(self, msg):
        """\
        broadcast a message to all players in a way that will catch their attention.
        """
        raise NotImplementedError

    def message(self, client, text):
        """\
        display a message to a given player
        """
        raise NotImplementedError

    def kick(self, client, reason='', admin=None, silent=False, *kwargs):
        """\
        kick a given players
        """
        raise NotImplementedError

    def ban(self, client, reason='', admin=None, silent=False, *kwargs):
        """\
        ban a given players
        """
        raise NotImplementedError

    def unban(self, client, reason='', admin=None, silent=False, *kwargs):
        """\
        unban a given players
        """
        raise NotImplementedError

    def tempban(self, client, reason='', duration=2, admin=None, silent=False, *kwargs):
        """\
        tempban a given players
        """
        raise NotImplementedError

    def getMap(self):
        """\
        return the current map/level name
        """
        raise NotImplementedError

    def getMaps(self):
        """\
        return the available maps/levels name
        """
        raise NotImplementedError

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

    def getPlayerPings(self):
        """\
        returns a dict having players' id for keys and players' ping for values
        """
        raise NotImplementedError

    def getPlayerScores(self):
        """\
        returns a dict having players' id for keys and players' scores for values
        """
        raise NotImplementedError
        
    def inflictCustomPenalty(self, type, **kwargs):
        """
        Called if b3.admin.penalizeClient() does not know a given penalty type. 
        Overwrite this to add customized penalties for your game like 'slap', 'nuke', 
        'mute' or anything you want.
        /!\ This method must return True if the penalty was inflicted.
        """
        pass
