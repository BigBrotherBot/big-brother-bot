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

__version__ = '1.5'
__author__  = 'Courgette'


import b3
import b3.cron
import b3.plugin
import b3.timezones
import threading


class SchedulerPlugin(b3.plugin.Plugin):

    _tasks = None
    _tzOffset = 0
    _restart_tasks = set()

    ####################################################################################################################
    #                                                                                                                  #
    #    STARTUP                                                                                                       #
    #                                                                                                                  #
    ####################################################################################################################

    def onLoadConfig(self):
        """
        Load plugin configuration.
        """
        # remove eventual existing tasks
        if self._tasks:
            for t in self._tasks:
                t.cancel()
    
        # get time_zone from main B3 config
        tzName = self.console.config.get('b3', 'time_zone').upper()
        self._tzOffset = b3.timezones.timezones[tzName]
    
        # load cron tasks from config
        self._tasks = []

        for taskconfig in self.config.get('restart'):
            try:
                task = RestartTask(self, taskconfig)
                self._tasks.append(task)
                self.info("restart task [%s] loaded", task.name)
            except Exception, e:
                self.error("could not load task from configuration file: %s", e)

        for taskconfig in self.config.get('cron'):
            try:
                task = CronTask(self, taskconfig)
                self._tasks.append(task)
                self.info("cron task [%s] loaded", task.name)
            except Exception, e:
                self.error("could not load task from configuration file: %s", e)

        for taskconfig in self.config.get('hourly'):
            try:
                task = HourlyTask(self, taskconfig)
                self._tasks.append(task)
                self.info("hourly task [%s] loaded", task.name)
            except Exception, e:
                self.error("could not load task from configuration file: %s", e)

        for taskconfig in self.config.get('daily'):
            try:
                task = DaylyTask(self, taskconfig)
                self._tasks.append(task)
                self.info("daily task [%s] loaded", task.name)
            except Exception, e:
                self.error("could not load task from configuration file: %s", e)

        self.debug("%d tasks scheduled", len(self._tasks))

    def onStartup(self):
        """
        Startup the plugin.
        """
        for task in self._restart_tasks:
            try:
                task.runcommands()
            except Exception, e:
                self.error("could not run task %s : %s", task.name, e)

    ####################################################################################################################
    #                                                                                                                  #
    #    OTHER METHODS                                                                                                 #
    #                                                                                                                  #
    ####################################################################################################################

    def _convertCronHourToUTC(self, hourcron):
        """
        Works with "*", "*/4", "5" or 9
        """
        if hourcron.strip() == '*': 
            return hourcron
        if '/' in hourcron:
            h,divider = hourcron.split('/')
            if h.strip() == '*':
                return hourcron
            UTChour = (int(h.strip()) - self._tzOffset) % 24
            return "%d/%s" % (UTChour, divider)
        else:
            UTChour = (int(hourcron.strip()) - self._tzOffset) % 24
            tz = str(self._tzOffset)
            if not tz.startswith('-'):
                tz = '+' + tz
            self.debug("%s (UTC%s) -> %s UTC", hourcron, tz, UTChour)
            return UTChour
 
 
class TaskConfigError(Exception):
    pass


class Task(object):

    config = None
    plugin = None
    name = None
    
    def __init__(self, plugin, config):
        """
        Initialize a new Task.
        :param plugin: the scheduler plugin
        :param config: the scheduler plugin configuration file
        """
        self.plugin = plugin
        self.config = config
        
        self.name = config.attrib['name']
        if not 'name' in config.attrib:
            self.plugin.info("attribute 'name' not found in task")
        else:
            self.name = config.attrib['name']

        self.plugin.debug("setting up %s [%s]", self.__class__.__name__, self.name)

        num_commands_found = 0
        num_commands_found += self._init_rcon_commands()
        num_commands_found += self._init_enable_plugin_commands()
        num_commands_found += self._init_disable_plugin_commands()
        if num_commands_found == 0:
            raise TaskConfigError('no action found for task %s' % self.name)

    def _init_rcon_commands(self):
        if self.plugin.console.isFrostbiteGame():
            frostbitecommands = self.config.findall("frostbite") + self.config.findall("bfbc2")
            for cmd in frostbitecommands:
                if not 'command' in cmd.attrib:
                    raise TaskConfigError('cannot find \'command\' attribute for a frostbite element')
                text = cmd.attrib['command']
                for arg in cmd.findall('arg'):
                    text += " %s" % arg.text
                self.plugin.debug("frostbite : %s", text)
                return len(frostbitecommands)
        else:
            ## classical Q3 rcon command
            rconcommands = self.config.findall("rcon")
            for cmd in rconcommands:
                self.plugin.debug("rcon : %s", cmd.text)
            return len(rconcommands)

    def _init_enable_plugin_commands(self):
        commands = self.config.findall("enable_plugin")
        for cmd in commands:
            if not 'plugin' in cmd.attrib:
                raise TaskConfigError('cannot find \'plugin\' attribute for a enable_plugin element')
            if not self.plugin.console.getPlugin(cmd.attrib['plugin']):
                raise TaskConfigError('cannot find plugin %s' % cmd.attrib['plugin'])
            self.plugin.debug("enable_plugin : %s", cmd.attrib['plugin'])
        return len(commands)

    def _init_disable_plugin_commands(self):
        commands = self.config.findall("disable_plugin")
        for cmd in commands:
            if not 'plugin' in cmd.attrib:
                raise TaskConfigError('cannot find \'plugin\' attribute for a disable_plugin element')
            if not self.plugin.console.getPlugin(cmd.attrib['plugin']):
                raise TaskConfigError('cannot find plugin %s' % cmd.attrib['plugin'])
            self.plugin.debug("disable_plugin : %s", cmd.attrib['plugin'])
        return len(commands)

    def runcommands(self):
        self.plugin.info("running scheduled commands from %s", self.name)
        self._run_rcon_commands()
        self._run_enable_plugin_commands()
        self._run_disable_plugin_commands()

    def _run_rcon_commands(self):
        if self.plugin.console.isFrostbiteGame():
            # send frostbite commands
            nodes = self.config.findall("frostbite") + self.config.findall("bfbc2")
            for frostbitenode in nodes:
                try:
                    commandName = frostbitenode.attrib['command']
                    cmdlist = [commandName]
                    for arg in frostbitenode.findall('arg'):
                        cmdlist.append(arg.text)
                    result = self.plugin.console.write(tuple(cmdlist))
                    self.plugin.info("frostbite command result : %s", result)
                except Exception, e:
                    self.plugin.error("task %s : %s", self.name, e)
        else:
            # send rcon commands
            for cmd in self.config.findall("rcon"):
                try:
                    result = self.plugin.console.write("%s" % cmd.text)
                    self.plugin.info("rcon command result : %s",  result)
                except Exception, e:
                    self.plugin.error("task %s : %s", self.name, e)

    def _run_enable_plugin_commands(self):
        for cmd in self.config.findall("enable_plugin"):
            try:
                pluginName = cmd.attrib['plugin'].strip().lower()
                plugin = self.plugin.console.getPlugin(pluginName)
                if plugin:
                    if plugin.isEnabled():
                        self.plugin.info('plugin %s is already enabled', pluginName)
                    else:
                        plugin.enable()
                        self.plugin.info('plugin %s is now ON', pluginName)
                else:
                    self.plugin.warn('no plugin named %s loaded', pluginName)
            except Exception, e:
                self.plugin.error("task %s : %s" % (self.name, e))

    def _run_disable_plugin_commands(self):
        for cmd in self.config.findall("disable_plugin"):
            try:
                pluginName = cmd.attrib['plugin'].strip().lower()
                plugin = self.plugin.console.getPlugin(pluginName)
                if plugin:
                    if not plugin.isEnabled():
                        self.plugin.info('plugin %s is already disabled', pluginName)
                    else:
                        plugin.disable()
                        self.plugin.info('plugin %s is now OFF', pluginName)
                else:
                    self.plugin.warn('no plugin named %s loaded', pluginName)
            except Exception, e:
                self.plugin.error("task %s : %s", self.name, e)


class RestartTask(Task):

    def __init__(self, plugin, config):
        Task.__init__(self, plugin, config)
        self.schedule()

    def schedule(self):
        """
        schedule this task
        """
        self.plugin._restart_tasks.add(self)

    def cancel(self):
        """
        remove this task from schedule
        """
        self.plugin._restart_tasks.remove(self)

    def runcommands(self):
        if 'delay' in self.config.attrib:
            delay_minutes = b3.functions.time2minutes(self.config.attrib['delay'])
            threading.Timer(delay_minutes * 60, Task.runcommands, [self]).start()
        else:
            Task.runcommands(self)


class CronTask(Task):

    cronTab = None
    seconds = None
    minutes = None
    hour = None
    day = None
    month = None
    dow = None

    def __init__(self, plugin, config):
        Task.__init__(self, plugin, config)
        self.schedule()
        
    def schedule(self):
        """
        schedule this task
        """
        self._getScheduledTime(self.config.attrib)
        self.cronTab = b3.cron.PluginCronTab(self.plugin, self.runcommands, 
            self.seconds, self.minutes, self.plugin._convertCronHourToUTC(self.hour), self.day, self.month, self.dow)
        self.plugin.console.cron + self.cronTab
        
    def cancel(self):
        """
        remove this task from schedule
        """
        if self.cronTab:
            self.plugin.info("canceling scheduled task [%s]", self.name)
            self.plugin.console.cron - self.cronTab

    def _getScheduledTime(self, attrib):

        if not 'seconds' in attrib:
            self.seconds = 0
        else:
            self.seconds = attrib['seconds']
                    
        if not 'minutes' in attrib:
            self.minutes = '*'
        else:
            self.minutes = attrib['minutes']        
            
        if not 'hour' in attrib:
            self.hour = '*'
        else:
            self.hour = attrib['hour']
            
        if not 'day' in attrib:
            self.day = '*'
        else:
            self.day = attrib['day']
                        
        if not 'month' in attrib:
            self.month = '*'
        else:
            self.month = attrib['month']
            
        if not 'dow' in attrib:
            self.dow = '*'
        else:
            self.dow = attrib['dow']
        
        self.plugin.info('%s %s %s\t%s %s %s', self.seconds, self.minutes, self.hour, self.day, self.month, self.dow)
 
class HourlyTask(CronTask):

    def _getScheduledTime(self, attrib):
        self.seconds = 0

        if not 'minutes' in attrib:
            self.plugin.debug("default minutes : 0. Provide a 'minutes' attribute to override")
            self.minutes = 0
        else:
            self.minutes = attrib['minutes']        
            
        self.hour = '*'
        self.day = '*'
        self.month = '*'
        self.dow = '*'
        
class DaylyTask(CronTask):

    def _getScheduledTime(self, attrib):
        self.seconds = 0

        if not 'hour' in attrib:
            self.plugin.debug("default hour : 0. Provide a 'hour' attribute to override")
            self.hour = 0
        else:
            self.hour = attrib['hour']     
            
        if not 'minutes' in attrib:
            self.plugin.debug("default minutes : 0. Provide a 'minutes' attribute to override")
            self.minutes = 0
        else:
            self.minutes = attrib['minutes']        
            
        self.day = '*'
        self.month = '*'
        self.dow = '*'