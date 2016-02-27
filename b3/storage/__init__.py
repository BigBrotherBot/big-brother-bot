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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301 USA

__author__ = 'Courgette'
__version__ = '1.2'

PROTOCOLS = ('mysql', 'sqlite', 'postgresql')

class Storage(object):

    console = None
    protocol = None

    def connect(self):
        raise NotImplementedError

    def shutdown(self):
        raise NotImplementedError

    def getConnection(self):
        raise NotImplementedError

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
    
    def setClientIpAddress(self, ipalias):
        raise NotImplementedError
    
    def getClientIpAddress(self, ipalias):
        raise NotImplementedError
    
    def getClientIpAddresses(self, client):
        raise NotImplementedError
    
    def getLastPenalties(self, types='Ban', num=5):
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

    def getTables(self):
        raise NotImplementedError

    def truncateTable(self, table):
        raise NotImplementedError

    def status(self):
        raise NotImplementedError

from mysql import MysqlStorage
from sqlite import SqliteStorage
from postgresql import PostgresqlStorage

def getStorage(dsn, dsnDict, console):
    """
    Return an initialized storage module instance (not connected with the underlying storage layer).
    Every exception raised by this function should make B3 non-operational since we won't have storage support.
    :param dsn: The database connection string.
    :param dsnDict: The database connection string parsed into a dict.
    :param console: The console instance.
    :raise AttributeError: If we don't manage to setup a valid storage module.
    :raise ImportError: If the system misses the necessary libraries needed to setup the storage module.
    :return: The storage module object instance connected with the underlying storage layer.
    """
    if not dsnDict:
        raise AttributeError('invalid database configuration specified: %s' % dsn)

    if not dsnDict['protocol'] in PROTOCOLS:
        raise AttributeError('invalid storage protocol specified: %s: supported storage '
                             'protocols are: %s' % (dsnDict['protocol'], ','.join(PROTOCOLS)))

    construct = globals()['%sStorage' % dsnDict['protocol'].title()]
    return construct(dsn, dsnDict, console)