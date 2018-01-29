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

from b3.storage.common import DatabaseStorage


class SqliteStorage(DatabaseStorage):

    protocol = 'sqlite'

    def __init__(self, dsn, dsnDict, console):
        """
        Object constructor.
        :param dsn: The database connection string.
        :param dsnDict: The database connection string parsed into a dict.
        :param console: The console instance.
        """
        super(SqliteStorage, self).__init__(dsn, dsnDict, console)

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
        try:
            import sqlite3
            path = b3.getWritableFilePath(self.dsn[9:])
            self.console.bot("Using database file: %s" % path)
            is_new_database = not os.path.isfile(path)
            self.db = sqlite3.connect(path, check_same_thread=False)
            self.db.isolation_level = None  # set autocommit mode
        except Exception, e:
            self.db = None
            self.console.error('Database connection failed: %s', e)
            if self._consoleNotice:
                self.console.screen.write('Connecting to DB : FAILED\n')
                self._consoleNotice = False
        else:
            # import SQL script if necessary
            if path == ':memory:' or is_new_database:
                self.console.info("Importing SQL file: %s..." % b3.getAbsolutePath("@b3/sql/sqlite/b3.sql"))
                self.queryFromFile("@b3/sql/sqlite/b3.sql")

            if self._consoleNotice:
                self.console.screen.write('Connecting to DB : OK\n')
                self._consoleNotice = False
        finally:
            return self.db

    def getConnection(self):
        """
        Return the database connection. If the connection has not been established yet, will establish a new one.
        :return The connection instance, or None if no connection can be established.
        """
        if self.db:
            return self.db
        return self.connect()

    def shutdown(self):
        """
        Close the current active database connection.
        """
        if self.db:
            # checking 'open' will prevent exception raising
            self.console.bot('Closing connection with SQLite database...')
            self.db.close()
        self.db = None

    ####################################################################################################################
    #                                                                                                                  #
    #   STORAGE INTERFACE                                                                                              #
    #                                                                                                                  #
    ####################################################################################################################

    def getTables(self):
        """
        List the tables of the current database.
        :return: List of strings.
        """
        tables = []
        cursor = self.query("SELECT * FROM sqlite_master WHERE type='table'")
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
        current_tables = self.getTables()
        if isinstance(table, tuple) or isinstance(table, list):
            for v in table:
                if not v in current_tables:
                    raise KeyError("could not find table '%s' in the database" % v)
                self.query("DELETE FROM %s;" % v)
                self.query("DELETE FROM sqlite_sequence WHERE name='%s';" % v)
        else:
            if not table in current_tables:
                 raise KeyError("could not find table '%s' in the database" % table)
            self.query("DELETE FROM %s;" % table)
            self.query("DELETE FROM sqlite_sequence WHERE name='%s';" % table)

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
        return self.db is None