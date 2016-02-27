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
# 26/12/2014 - Fenix - moved into separate module
# 05/01/2015 - Fenix - added truncateTable() method: empty a database table (or multiple tables) and reset identity
# 07/01/2015 - Fenix - reintroduced MySQLdb support: backup as 3rd driver option

import b3
import sys

from b3.storage.common import DatabaseStorage
from time import time
from traceback import extract_tb

class PymysqlStorage(DatabaseStorage):
    """
    Base inheritance class for MysqlStorage when using pymysql driver.
    """
    def __init__(self, dsn, dsnDict, console):
        """
        Object constructor.
        Every exception raised from here should make B3 non-operational since we won't have storage support.
        :param dsn: The database connection string.
        :param dsnDict: The database connection string parsed into a dict.
        :param console: The console instance.
        """
        super(PymysqlStorage, self).__init__(dsn, dsnDict, console)

    ####################################################################################################################
    #                                                                                                                  #
    #   CONNECTION INITIALIZATION/TERMINATION/RETRIEVAL                                                                #
    #                                                                                                                  #
    ####################################################################################################################

    def getConnection(self):
        """
        Return the database connection. If the connection has not been established yet, will establish a new one.
        :return The connection instance, or None if no connection can be established.
        """
        if self.db and self.db.open:
            return self.db
        return self.connect()

    def shutdown(self):
        """
        Close the current active database connection.
        """
        if self.db and self.db.open:
            # checking 'open' will prevent exception raising
            self.console.bot('Closing connection with MySQL database...')
            self.db.close()
        self.db = None

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
        if self.db and self.db.open:
           return True
        return False


class MysqlConnectorStorage(DatabaseStorage):
    """
    Base inheritance class for MysqlStorage when using mysql.connector driver.
    """
    def __init__(self, dsn, dsnDict, console):
        """
        Object constructor.
        Every exception raised from here  should make B3 non-operational since we won't have storage support.
        :param dsn: The database connection string.
        :param dsnDict: The database connection string parsed into a dict.
        :param console: The console instance.
        """
        super(MysqlConnectorStorage, self).__init__(dsn, dsnDict, console)

    ####################################################################################################################
    #                                                                                                                  #
    #   CONNECTION INITIALIZATION/TERMINATION/RETRIEVAL                                                                #
    #                                                                                                                  #
    ####################################################################################################################

    def getConnection(self):
        """
        Return the database connection. If the connection has not been established yet, will establish a new one.
        :return The connection instance, or None if no connection can be established.
        """
        if self.db and self.db._socket is not None:
            return self.db
        return self.connect()

    def shutdown(self):
        """
        Close the current active database connection.
        """
        if self.db and self.db._socket is not None:
            # the shutdown method is already exception safe
            self.console.bot('Closing connection with MySQL database...')
            self.db.shutdown()
        self.db = None

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
        if self.db and self.db._socket is not None:
            return True
        return False


class MySQLdbStorage(DatabaseStorage):
    """
    Base inheritance class for MysqlStorage when using MySQLdb driver.
    """
    def __init__(self, dsn, dsnDict, console):
        """
        Object constructor.
        Every exception raised from here should make B3 non-operational since we won't have storage support.
        :param dsn: The database connection string.
        :param dsnDict: The database connection string parsed into a dict.
        :param console: The console instance.
        """
        super(MySQLdbStorage, self).__init__(dsn, dsnDict, console)

    ####################################################################################################################
    #                                                                                                                  #
    #   CONNECTION INITIALIZATION/TERMINATION/RETRIEVAL                                                                #
    #                                                                                                                  #
    ####################################################################################################################

    def getConnection(self):
        """
        Return the database connection. If the connection has not been established yet, will establish a new one.
        :return The connection instance, or None if no connection can be established.
        """
        if self.db and self.db.open:
            return self.db
        return self.connect()

    def shutdown(self):
        """
        Close the current active database connection.
        """
        if self.db and self.db.open:
            # checking 'open' will prevent exception raising
            self.console.bot('Closing connection with MySQL database...')
            self.db.close()
        self.db = None

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
        if self.db and self.db.open:
           return True
        return False


class MysqlStorage(DatabaseStorage):

    _reconnectDelay = 60
    protocol = 'mysql'

    def __new__(cls, *args, **kwargs):
        """
        Will set the MysqlStorage base class according to the driver available on the system running B3.
        :raise ImportError: If the system misses the necessary libraries needed to setup the storage module.
        """
        try:

            # PREFER PYMYSQL
            import pymysql as mysqldriver
            cls.__bases__ = (PymysqlStorage,)
            cls.__driver = mysqldriver
            # new inheritance: MysqlStorage -> PymysqlStorage -> DatabaseStorage -> Storage
        except ImportError:

            try:
                # BACKUP USING MYSQL.CONNECTOR
                import mysql.connector as mysqldriver
                cls.__bases__ = (MysqlConnectorStorage,)
                cls.__driver = mysqldriver
                # new inheritance: MysqlStorage -> MysqlConnectorStorage -> DatabaseStorage -> Storage
            except ImportError:

                try:
                    # USE MYSQLDB AS LAST OPTION
                    import MySQLdb as mysqldriver
                    cls.__bases__ = (MySQLdbStorage,)
                    cls.__driver = mysqldriver
                    # new inheritance: MysqlStorage -> MySQLdbStorage -> DatabaseStorage -> Storage
                except ImportError:
                    mysqldriver = None
                    # re-raise ImportError with a custom message since it will be logged and it may
                    # help end users in fixing the problem by themselves (installing libraries)
                    raise ImportError("missing MySQL connector driver. You need to install one of the following MySQL "
                                      "connectors: 'pymysql', 'python-mysql.connector', 'MySQL-python': look for "
                                      "'dependencies' in B3 documentation.")

        return super(MysqlStorage, cls).__new__(cls)

    def __init__(self, dsn, dsnDict, console):
        """
        Object constructor.
        Every exception raised from here should make B3 non-operational since we won't have storage support.
        :param dsn: The database connection string.
        :param dsnDict: The database connection string parsed into a dict.
        :param console: The console instance.
        :raise AttributeError: if the given dsnDict is missing required information.
        """
        super(MysqlStorage, self).__init__(dsn, dsnDict, console)
        # check for valid MySQL host
        if not self.dsnDict['host']:
            raise AttributeError("invalid MySQL host in %(protocol)s://%(user)s:******@%(host)s:%(port)s%(path)s" % self.dsnDict)
        # check for valid MySQL database name
        if not self.dsnDict['path'] or not self.dsnDict['path'][1:]:
            raise AttributeError("missing MySQL database name in %(protocol)s://%(user)s:******@%(host)s:%(port)s%(path)s" % self.dsnDict)

    ####################################################################################################################
    #                                                                                                                  #
    #   CONNECTION INITIALIZATION/TERMINATION/RETRIEVAL                                                                #
    #                                                                                                                  #
    ####################################################################################################################

    def connect(self):
        """
        Establish and return a connection with the storage layer.
        Will store the connection object also in the 'db' attribute so in the future we can reuse it.
        :return The connection instance if established successfully, otherwise None.
        """
        # do not retry too soon because the MySQL server could
        # have connection troubles and we do not want to spam it
        if time() - self._lastConnectAttempt < self._reconnectDelay:
            self.db = None
            self.console.bot('New MySQL database connection requested but last connection attempt '
                             'failed less than %s seconds ago: exiting...' % self._reconnectDelay)
        else:
            # close the active connection (if any)
            self.shutdown()
            self.console.bot('Connecting to MySQL database: %(protocol)s://%(user)s:******@%(host)s:%(port)s%(path)s...', self.dsnDict)

            try:
                # create the connection instance using the specified connector
                self.db = self.__driver.connect(host=self.dsnDict['host'],
                                                port=self.dsnDict['port'],
                                                user=self.dsnDict['user'],
                                                passwd=self.dsnDict['password'],
                                                db=self.dsnDict['path'][1:],
                                                charset="utf8")

                self.console.bot('Successfully established a connection with MySQL database')
                self._lastConnectAttempt = 0

                if self._consoleNotice:
                    self.console.screen.write('Connecting to DB : OK\n')
                    self._consoleNotice = False

                # check whether the database is ready for usage or if we have to import B3 sql files to generate necessary
                # tables: if database is empty, then then AdminPlugin will raise an exception upon loading hence B3 won't be
                # operational. I placed the check here since it doesn't make sense to keep loading plugins if B3 will crash.
                if not self.getTables():

                    try:
                        self.console.info("Missing MySQL database tables: importing SQL file: %s..." % b3.getAbsolutePath("@b3/sql/mysql/b3.sql"))
                        self.queryFromFile("@b3/sql/mysql/b3.sql")
                    except Exception, e:
                        self.shutdown()
                        self.console.critical("Missing MySQL database tables. You need to create the necessary tables for "
                                              "B3 to work. You can do so by importing the following SQL script into your "
                                              "database: %s. An attempt of creating tables automatically just failed: %s" %
                                              (b3.getAbsolutePath("@b3/sql/mysql/b3.sql"), e))
            except Exception, e:
                self.console.error('Database connection failed: working in remote mode: %s - %s', e, extract_tb(sys.exc_info()[2]))
                self.db = None
                self._lastConnectAttempt = time()
                if self._consoleNotice:
                    self.console.screen.write('Connecting to DB : FAILED!\n')
                    self._consoleNotice = False

        return self.db

    ####################################################################################################################
    #                                                                                                                  #
    #   STORAGE INTERFACE                                                                                              #
    #                                                                                                                  #
    ####################################################################################################################

    def getTables(self):
        """
        List the tables of the current database.
        :return: list of strings.
        """
        tables = []
        cursor = self.query("SHOW TABLES")
        if cursor and not cursor.EOF:
            while not cursor.EOF:
                row = cursor.getRow()
                tables.append(row.values()[0])
                cursor.moveNext()
        cursor.close()
        return tables

    def truncateTable(self, table):
        """
        Empty a database table (or a collection of tables)
        :param table: The database table or a collection of tables
        :raise KeyError: If the table is not present in the database
        """
        try:
            self.query("""SET FOREIGN_KEY_CHECKS=0;""")
            current_tables = self.getTables()
            if isinstance(table, tuple) or isinstance(table, list):
                for v in table:
                    if not v in current_tables:
                        raise KeyError("could not find table '%s' in the database" % v)
                    self.query("TRUNCATE TABLE %s;" % v)
            else:
                if not table in current_tables:
                     raise KeyError("could not find table '%s' in the database" % table)
                self.query("TRUNCATE TABLE %s;" % table)
        finally:
            self.query("""SET FOREIGN_KEY_CHECKS=1;""")