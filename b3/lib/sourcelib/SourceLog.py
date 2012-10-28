#!/usr/bin/python
# -*- coding: utf-8 -*-

#------------------------------------------------------------------------------
# SourceLog - Python class for parsing logs of Source Dedicated Servers
# Copyright (c) 2010 Andreas Klauer <Andreas.Klauer@metamorpher.de>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#------------------------------------------------------------------------------

# TODO:  Support games other than Team Fortress 2

"""http://developer.valvesoftware.com/wiki/HL_Log_Standard"""

import re
import socket
import asyncore

PACKETSIZE=1400

# --- Regular Expressions: ---

TOKEN = {
    'address': '(?P<ip>[0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3})(|:(?P<port>[0-9]+))',
    'attacker': '(?P<attacker_name>.*?)<(?P<attacker_uid>[0-9]*)><(?P<attacker_steamid>(Console|BOT|STEAM_[01]:[01]:[0-9]{1,12}))><(?P<attacker_team>[^<>"]*)>',
    'class': '(?P<class>[^"]+)',
    'command': '(?P<command>.*)',
    'key': '(?P<key>[^"]+)',
    'map': '(?P<map>[^"]+)',
    'message': '(?P<message>.*)',
    'name': '(?P<name>.*)',
    'numplayers': '(?P<numplayers>[0-9]+)',
    'player': '(?P<player_name>.*?)<(?P<player_uid>[0-9]*)><(?P<player_steamid>(Console|BOT|STEAM_[01]:[01]:[0-9]{1,12}))><(?P<player_team>[^<>"]*)>',
    'position': '^(?P<x>-?[0-9]+) (?P<y>-?[0-9]+) (?P<z>-?[0-9]+)',
    'property': ' \((?P<property_key>[^() ]+) "(?P<property_value>[^"]*)"\)',
    'propertybug': '(?P<rest>.*" disconnected) \((?P<property_key>reason) "(?P<proprety_value>[^"]*)',
    'reason': '(?P<reason>.*)',
    'rest': '(?P<rest>.*)',
    'score': '(?P<score>-?[0-9]+)',
    'team': '(?P<team>[^"]+)',
    'timestamp': '(?P<month>[0-9]{2})/(?P<day>[0-9]{2})/(?P<year>[0-9]{4}) - (?P<hour>[0-9]{2}):(?P<minute>[0-9]{2}):(?P<second>[0-9]{2}): ',
    'trigger': '(?P<trigger>[^"]+)',
    'type': '(?P<type>RL|L) ',
    'value': '(?P<value>.*)',
    'victim': '(?P<victim_name>.*?)<(?P<victim_uid>[0-9]*)><(?P<victim_steamid>(Console|BOT|STEAM_[01]:[01]:[0-9]{1,12}))><(?P<victim_team>[^<>"]*)>',
    'weapon': '(?P<weapon>[^"]+)',
}

REHEADER = re.compile('^'+TOKEN['type']+TOKEN['timestamp']+TOKEN['rest']+'$', re.U)
REPROPERTY = re.compile('^'+TOKEN['rest']+TOKEN['property']+'$', re.U)
REPROPERTYBUG = re.compile('^'+TOKEN['propertybug']+'$', re.U)
RERULES = re.compile('^"'+TOKEN['key']+'" = "'+TOKEN['value']+'"$', re.U)

RELOG = [
    ['change_name', re.compile('^"'+TOKEN['player']+'" changed name to "'+TOKEN['name']+'"$', re.U)],
    ['class', re.compile('^"'+TOKEN['player']+'" changed role to "'+TOKEN['class']+'"$', re.U)],
    ['connect', re.compile('^"'+TOKEN['player']+'" connected, address "(none|'+TOKEN['address']+')"$', re.U)],
    ['disconnect', re.compile('^"'+TOKEN['player']+'" disconnected$', re.U)],
    ['enter', re.compile('^"'+TOKEN['player']+'" entered the game$', re.U)],
    ['kill', re.compile('^"'+TOKEN['attacker']+'" killed "'+TOKEN['victim']+'" with "'+TOKEN['weapon']+'"$', re.U)],
    ['log_start', re.compile('^Log file started$', re.U)],
    ['log_stop', re.compile('^Log file closed$', re.U)],
    ['map_load', re.compile('^Loading map "'+TOKEN['map']+'"$', re.U)],
    ['map_start', re.compile('^Started map "'+TOKEN['map']+'"$', re.U)],
    ['position_report', re.compile('^"'+TOKEN['player']+'" position_report$', re.U)],
    ['rcon', re.compile('^rcon from "'+TOKEN['address']+'": command "'+TOKEN['command']+'"$', re.U)],
    ['rcon_badpw', re.compile('^rcon from "'+TOKEN['address']+'": Bad Password$', re.U)],
    ['say', re.compile('^"'+TOKEN['player']+'" say "'+TOKEN['message']+'"$', re.U)],
    ['say_team', re.compile('^"'+TOKEN['player']+'" say_team "'+TOKEN['message']+'"$', re.U)],
    ['score', re.compile('^Team "'+TOKEN['team']+'" current score "'+TOKEN['score']+'" with "'+TOKEN['numplayers']+'" players$', re.U)],
    ['score_final', re.compile('^Team "'+TOKEN['team']+'" final score "'+TOKEN['score']+'" with "'+TOKEN['numplayers']+'" players$', re.U)],
    ['server_cvar', re.compile('^server_cvar: "'+TOKEN['key']+'" "'+TOKEN['value']+'"$', re.U)],
    ['server_message', re.compile('^server_message: "'+TOKEN['message']+'"$', re.U)],
    ['suicide', re.compile('^"'+TOKEN['player']+'" committed suicide with "'+TOKEN['weapon']+'"$', re.U)],
    ['team', re.compile('^"'+TOKEN['player']+'" joined team "'+TOKEN['team']+'"$', re.U)],
    ['trigger', re.compile('^"'+TOKEN['player']+'" triggered "'+TOKEN['trigger']+'"$', re.U)],
    ['trigger_attack', re.compile('^"'+TOKEN['attacker']+'" triggered "'+TOKEN['trigger']+'" against "'+TOKEN['victim']+'"$', re.U)],
    ['trigger_attack_weapon', re.compile('^"'+TOKEN['attacker']+'" triggered "'+TOKEN['trigger']+'" against "'+TOKEN['victim']+'" with "'+TOKEN['weapon']+'"$', re.U)],
    ['trigger_team', re.compile('^Team "'+TOKEN['team']+'" triggered "'+TOKEN['trigger']+'"$', re.U)],
    ['trigger_world', re.compile('^World triggered "'+TOKEN['trigger']+'"$', re.U)],
    ['trigger_world_reason', re.compile('^World triggered "'+TOKEN['trigger']+'" reason "'+TOKEN['reason']+'"$', re.U)],
    ['update', re.compile('^Your server will be restarted on map change\\.$', re.U)],
    ['valid', re.compile('^"'+TOKEN['player']+'" STEAM USERID validated$', re.U)],
]

REVALUE = [
    ['player', re.compile('^'+TOKEN['player']+'$', re.U)],
    ['position', re.compile('^'+TOKEN['position']+'$', re.U)],
]

class SourceLogParser(object):
    def __init__(self):
        self.rules = False

    def parse_value(self, key, value):
        for k, v in REVALUE:
            match = v.match(value)

            if match:
                r = match.groupdict()
                r['type'] = k
                return r

        return value

    def action(self, remote, timestamp, key, value, properties):
        pass

    def parse(self, line):
        line = line.strip('\x00\xff\r\n\t ')

        # parse header (type and date)
        match = REHEADER.match(line)

        if not match:
            # invalid log entry
            return

        line = match.group('rest')

        remote = False
        if match.group('type') == 'RL':
            remote = True

        timestamp = map(int, match.group('year', 'month', 'day', 'hour', 'minute', 'second'))

        # parse properties (key "value"), optional
        properties = {}

        while 1:
            match = REPROPERTY.match(line)

            if not match:
                break

            line = match.group('rest')
            key = match.group('property_key')
            value = match.group('property_value')
            value = self.parse_value(key, value)
            properties[key] = value

        # TF2 Bug - should be a property, but ") is missing
        match = REPROPERTYBUG.match(line)

        if match:
            line = match.group('rest')
            key = match.group('property_key')
            value = match.group('property_value')
            value = self.parse_value(key, value)
            properties[key] = value

        # parse the log entry
        for k, v in RELOG:
            match = v.match(line)

            if match:
                self.action(remote, timestamp, k, match.groupdict(), properties)
                return

        # special case: cvarlist / gamerules
        if line == 'server cvars start':
            self.rules = {}
            return

        if self.rules is not False:
            if line == 'server cvars end':
                rules = self.rules
                self.rules = False
                self.action(remote, timestamp, 'rules', rules, properties)
                return

            match = RERULES.match(line)

            if match:
                key = match.group('key')
                value = match.group('value')
                self.rules[key] = value
                return

        # not sure what else to do here, could be plugin output
        self.action(remote, timestamp, 'unknown', line, properties)

    def parse_file(self, filename):
        f = open(filename, 'r')

        for line in f:
            self.parse(line)

class SourceLogListenerError(Exception):
    pass

class SourceLogListener(asyncore.dispatcher):
    def __init__(self, local, remote, parser):
        asyncore.dispatcher.__init__(self)
        self.parser = parser
        self.create_socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.bind(local)
        self.connect(remote)

    def handle_connect(self):
        pass

    def handle_close(self):
        self.close()

    def handle_read(self):
        data = self.recv(PACKETSIZE)

        if data.startswith('\xff\xff\xff\xff') and data.endswith('\n\x00'):
            self.parser.parse(data)

        else:
            raise SourceLogListenerError("Received invalid packet.")

    def writable(self):
        return False

    def handle_write(self):
        pass
