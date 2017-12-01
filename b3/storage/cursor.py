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


class Cursor(object):

    _cursor = None
    _conn = None

    fields = None
    lastrowid = 0
    rowcount = 0

    EOF = False

    def __init__(self, cursor, conn):
        """
        Object constructor.
        :param cursor: The opened result cursor.
        :param conn: The database connection instance.
        """
        self._cursor = cursor
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
            self.EOF = not self.fields or not self._cursor
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
        row = self.getRow()
        self.close()
        return row

    def getRow(self):
        """
        Return a result set row into a dict.
        :return The result set row or an empty dict if there are no more records in this result set.
        """
        if self.EOF:
            return dict()
        d = dict()
        desc = self._cursor.description
        for i in xrange(0, len(self.fields)):
            d[desc[i][0]] = self.fields[i]
        return d

    def getValue(self, key, default=None):
        """
        Return a value from the current result set row.
        :return The value extracted from the result set or default if the the given key doesn't match any field.
        """
        row = self.getRow()
        if key in row:
           return row[key]
        return default

    def close(self):
        """
        Close the active result set.
        """
        if self._cursor:
            self._cursor.close()
        self._cursor = None
        self.EOF = True