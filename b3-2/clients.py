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


import copy
import enum
import re
import threading
import typing

from .plugin import Plugin


@enum.unique
class Group(enum.Enum):
    """B3 client group constants"""
    GUEST = (0, 'guest', 'Guest')
    USER = (1, 'user', 'User')
    REGULAR = (2, 'reg', 'Regular')
    MODERATOR = (20, 'mod', 'Moderator')
    ADMIN = (40, 'admin', 'Admin')
    FULLADMIN = (60, 'fulladmin', 'Full Admin')
    SENIORADMIN = (80, 'senioradmin', 'Senior Admin')
    SUPERADMIN = (100, 'superadmin', 'Super Admin')

    def level(self) -> int:
        """Returns the group level"""
        return self.value[0]

    def keyword(self) -> str:
        """Returns the group keyword"""
        return self.value[1]

    def name(self) -> str:
        """Returns the group name"""
        return self.value[2]

    @classmethod
    def valueOf(cls, match) -> 'Group':
        """Returns the enum member matching the given input"""
        if match is None:
            return Group.GUEST
        if isinstance(match, Group):
            return match
        match = str(match).lower().strip()
        # MATCH LEVEL
        if match.isdigit():
            for x in cls:
                if x.level == int(match):
                    return x
        # MATCH KEYWORD
        for x in cls:
            if x.keyword == match:
                return x
        return Group.GUEST


@enum.unique
class State(enum.IntEnum):
    """B3 state constants"""
    UNKNOWN = 0
    ALIVE = 1
    DEAD = 2


@enum.unique
class Team(enum.IntEnum):
    """B3 team constants"""
    UNKNOWN = -1
    FREE = 0
    SPECTATOR = 1
    RED = 2
    BLUE = 3

    @classmethod
    def valueOf(cls, match) -> 'Team':
        """Returns the enum member matching the given input"""
        if match is None:
            return Team.UNKNOWN
        if isinstance(match, Team):
            return match
        # MATCH VALUE
        match = str(match).upper().strip()
        if match.isdigit():
            for x in cls:
                if x.level == int(match):
                    return x
        # MATCH NAME
        for x in cls:
            if x.name == match:
                return x
        # MATCH PARTIAL NAME
        for x in cls:
            if match in x.name:
                return x
        return Team.UNKNOWN


class ClientVar(object):
    """Dynamically allocated variable"""

    def __init__(self, value):
        self.value = value

    @property
    def boolean(self) -> bool:
        """Returns the current variable as a bool"""
        return str(self.value).lower() in {'1', 'true', 'yes', 'on'}

    @property
    def float(self) -> float:
        """Returns the current variable as a float"""
        try:
            return float(self.value)
        except TypeError:
            return 0

    @property
    def integer(self) -> int:
        """Returns the current variable as a interger"""
        try:
            return int(self.value)
        except TypeError:
            return 0

    @property
    def string(self) -> str:
        """Returns the current variable as a string"""
        if self.value is None:
            return ''
        return str(self.value)

    def __deepcopy__(self, memodict=None):
        return ClientVar(self.value)


class Client(object):
    """B3 client object representation"""

    def __init__(self):
        self.authed : bool = False
        self.authorizing : bool = False
        self.bot : bool = False
        self.cid : int = None
        self.data : typing.Dict[int, typing.Dict[str, ClientVar]] = {}
        self.exactName : str = None
        self.group : Group = Group.GUEST
        self.guid : str = None
        self.id : int = None
        self.ip : str = None
        self.name : str = None
        self.maskGroup : Group = None
        self.pbid : str = None
        self.state : State = State.UNKNOWN
        self.team : Team = Team.UNKNOWN
        self.firstseen : float = 0
        self.lastseen : float = 0

    def update(self, other:'Client'):
        """Update client information according with the provided data"""
        self.authed = other.authed
        self.authorizing = other.authorizing
        self.bot = other.bot
        self.cid = other.cid
        self.data = other.data
        self.exactName = other.exactName
        self.group = other.group
        self.guid = other.guid
        self.id = other.id
        self.ip = other.ip
        self.name = other.name
        self.maskGroup = other.maskGroup
        self.pbid = other.pbid
        self.state = other.state
        self.team = other.team
        self.firstseen = other.firstseen
        self.lastseen = other.lastseen

    # #########################################################################
    # DYNAMIC VARIABLE MANAGEMENT
    # #########################################################################

    def delVar(self, plugin:Plugin, key:str):
        """Delete the ClientVar stored for the given plugin/key combination"""
        try:
            del self.data[hash(plugin)][key]
        except KeyError:
            pass

    def isVar(self, plugin:Plugin, key:str) -> bool:
        """Checks whether the client stores a ClientVar for the given plugin/key combination"""
        try:
            # noinspection PyStatementEffect
            self.data[hash(plugin)][key]
            return True
        except KeyError:
            return False

    def setVar(self, plugin:Plugin, key:str, value=None) -> ClientVar:
        """Store a new ClientVar for the given plugin/key combination"""
        try:
            self.data[hash(plugin)]
        except KeyError:
            self.data[hash(plugin)] = {}
        try:
            self.data[hash(plugin)][key].value = value
        except (KeyError, AttributeError):
            self.data[hash(plugin)][key] = ClientVar(value)
        return self.data[hash(plugin)][key]

    def var(self, plugin:Plugin, key:str, default=None) -> ClientVar:
        """Returns a previously stored ClientVar for the given plugin/key combination"""
        try:
            return self.data[hash(plugin)][key]
        except KeyError:
            return self.setVar(plugin, key, default)

    # #########################################################################

    def __eq__(self, other):
        if not isinstance(other, Client):
            return False
        return self.id == other.id and self.cid == other.cid

    def __hash__(self):
        return hash(self.id) ^ hash(self.cid)

    def __deepcopy__(self, memodict=None):
        client = Client()
        client.authed = self.authed
        client.authorizing = self.authorizing
        client.bot = self.bot
        client.cid = self.cid
        client.data = self.data
        client.exactName = self.exactName
        client.group = self.group
        client.guid = self.guid
        client.id = self.id
        client.ip = self.ip
        client.name = self.name
        client.maskGroup = self.maskGroup
        client.pbid = self.pbid
        client.state = self.state
        client.team = self.team
        client.firstseen = self.firstseen
        client.lastseen = self.lastseen
        return client


class ClientManager(object):
    """B3 client manager implementation"""

    def __init__(self):
        super(ClientManager, self).__init__()
        self._clients : typing.List[Client] = []
        self._lock = threading.Lock()

    def add(self, client:Client):
        """Add a client to the index"""
        with self._lock:
            index = next((i for i, x in enumerate(self._clients) if x.id == client.id), -1)
            if index == -1:
                self._clients.append(client)
                self._clients.sort(key=lambda arg:arg.cid)

    def clear(self):
        """Clear the client index"""
        with self._lock:
            self._clients.clear()

    def count(self) -> int:
        """Returns the number of clients stored in the index"""
        with self._lock:
            return len(self._clients)

    def remove(self, client:Client) -> typing.Optional[Client]:
        """Remove a client from the index"""
        with self._lock:
            index = next((i for i, x in enumerate(self._clients) if x.id == client.id), -1)
            if index != -1:
                try:
                    return self._clients.pop(index)
                except IndexError:
                    return None

    def save(self, client:Client):
        """Save client data in the index (either adding or updating)"""
        with self._lock:
            index = next((i for i, x in enumerate(self._clients) if x.id == client.id), -1)
            if index == -1:
                self._clients.append(client)
                self._clients.sort(key=lambda arg: arg.cid)
            else:
                saved = self._clients[index]
                saved.update(client)

    # #########################################################################
    # SEARCH
    # #########################################################################

    def getByCID(self, cid:int) -> typing.Optional[Client]:
        """Returns the client matching the given slot number"""
        with self._lock:
            for client in self._clients:
                if client.cid == cid:
                    return copy.deepcopy(client)
        return None

    def getByGroup(self, group:Group, mask:bool=False) -> typing.List[Client]:
        """Returns a list of clients matching the given group"""
        collection = []
        with self._lock:
            for client in self._clients:
                if mask and client.maskGroup:
                    if client.maskGroup is group:
                        collection += copy.deepcopy(client)
                elif client.group is group:
                    collection += copy.deepcopy(client)
        return collection

    def getByGUID(self, guid:str) -> typing.Optional[Client]:
        """Returns the client matching the given GUID"""
        guid = guid.upper()
        with self._lock:
            for client in self._clients:
                if client.guid == guid:
                    return copy.deepcopy(client)
        return None

    def getById(self, id:int) -> typing.Optional[Client]:
        """Returns the client matching the given id"""
        with self._lock:
            for client in self._clients:
                if client.id == id:
                    return copy.deepcopy(client)
        return None

    def getByMagic(self, handle:typing.Union[str, int]) -> typing.List[Client]:
        """Returns the client matching the given handle"""
        handle = str(handle)
        handle = handle.strip()
        if re.match(r'^[0-9]+$', handle):
            client = self.getByCID(int(handle))
            if client:
                return [client]
            return []
        if re.match(r'^@([0-9]+)$', handle):
            client = self.getById(int(handle[1:]))
            if client:
                return [client]
            return []
        return self.getByName(handle)

    def getByName(self, name) -> typing.List[Client]:
        """Returns a list of clients matching the given name"""
        collection = []
        name = name.lower()
        with self._lock:
            for client in self._clients:
                if name in client.name.lower():
                    collection += copy.deepcopy(client)
        return collection

    def getByState(self, state:State) -> typing.List[Client]:
        """Returns a list of clients matching the given state"""
        collection = []
        with self._lock:
            for client in self._clients:
                if client.state is state:
                    collection += copy.deepcopy(client)
        return collection

    def getByTeam(self, team:Team) -> typing.List[Client]:
        """Returns a list of clients matching the given team"""
        collection = []
        with self._lock:
            for client in self._clients:
                if client.team is team:
                    collection += copy.deepcopy(client)
        return collection

    def getList(self) -> typing.List[Client]:
        """Returns the list of connected clients"""
        with self._lock:
            return copy.deepcopy(self._clients)