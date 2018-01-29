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

__author__ = 'ThorN'
__version__ = '1.1'


class Cvar(object):

    name = ''
    value = None
    default = None

    def __init__(self, name, **kwargs):
        """
        Object constructor.
        :param name: The CVAR name.
        :param kwargs: A dict containing optional value and default.
        """
        self.name = name

        if 'value' in kwargs:
            self.value = kwargs['value']

        if 'default' in kwargs:
            self.default = kwargs['default']

    def __getitem__(self, key):
        """
        Used to get CVAR attributes using dict keys:
            - name = cvar['name']
            - value = cvar['value']
            - default = cvar['default']
            - value = cvar[0]
            - default = cvar[1]
        """
        if isinstance(key, int):
            if key == 0:
                return self.value
            elif key == 1:
                return self.default
            else:
                raise KeyError('no key %s' % key)
        else:
            return self.__dict__[key]

    def __repr__(self):
        """
        String object representation.
        :return A string representing this CVAR.
        """
        return '<%s name: "%s", value: "%s", default: "%s">' % (self.__class__.__name__,
                                                                self.name,
                                                                self.value,
                                                                self.default)

    def getString(self):
        """
        Return the CVAR value as a string.
        :return basestring
        """
        return str(self.value)
        
    def getInt(self):
        """
        Return the CVAR value as an integer.
        :return int
        """
        return int(self.value)

    def getFloat(self):
        """
        Return the CVAR value as a floating point number.
        :return float
        """
        return float(self.value)

    def getBoolean(self):
        """
        Return the CVAR value as a boolean value.
        :return boolean
        """
        if self.value in ('yes', '1', 'on', 'true'):
            return True
        elif self.value in ('no', '0', 'off', 'false'):
            return False
        else:
            raise ValueError('%s is not a boolean value' % self.value)

    def save(self, console):
        """
        Set the CVAR current value.
        :param console: The console to be used to send the cvar set command.
        """
        console.setCvar(self.name, self.value)