# -*- coding: utf-8 -*-

# ################################################################### #
#                                                                     #
#  BigBrotherBot(B3) (www.bigbrotherbot.net)                          #
#  Copyright (C) 2005 Michael "ThorN" Thornton                        #
#                                                                     #
#  This program is free software; you can redistribute it and/or      #
#  modify it under the terms of the GNU General Public License        #
#  as published by the Free Software Foundation; either version 2     #
#  of the License, or (at your option) any later version.             #
#                                                                     #
#  This program is distributed in the hope that it will be useful,    #
#  but WITHOUT ANY WARRANTY; without even the implied warranty of     #
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the       #
#  GNU General Public License for more details.                       #
#                                                                     #
#  You should have received a copy of the GNU General Public License  #
#  along with this program; if not, write to the Free Software        #
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA      #
#  02110-1301, USA.                                                   #
#                                                                     #
# ################################################################### #

import b3
import os
import re
import sys
import thread

from b3.clients import Client
from b3.clients import ClientBan
from b3.clients import ClientKick
from b3.clients import ClientNotice
from b3.clients import ClientTempBan
from b3.clients import ClientWarning
from b3.clients import Penalty
from b3.querybuilder import QueryBuilder
from b3.storage import Storage
from b3.storage.cursor import Cursor as DBCursor
from contextlib import contextmanager
from time import time

class DatabaseStorage(Storage):

    _lock = None
    _lastConnectAttempt = 0
    _consoleNotice = True
    _reName = re.compile(r'([A-Z])')
    _reVar = re.compile(r'_([a-z])')

    db = None
    dsn = None
    dsnDict = None

    def __init__(self, dsn, dsnDict, console):
        """
        Object constructor.
        :param dsn: The database connection string.
        :param dsnDict: The database connection string parsed into a dict.
        :param console: The console instance.
        """
        self.dsn = dsn
        self.dsnDict = dsnDict
        self.console = console
        self.db = None
        self._lock = thread.allocate_lock()

    ####################################################################################################################
    #                                                                                                                  #
    #   CONNECTION INITIALIZATION/TERMINATION/RETRIEVAL                                                                #
    #                                                                                                                  #
    ####################################################################################################################

    def connect(self):
        """
        Establish and return a connection with the storage layer.
        :return The connection instance if established successfully, otherwise None.
        """
        raise NotImplementedError

    def getConnection(self):
        """
        Return the database connection. If the connection has not been established yet, will establish a new one.
        :return The connection instance, or None if no connection can be established.
        """
        raise NotImplementedError

    def shutdown(self):
        """
        Close the current active database connection.
        """
        raise NotImplementedError

    def closeConnection(self):
        """
        Just an alias for shutdown (backwards compatibility).
        """
        self.shutdown()

    ####################################################################################################################
    #                                                                                                                  #
    #   STORAGE INTERFACE                                                                                              #
    #                                                                                                                  #
    ####################################################################################################################

    def getCounts(self):
        """
        Return a dictionary containing the number of clients, Bans, Kicks, Warnings and Tempbans.
        """
        counts = {'clients': 0, 'Bans': 0, 'Kicks': 0, 'Warnings': 0, 'TempBans': 0}
        cursor = self.query("""SELECT COUNT(id) total FROM clients""")
        if cursor.rowcount:
            counts['clients'] = int(cursor.getValue('total'))

        cursor = self.query("""SELECT COUNT(id) total, type FROM penalties GROUP BY type""")
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
        where = {'id': client.id} if client.id > 0 else {'guid': client.guid}

        try:

            cursor = self.query(QueryBuilder(self.db).SelectQuery('*', 'clients', where, None, 1))
            if not cursor.rowcount:
                raise KeyError('no client matching guid %s' % client.guid)

            found = False
            for k, v in cursor.getRow().iteritems():
                #if hasattr(client, k) and getattr(client, k):
                #    # don't set already set items
                #    continue
                setattr(client, self.getVar(k), v)
                found = True

            cursor.close()
            if not found:
                raise KeyError('no client matching guid %s' % client.guid)

            return client

        except Exception:
            # query failed, try local cache
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

    def getClientsMatching(self, match):
        """
        Return a list of clients matching the given data:
        :param match: The data to match clients against.
        """
        self.console.debug('Storage: getClientsMatching %s' % match)
        cursor = self.query(QueryBuilder(self.db).SelectQuery('*', 'clients', match, 'time_edit DESC', 5))

        clients = []
        while not cursor.EOF:
            g = cursor.getRow()
            client = Client()
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
        :return: The ID of the client stored into the database.
        """
        self.console.debug('Storage: setClient %s' % client)
        fields = ('ip', 'greeting', 'connections', 'time_edit',
                  'guid', 'pbid', 'name', 'time_add', 'auto_login',
                  'mask_level', 'group_bits', 'login', 'password')

        data = {'id': client.id} if client.id > 0 else {}

        for f in fields:
            if hasattr(client, self.getVar(f)):
                data[f] = getattr(client, self.getVar(f))

        self.console.debug('Storage: setClient data %s' % data)
        if client.id > 0:
            self.query(QueryBuilder(self.db).UpdateQuery(data, 'clients', {'id': client.id}))
        else:
            cursor = self.query(QueryBuilder(self.db).InsertQuery(data, 'clients'))
            client.id = cursor.lastrowid
            cursor.close()

        return client.id

    def setClientAlias(self, alias):
        """
        Insert/update an alias in the storage.
        :param alias: The alias to be saved.
        :return: The ID of the alias stored into the database.
        """
        self.console.debug('Storage: setClientAlias %s' % alias)
        fields = ('num_used', 'alias', 'client_id', 'time_add', 'time_edit')
        data = {'id':alias.id} if alias.id else {}

        for f in fields:
            if hasattr(alias, self.getVar(f)):
                data[f] = getattr(alias, self.getVar(f))

        self.console.debug('Storage: setClientAlias data %s' % data)
        if alias.id:
            self.query(QueryBuilder(self.db).UpdateQuery(data, 'aliases', {'id':alias.id}))
        else:
            cursor = self.query(QueryBuilder(self.db).InsertQuery(data, 'aliases'))
            alias.id = cursor.lastrowid
            cursor.close()

        return alias.id

    def getClientAlias(self, alias):
        """
        Return an alias object fetching data from the storage.
        :param alias: The alias object to fill with fetch data.
        :return: The alias object given in input with all the fields set.
        """
        self.console.debug('Storage: getClientAlias %s' % alias)
        if hasattr(alias, 'id') and alias.id > 0:
            query = QueryBuilder(self.db).SelectQuery('*', 'aliases', {'id': alias.id}, None, 1)
        elif hasattr(alias, 'alias') and hasattr(alias, 'clientId'):
            query = QueryBuilder(self.db).SelectQuery('*', 'aliases', {'alias': alias.alias,
                                                                       'client_id': alias.clientId}, None, 1)
        else:
            raise KeyError('no alias found matching %s' % alias)

        cursor = self.query(query)
        if cursor.EOF:
            cursor.close()
            raise KeyError('no alias found matching %s' % alias)

        row = cursor.getOneRow()
        alias.id = int(row['id'])
        alias.alias = row['alias']
        alias.timeAdd = int(row['time_add'])
        alias.timeEdit = int(row['time_edit'])
        alias.clientId = int(row['client_id'])
        alias.numUsed = int(row['num_used'])

        return alias

    def getClientAliases(self, client):
        """
        Return the aliases of the given client
        :param client: The client whose aliases we want to retrieve.
        :return: List of b3.clients.Alias instances.
        """
        self.console.debug('Storage: getClientAliases %s' % client)
        cursor = self.query(QueryBuilder(self.db).SelectQuery('*', 'aliases', {'client_id': client.id}, 'id'))

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
        data = {'id': ipalias.id} if ipalias.id else {}

        for f in fields:
            if hasattr(ipalias, self.getVar(f)):
                data[f] = getattr(ipalias, self.getVar(f))

        self.console.debug('Storage: setClientIpAddress data %s' % data)
        if ipalias.id:
            self.query(QueryBuilder(self.db).UpdateQuery(data, 'ipaliases', {'id': ipalias.id}))
        else:
            cursor = self.query(QueryBuilder(self.db).InsertQuery(data, 'ipaliases'))
            ipalias.id = cursor.lastrowid
            cursor.close()

        return ipalias.id

    def getClientIpAddress(self, ipalias):
        """
        Return an ipalias object fetching data from the storage.
        :param ipalias: The ipalias object to fill with fetch data.
        :return: The ip alias object given in input with all the fields set.
        """
        self.console.debug('Storage: getClientIpAddress %s' % ipalias)
        if hasattr(ipalias, 'id') and ipalias.id > 0:
            query = QueryBuilder(self.db).SelectQuery('*', 'ipaliases', {'id': ipalias.id}, None, 1)
        elif hasattr(ipalias, 'ip') and hasattr(ipalias, 'clientId'):
            query = QueryBuilder(self.db).SelectQuery('*', 'ipaliases', {'ip': ipalias.ip,
                                                                         'client_id': ipalias.clientId}, None, 1)
        else:
            raise KeyError('no ip found matching %s' % ipalias)

        cursor = self.query(query)
        if cursor.EOF:
            cursor.close()
            raise KeyError('no ip found matching %s' % ipalias)

        row = cursor.getOneRow()
        ipalias.id = int(row['id'])
        ipalias.ip = row['ip']
        ipalias.timeAdd  = int(row['time_add'])
        ipalias.timeEdit = int(row['time_edit'])
        ipalias.clientId = int(row['client_id'])
        ipalias.numUsed = int(row['num_used'])

        return ipalias

    def getClientIpAddresses(self, client):
        """
        Return the ip aliases of the given client.
        :param client: The client whose ip aliases we want to retrieve.
        :return: List of b3.clients.IpAlias instances
        """
        self.console.debug('Storage: getClientIpAddresses %s' % client)
        cursor = self.query(QueryBuilder(self.db).SelectQuery('*', 'ipaliases', {'client_id': client.id}, 'id'))

        aliases = []
        while not cursor.EOF:
            row = cursor.getRow()
            ip = b3.clients.IpAlias()
            ip.id = int(row['id'])
            ip.ip = row['ip']
            ip.timeAdd  = int(row['time_add'])
            ip.timeEdit = int(row['time_edit'])
            ip.clientId = int(row['client_id'])
            ip.numUsed = int(row['num_used'])
            aliases.append(ip)
            cursor.moveNext()

        cursor.close()
        return aliases

    def getLastPenalties(self, types='Ban', num=5):
        """
        Return the last 'num' penalties saved in the storage.
        :param types: The penalties type.
        :param num: The amount of penalties to retrieve.
        """
        penalties = []
        where = QueryBuilder(self.db).WhereClause({'type': types, 'inactive': 0})
        where += ' AND (time_expire = -1 OR time_expire > %s)' % int(time())
        cursor = self.query(QueryBuilder(self.db).SelectQuery(fields='*', table='penalties', where=where,
                                                              orderby='time_add DESC, id DESC', limit=num))
        while not cursor.EOF and len(penalties) < num:
            penalties.append(self._createPenaltyFromRow(cursor.getRow()))
            cursor.moveNext()

        cursor.close()
        return penalties

    def setClientPenalty(self, penalty):
        """
        Insert/update a penalty in the storage.
        :param penalty: The penalty to be saved.
        :return: The ID of the penalty saved in the storage.
        """
        fields = ('type', 'duration', 'inactive', 'admin_id',
                  'time_add', 'time_edit', 'time_expire', 'reason',
                  'keyword', 'client_id', 'data')

        data = {'id': penalty.id} if penalty.id else {}
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
            self.query(QueryBuilder(self.db).UpdateQuery(data, 'penalties', {'id': penalty.id}))
        else:
            cursor = self.query(QueryBuilder(self.db).InsertQuery(data, 'penalties'))
            penalty.id = cursor.lastrowid
            cursor.close()

        return penalty.id

    def getClientPenalty(self, penalty):
        """
        Return a penalty object fetching data from the storage.
        :param penalty: The penalty object to fill with fetch data.
        :return: The penalty given as input with all the fields set.
        """
        self.console.debug('Storage: getClientPenalty %s' % penalty)
        cursor = self.query(QueryBuilder(self.db).SelectQuery('*', 'penalties', {'id': penalty.id}, None, 1))
        if cursor.EOF:
            cursor.close()
            raise KeyError('no penalty matching id %s' % penalty.id)
        row = cursor.getOneRow()
        return self._createPenaltyFromRow(row)

    def getClientPenalties(self, client, type='Ban'):
        """
        Return the penalties of the given client.
        :param client: The client whose penalties we want to retrieve.
        :param type: The type of the penalties we want to retrieve.
        :return: List of penalties
        """
        self.console.debug('Storage: getClientPenalties %s' % client)
        where = QueryBuilder(self.db).WhereClause({'type': type, 'client_id': client.id, 'inactive': 0})
        where += ' AND (time_expire = -1 OR time_expire > %s)' % int(time())
        cursor = self.query(QueryBuilder(self.db).SelectQuery('*', 'penalties', where, 'time_add DESC'))

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
        :return: The last penalty added for the given client
        """
        where = QueryBuilder(self.db).WhereClause({'type': type, 'client_id': client.id, 'inactive': 0})
        where += ' AND (time_expire = -1 OR time_expire > %s)' % int(time())
        cursor = self.query(QueryBuilder(self.db).SelectQuery('*', 'penalties', where, 'time_add DESC', 1))

        row = cursor.getOneRow()
        if not row:
            return None

        return self._createPenaltyFromRow(row)

    def getClientFirstPenalty(self, client, type='Ban'):
        """
        Return the first penalty added for the given client.
        :param client: The client whose penalty we want to retrieve.
        :param type: The type of the penalty we want to retrieve.
        :return: The first penalty added for the given client.
        """
        where = QueryBuilder(self.db).WhereClause({'type': type, 'client_id': client.id, 'inactive': 0})
        where += ' AND (time_expire = -1 OR time_expire > %s)' % int(time())
        cursor = self.query(QueryBuilder(self.db).SelectQuery('*', 'penalties', where,
                                                              'time_expire DESC, time_add ASC', 1))
        row = cursor.getOneRow()
        if not row:
            return None

        return self._createPenaltyFromRow(row)

    def disableClientPenalties(self, client, type='Ban'):
        """
        Disable all the penalties for the given client.
        :param client: The client whose penalties we want to disable.
        :param type: The type of the penalties we want to disable.
        """
        self.query(QueryBuilder(self.db).UpdateQuery({'inactive': 1}, 'penalties',
                                                     {'type': type, 'client_id': client.id, 'inactive': 0}))

    def numPenalties(self, client, type='Ban'):
        """
        Return the amount of penalties the given client has according to the given type.
        :param client: The client whose number of penalties we are interested into.
        :param type: The penalties type.
        :return The number of penalties.
        """
        where = QueryBuilder(self.db).WhereClause({'type': type, 'client_id': client.id, 'inactive': 0})
        where += ' AND (time_expire = -1 OR time_expire > %s)' % int(time())
        cursor = self.query("""SELECT COUNT(id) total FROM penalties WHERE %s""" % where)
        value = int(cursor.getValue('total', 0))
        cursor.close()
        return value

    _groups = None

    def getGroups(self):
        """
        Return a list of available client groups.
        """
        if not self._groups:
            cursor = self.query(QueryBuilder(self.db).SelectQuery('*', 'groups', None, 'level'))
            self._groups = []
            while not cursor.EOF:
                row = cursor.getRow()
                group = b3.clients.Group()
                group.id = int(row['id'])
                group.name = row['name']
                group.keyword = row['keyword']
                group.level = int(row['level'])
                group.timeAdd = int(row['time_add'])
                group.timeEdit = int(row['time_edit'])
                self._groups.append(group)
                cursor.moveNext()
            cursor.close()

        return self._groups

    def getGroup(self, group):
        """
        Return a group object fetching data from the storage layer.
        :param group: A group object with level or keyword filled.
        :return: The group instance given in input with all the fields set.
        """
        if hasattr(group, 'keyword') and group.keyword:
            query = QueryBuilder(self.db).SelectQuery('*', 'groups', dict(keyword=group.keyword), None, 1)
            self.console.verbose2(query)
            cursor = self.query(query)
            row = cursor.getOneRow()
            if not row:
                raise KeyError('no group matching keyword: %s' % group.keyword)

        elif hasattr(group, 'level') and group.level >= 0:
            query = QueryBuilder(self.db).SelectQuery('*', 'groups', dict(level=group.level), None, 1)
            self.console.verbose2(query)
            cursor = self.query(query)
            row = cursor.getOneRow()
            if not row:
                raise KeyError('no group matching level: %s' % group.level)
        else:
            raise KeyError("cannot find Group as no keyword/level provided")

        group.id = int(row['id'])
        group.name = row['name']
        group.keyword = row['keyword']
        group.level = int(row['level'])
        group.timeAdd = int(row['time_add'])
        group.timeEdit = int(row['time_edit'])

        return group

    def truncateTable(self, table):
        """
        Empty a database table (or a collection of tables)
        :param table: The database table or a collection of tables
        :raise KeyError: If the table is not present in the database
        """
        raise NotImplementedError

    def getTables(self):
        """
        List the tables of the current database.
        :return: list of strings.
        """
        raise NotImplementedError

    ####################################################################################################################
    #                                                                                                                  #
    #   QUERY PROCESSING                                                                                               #
    #                                                                                                                  #
    ####################################################################################################################

    def _query(self, query, bindata=None):
        """
        Execute a query on the storage layer (internal method).
        :param query: The query to execute.
        :param bindata: Data to bind to the given query.
        :raise Exception: If the query cannot be evaluated.
        """
        self._lock.acquire()
        try:
            cursor = self.db.cursor()
            if bindata is None:
                cursor.execute(query)
            else:
                cursor.execute(query, bindata)
            dbcursor = DBCursor(cursor, self.db)
        finally:
            self._lock.release()
        return dbcursor

    def query(self, query, bindata=None):
        """
        Execute a query on the storage layer.
        :param query: The query to execute.
        :param bindata: Data to bind to the given query.
        :raise Exception: If the query cannot be evaluated.
        """
        # use existing connection or create a new one
        connection = self.getConnection()
        if not connection:
            raise Exception('lost connection with the storage layer during query')

        try:
            # always return a cursor instance (also when EOF is reached)
            return self._query(query=query, bindata=bindata)
        except Exception, e:
            # log so we can inspect the issue and raise again
            self.console.error('Query failed [%s] %r: %s', query, bindata, e)
            raise e

    @contextmanager
    def query2(self, query, bindata=None):
        """
        Alias for query method which make use of the python 'with' statement.
        The contextmanager approach ensures that the generated cursor object instance
        is always closed whenever the execution goes out of the 'with' statement block.
        Example:

        >> with self.console.storage.query(query) as cursor:
        >>     if not cursor.EOF:
        >>         cursor.getRow()
        >>         ...

        :param query: The query to execute.
        :param bindata: Data to bind to the given query.
        """
        cursor = None
        try:
            cursor = self.query(query, bindata)
            yield cursor
        finally:
            if cursor:
                cursor.close()

    def queryFromFile(self, fp, silent=False):
        """
        This method executes an external sql file on the current database.
        :param fp: The filepath of the file containing the SQL statements.
        :param silent: Whether or not to silence MySQL warnings.
        :raise Exception: If the query cannot be evaluated or if the given path cannot be resolved.
        """
        # use existing connection or create a new one
        # duplicate code of query() method which is needed not to spam the database
        # with useless connection attempts (one for each query in the SQL file)
        connection = self.getConnection()
        if not connection:
            raise Exception('lost connection with the storage layer during query')

        # save standard error output
        orig_stderr = sys.stderr
        if silent:
            # silence mysql warnings and such
            sys.stderr = open(os.devnull, 'w')

        path = b3.getAbsolutePath(fp)
        if not os.path.exists(path):
            raise Exception('SQL file does not exist: %s' % path)

        with open(path, 'r') as sqlfile:
            statements = self.getQueriesFromFile(sqlfile)

        for stmt in statements:
            # will stop if a single query generate an exception
            self.query(stmt)

        # reset standard error output
        sys.stderr = orig_stderr

    ####################################################################################################################
    #                                                                                                                  #
    #   UTILITY METHODS                                                                                                #
    #                                                                                                                  #
    ####################################################################################################################

    def status(self):
        """
        Check whether the connection with the storage layer is active or not.
        :return True if the connection is active, False otherwise.
        """
        raise NotImplementedError

    def getField(self, name):
        """
        Return a database field name given the correspondent variable name.
        :param name: The variable name.
        """
        return self._reName.sub(r'_\1', name)

    def getVar(self, name):
        """
        Return a variable name given the correspondent database field name.
        :param name: The database field name.
        """
        return self._reVar.sub(lambda m: m.group(1).upper(), name)

    @staticmethod
    def getQueriesFromFile(sqlfile):
        """
        Return a list of SQL queries given an open file pointer.
        :param sqlfile: An open file pointer to a SQL script file.
        :return: List of strings
        """
        lines = [x.strip() for x in sqlfile if x and not x.startswith('#') and not x.startswith('--')]
        return [x.strip() for x in ' '.join(lines).split(';') if x]

    @staticmethod
    def _createPenaltyFromRow(row):
        """
        Create a Penalty object given a result set row.
        :param row: The result set row
        """
        constructors = {
            'Warning': ClientWarning,
            'TempBan': ClientTempBan,
            'Kick': ClientKick,
            'Ban': ClientBan,
            'Notice': ClientNotice
        }

        try:
            constructor = constructors[row['type']]
            penalty = constructor()
        except KeyError:
            penalty = Penalty()

        penalty.id = int(row['id'])
        penalty.type = row['type']
        penalty.keyword = row['keyword']
        penalty.reason = row['reason']
        penalty.data = row['data']
        penalty.inactive = int(row['inactive'])
        penalty.timeAdd = int(row['time_add'])
        penalty.timeEdit = int(row['time_edit'])
        penalty.timeExpire = int(row['time_expire'])
        penalty.clientId = int(row['client_id'])
        penalty.adminId = int(row['admin_id'])
        penalty.duration = int(row['duration'])
        return penalty