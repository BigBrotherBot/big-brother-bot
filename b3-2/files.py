# -*- coding: utf-8 -*-

# ################################################################### #
#                                                                     #
#  BigBrotherBot (B3) (www.bigbrotherbot.net)                         #
#  Copyright (C) 2018 Daniele Pantaleone <danielepantaleone@me.com>   #
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


import io
import shutil
import os
import sys
import typing

from .output import LoggerMixin


# #############################################################################
# BEGIN SETUP
# #############################################################################


if hasattr(sys, 'frozen'):
    MODULE = os.path.normpath(os.path.expanduser(os.path.dirname(sys.executable)))
    ROOT = MODULE
else:
    MODULE = os.path.normpath(os.path.expanduser(os.path.dirname(sys.modules['b3'].__file__)))
    ROOT = os.path.join(MODULE, '..')

HOME = os.path.normpath(os.path.expanduser('~/.b3'))
CONF = os.path.join(HOME, 'conf')
PLUGINS = os.path.join(ROOT, 'plugins')
EXTPLUGINS = os.path.join(HOME, 'plugins')

if not os.path.isdir(HOME):
    os.mkdir(HOME)
if not os.path.isdir(CONF):
    os.mkdir(CONF)
if not os.path.isdir(EXTPLUGINS):
    os.mkdir(EXTPLUGINS)


# #############################################################################
# END SETUP
# #############################################################################


class FileManager(LoggerMixin, object):
    """Manager to deal with the underlying file system"""

    def cpdir(self, src:str, dst:str):
        """Copy a file or a directory"""
        src = self.expand(src)
        dst = self.expand(dst)
        if self.isDir(src):
            shutil.copytree(src, dst)
            self.verbose("Copying directory: %s -> %s", src, dst)
        elif self.isFile(src):
            self.verbose("Copying file: %s -> %s", src, dst)
            shutil.copy(src, dst)

    def isDir(self, path:str) -> bool:
        """Returns True if the given path identifies a directory, False otherwise"""
        return os.path.isdir(self.expand(path))

    def isFile(self, path:str) -> bool:
        """Returns True if the given path identifies a regular file, False otherwise"""
        return os.path.isfile(self.expand(path))

    def mkdir(self, path:str):
        """Create the directory identified by the given path if it doesn't exists"""
        path = self.expand(path)
        if not self.isDir(path):
            self.verbose("Creating directory: %s", path)
            os.mkdir(path)

    def read(self, path:str) -> str:
        """Read the content of a file"""
        path = self.expand(path)
        self.verbose("Reading file: %s", path)
        with io.open(path, 'r', encoding='utf8') as ptr:
            return ptr.read()

    def rename(self, src:str, dst:str):
        """Rename a file or a directory"""
        src = self.expand(src)
        dst = self.expand(dst)
        self.verbose("Rename: %s -> %s", src, dst)
        os.rename(src, dst)

    def remove(self, path:str):
        """Remove a file or a directory"""
        path = self.expand(path)
        if self.isFile(path):
            self.verbose("Removing file: %s", path)
            os.remove(path)
        elif self.isDir(path):
            self.verbose("Removing directory: %s", path)
            shutil.rmtree(path)

    def write(self, content:typing.Union[bytes, str], path:str):
        """Write the given content to the specified path"""
        path = self.expand(path)
        self.verbose("Writing file: %s", path)
        components = os.path.split(path)
        staging = os.path.join(components[0], '.{0}'.format(components[1]))
        with io.open(staging, 'w', encoding='utf8') as ptr:
            ptr.write(content)
        self.remove(path)
        self.rename(staging, path)

    # #########################################################################

    @staticmethod
    def expand(path:str) -> str:
        """Return an absolute path by expanding the given relative one.
        The following tokens will be expanded:

            - @b3 => B3 module directory
            - @conf => B3 main configuration directory
            - @home => B3 home directory (.b3 in $HOME)
            - @root => B3 root (matches @b3 if running a frozen application)
            - @plugins => B3 plugins directory
            - @extplugins => B3 external plugins directory
            - ~ => will be expanded to the user home directory ($HOME)
        """
        if path.startswith('@b3/') or path.startswith('@b3\\'):
            path = os.path.join(MODULE, path[4:])
        elif path.startswith('@conf/') or path.startswith('@conf\\'):
            path = os.path.join(CONF, path[6:])
        elif path.startswith('@home/') or path.startswith('@home\\'):
            path = os.path.join(HOME, path[6:])
        elif path.startswith('@root/') or path.startswith('@root\\'):
            path = os.path.join(ROOT, path[6:])
        elif path.startswith('@plugins/') or path.startswith('@plugins\\'):
            path = os.path.join(PLUGINS, path[9:])
        elif path.startswith('@extplugins/') or path.startswith('@extplugins\\'):
            path = os.path.join(EXTPLUGINS, path[12:])
        return os.path.abspath(os.path.normpath(os.path.expanduser(path)))