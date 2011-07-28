#
# BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2005 Michael "ThorN" Thornton
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

__author__  = 'Courgette'
__version__ = '1.0.0'


class Storage(object):
    console = None
        
    def getCounts(self):
        raise NotImplementedError
    
    def getClient(self, client):
        raise NotImplementedError
    
    def getClientsMatching(self, match):
        raise NotImplementedError
    
    def setClient(self, client):
        raise NotImplementedError
    
    def setClientAlias(self, alias):
        raise NotImplementedError
    
    def getClientAlias(self, alias):
        raise NotImplementedError
    
    def getClientAliases(self, client):
        raise NotImplementedError
    
    def setClientIpAddresse(self, ipalias):
        raise NotImplementedError
    
    def getClientIpAddress(self, ipalias):
        raise NotImplementedError
    
    def getClientIpAddresses(self, client):
        raise NotImplementedError
    
    def setClientPenalty(self, penalty):
        raise NotImplementedError
    
    def getClientPenalty(self, penalty):
        raise NotImplementedError
    
    def getClientPenalties(self, client, type='Ban'):
        raise NotImplementedError
    
    def getClientLastPenalty(self, client, type='Ban'):
        raise NotImplementedError
    
    def getClientFirstPenalty(self, client, type='Ban'):
        raise NotImplementedError
    
    def disableClientPenalties(self, client, type='Ban'):
        raise NotImplementedError
    
    def numPenalties(self, client, type='Ban'):
        raise NotImplementedError
    
    def getGroups(self):
        raise NotImplementedError

    def getGroup(self, group):
        raise NotImplementedError
        
        
from database import DatabaseStorage


def getStorage(type, *args):
    return globals()['%sStorage' % type.title()](*args)


