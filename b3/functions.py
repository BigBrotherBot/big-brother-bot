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


import re


def getBytes(size:str) -> int:
    """Returns the amount of bytes identified by the given string format"""
    size = size.upper()
    r = re.compile(r'''^(?P<size>\d+)\s*(?P<multiplier>KB|MB|GB|TB|K|M|G|T?)$''')
    m = r.match(size)
    if not m:
        raise TypeError('invalid input given: %s' % size)
    size = m.group('size')
    multiplier = m.group('multiplier')
    if multiplier in {'K', 'KB'}:
        return int(size) * 1024
    if multiplier in {'M', 'MB'}:
        return int(size) * 1024 * 1024
    if multiplier in {'G', 'GB'}:
        return int(size) * 1024 * 1024 * 1024
    if multiplier in {'T', 'TB'}:
        return int(size) * 1024 * 1024 * 1024
    return int(size)


def rchop(string:str, ending:str) -> str:
    """Remove 'ending' from 'string' if present"""
    if string.endswith(ending):
        return string[:-len(ending)]
    return string
