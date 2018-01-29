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

import b3
import os
import logging

from b3.cron import PluginCronTab
from b3.plugin import Plugin
from b3.config import ConfigParser
from b3.timezones import timezones
from logging.handlers import TimedRotatingFileHandler

__version__ = '1.5'
__author__ = 'Courgette, xlr8or, BlackMamba, OliverWieland'


class ChatloggerPlugin(Plugin):

    _cronTab = None
    _max_age_in_days = None
    _max_age_cmd_in_days = None
    _hours = None
    _minutes = None
    _db_table = 'chatlog'
    _db_table_cmdlog = 'cmdlog'
    _file_name = None
    _filelogger = None
    _save2db = None
    _save2file = None
    _file_rotation_rate = None

    ####################################################################################################################
    #                                                                                                                  #
    #    STARTUP                                                                                                       #
    #                                                                                                                  #
    ####################################################################################################################

    def onLoadConfig(self):
        """
        Load plugin configuration
        """
        # remove eventual existing crontab
        if self._cronTab:
            self.console.cron - self._cronTab

        try:
            self._save2db = self.config.getboolean('general', 'save_to_database')
            self.debug('save chat to database : %s', 'enabled' if self._save2db else 'disabled')
        except ConfigParser.NoOptionError:
            self._save2db = True
            self.info("using default value '%s' for save_to_database", self._save2db)
        except ValueError, e:
            self._save2db = True
            self.warning('unexpected value for save_to_database: using default value (%s) instead (%s)', self._save2db, e)

        try:
            self._save2file = self.config.getboolean('general', 'save_to_file')
            self.debug('save chat to file : %s', 'enabled' if self._save2file else 'disabled')
        except ConfigParser.NoOptionError:
            self._save2file = False
            self.info("using default value '%s' for save_to_file", self._save2file)
        except ValueError, e:
            self._save2file = False
            self.warning('unexpected value for save_to_file: using default value (%s) instead (%s)', self._save2file, e)

        if not (self._save2db or self._save2file):
            self.warning("your config explicitly specify to log nowhere: disabling plugin")
            self.disable()

        if self._save2db:
            self.loadConfig_database()
        if self._save2file:
            self.loadConfig_file()

    def loadConfig_file(self):
        """
        Load configuration values for file logging
        """
        try:
            self._file_name = self.config.getpath('file', 'logfile')
            self.info('using file (%s) to store log', self._file_name)
        except Exception, e:
            self.error('error while reading logfile name: disabling logging to file (%s)' % e)
            self._save2file = False
        else:

            try:
                self._file_rotation_rate = self.config.get('file', 'rotation_rate')
                if self._file_rotation_rate.upper() not in ('H', 'D', 'W0', 'W1', 'W2', 'W3', 'W4', 'W5', 'W6'):
                    raise ValueError('invalid rate specified: %s' % self._file_rotation_rate)
                self.info("using value '%s' for the file rotation rate", self._file_rotation_rate)
            except ConfigParser.NoOptionError:
                self._file_rotation_rate = 'D'
                self.info("using default value '%s' for the file rotation rate", self._file_rotation_rate)
            except ValueError, e:
                self._file_rotation_rate = 'D'
                self.warning("unexpected value for file rotation rate: "
                             "falling back on default value: '%s' (%s)", self._file_rotation_rate, e)

            self.setup_fileLogger()

    def setup_fileLogger(self):
        """
        Setup the file logger
        """
        try:
            self._filelogger = logging.getLogger('chatlogfile')
            handler = TimedRotatingFileHandler(self._file_name, when=self._file_rotation_rate, encoding="UTF-8")
            handler.setFormatter(logging.Formatter('%(asctime)s\t%(message)s', '%y-%m-%d %H:%M:%S'))
            self._filelogger.addHandler(handler)
            self._filelogger.setLevel(logging.INFO)
        except Exception, e:
            self._save2file = False
            self.error("cannot setup file chat logger: disabling logging to file (%s)" % e, exc_info=e)

    def loadConfig_database(self):
        """
        Load configuration values for database logging
        """
        try:
            max_age = self.config.get('purge', 'max_age')
        except:
            max_age = "0d"
            self.debug('using default value (%s) for max_age', max_age)

        days = self.string2days(max_age)
        self.debug('max age : %s => %s days' % (max_age, days))

        # force max age to be at least one day
        if days != 0 and days < 1:
            self._max_age_in_days = 1
        else:
            self._max_age_in_days = days

        try:
            max_age_cmd = self.config.get('purge', 'max_age_cmd')
        except:
            max_age_cmd = "0d"
            self.debug('using default value (%s) for max_age_cmd', max_age_cmd)

        days_cmd = self.string2days(max_age_cmd)
        self.debug('max age cmd : %s => %s days' % (max_age_cmd, days_cmd))

        # force max age to be at least one day
        if days_cmd != 0 and days_cmd < 1:
            self._max_age_cmd_in_days = 1
        else:
            self._max_age_cmd_in_days = days_cmd

        try:
            self._hours = self.config.getint('purge', 'hour')
            if self._hours < 0:
                self._hours = 0
            elif self._hours > 23:
                self._hours = 23
        except:
            self._hours = 0
            self.debug('using default value (%s) for hours', self._hours)

        try:
            self._minutes = self.config.getint('purge', 'min')
            if self._minutes < 0:
                self._minutes = 0
            elif self._minutes > 59:
                self._minutes = 59
        except:
            self._minutes = 0
            self.debug('using default value (%s) for minutes', self._minutes)

        if self._max_age_in_days != 0 or self._max_age_cmd_in_days != 0:
            # get time_zone from main B3 config
            tzName = self.console.config.get('b3', 'time_zone').upper()
            tzOffest = timezones[tzName]
            hoursGMT = (self._hours - tzOffest) % 24
            self.debug("%02d:%02d %s => %02d:%02d UTC" % (self._hours, self._minutes, tzName, hoursGMT, self._minutes))
            self.info('everyday at %2d:%2d %s, chat messages older than %s days will be deleted' % (
                self._hours, self._minutes, tzName, self._max_age_in_days))
            self.info('everyday at %2d:%2d %s, chat commands older than %s days will be deleted' % (
                self._hours, self._minutes, tzName, self._max_age_cmd_in_days))
            self._cronTab = PluginCronTab(self, self.purge, 0, self._minutes, hoursGMT, '*', '*', '*')
            self.console.cron + self._cronTab
        else:
            self.info("chat log messages are kept forever")

    def onStartup(self):
        """
        Startup the plugin
        """
        # create database tables (if needed)
        current_tables = self.console.storage.getTables()
        if 'chatlog' not in current_tables or 'cmdlog' not in current_tables:
            sql_path_main = b3.getAbsolutePath('@b3/plugins/chatlogger/sql')
            sql_path = os.path.join(sql_path_main, self.console.storage.dsnDict['protocol'], 'chatlogger.sql')
            self.console.storage.queryFromFile(sql_path)

        # listen for client events
        self.registerEvent('EVT_CLIENT_SAY', self.onSay)
        self.registerEvent('EVT_CLIENT_TEAM_SAY', self.onTeamSay)
        self.registerEvent('EVT_CLIENT_PRIVATE_SAY', self.onPrivateSay)
        self.registerEvent('EVT_ADMIN_COMMAND', self.onAdminCommand)

        if self.console.getEventID('EVT_CLIENT_SQUAD_SAY'):
            self.registerEvent('EVT_CLIENT_SQUAD_SAY', self.onSquadSay)

        if self.console.getEventID('EVT_CLIENT_RADIO'):
            self.registerEvent('EVT_CLIENT_RADIO', self.onRadio)

    ####################################################################################################################
    #                                                                                                                  #
    #    HANDLE EVENTS                                                                                                 #
    #                                                                                                                  #
    ####################################################################################################################

    def onSay(self, event):
        """
        Handle EVT_CLIENT_SAY
        """
        if event.client and event.data:
            chat = ChatData(self, event)
            chat._table = self._db_table
            chat.save()

    def onTeamSay(self, event):
        """
        Handle EVT_CLIENT_TEAM_SAY
        """
        if event.client and event.data:
            chat = TeamChatData(self, event)
            chat._table = self._db_table
            chat.save()

    def onPrivateSay(self, event):
        """
        Handle EVT_CLIENT_PRIVATE_SAY
        """
        if event.client and event.data:
            chat = PrivateChatData(self, event)
            chat._table = self._db_table
            chat.save()

    def onSquadSay(self, event):
        """
        Handle EVT_CLIENT_SQUAD_SAY
        """
        if event.client and event.data:
            chat = SquadChatData(self, event)
            chat._table = self._db_table
            chat.save()

    def onAdminCommand(self, event):
        """
        Handle EVT_ADMIN_COMMAND
        """
        if event.client and event.data:
            cmd = CmdData(self, event)
            cmd._table = self._db_table_cmdlog
            cmd.save()

    def onRadio(self, event):
        """
        Handle EVT_CLIENT_RADIO
        """
        if event.client and event.data:
            data = ClientRadioData(self, event)
            data._table = self._db_table
            data.save()

    ####################################################################################################################
    #                                                                                                                  #
    #    OTHER METHODS                                                                                                 #
    #                                                                                                                  #
    ####################################################################################################################

    def purge(self):
        """
        Clear log data from database
        """
        if self._max_age_in_days and (self._max_age_in_days != 0):
            self.info('purge of chat messages older than %s days ...' % self._max_age_in_days)
            q = "DELETE FROM %s WHERE msg_time < %i" % (self._db_table,
                                                        self.console.time() - (self._max_age_in_days * 24 * 60 * 60))
            self.debug(q)
            self.console.storage.query(q)
        else:
            self.warning('max_age is invalid [%s]' % self._max_age_in_days)

        if self._max_age_cmd_in_days and (self._max_age_cmd_in_days != 0):
            self.info('purge of commands older than %s days ...' % self._max_age_cmd_in_days)
            q = "DELETE FROM %s WHERE cmd_time < %i" % (self._db_table_cmdlog,
                                                        self.console.time() - (self._max_age_cmd_in_days * 24 * 60 * 60))
            self.debug(q)
            self.console.storage.query(q)
        else:
            self.warning('max_age_cmd is invalid [%s]' % self._max_age_cmd_in_days)

    def string2days(self, text):
        """
        Convert max age string to days. (max age can be written as : 2d for 'two days', etc)
        """
        try:
            if text[-1:].lower() == 'd':
                days = int(text[:-1])
            elif text[-1:].lower() == 'w':
                days = int(text[:-1]) * 7
            elif text[-1:].lower() == 'm':
                days = int(text[:-1]) * 30
            elif text[-1:].lower() == 'y':
                days = int(text[:-1]) * 365
            else:
                days = int(text)
        except ValueError, e:
            self.error("could not convert '%s' to a valid number of days: %s" % (text, e))
            days = 0
        return days


class AbstractData(object):

    def __init__(self, plugin):
        # default name of the table for this data object
        self._table = None
        self.plugin = plugin

    def _insertquery(self):
        raise NotImplementedError

    def save(self):
        """Should call self._save2db with correct parameters"""
        raise NotImplementedError

    def _save2db(self, data):
        q = self._insertquery()
        try:
            cursor = self.plugin.console.storage.query(q, data)
            if cursor.rowcount > 0:
                self.plugin.debug("rowcount: %s, id:%s" % (cursor.rowcount, cursor.lastrowid))
            else:
                self.plugin.warning("inserting into %s failed" % self._table)
        except Exception, e:
            if e[0] == 1146:
                self.plugin.error("could not save to database : %s" % e[1])
                self.plugin.info("refer to this plugin readme file for instruction on how to create the required tables")
            else:
                raise e


class CmdData(AbstractData):

    def __init__(self, plugin, event):
        AbstractData.__init__(self, plugin)
        # default name of the table for this data object
        self._table = 'cmdlog'

        self.admin_id = event.client.id
        self.admin_name = event.client.name

        self.command = event.data[0]
        self.data = event.data[1]
        self.result = event.data[2]
        self.event = event

    def _insertquery(self):
        return """INSERT INTO {table_name} (cmd_time, admin_id, admin_name, command, data, result)
                  VALUES (%(time)s, %(admin_id)s, %(admin_name)s, %(command)s, %(data)s, %(result)s) """.format(
                  table_name=self._table)

    def save(self):
        self.plugin.verbose("%s, %s, %s, %s, %s" % (self.admin_id, self.admin_name, self.command, self.data, self.result))
        data = {'time': self.plugin.console.time(),
                'admin_id': self.admin_id,
                'admin_name': self.admin_name,
                'command': self.command.command,
                'data': self.data,
                'result': self.result}

        if self.plugin._save2db:
            self._save2db(data)


class ChatData(AbstractData):

    #fields of the table
    msg_type = 'ALL' # ALL, TEAM or PM
    client_id = None
    client_name = None
    client_team = None
    msg = None

    def __init__(self, plugin, event):
        AbstractData.__init__(self, plugin)
        # default name of the table for this data object
        self._table = 'chatlog'
        self.client_id = event.client.id
        self.client_name = event.client.name
        self.client_team = event.client.team
        self.msg = event.data
        self.target_id = None
        self.target_name = None
        self.target_team = None

    def _insertquery(self):
        return """INSERT INTO {table_name}
                  (msg_time, msg_type, client_id, client_name, client_team, msg, target_id, target_name, target_team)
                  VALUES (%(time)s, %(type)s, %(client_id)s, %(client_name)s, %(client_team)s, %(msg)s, %(target_id)s,
                  %(target_name)s, %(target_team)s )""".format(table_name=self._table)

    def save(self):
        self.plugin.verbose("%s, %s, %s, %s" % (self.msg_type, self.client_id, self.client_name, self.msg))
        data = {'time': self.plugin.console.time(),
                'type': self.msg_type,
                'client_id': self.client_id,
                'client_name': self.client_name,
                'client_team': self.client_team,
                'msg': self.msg,
                'target_id': self.target_id,
                'target_name': self.target_name,
                'target_team': self.target_team}

        if self.plugin._save2file:
            self._save2file(data)
        if self.plugin._save2db:
            self._save2db(data)

    def _save2file(self, data):
        self.plugin._filelogger.info("@%(client_id)s [%(client_name)s] to %(type)s:\t%(msg)s" % data)


class TeamChatData(ChatData):

    msg_type = 'TEAM'


class SquadChatData(ChatData):

    msg_type = 'SQUAD'


class PrivateChatData(ChatData):

    msg_type = 'PM'

    def __init__(self, plugin, event):
        ChatData.__init__(self, plugin, event)
        self.target_id = event.target.id
        self.target_name = event.target.name
        self.target_team = event.target.team


class ClientRadioData(TeamChatData):

    def __init__(self, plugin, event):
        TeamChatData.__init__(self, plugin, event)
        self.msg = 'RADIO %s %s (%s) %s' % (
            event.data['msg_group'], event.data['msg_id'], event.data['location'], event.data['text'])
