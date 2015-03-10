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
# 2015-03-08 - 1.0 - Fenix - initial release
# 2015-03-09 - 1.1 - Fenix - added ProgrammingError exception class


class ConfigFileNotFound(Exception):
    """
    Raised whenever the configuration file can't be found.
    """
    def __init__(self, message):
        Exception.__init__(self, message)
        
    def __str__(self):
        return repr(self.message)


class ConfigFileNotValid(Exception):
    """
    Raised whenever we are parsing an invalid configuration file.
    """
    def __init__(self, message):
        Exception.__init__(self, message)
        
    def __str__(self):
        return repr(self.message)


class MissingRequirement(Exception):
    """
    Raised whenever we can't initialize a functionality because some modules are missing.
    """
    def __init__(self, message, throwable=None):
        Exception.__init__(self, message)
        self.throwable = throwable

    def __str__(self):
        if self.throwable:
            return '%r - %r' % (repr(self.message), repr(self.throwable))
        return repr(self.message)


class ProgrammingError(Exception):
    """
    Raised whenever a programming error is detected.
    """
    def __init__(self, message):
        Exception.__init__(self, message)

    def __str__(self):
        return repr(self.message)