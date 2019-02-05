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


def str_to_bytes(size:str) -> int:
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


def topological_sort(source:list):
    """
    Perform topological sort on elements using generators.
    http://stackoverflow.com/questions/11557241/python-sorting-a-dependency-list
    :param source: list of (name, set(names of dependancies)) pairs
    """
    pending = [(name, set(deps)) for name, deps in source] # copy deps so we can modify set in-place
    emitted = []
    while pending:
        next_pending = []
        next_emitted = []
        for entry in pending:
            name, deps = entry
            deps.difference_update(emitted) # remove deps we emitted last pass
            if deps: # still has deps? recheck during next pass
                next_pending.append(entry)
            else: # no more deps? time to emit
                yield name
                emitted.append(name) # <-- not required, but helps preserve original ordering
                next_emitted.append(name) # remember what we emitted for difference_update() in next pass
        if not next_emitted: # all entries have unmet deps, one of two things is wrong...
            raise RuntimeError("cyclic or missing dependancy detected: %r" % (next_pending,))
        pending = next_pending
        emitted = next_emitted
