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

import configparser
import socket
import threading
import time
import typing

from ...output import LoggerMixin


class Rcon(LoggerMixin, object):
    """Quake 3 Arena RCON interface"""

    def __init__(self, config:configparser.ConfigParser):
        super(Rcon, self).__init__()
        self._rcon_ip = config.get('server', 'rcon_ip', fallback='127.0.0.1')
        self._rcon_port = config.getint('server', 'rcon_port', fallback=27960)
        self._rcon_password = config.get('server', 'rcon_password', fallback='')
        self._rcon_timeout = config.getfloat('server', 'rcon_timeout', fallback=0.75)
        self._rcon_delay = config.getfloat('server', 'rcon_delay', fallback=0.25)
        self._rcon_last_exec_time = 0
        self._condition = threading.Condition(threading.RLock())
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket.connect((self._rcon_ip, self._rcon_port))

    def _recv(self, timeout:int=2, buffersize=4096) -> typing.Optional[str]:
        """Read data from the socket"""
        with self._condition:
            self._socket.settimeout(timeout)
            data:str = self._socket.recv(buffersize)
            if data is not None:
                data.replace('\xFF\xFF\xFF\xFFprint', '')
                data = data.strip() or None
            return data

    def _write(self, data:str):
        """Write the RCON command"""
        with self._condition:
            delay = time.time() - self._rcon_last_exec_time
            if delay < self._rcon_delay:
                self._condition.wait(self._rcon_delay - delay)
            self.verbose('RCON: sending (%s:%s) %r', self._rcon_ip, self._rcon_port, data)
            self._socket.settimeout(self._rcon_timeout)
            self._socket.send('\xFF\xFF\xFF\xFFrcon "%s" %s' % (self._rcon_password, data))
            self._rcon_last_exec_time = time.time()

    # #########################################################################

    def send(self, data:str, retries:int=2, timeout:int=2, buffersize:int=4096) -> typing.Optional[str]:
        """Send an RCON command"""
        with self._condition:
            while retries > 0:
                try:
                    self._write(data)
                    response = self._recv(timeout, buffersize)
                except (socket.error, socket.timeout) as e:
                    self.warning('RCON: error sending: %r', e)
                    retries -= 1
                else:
                    return response
        self.error('RCON: too many retries: aborting (%r)', data)
        return None