#
# BigBrotherBot(B3) (www.bigbrotherbot.com)
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

__author__  = 'ThorN'
__version__ = '1.0.1'

class QueryBuilder(object):
    def __init__(self, db=None):
        # db is not used yet
        # the intention is for the class to use the db's escape method
        pass

    def escape(self, word):
        if isinstance(word, int):
            return str(word)
        else:
            return '"%s"' % word

    def quoteArgs(self, args):
        if type(args[0]) is tuple or type(args[0]) is list:
            args = args[0]

        nargs = []
        for a in args:
            nargs.append(self.escape(a))

        return tuple(nargs)

    def fieldStr(self, fields):
        if isinstance(fields, tuple) or isinstance(fields, list):
            return '`%s`' % '`, `'.join(fields)
        elif isinstance(fields, str):
            if fields == '*':
                return fields
            else:
                return '`%s`' % fields
        else:
            raise TypeError, 'Field must be a tuple, list, or string'

    def WhereClause(self, fields=None, values=None, concat=' && '):
        sql = []
            
        if isinstance(fields, tuple) and values == None \
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
                for k,field in enumerate(fields):
                    v = values[k]
                    sql.append(self.FieldClause(field, v))

        elif fields != None and not isinstance(fields, tuple) \
            and values != None and not isinstance(values, tuple):
            sql.append(self.FieldClause(fields, values))

        elif isinstance(fields, tuple) \
            and len(fields) == 1 \
            and isinstance(values, str):
            sql.append(self.FieldClause(fields[0], values))

        elif isinstance(fields, tuple) \
            and len(fields) > 0 \
            and isinstance(values, str):

            sql.append(self.FieldClause(fields[0], values))

            for field in fields[1:]:
                sql.append(self.FieldClause(field, ''))

        elif isinstance(fields, dict):
            for k,v in fields.iteritems():
                sql.append(self.FieldClause(k, v))

        else:
            # its type is unknown, nothing we can do
            return fields

        return concat.join(sql)


    def SelectQuery(self, fields, table, where='', orderby='', limit=0, offset='', groupby='', having='', **keywords):
        sql = []
        sql.append('SELECT %s FROM %s' % (self.fieldStr(fields), table))
            
        if where:   sql.append('WHERE %s' % self.WhereClause(where))
        if groupby: sql.append('GROUP BY %s' % orderby)
        if having:  sql.append('HAVING %s' % having)
        if orderby: sql.append('ORDER BY %s' % orderby)

        if limit:   sql.append('LIMIT')
        if offset:  sql.append(offset + ',')
        if limit:   sql.append(str(limit))

        return ' '.join(sql)

    def FieldClause(self, field, value=None): 
        field = field.strip()

        if type(value) == list or type(value) == tuple:
            values = []
            for v in value:
                values.append(self.escape(v))
            return '`' +  field + '` IN(' + ','.join(values) + ')'
        elif value == None:
            value = self.escape('')
        else:
            value = self.escape(value)

        if len(field) >= 2:
            if field[-2] == '>=': 
                return '`' +  field[:-2].strip() + '` >= ' + value
            elif field[-2] == '<=':
                return '`' +  field[:-2].strip() + '` <= ' + value
            elif field[-1] == '<':
                return '`' +  field[:-1].strip() + '` < ' + value
            elif field[-1] == '>':
                return '`' +  field[:-1].strip() + '` > ' + value
            elif field[-1] == '=':
                return '`' +  field[:-1].strip() + '` = ' + value
            elif field[-1] == '%' and field[0] == '%':
                return '`' +  field[1:-1].strip() + '` LIKE "%' + value[1:-1] + '%"'
            elif field[-1] == '%':
                return '`' +  field[:-1].strip() + '` LIKE "' + value[1:-1] + '%"'
            elif field[0] == '%':
                return '`' +  field[1:].strip() + '` LIKE "%' + value[1:-1] + '"'
            elif field[0] == '&':
                return '`' +  field[1:].strip() + '` & ' + value
            elif field[0] == '|':
                return '`' +  field[1:].strip() + '` | ' + value

        return '`' + field + '` = ' + value

    def UpdateQuery(self, data, table, where, delayed=None): 
        sql = 'UPDATE '

        if delayed:
            sql += 'DELAYED '

        sql += table + ' SET '

        sets = []    
        for k,v in data.iteritems():
            sets.append(self.FieldClause(k, v))

        sql += ', '.join(sets)

        sql += ' WHERE ' + self.WhereClause(where)

        return sql

    def InsertQuery(self, data, table, delayed=None): 
        sql = 'INSERT '

        if delayed:
            sql += 'DELAYED '

        sql += 'INTO ' + table

        keys = []
        values = []
        for k,v in data.iteritems():
            keys.append(k)
            values.append(self.escape(v))

        sql += '(' + self.fieldStr(keys) + ') VALUES (' + ', '.join(values) + ')'

        return sql

    def ReplaceQuery(self, data, table, delayed=None): 
        sql = 'REPLACE '

        if delayed:
            sql += 'DELAYED '

        sql += 'INTO ' + table

        keys = []
        values = []
        for k,v in data.iteritems():
            keys.append(k)
            values.append(self.escape(v))

        sql += '(' + self.fieldStr(keys) + ') VALUES (' + ', '.join(values) + ')'

        return sql