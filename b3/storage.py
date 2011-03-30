#
# BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2005 Michael "ThorN" Thornton
# 
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

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
#   2/22/2011  - 1.8a - SGT
#   Order aliases by num_used
#   07/01/2011 - 1.8 - xlr8or
#   Added queryFromFile to execute .sql files
#   12/12/2010 - 1.7.3 - courgette
#   fix setGroup for update query
#   29/06/2010 - 1.7.2 - xlr8or
#   fixed typo myqsldb -> msqldb in error message (thanks ryry46d9)
#   20/05/2010 - 1.7.2 - SGT
#   add IP to aliasses
#   27/03/2010 - 1.7.1 - xlr8or
#   enable setting different port for mysql connections
#   02/13/2010 - 1.7.0 - xlr8or
#   Added 'silent' option to query. Defaults to false. 
#   When set True it will raise an Exception for use in a try/except construction for a failed query
#   instead of just logging an error.
#   08/30/2009 - 1.6.3 - Bakes
#   Removed limit to number of aliases selected.
#   12/23/2008 - 1.6.2 - xlr8or
#   Added fix to catch mySQL connnection error 'mySQL server has gone away' and reconnect
#   01/23/2006 - 1.5.0 - ThorN
#   Added SQLite support, set "database" to "sqlite:///path/to/database.db"
#   11/19/2005 - 1.4.0 - ThorN
#   Added some convenience functions to the Cursor class and added better
#    error checking
#   10/31/2005 - 1.2.0 - ThorN
#   Changed it to use Python DB 2.0 API instead of ADODB
#   8/29/2005 - 1.2.0 - ThorN
#   Changed function to explicitly close the cursor
#   8/29/2005 - 1.1.1 - ThorN
#   Added getCounts()
#   7/23/2005 - 1.1.0 - ThorN
#   Added data column to penalties table

__author__  = 'ThorN'
__version__ = '1.8a'

import re, time, traceback, sys, thread, os

from b3.querybuilder import QueryBuilder
import b3.clients
import b3
from b3 import functions

#--------------------------------------------------------------------------------------------------
class Storage(object):
    console = None
        
    def getClient(self, client):
        return None
    
    def setClient(self, client):
        return None

    def shutdown(self):
        pass

#--------------------------------------------------------------------------------------------------
class DatabaseStorage(Storage):
    _reName = re.compile(r'([A-Z])')
    _reVar  = re.compile(r'_([a-z])')
    _lastConnectAttempt = 0
    _connections = []
    _lock = None
    _count = 0

    class Cursor:
        _cursor = None
        _conn = None
        fields = None
        EOF = False
        rowcount = 0
        lastrowid = 0
        
        def __init__(self, rs, conn):
            self._cursor = rs
            self._conn = conn

            self.rowcount  = self._cursor.rowcount
            self.lastrowid = self._cursor.lastrowid

            try:
                self.moveNext()
            except:
                pass # not a select statement

            self.EOF = (not self.fields or self.rowcount <= 0 or not self._cursor)

        def moveNext(self):
            if not self.EOF:
                self.fields = self._cursor.fetchone()
                self.EOF    = (not self.fields or not self._cursor)

                if self.EOF:
                    self.close()

            return self.EOF

        def getOneRow(self, default=None):
            if self.EOF:
                return default
            else:
                d = self.getRow()
                self.close()
                return d

        def getValue(self, key, default=None):
            d = self.getRow()
            if d.has_key(key):
                return d[key]
            else:
                return default

        def getRow(self):
            if self.EOF:
                return {}

            d = {}
            i = 0
            desc = self._cursor.description
            for i in xrange(0,len(self.fields)):
                d[desc[i][0]] = self.fields[i]

            return d
        
        def close(self):
            if self._cursor: self._cursor.close()
            self._cursor = None
            self.EOF = True

    def __init__(self, dsn, console):
        self.console = console
        self._lock = thread.allocate_lock()
        self.db = None
        self.dsn = dsn
        self.dsnDict = functions.splitDSN(self.dsn)
        self.connect()

    def getField(self, name):
        return self._reName.sub(r'_\1', name)

    def getVar(self, name):
        return self._reVar.sub(lambda m: m.group(1).upper(), name)

    def getConnection(self):
        protocol = self.dsnDict['protocol']

        if protocol == 'mysql':
            try:
                import MySQLdb
                return MySQLdb.connect(host=self.dsnDict['host'], port=self.dsnDict['port'], user=self.dsnDict['user'], passwd=self.dsnDict['password'], db=self.dsnDict['path'][1:]) 
            except ImportError, err:
                self.console.critical("%s. You need to install python-mysqldb. Look for 'dependencies' in B3 documentation.",err)
        elif protocol == 'sqlite':
            # Break it off here
            self.console.critical('SQLite is currently not supported!')
            import sqlite3
            path = self.dsnDict['path']
            if self.dsnDict['host']:
                path = self.dsnDict['host'] + path
            return sqlite3.connect(path)
        else:
            raise Exception('Unknown database protocol %s' % protocol)

    def closeConnection(self):
        for c in self._connections:
            try:
                c.close()
            except:
                pass
        
        self._connections = []
            
        if self.db:
            try:
                self.db.close()
            except:
                pass
            
            self.db = None

    def shutdown(self):
        self.closeConnection()

    def connect(self):
        self.console.bot('Attempting to connect to database %s://%s:******@%s%s...', self.dsnDict['protocol'], self.dsnDict['user'], self.dsnDict['host'], self.dsnDict['path'])
        self._count += 1

        self.closeConnection()

        if time.time() - self._lastConnectAttempt < 60:
            # dont retry for 60 seconds
            self.db = None
            return None

        try:
            self.db = self.getConnection()

            self._connections.append(self.db)
            self._lastConnectAttempt = 0
            self.console.bot('Connected to database [%s times]' % self._count)
            if self._count == 1:
                self.console.screen.write('Connecting to DB : OK\n')
        except Exception, e:
            self.console.error('Database connection failed, working in remote mode: %s - %s', e, traceback.extract_tb(sys.exc_info()[2]))
            if self._count == 1:
                self.console.screen.write('Connecting to DB : FAILED!\n')
            self.db = None
            self._lastConnectAttempt = time.time()

        return self.db

    def status(self):
        if self.db:
            return True
        else:
            return False

    def _query(self, query):
        self._lock.acquire()
        try:
            cursor = self.db.cursor()
            cursor.execute(query)
            c = DatabaseStorage.Cursor(cursor, self.db)
        finally:
            self._lock.release()
        return c

    def queryFromFile(self, file, silent=False):
        """This method executes an external sql file on the current database"""
        if self.db or self.connect():
            orig_stderr = sys.stderr # save standard error output
            if silent:
                sys.stderr = open(os.devnull, 'w') # silence the mysql warnings for existing tables and such
            sqlFile = b3.getAbsolutePath(file)
            if os.path.exists(sqlFile):
                f = open(sqlFile, 'r')
                sql_text = f.read()
                f.close()
                sql_statements = sql_text.split(';')
                for s in sql_statements:
                    try:
                        self.query(s, silent=True)
                    except:
                        pass
            else:
                raise Exception('sqlFile does not exist: %s' %sqlFile)
            sys.stderr = orig_stderr # reset standard error output
        return None


    def query(self, query, silent=False):
        # use existing connection or create a new one
        if self.db or self.connect():
            try:
                return self._query(query)
            except Exception, e:
                # (2013, 'Lost connection to MySQL server during query')
                # (2006, 'MySQL server has gone away')

                if e[0] == 2013 or e[0] == 2006:
                    self.console.warning('Query failed, trying to reconnect - %s: %s' % (type(e), e))

                    # query failed, try to reconnect
                    if self.connect():
                        try:
                            # retry query
                            return self._query(query)
                        except Exception, e:
                            # fall through to log error message
                            pass

                if silent:
                    raise Exception(e[0], e[1])
                else:
                    self.console.error('Query failed - %s: %s' % (type(e), e))

        return None
        
    def getCounts(self):
        counts = {
            'clients' : 0,
            'bans' : 0,
            'kicks' : 0,
            'warnings' : 0,
            'tempbans' : 0
        }

        cursor = self.query('SELECT COUNT(id) total FROM clients')

        if cursor and cursor.rowcount:
            counts['clients'] = int(cursor.getRow()['total'])
        
        cursor = self.query('SELECT COUNT(id) total, type FROM penalties GROUP BY type')

        if cursor:
            while not cursor.EOF:
                r = cursor.getRow()
                counts[r['type'] + 's'] = int(r['total'])
                cursor.moveNext()

            cursor.close()

        return counts            

    def getClient(self, client):
        self.console.debug('Storage: getClient %s' % str(client))

        if client.id > 0:        
            cursor = self.query(QueryBuilder(self.db).SelectQuery('*', 'clients', { 'id' : client.id }, None, 1))
        else:
            cursor = self.query(QueryBuilder(self.db).SelectQuery('*', 'clients', { 'guid' : client.guid }, None, 1))

        if not cursor:
            # connection failed, try local cache
            if self.console.config.has_option('admins_cache', client.guid):
                data = self.console.config.get('admins_cache', client.guid, True)
                self.console.debug('Pulling user form admins_cache %s' % data)
                id, name, level   = data.split(',')
                client.id         = id.strip()
                client.name       = name.strip()
                client._tempLevel = int(level.strip())

                return client
            else:
                raise KeyError, 'No client matching guid %s in admins_cache' % client.guid

        if not cursor.rowcount:
            cursor.close()
            raise KeyError, 'No client matching guid %s' % client.guid

        for k,v in cursor.getRow().iteritems():
            """
            if hasattr(client, k) and getattr(client, k):
                # don't set already set items
                continue
            """
            setattr(client, self.getVar(k), v)
        
        cursor.close()

        return client
    
    def getClientsMatching(self, match):
        self.console.debug('Storage: getClientsMatching %s' % str(match))

        cursor = self.query(QueryBuilder(self.db).SelectQuery('*', 'clients', match, 'time_edit DESC', 5))

        if not cursor:
            return ()

        clients = []
        while not cursor.EOF:
            g = cursor.getRow()

            client = b3.clients.Client()
            for k,v in g.iteritems():
                setattr(client, self.getVar(k), v)
            clients.append(client)
            cursor.moveNext()

        cursor.close()

        return clients

    def setClient(self, client):
        """
        id int(11)   PRI NULL auto_increment 
        ip varchar(16) YES   NULL   
        greeting varchar(128) YES   NULL   
        connections int(11) YES   NULL   
        time_edit int(11) YES   NULL   
        guid varchar(32)   MUL     
        pbid varchar(32) YES   NULL   
        name varchar(32) YES   NULL   
        time_add int(11) YES   NULL   
        auto_login int(11) YES   NULL   
        mask_level int(11) YES   NULL   
        group_bits int(11) 
        """

        self.console.debug('Storage: setClient %s' % str(client))

        fields = (
            'ip',
            'greeting',
            'connections',
            'time_edit',
            'guid',
            'pbid',
            'name',
            'time_add',
            'auto_login',
            'mask_level',
            'group_bits'
        )
    
        if client.id > 0:
            data = { 'id' : client.id }
        else:
            data = {}

        for f in fields:
            if hasattr(client, self.getVar(f)):
                data[f] = getattr(client, self.getVar(f))


        self.console.debug('Storage: setClient data %s' % str(data))
        if client.id > 0:
            self.query(QueryBuilder(self.db).UpdateQuery(data, 'clients', { 'id' : client.id }))
        else:
            cursor = self.query(QueryBuilder(self.db).InsertQuery(data, 'clients'))
            if cursor:
                client.id = cursor.lastrowid
            else:
                client.id = None

        return client.id    

    def setClientAlias(self, alias):
        """
        id  int(10)  UNSIGNED No    auto_increment              
        num_used  int(10)  UNSIGNED No  0                
        alias  varchar(32)   No                  
        ip varchar(16) YES   NULL   
        client_id  int(10)  UNSIGNED No  0                
        time_add  int(10)  UNSIGNED No  0                
        time_edit  int(10)  UNSIGNED No  0            
        """

        self.console.debug('Storage: setClientAlias %s' % str(alias))

        fields = (
            'num_used',
            'alias',
            'client_id',
            'time_add',
            'time_edit',
            'ip'
        )
    
        if alias.id:
            data = { 'id' : alias.id }
        else:
            data = {}

        for f in fields:
            if hasattr(alias, self.getVar(f)):
                data[f] = getattr(alias, self.getVar(f))

        self.console.debug('Storage: setClientAlias data %s' % str(data))
        if alias.id:
            self.query(QueryBuilder(self.db).UpdateQuery(data, 'aliases', { 'id' : alias.id }))
        else:
            cursor = self.query(QueryBuilder(self.db).InsertQuery(data, 'aliases'))

            if cursor:
                alias.id = cursor.lastrowid
            else:
                alias.id = None

        return alias.id

    def getClientAlias(self, alias):
        self.console.debug('Storage: getClientAlias %s' % str(alias))

        cursor = None
        if hasattr(alias, 'id') and alias.id > 0:
            cursor = self.query(QueryBuilder(self.db).SelectQuery('*', 'aliases', { 'id' : alias.id }, None, 1))
        elif hasattr(alias, 'alias') and hasattr(alias, 'clientId'):
            cursor = self.query(QueryBuilder(self.db).SelectQuery('*', 'aliases', { 'alias' : alias.alias, 'client_id' : alias.clientId }, None, 1))

        if not cursor or cursor.EOF:
            raise KeyError, 'No alias matching %s' % alias

        g = cursor.getOneRow()

        alias.id = int(g['id'])
        alias.alias    = g['alias']
        alias.timeAdd  = int(g['time_add'])
        alias.timeEdit = int(g['time_edit'])
        alias.clientId = int(g['client_id'])
        alias.numUsed = int(g['num_used'])
        alias.ip = g['ip']
        return alias

    def getClientAliases(self, client):
        self.console.debug('Storage: getClientAliases %s' % str(client))
        cursor = self.query(QueryBuilder(self.db).SelectQuery('*', 'aliases', { 'client_id' : client.id }, 'num_used DESC'))

        if not cursor:
            return ()

        aliases = []
        while not cursor.EOF:
            g = cursor.getRow()

            alias = b3.clients.Alias()
            alias.id = int(g['id'])
            alias.alias    = g['alias']
            alias.timeAdd  = int(g['time_add'])
            alias.timeEdit = int(g['time_edit'])
            alias.clientId = int(g['client_id'])
            alias.numUsed = int(g['num_used'])
            aliases.append(alias)
            cursor.moveNext()

        cursor.close()

        return aliases

    def setClientPenalty(self, penalty):
        """
        id  int(10)  UNSIGNED No    auto_increment              
        type  enum('Ban', 'TempBan', 'Kick', 'Warning')   No  Ban                
        duration  int(10)  UNSIGNED No  0                
        inactive  tinyint(1)  UNSIGNED No  0                
        admin_id  int(10)  UNSIGNED No  0                
        time_add  int(10)  UNSIGNED No  0                
        time_edit  int(10)  UNSIGNED No  0                
        time_expire  int(11)   No  0                
        reason  varchar(255)   No                  
        keyword  varchar(16)   No                  
        client_id  int(10)  UNSIGNED No  0       
        """

        fields = (
            'type',
            'duration',
            'inactive',
            'admin_id',
            'time_add',
            'time_edit',
            'time_expire',
            'reason',
            'keyword',
            'client_id',
            'data'
        )

        if penalty.id:
            data = { 'id' : penalty.id }
        else:
            data = {}

        if penalty.keyword and not re.match(r'^[a-z0-9]$', penalty.keyword, re.I):
            penalty.keyword = ''

        for f in fields:
            if hasattr(penalty, self.getVar(f)):
                data[f] = getattr(penalty, self.getVar(f))

        self.console.debug('Storage: setClientPenalty data %s' % str(data))
        if penalty.id:
            self.query(QueryBuilder(self.db).UpdateQuery(data, 'penalties', { 'id' : penalty.id }))
        else:
            cursor = self.query(QueryBuilder(self.db).InsertQuery(data, 'penalties'))
            if cursor:
                penalty.id = cursor.lastrowid
            else:
                penalty.id = None

        return penalty.id

    def getClientPenalty(self, penalty):
        self.console.debug('Storage: getClientPenalty %s' % str(penalty))

        cursor = self.query(QueryBuilder(self.db).SelectQuery('*', 'penalties', { 'id' : penalty.id }, None, 1))
        g = cursor.getOneRow()
        if not g:
            raise KeyError, 'No penalty matching id %s' % penalty.id
    
        penalty.id = int(g['id'])
        penalty.type    = g['type']
        penalty.keyword = g['keyword']
        penalty.reason = g['reason']
        penalty.data = g['data']
        penalty.duration = g['duration']
        penalty.inactive    = int(g['inactive'])
        penalty.timeAdd  = int(g['time_add'])
        penalty.timeEdit = int(g['time_edit'])
        penalty.timeExpire = int(g['time_expire'])
        penalty.clientId = int(g['client_id'])
        penalty.adminId = int(g['admin_id'])
    
        return penalty

    def getClientPenalties(self, client, type='Ban'):
        self.console.debug('Storage: getClientPenalties %s' % str(client))

        where = QueryBuilder(self.db).WhereClause( { 'type' : type, 'client_id' : client.id, 'inactive' : 0 } )
        where += ' && (time_expire = -1 || time_expire > %s)' % int(time.time())

        cursor = self.query(QueryBuilder(self.db).SelectQuery('*', 'penalties', where, 'time_add DESC'))

        if not cursor:
            return ()

        penalties = []
        while not cursor.EOF:
            g = cursor.getRow()

            if g['type'] == 'Warning':
                penaltyType = b3.clients.ClientWarning
            elif g['type'] == 'TempBan':
                penaltyType = b3.clients.ClientTempBan
            elif g['type'] == 'Kick':
                penaltyType = b3.clients.ClientKick
            elif g['type'] == 'Ban':
                penaltyType = b3.clients.ClientBan
            elif g['type'] == 'Notice':
                penaltyType = b3.clients.ClientNotice
            else:
                penaltyType = b3.clients.Penalty

            penalty = penaltyType()
            penalty.id = int(g['id'])
            penalty.type    = g['type']
            penalty.keyword = g['keyword']
            penalty.reason = g['reason']
            penalty.data = g['data']
            penalty.inactive    = int(g['inactive'])
            penalty.timeAdd  = int(g['time_add'])
            penalty.timeEdit = int(g['time_edit'])
            penalty.timeExpire = int(g['time_expire'])
            penalty.clientId = int(g['client_id'])
            penalty.adminId = int(g['admin_id'])
            penalty.duration = int(g['duration'])
            penalties.append(penalty)
            cursor.moveNext()

        cursor.close()

        return penalties

    def getClientLastPenalty(self, client, type='Ban'):
        where = QueryBuilder(self.db).WhereClause( { 'type' : type, 'client_id' : client.id, 'inactive' : 0 } )
        where += ' && (time_expire = -1 || time_expire > %s)' % int(time.time())

        cursor = self.query(QueryBuilder(self.db).SelectQuery('*', 'penalties', where, 'time_add DESC', 1))
        g = cursor.getOneRow()
        if not g:
            return None

        if g['type'] == 'Warning':
            P = b3.clients.ClientWarning()
        elif g['type'] == 'TempBan':
            P = b3.clients.ClientTempBan()
        elif g['type'] == 'Kick':
            P = b3.clients.ClientKick()
        elif g['type'] == 'Ban':
            P = b3.clients.ClientBan()
        else:
            P = b3.clients.ClientPenalty()

        P.id = int(g['id'])
        P.type    = g['type']
        P.keyword = g['keyword']
        P.reason = g['reason']
        P.data = g['data']
        P.inactive    = int(g['inactive'])
        P.timeAdd  = int(g['time_add'])
        P.timeEdit = int(g['time_edit'])
        P.timeExpire = int(g['time_expire'])
        P.clientId = int(g['client_id'])
        P.adminId = int(g['admin_id'])
        P.duration = int(g['duration'])

        return P

    def getClientFirstPenalty(self, client, type='Ban'):
        where = QueryBuilder(self.db).WhereClause( { 'type' : type, 'client_id' : client.id, 'inactive' : 0 } )
        where += ' && (time_expire = -1 || time_expire > %s)' % int(time.time())

        cursor = self.query(QueryBuilder(self.db).SelectQuery('*', 'penalties', where, 'time_expire DESC, time_add ASC', 1))
        g = cursor.getOneRow()
        if g:
            return None

        if g['type'] == 'Warning':
            P = b3.clients.ClientWarning()
        elif g['type'] == 'TempBan':
            P = b3.clients.ClientTempBan()
        elif g['type'] == 'Kick':
            P = b3.clients.ClientKick()
        elif g['type'] == 'Ban':
            P = b3.clients.ClientBan()
        else:
            P = b3.clients.ClientPenalty()

        P.id = int(g['id'])
        P.type    = g['type']
        P.keyword = g['keyword']
        P.reason = g['reason']
        P.data = g['data']
        P.inactive    = int(g['inactive'])
        P.timeAdd  = int(g['time_add'])
        P.timeEdit = int(g['time_edit'])
        P.timeExpire = int(g['time_expire'])
        P.clientId = int(g['client_id'])
        P.adminId = int(g['admin_id'])
        P.duration = int(g['duration'])

        return P

    def disableClientPenalties(self, client, type='Ban'):
        self.query(QueryBuilder(self.db).UpdateQuery( { 'inactive' : 1 }, 'penalties', { 'type' : type, 'client_id' : client.id, 'inactive' : 0 } ))        

    def numPenalties(self, client, type='Ban'):
        where = QueryBuilder(self.db).WhereClause( { 'type' : type, 'client_id' : client.id, 'inactive' : 0 } )
        where += ' && (time_expire = -1 || time_expire > %s)' % int(time.time())


        cursor = self.query('SELECT COUNT(id) total FROM penalties WHERE %s' % where)

        if not cursor:
            return 0

        return int(cursor.getValue('total', 0))

    _groups = None
    def getGroups(self):
        if not self._groups:
            cursor = self.query(QueryBuilder(self.db).SelectQuery('*', 'groups', None, 'level'))
            if not cursor:
                return []

            self._groups = []
            while not cursor.EOF:
                g = cursor.getRow()
                G = b3.clients.Group()

                G.id = int(g['id'])
                G.name    = g['name']
                G.keyword = g['keyword']
                G.level    = int(g['level'])
                G.timeAdd  = int(g['time_add'])
                G.timeEdit = int(g['time_edit'])

                self._groups.append(G)
                cursor.moveNext()
            cursor.close()

        return self._groups

    def getGroup(self, group):
        q = QueryBuilder(self.db).SelectQuery('*', 'groups', { 'keyword' : group.keyword }, None, 1)
        self.console.debug(q)
        cursor = self.query(q)
        g = cursor.getOneRow()
        if not g:
            raise KeyError, 'No group matching keyword %s' % group.keyword

        group.id = int(g['id'])
        group.name    = g['name']
        group.keyword = g['keyword']
        group.level    = int(g['level'])
        group.timeAdd  = int(g['time_add'])
        group.timeEdit = int(g['time_edit'])
    
        return group

    def setGroup(self, group):
        """
        id  int(10)  UNSIGNED No    auto_increment              
        time_edit  int(10)  UNSIGNED No  0                
        name  varchar(32)   No                  
        keyword  varchar(32)   No                  
        time_add  int(10)  UNSIGNED No  0                
        level  int(10)  UNSIGNED No  0
        """

        self.console.debug('Storage: setGroup %s' % str(group))

        fields = (
            'time_edit',
            'name',
            'keyword',
            'time_add',
            'level'
        )
    
        if group.id:
            data = { 'id' : group.id }
        else:
            data = {}

        for f in fields:
            if hasattr(group, self.getVar(f)):
                data[f] = getattr(group, self.getVar(f))


        self.console.debug('Storage: setGroup data %s' % str(data))
        if group.id:
            self.query(QueryBuilder(self.db).UpdateQuery(data, 'groups', { 'group' : group.id }))
        else:
            cursor = self.query(QueryBuilder(self.db).InsertQuery(data, 'groups'))

            if not cursor:
                group.id = None
            else:
                group.id = cursor.lastrowid

        return group.id

#--------------------------------------------------------------------------------------------------
def getStorage(type, *args):
    return globals()['%sStorage' % type.title()](*args)

if __name__ == '__main__':
    print getStorage('database', 'test', 'test')
