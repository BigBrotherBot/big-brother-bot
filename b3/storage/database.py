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
#
# CHANGELOG
#
# 25/07/2014 - 1.16   - Fenix          - syntax cleanup
#                                      - removed executeSql() method: using only queryFromFile() which does the same
#                                      - reformat changelog
# 15/04/2014 - 1.15.1 - Fenix          - added missing import: b3.clients
# 20/01/2014 - 1.15   - Fenix          - refactored syntax: get close to PEP8
#                                      - fixed impossibility to retrieve group 'guest' in get_group()
# 12/08/2013 - 1.14   - Courgette      - add method get_tables()
# 26/11/2012 - 1.13   - Courgette      - add database columns 'login' and 'password' to the Client model
# 11/08/2012 - 1.12   - Courgette      - get_group can find group by level if keyword is not provided
# 29/10/2011 - 1.11.1 - 82ndab-Bravo17 - decode reason in penalty from system encodig and recode to UTF-8 to ensure
#                                        name is correctly encoded
# 31/05/2011 - 1.11.0 - Courgette      - sqlite compatible
#                                      - few fixes discovered doing unittests
# 11/04/2011 - 1.10.0 - Courgette      - the query() method now accepts a second parameter which can be an optional
#                                        dict of variables to bind on the query
# 08/04/2011 - 1.9.1  - Courgette      - remove str() wherever we could have unicode
# 02/03/2011 - 1.9    - Courgette      - do not catch exception when query fails
# 07/01/2011 - 1.8    - xlr8or         - added query_from_file to execute .sql files
# 12/12/2010 - 1.7.3  - Courgette      - fix set_group for update query
# 29/06/2010 - 1.7.2  - xlr8or         - fixed typo myqsldb -> msqldb in error message (thanks ryry46d9)
# 27/03/2010 - 1.7.1  - xlr8or         - enable setting different port for mysql connections
# 02/13/2010 - 1.7.0  - xlr8or         - added 'silent' option to query. Defaults to false.
#                                      - when set True it will raise an Exception for use in a try/except construction
#                                        for a failed query instead of just logging an error
# 08/30/2009 - 1.6.3  - Bakes          - removed limit to number of aliases selected
# 12/23/2008 - 1.6.2  - xlr8or         - added fix to catch mySQL connnection error 'mySQL server has gone away'
#                                        and reconnect
# 01/23/2006 - 1.5.0  - ThorN          - added SQLite support, set "database" to "sqlite:///path/to/database.db"
# 11/19/2005 - 1.4.0  - ThorN          - added some convenience functions to the Cursor class and added better
#                                        error checking
# 10/31/2005 - 1.2.0  - ThorN          - changed it to use Python DB 2.0 API instead of ADODB
# 08/29/2005 - 1.2.0  - ThorN          - changed function to explicitly close the cursor
# 08/29/2005 - 1.1.1  - ThorN          - added getCounts()
# 07/23/2005 - 1.1.0  - ThorN          - added data column to penalties table

__author__ = 'ThorN'
__version__ = '1.16'


import os
import re
import sys
import thread
import time
import traceback
import b3
import b3.clients

from b3 import functions
from b3.querybuilder import QueryBuilder
from b3.storage import Storage


class DatabaseStorage(Storage):

    _reName = re.compile(r'([A-Z])')
    _reVar = re.compile(r'_([a-z])')
    _lastConnectAttempt = 0
    _connections = []
    _lock = None
    _count = 0

    class Cursor:

        _cursor = None
        _conn = None

        fields = None
        lastrowid = 0
        rowcount = 0

        EOF = False

        def __init__(self, rs, conn):
            """
            Object constructor.
            :param rs: The opened result set
            :param conn: The database connection instance
            """
            self._cursor = rs
            self._conn = conn
            self.rowcount = self._cursor.rowcount
            self.lastrowid = self._cursor.lastrowid

            try:
                self.EOF = self.moveNext()
            except Exception:
                # not a select statement
                self.EOF = not self.fields or self.rowcount <= 0 or not self._cursor

        def moveNext(self):
            """
            Move the cursor to the next available record.
            :return True if there is one more record, False otherwise.
            """
            if not self.EOF:
                self.fields = self._cursor.fetchone()
                self.EOF = (not self.fields or not self._cursor)
                if self.EOF:
                    self.close()
            return self.EOF

        def getOneRow(self, default=None):
            """
            Return a row from the current result set and close it.
            :return The row fetched from the result set or default if the result set is empty.
            """
            if self.EOF:
                return default
            else:
                d = self.getRow()
                self.close()
                return d

        def getValue(self, key, default=None):
            """
            Return a value from the current result set row.
            :return The value extracted from the result set or default
                    if the the given key doesn't match a field of the result set.
            """
            d = self.getRow()
            if key in d.keys():
                return d[key]
            else:
                return default

        def getRow(self):
            """
            Return a result set row into a dict.
            :return The result set row or an empty dict if there
                    are no more records in this result set.
            """
            if self.EOF:
                return dict()
            d = dict()
            desc = self._cursor.description
            for i in xrange(0, len(self.fields)):
                d[desc[i][0]] = self.fields[i]
            return d

        def close(self):
            """
            Close the active result set.
            """
            if self._cursor:
                self._cursor.close()
            self._cursor = None
            self.EOF = True

    def __init__(self, dsn, console):
        """
        Object consstructor.
        :param dsn: The database connection string.
        :param console: The console instance.
        """
        self.console = console
        self._lock = thread.allocate_lock()
        self.db = None
        self.dsn = dsn
        self.dsnDict = functions.splitDSN(self.dsn)
        self.connect()

    def getTables(self):
        """
        List the tables of the current database.
        :return: list of strings.
        """
        tables = []
        protocol = self.dsnDict['protocol']

        if protocol == 'mysql':
            q = """SHOW TABLES"""
        elif protocol == 'sqlite':
            q = """SELECT * FROM sqlite_master WHERE type='table'"""
        else:
            raise AssertionError("unsupported database %s" % protocol)

        cursor = self.query(q)
        if cursor and not cursor.EOF:
            while not cursor.EOF:
                r = cursor.getRow()
                tables.append(r.values()[0])
                cursor.moveNext()
        return tables

    def getField(self, name):
        return self._reName.sub(r'_\1', name)

    def getVar(self, name):
        return self._reVar.sub(lambda m: m.group(1).upper(), name)

    def getConnection(self):
        """
        Establish a connection with the underlying storage layer.
        :return The connection instance.
        """
        protocol = self.dsnDict['protocol']

        if protocol == 'mysql':

            try:
                # validate dsnDict
                if not self.dsnDict['host']:
                    self.console.critical("Invalid MySQL host in "
                                          "%(protocol)s://%(user)s:******@%(host)s:%(port)s%(path)s" % self.dsnDict)
                elif not self.dsnDict['path'] or not self.dsnDict['path'][1:]:
                    self.console.critical("Missing MySQL database name in "
                                          "%(protocol)s://%(user)s:******@%(host)s:%(port)s%(path)s" % self.dsnDict)
                else:
                    import MySQLdb
                    return MySQLdb.connect(host=self.dsnDict['host'],
                                           port=self.dsnDict['port'],
                                           user=self.dsnDict['user'],
                                           passwd=self.dsnDict['password'],
                                           db=self.dsnDict['path'][1:],
                                           charset="utf8",
                                           use_unicode=True)
            except ImportError, e:
                MySQLdb = None # just to remove a warning
                self.console.critical("%s. You need to install python-mysqldb: look for 'dependencies' "
                                      "in B3 documentation.", e)

        elif protocol == 'sqlite':
            import sqlite3
            path = self.dsn[9:]
            filepath = b3.getAbsolutePath(path)
            self.console.info("Using database file: %s" % filepath)
            is_new_database = not os.path.isfile(filepath)
            conn = sqlite3.connect(filepath, check_same_thread=False)
            conn.isolation_level = None  # set autocommit mode
            if path == ':memory:' or is_new_database:
                self.console.info("Creating tables...")
                sql_file = b3.getAbsolutePath("@b3/sql/sqlite/b3.sql")
                with open(sql_file) as f:
                    conn.executescript(f.read())
            return conn

        else:
            raise Exception('unknown database protocol: %s' % protocol)

    def closeConnection(self):
        """
        Close the current active database connections.
        """
        for c in self._connections:
            try:
                c.close()
            except Exception:
                pass

        self._connections = []

        if self.db:
            try:
                self.db.close()
            except Exception:
                pass

            self.db = None

    def shutdown(self):
        """
        Just an alias for close_connection().
        """
        self.closeConnection()

    def connect(self):
        """
        Establish and return a connection with the storage layer.
        :return The connection instance.
        """
        if self.dsnDict['protocol'] == 'mysql':
            self.console.bot('Attempting to connect to database: %s://%s:******@%s%s...',
                             self.dsnDict['protocol'], self.dsnDict['user'],
                             self.dsnDict['host'], self.dsnDict['path'])
        else:
            self.console.bot('Attempting to connect to database: %s...', self.dsn)

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
            self.console.error('Database connection failed: working in remote mode: %s - %s',
                               e, traceback.extract_tb(sys.exc_info()[2]))
            if self._count == 1:
                self.console.screen.write('Connecting to DB : FAILED!\n')
            self.db = None
            self._lastConnectAttempt = time.time()

        return self.db

    def status(self):
        """
        Check whether the connection with the storage layer is active or not.
        :return True if the connection is active, False otherwise.
        """
        if self.db:
            return True
        else:
            return False

    def _query(self, query, bindata=None):
        """
        Execute a query on the storage layer (internal method).
        :param query: The query to execute.
        :param bindata: Data to bind to the given query.
        """
        self._lock.acquire()
        try:
            cursor = self.db.cursor()
            if bindata is None:
                cursor.execute(query)
            else:
                cursor.execute(query, bindata)
            c = DatabaseStorage.Cursor(cursor, self.db)
        finally:
            self._lock.release()
        return c

    def queryFromFile(self, fp, silent=False):
        """
        This method executes an external sql file on the current database.
        :param fp: The filepath of the file containing the SQL statements.
        :param silent: Whether or not to silence MySQL warnings.
        """
        if self.db or self.connect():
            # save standard error output
            orig_stderr = sys.stderr
            if silent:
                # silence the mysql warnings for existing tables and such
                sys.stderr = open(os.devnull, 'w')
            sql_file = b3.getAbsolutePath(fp)
            if os.path.exists(sql_file):
                f = open(sql_file, 'r')
                sql_text = f.read()
                f.close()
                sql_statements = sql_text.split(';')
                for s in sql_statements:
                    try:
                        self.query(s)
                    except Exception:
                        pass
            else:
                raise Exception('SQL file does not exist: %s' % sql_file)
            # reset standard error output
            sys.stderr = orig_stderr
        return None

    def query(self, query, bindata=None):
        """
        Execute a query on the storage layer.
        :param query: The query to execute.
        :param bindata: Data to bind to the given query.
        """
        # use existing connection or create a new one
        if self.db or self.connect():
            try:
                return self._query(query, bindata)
            except Exception, e:
                # (2013, 'Lost connection to MySQL server during query')
                # (2006, 'MySQL server has gone away')
                self.console.error('[%s] %r' % (query, bindata))

                if e[0] == 2013 or e[0] == 2006:
                    self.console.warning('Query failed: trying to reconnect - %s: %s' % (type(e), e))
                    # query failed, try to reconnect
                    if self.connect():
                        try:
                            # retry query
                            return self._query(query, bindata)
                        except Exception:
                            # fall through to log error message
                            pass
                else:
                    raise e
        return None

    def getCounts(self):
        """
        Return a dictionary containing the number of
        clients, Bans, Kicks, Warnings and Tempbans.
        """
        counts = dict(clients=0, Bans=0, Kicks=0, Warnings=0, TempBans=0)
        cursor = self.query("""SELECT COUNT(id) total FROM clients""")

        if cursor and cursor.rowcount:
            counts['clients'] = int(cursor.getRow()['total'])

        cursor = self.query("""SELECT COUNT(id) total, type FROM penalties GROUP BY type""")

        if cursor:
            while not cursor.EOF:
                r = cursor.getRow()
                counts[r['type'] + 's'] = int(r['total'])
                cursor.moveNext()

            cursor.close()
        return counts

    def getClient(self, client):
        """
        Return a client object fetching data from the storage.
        :param client: The client object to fill with fetch data.
        """
        self.console.debug('Storage: getClient %s' % client)

        if client.id > 0:
            cursor = self.query(QueryBuilder(self.db).SelectQuery('*', 'clients', dict(id=client.id), None, 1))
        else:
            cursor = self.query(QueryBuilder(self.db).SelectQuery('*', 'clients', dict(guid=client.guid), None, 1))

        if not cursor:
            # connection failed, try local cache
            if self.console.config.has_option('admins_cache', client.guid):
                data = self.console.config.get('admins_cache', client.guid, True)
                self.console.debug('pulling user form admins_cache %s' % data)
                cid, name, level = data.split(',')
                client.id = cid.strip()
                client.name = name.strip()
                client._tempLevel = int(level.strip())

                return client
            else:
                raise KeyError('no client matching guid %s in admins_cache' % client.guid)

        if not cursor.rowcount:
            cursor.close()
            raise KeyError('no client matching guid %s' % client.guid)

        found = False
        for k, v in cursor.getRow().iteritems():
            #if hasattr(client, k) and getattr(client, k):
            #    # don't set already set items
            #    continue
            setattr(client, self.getVar(k), v)
            found = True

        cursor.close()

        if found:
            return client
        else:
            raise KeyError('no client matching guid %s' % client.guid)

    def getClientsMatching(self, match):
        """
        Return a list of clients matching the given data:
        :param match: The data to match clients against.
        """
        self.console.debug('Storage: getClientsMatching %s' % match)
        cursor = self.query(QueryBuilder(self.db).SelectQuery('*', 'clients', match, 'time_edit DESC', 5))

        if not cursor:
            return ()

        clients = []
        while not cursor.EOF:
            g = cursor.getRow()
            client = b3.clients.Client()
            for k, v in g.iteritems():
                setattr(client, self.getVar(k), v)
            clients.append(client)
            cursor.moveNext()

        cursor.close()
        return clients

    def setClient(self, client):
        """
        Insert/update a client in the storage.
        :param client: The client to be saved.
        """
        self.console.debug('Storage: setClient %s' % client)
        fields = ('ip', 'greeting', 'connections', 'time_edit', 'guid', 'pbid', 'name',
                  'time_add', 'auto_login', 'mask_level', 'group_bits', 'login', 'password')

        if client.id > 0:
            data = dict(id=client.id)
        else:
            data = dict()

        for f in fields:
            if hasattr(client, self.getVar(f)):
                data[f] = getattr(client, self.getVar(f))

        self.console.debug('Storage: setClient data %s' % data)
        if client.id > 0:
            self.query(QueryBuilder(self.db).UpdateQuery(data, 'clients', dict(id=client.id)))
        else:
            cursor = self.query(QueryBuilder(self.db).InsertQuery(data, 'clients'))
            if cursor:
                client.id = cursor.lastrowid
            else:
                client.id = None

        return client.id

    def setClientAlias(self, alias):
        """
        Insert/update an alias in the storage.
        :param alias: The alias to be saved.
        """
        self.console.debug('Storage: setClientAlias %s' % alias)
        fields = ('num_used', 'alias', 'client_id', 'time_add', 'time_edit')
        data = dict(id=alias.id) if alias.id else dict()

        for f in fields:
            if hasattr(alias, self.getVar(f)):
                data[f] = getattr(alias, self.getVar(f))

        self.console.debug('Storage: setClientAlias data %s' % data)
        if alias.id:
            self.query(QueryBuilder(self.db).UpdateQuery(data, 'aliases', dict(id=alias.id)))
        else:
            cursor = self.query(QueryBuilder(self.db).InsertQuery(data, 'aliases'))
            alias.id = cursor.lastrowid if cursor else None

        return alias.id

    def getClientAlias(self, alias):
        """
        Return an alias object fetching data from the storage.
        :param alias: The alias object to fill with fetch data.
        """
        self.console.debug('Storage: getClientAlias %s' % alias)
        cursor = None
        if hasattr(alias, 'id') and alias.id > 0:
            cursor = self.query(QueryBuilder(self.db).SelectQuery('*', 'aliases', dict(id=alias.id), None, 1))
        elif hasattr(alias, 'alias') and hasattr(alias, 'clientId'):
            cursor = self.query(QueryBuilder(self.db).SelectQuery('*', 'aliases',
                                                                  dict(alias=alias.alias,
                                                                       client_id=alias.clientId), None, 1))

        if not cursor or cursor.EOF:
            raise KeyError('no alias matching %s' % alias)

        g = cursor.getOneRow()
        alias.id = int(g['id'])
        alias.alias = g['alias']
        alias.timeAdd = int(g['time_add'])
        alias.timeEdit = int(g['time_edit'])
        alias.clientId = int(g['client_id'])
        alias.numUsed = int(g['num_used'])

        return alias

    def getClientAliases(self, client):
        """
        Return the aliases of the given client
        :param client: The client whose aliases we want to retrieve.
        """
        self.console.debug('Storage: getClientAliases %s' % client)
        cursor = self.query(QueryBuilder(self.db).SelectQuery('*', 'aliases', dict(client_id=client.id), 'id'))

        if not cursor:
            return ()

        aliases = []
        while not cursor.EOF:
            g = cursor.getRow()
            alias = b3.clients.Alias()
            alias.id = int(g['id'])
            alias.alias = g['alias']
            alias.timeAdd = int(g['time_add'])
            alias.timeEdit = int(g['time_edit'])
            alias.clientId = int(g['client_id'])
            alias.numUsed = int(g['num_used'])
            aliases.append(alias)
            cursor.moveNext()

        cursor.close()

        return aliases

    def setClientIpAddress(self, ipalias):
        """
        Insert/update an ipalias in the storage.
        :param ipalias: The ipalias to be saved.
        """
        self.console.debug('Storage: setClientIpAddress %s' % ipalias)
        fields = ('num_used', 'ip', 'client_id', 'time_add', 'time_edit' )
        data = dict(id=ipalias.id) if ipalias.id else dict()

        for f in fields:
            if hasattr(ipalias, self.getVar(f)):
                data[f] = getattr(ipalias, self.getVar(f))

        self.console.debug('Storage: setClientIpAddress data %s' % data)
        if ipalias.id:
            self.query(QueryBuilder(self.db).UpdateQuery(data, 'ipaliases', dict(id=ipalias.id)))
        else:
            cursor = self.query(QueryBuilder(self.db).InsertQuery(data, 'ipaliases'))
            ipalias.id = cursor.lastrowid if cursor else None

        return ipalias.id

    def getClientIpAddress(self, ipalias):
        """
        Return an ipalias object fetching data from the storage.
        :param ipalias: The ipalias object to fill with fetch data.
        """
        self.console.debug('Storage: getClientIpAddress %s' % ipalias)

        cursor = None
        if hasattr(ipalias, 'id') and ipalias.id > 0:
            cursor = self.query(QueryBuilder(self.db).SelectQuery('*', 'ipaliases', dict(id=ipalias.id), None, 1))
        elif hasattr(ipalias, 'ip') and hasattr(ipalias, 'clientId'):
            cursor = self.query(QueryBuilder(self.db).SelectQuery('*', 'ipaliases',
                                                                  dict(ip=ipalias.ip,
                                                                       client_id=ipalias.clientId), None, 1))

        if not cursor or cursor.EOF:
            raise KeyError('no ip matching %s' % ipalias)

        g = cursor.getOneRow()
        ipalias.id = int(g['id'])
        ipalias.ip = g['ip']
        ipalias.timeAdd  = int(g['time_add'])
        ipalias.timeEdit = int(g['time_edit'])
        ipalias.clientId = int(g['client_id'])
        ipalias.numUsed = int(g['num_used'])

        return ipalias

    def getClientIpAddresses(self, client):
        """
        Return the ip aliases of the given client.
        :param client: The client whose ip aliases we want to retrieve.
        """
        self.console.debug('Storage: getClientIpAddresses %s' % client)
        cursor = self.query(QueryBuilder(self.db).SelectQuery('*', 'ipaliases', dict(client_id=client.id), 'id'))

        if not cursor:
            return ()

        aliases = []
        while not cursor.EOF:
            g = cursor.getRow()
            ip = b3.clients.IpAlias()
            ip.id = int(g['id'])
            ip.ip = g['ip']
            ip.timeAdd  = int(g['time_add'])
            ip.timeEdit = int(g['time_edit'])
            ip.clientId = int(g['client_id'])
            ip.numUsed = int(g['num_used'])
            aliases.append(ip)
            cursor.moveNext()

        cursor.close()
        return aliases

    def getLastPenalties(self, types='Ban', num=5):
        """
        Return the X penalties saved in the storage.
        :param types: The penalties type.
        :param num: The amount of penalties to retrieve.
        """
        where = QueryBuilder(self.db).WhereClause(dict(type=types, inactive=0))
        where += ' and (time_expire = -1 or time_expire > %s)' % int(time.time())
        cursor = self.query(QueryBuilder(self.db).SelectQuery(fields='*', table='penalties', where=where,
                                                              orderby='time_add DESC, id DESC', limit=num))
        if not cursor:
            return []

        penalties = []
        while not cursor.EOF and len(penalties) < num:
            penalties.append(self._createPenaltyFromRow(cursor.getRow()))
            cursor.moveNext()
        cursor.close()

        return penalties

    def setClientPenalty(self, penalty):
        """
        Insert/update a penalty in the storage.
        :param penalty: The penalty to be saved.
        """
        fields = ('type', 'duration', 'inactive', 'admin_id', 'time_add', 'time_edit',
                  'time_expire', 'reason', 'keyword', 'client_id', 'data')

        data = dict(id=penalty.id) if penalty.id else dict()
        if penalty.keyword and not re.match(r'^[a-z0-9]+$', penalty.keyword, re.I):
            penalty.keyword = ''

        if penalty.reason:
            # decode the reason data, as the name may need it
            if hasattr(self.console, "encoding") and self.console.encoding:
                try:
                    penalty.reason = penalty.reason.decode(self.console.encoding)
                except Exception, msg:
                    self.console.warning('ERROR: decoding reason: %r', msg)

                try:
                    penalty.reason = penalty.reason.encode('UTF-8', 'replace')
                except Exception, msg:
                    self.console.warning('ERROR: encoding reason: %r', msg)

        for f in fields:
            if hasattr(penalty, self.getVar(f)):
                data[f] = getattr(penalty, self.getVar(f))

        self.console.debug('Storage: setClientPenalty data %s' % data)
        if penalty.id:
            self.query(QueryBuilder(self.db).UpdateQuery(data, 'penalties', dict(id=penalty.id)))
        else:
            cursor = self.query(QueryBuilder(self.db).InsertQuery(data, 'penalties'))
            penalty.id = cursor.lastrowid if cursor else None

        return penalty.id

    def _createPenaltyFromRow(self, g):
        if g['type'] == 'Warning':
            penalty = b3.clients.ClientWarning()
        elif g['type'] == 'TempBan':
            penalty = b3.clients.ClientTempBan()
        elif g['type'] == 'Kick':
            penalty = b3.clients.ClientKick()
        elif g['type'] == 'Ban':
            penalty = b3.clients.ClientBan()
        elif g['type'] == 'Notice':
            penalty = b3.clients.ClientNotice()
        else:
            penalty = b3.clients.Penalty()

        penalty.id = int(g['id'])
        penalty.type = g['type']
        penalty.keyword = g['keyword']
        penalty.reason = g['reason']
        penalty.data = g['data']
        penalty.inactive = int(g['inactive'])
        penalty.timeAdd = int(g['time_add'])
        penalty.timeEdit = int(g['time_edit'])
        penalty.timeExpire = int(g['time_expire'])
        penalty.clientId = int(g['client_id'])
        penalty.adminId = int(g['admin_id'])
        penalty.duration = int(g['duration'])
        return penalty

    def getClientPenalty(self, penalty):
        """
        Return a penalty object fetching data from the storage.
        :param penalty: The penalty object to fill with fetch data.
        """
        self.console.debug('Storage: getClientPenalty %s' % penalty)

        cursor = self.query(QueryBuilder(self.db).SelectQuery('*', 'penalties', dict(id=penalty.id), None, 1))
        g = cursor.getOneRow()
        if not g:
            raise KeyError('no penalty matching id %s' % penalty.id)

        return self._createPenaltyFromRow(g)

    def getClientPenalties(self, client, type='Ban'):
        """
        Return the penalties of the given client.
        :param client: The client whose penalties we want to retrieve.
        :param type: The type of the penalties we want to retrieve.
        """
        self.console.debug('Storage: getClientPenalties %s' % client)
        where = QueryBuilder(self.db).WhereClause(dict(type=type, client_id=client.id, inactive=0))
        where += ' and (time_expire = -1 or time_expire > %s)' % int(time.time())
        cursor = self.query(QueryBuilder(self.db).SelectQuery('*', 'penalties', where, 'time_add DESC'))

        if not cursor:
            return ()

        penalties = []
        while not cursor.EOF:
            penalties.append(self._createPenaltyFromRow(cursor.getRow()))
            cursor.moveNext()
        cursor.close()

        return penalties

    def getClientLastPenalty(self, client, type='Ban'):
        """
        Return the last penalty added for the given client.
        :param client: The client whose penalty we want to retrieve.
        :param type: The type of the penalty we want to retrieve.
        """
        where = QueryBuilder(self.db).WhereClause(dict(type=type, client_id=client.id, inactive=0))
        where += ' and (time_expire = -1 or time_expire > %s)' % int(time.time())
        cursor = self.query(QueryBuilder(self.db).SelectQuery('*', 'penalties', where, 'time_add DESC', 1))

        g = cursor.getOneRow()
        if not g:
            return None

        return self._createPenaltyFromRow(g)

    def getClientFirstPenalty(self, client, type='Ban'):
        """
        Return the  first penalty added for the given client.
        :param client: The client whose penalty we want to retrieve.
        :param type: The type of the penalty we want to retrieve.
        """
        where = QueryBuilder(self.db).WhereClause(dict(type=type, client_id=client.id, inactive=0))
        where += ' and (time_expire = -1 or time_expire > %s)' % int(time.time())
        cursor = self.query(QueryBuilder(self.db).SelectQuery('*', 'penalties', where,
                                                              'time_expire DESC, time_add ASC', 1))
        g = cursor.getOneRow()
        if not g:
            return None

        return self._createPenaltyFromRow(g)

    def disableClientPenalties(self, client, type='Ban'):
        """
        Disable all the penalties for the given client.
        :param client: The client whose penalties we want to disable.
        :param type: The type of the penalties we want to disable.
        """
        self.query(QueryBuilder(self.db).UpdateQuery(dict(inactive=1), 'penalties',
                                                     dict(type=type, client_id=client.id, inactive=0)))

    def numPenalties(self, client, type='Ban'):
        """
        Return the amount of penalties the given client has according to the given type.
        :param client: The client whose number of penalties we are interested into.
        :param type: The penalties type.
        :return The number of penalties.
        """
        where = QueryBuilder(self.db).WhereClause(dict(type=type, client_id=client.id, inactive=0))
        where += ' and (time_expire = -1 or time_expire > %s)' % int(time.time())
        cursor = self.query("""SELECT COUNT(id) total FROM penalties WHERE %s""" % where)

        if not cursor:
            return 0

        return int(cursor.getValue('total', 0))

    _groups = None

    def getGroups(self):
        """
        Return a list of available client groups.
        """
        if not self._groups:
            cursor = self.query(QueryBuilder(self.db).SelectQuery('*', 'groups', None, 'level'))
            if not cursor:
                return []

            self._groups = []
            while not cursor.EOF:
                g = cursor.getRow()
                group = b3.clients.Group()
                group.id = int(g['id'])
                group.name = g['name']
                group.keyword = g['keyword']
                group.level = int(g['level'])
                group.timeAdd = int(g['time_add'])
                group.timeEdit = int(g['time_edit'])
                self._groups.append(group)
                cursor.moveNext()
            cursor.close()

        return self._groups

    def getGroup(self, group):
        """
        Return a group object fetching data from the storage layer.
        :param group: A group object with level or keyword filled
        """
        if hasattr(group, 'keyword') and group.keyword:
            q = QueryBuilder(self.db).SelectQuery('*', 'groups', dict(keyword=group.keyword), None, 1)
            self.console.verbose2(q)
            cursor = self.query(q)
            g = cursor.getOneRow()
            if not g:
                raise KeyError('no group matching keyword: %s' % group.keyword)

        elif hasattr(group, 'level') and group.level >= 0:
            q = QueryBuilder(self.db).SelectQuery('*', 'groups', dict(level=group.level), None, 1)
            self.console.verbose2(q)
            cursor = self.query(q)
            g = cursor.getOneRow()
            if not g:
                raise KeyError('no group matching level: %s' % group.level)
        else:
            raise KeyError("cannot find Group as no keyword/level provided")

        group.id = int(g['id'])
        group.name = g['name']
        group.keyword = g['keyword']
        group.level = int(g['level'])
        group.timeAdd = int(g['time_add'])
        group.timeEdit = int(g['time_edit'])

        return group