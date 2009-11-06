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

__author__  = 'ThorN'
__version__ = '1.0.1'

class Cvar(object):
    name = ''
    value = None
    default = None

    def __init__(self, name, **kwargs):
        self.name = name

        if kwargs.has_key('value'):
            self.value = kwargs['value']

        if kwargs.has_key('default'):
            self.default = kwargs['default']

    def __getitem__(self, key):
        if type(key) is int:
            if key == 0:
                return self.value
            elif key == 1:
                return self.default
            else:
                raise KeyError('No key %s' % key)
        else:
            return self.__dict__[key]

    def __repr__(self):
        return '<%s name="%s", value="%s", default="%s">' % (self.__class__.__name__, self.name, self.value, self.default)

    def getString(self):
        return str(self.value)
        
    def getInt(self):
        return int(self.value)

    def getFloat(self):
        return float(self.value)

    def getBoolean(self):
        if self.value in ('yes', '1', 'on', 'true'):
            return True
        elif self.value in ('no', '0', 'off', 'false'):
            return False
        else:
            raise ValueError('%s is not a boolean value' % (self.value))

    def save(self, console):
        """\
        Set the cvars current value
        """
        console.setCvar(self.name, self.value)        

if __name__ == '__main__':
    x = Cvar('testvar', value='1', default='1')

    print x

    print x.name
    print x.value
    print x.default

    print x.getString()
    print x.getInt()
    print x.getFloat()
    print x.getBoolean()

    print x[0]
    print x[1]
    print x[2]