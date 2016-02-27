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
# 2011-04-16 - 1.0.2         - Courgette - fix bug in escaping strings containing "
# 2011-04-17 - 1.0.3 / 1.0.4 - Courgette - fix bug introduced in 1.0.2
# 2011-05-31 - 1.1.0         - Courgette - sqlite compatible
# 2014-07-25 - 1.2.0         - Fenix     - syntax cleanup
# 2014-12-28 - 1.3.0         - Fenix     - postgresql support

__author__  = 'ThorN'
__version__ = '1.3.0'

class QueryBuilder(object):

    def __init__(self, db=None):
        """
        Object constructor.
        :param db: The current database connection.
        """
        self.db = db

    def escape(self, word):
        """
        Escape quotes from a given string.
        :param word: The string on which to perform the escape
        """
        if isinstance(word, int) or isinstance(word, long) or isinstance(word, complex) or isinstance(word, float):
            return str(word)
        elif word is None:
            return '"None"'
        else:
            return '"%s"' % word.replace('"', '\\"')

    def quoteArgs(self, args):
        """
        Return a list of quoted arguments.
        :param args: The list of arguments to format.
        """
        if type(args[0]) is tuple or type(args[0]) is list:
            args = args[0]
        nargs = []
        for a in args:
            nargs.append(self.escape(a))
        return tuple(nargs)

    def fieldStr(self, fields):
        """
        Return a list of fields whose keywords are surrounded by backticks.
        :param fields: The list of fields to format.
        """
        if isinstance(fields, tuple) or isinstance(fields, list):
            return "`%s`" % "`, `".join(fields)
        elif isinstance(fields, str):
            if fields == "*":
                return fields
            else:
                return "`%s`" % fields
        else:
            raise TypeError('field must be a tuple, list, or string')

    def FieldClause(self, field, value=None):
        """
        Format a field clause in SQL according to the given parameters.
        :param field: The comparision type for this clause.
        :param value: The value of the comparision.
        """
        field = field.strip()

        if type(value) == list or type(value) == tuple:
            values = []
            for v in value:
                values.append(self.escape(v))
            return "`" + field + "` IN(" + ",".join(values) + ")"
        elif value is None:
            value = self.escape('')
        else:
            value = self.escape(value)

        if len(field) >= 2:
            if field[-2] == ">=":
                return "`" + field[:-2].strip() + "` >= " + value
            elif field[-2] == "<=":
                return "`" + field[:-2].strip() + "` <= " + value
            elif field[-1] == "<":
                return "`" + field[:-1].strip() + "` < " + value
            elif field[-1] == ">":
                return "`" + field[:-1].strip() + "` > " + value
            elif field[-1] == "=":
                return "`" + field[:-1].strip() + "` = " + value
            elif field[-1] == "%" and field[0] == "%":
                return "`" + field[1:-1].strip() + "` LIKE '%" + value[1:-1] + "%'"
            elif field[-1] == "%":
                return "`" + field[:-1].strip() + "` LIKE '" + value[1:-1] + "%'"
            elif field[0] == '%':
                return "`" + field[1:].strip() + "` LIKE '%" + value[1:-1] + "'"
            elif field[0] == '&':
                return "`" + field[1:].strip() + "` & " + value
            elif field[0] == '|':
                return "`" + field[1:].strip() + "` | " + value

        return "`" + field + "` = " + value

    def WhereClause(self, fields=None, values=None, concat=' and '):
        """
        Construct a where clause for an SQL query.
        :param fields: The fields of the where clause.
        :param values: The value of each field.
        :param concat: The concat value for multiple where clauses
        """
        sql = []
        if isinstance(fields, tuple) and values is None \
                and len(fields) == 2:
            if isinstance(fields[1], list):
                values = tuple(fields[1])
            elif not isinstance(fields[1], tuple):
                values = (str(fields[1]),)

            if isinstance(fields[0], tuple) or isinstance(fields[0], list):
                fields = tuple(fields[0])
            elif not isinstance(fields[0], tuple):
                fields = (str(fields[0]),)
        else:
            if isinstance(fields, list):
                fields = tuple(fields)
            if isinstance(values, list):
                values = tuple(values)

        if isinstance(fields, tuple) and isinstance(values, tuple):
            # this will be a combination of both
            if len(fields) == 1 and len(values) == 1:
                sql.append(self.FieldClause(fields[0], values[0]))
            else:
                print fields
                for k, field in enumerate(fields):
                    v = values[k]
                    sql.append(self.FieldClause(field, v))

        elif fields is not None and not isinstance(fields, tuple) \
                and values is not None and not isinstance(values, tuple):
            sql.append(self.FieldClause(fields, values))

        elif isinstance(fields, tuple) and len(fields) == 1 \
                and isinstance(values, str):
            sql.append(self.FieldClause(fields[0], values))

        elif isinstance(fields, tuple) and len(fields) > 0 \
                and isinstance(values, str):

            sql.append(self.FieldClause(fields[0], values))

            for field in fields[1:]:
                sql.append(self.FieldClause(field, ''))

        elif isinstance(fields, dict):
            for k, v in fields.iteritems():
                sql.append(self.FieldClause(k, v))

        else:
            # its type is unknown, nothing we can do
            return fields

        return concat.join(sql)

    def SelectQuery(self, fields, table, where='', orderby='', limit=0, offset='', groupby='', having='', **keywords):
        """
        Construct a SQL select query.
        :param fields: A list of fields to select.
        :param table: The table from where to fetch data.
        :param where: A WHERE clause for this select statement.
        :param orderby: The ORDER BY clayse for this select statement.
        :param limit: The amount of data data to collect.
        :param offset: An offset which specifies how many records to skip.
        :param groupby: The GROUP BY clause for this select statement.
        :param having: The HAVING clause for this select statement.
        :param keywords: Unused at the moment.
        """
        sql = ['SELECT %s FROM %s' % (self.fieldStr(fields), table)]

        if where:
            sql.append("WHERE %s" % self.WhereClause(where))
        if groupby:
            sql.append("GROUP BY %s" % orderby)
        if having:
            sql.append("HAVING %s" % having)
        if orderby:
            sql.append("ORDER BY %s" % orderby)
        if limit:
            sql.append("LIMIT")
        if offset:
            sql.append(offset + ",")
        if limit:
            sql.append(str(limit))

        return " ".join(sql)

    def UpdateQuery(self, data, table, where, delayed=None): 
        """
        Construct a SQL update query.
        :param data: A dictionary of key-value pairs for the update.
        :param table: The table from where to fetch data.
        :param where: A WHERE clause for this select statement.
        :param delayed: Whether to add the DELAYED clause to the query.
        """
        sql = "UPDATE "

        if delayed:
            sql += "DELAYED "

        sql += table + " SET "

        sets = []
        for k, v in data.iteritems():
            sets.append(self.FieldClause(k, v))

        sql += ", ".join(sets)
        sql += " WHERE " + self.WhereClause(where)

        return sql

    def InsertQuery(self, data, table, delayed=None): 
        """
        Construct a SQL insert query.
        :param data: A dictionary of key-value pairs for the update.
        :param table: The table from where to fetch data.
        :param delayed: Whether to add the DELAYED clause to the query.
        """
        sql = "INSERT "

        if delayed:
            sql += "DELAYED "

        sql += "INTO " + table

        keys = []
        values = []
        for k, v in data.iteritems():
            keys.append(k)
            values.append(self.escape(v))

        sql += "(" + self.fieldStr(keys) + ") VALUES (" + ", ".join(values) + ")"

        return sql

    def ReplaceQuery(self, data, table, delayed=None): 
        """
        Construct a SQL replace query.
        :param data: A dictionary of key-value pairs for the update.
        :param table: The table from where to fetch data.
        :param delayed: Whether to add the DELAYED clause to the query.
        """
        sql = "REPLACE "

        if delayed:
            sql += "DELAYED "

        sql += "INTO " + table

        keys = []
        values = []
        for k, v in data.iteritems():
            keys.append(k)
            values.append(self.escape(v))

        sql += "(" + self.fieldStr(keys) + ") VALUES (" + ", ".join(values) + ")"

        return sql