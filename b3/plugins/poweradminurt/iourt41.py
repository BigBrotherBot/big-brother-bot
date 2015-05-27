# PowerAdmin Plugin for BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2008 Mark Weirath (xlr8or@xlr8or.com)
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

import b3
import b3.events
import b3.plugin
import b3.cron
import time
import thread
import threading
import re
import os
import random
import string
import ConfigParser

from b3.plugins.poweradminurt import __version__
from b3.plugins.poweradminurt import __author__


class Poweradminurt41Plugin(b3.plugin.Plugin):

    # ClientUserInfo and ClientUserInfoChanged lines return different names, unsanitized and sanitized
    # this regexp designed to make sure either one is sanitized before namecomparison in onNameChange()
    _reClean = re.compile(r'(\^.)|[\x00-\x20]|[\x7E-\xff]', re.I)

    _adminPlugin = None
    _ignoreTill = 0
    _checkdupes = True
    _checkunknown = True
    _checkbadnames = True
    _checkchanges = True
    _checkallowedchanges = 7
    _ncronTab = None
    _tcronTab = None
    _scronTab = None
    _skcronTab = None
    _ninterval = 0
    _tinterval = 0
    _sinterval = 0
    _skinterval = 0
    _minbalinterval = 2  # minimum time in minutes between !bal or !sk for non-mods
    _lastbal = 0  # time since last !bal or !sk
    _oldadv = (None, None, None)
    _teamred = 0
    _teamblue = 0
    _teamdiff = 1
    _skilldiff = 0.5
    _skill_balance_mode = 0
    _balancing = False
    _origvote = 0
    _lastvote = 0
    _votedelay = 0
    _tmaxlevel = 20
    _announce = 2
    _smaxspectime = 0
    _smaxlevel = 0
    _smaxplayers = 0
    _sv_maxclients = 0
    _g_maxGameClients = 0
    _teamsbalanced = False
    _matchmode = False
    _botenable = False
    _botskill = 4
    _botminplayers = 4
    _botmaps = []
    _hsenable = False
    _hsresetvars = 'map'
    _hsbroadcast = True
    _hsall = True
    _hspercent = True
    _hspercentmin = 20
    _hswarnhelmet = True
    _hswarnhelmetnr = 7
    _hswarnkevlar = True
    _hswarnkevlarnr = 50
    _rmenable = False
    _dontcount = 0
    _mapchanged = False
    _playercount = -1
    _oldplayercount = None
    _currentrotation = 0
    _switchcount1 = 12
    _switchcount2 = 24
    _hysteresis = 0
    _rotation_small = ''
    _rotation_medium = ''
    _rotation_large = ''
    _gamepath = ''
    _origgear = 0
    _randnum = 0
    _pass_lines = None
    _papublic_password = None
    _match_plugin_disable = []
    _gameconfig = {}
    _team_change_force_balance_enable = True
    _teamLocksPermanent = False
    _autobalance_gametypes = 'tdm'
    _autobalance_gametypes_array = []
    _max_dic_size = 512000  # max dictionary size in bytes
    _moon_on_gravity = 100
    _moon_off_gravity = 800
    _slapSafeLevel = 60
    _ignorePlus = 30
    _full_ident_level = 60
    _killhistory = []
    _hitlocations = {}

    requiresParsers = ['iourt41']

    def onStartup(self):
        """
        Initialize plugin settings
        """
        # get the admin plugin so we can register commands
        self._adminPlugin = self.console.getPlugin('admin')

        # get some constants from the B3 parser
        
        try:
            self._hitlocations['HL_HEAD'] = self.console.HL_HEAD
        except AttributeError, e:
            self._hitlocations['HL_HEAD'] = '0'
            self.warning("could not get HL_HEAD value from B3 parser: %s" % e)

        self.debug("HL_HEAD is %s" % self._hitlocations['HL_HEAD'])

        try:
            self._hitlocations['HL_HELMET'] = self.console.HL_HELMET
        except AttributeError, e:
            self._hitlocations['HL_HELMET'] = '1'
            self.warning("could not get HL_HELMET value from B3 parser: %s" % e)

        self.debug("HL_HELMET is %s" % self._hitlocations['HL_HELMET'])

        try:
            self._hitlocations['HL_TORSO'] = self.console.HL_TORSO
        except AttributeError, e:
            self._hitlocations['HL_TORSO'] = '2'
            self.warning("could not get HL_TORSO value from B3 parser: %s" % e)

        self.debug("HL_TORSO is %s" % self._hitlocations['HL_TORSO'])

        # register our commands
        if 'commands' in self.config.sections():
            for cmd in self.config.options('commands'):
                level = self.config.get('commands', cmd)
                sp = cmd.split('-')
                alias = None
                if len(sp) == 2:
                    cmd, alias = sp

                func = self.getCmd(cmd)
                if func:
                    self._adminPlugin.registerCommand(self, cmd, level, func, alias)

        self._adminPlugin.registerCommand(self, 'paversion', 0, self.cmd_paversion, 'paver')

        # register our events
        self.registerEvents()

        # create event
        self.createEvent('EVT_CLIENT_PUBLIC', 'Server Public Mode Changed')

        # don't run cron-checks on startup
        self.ignoreSet(self._ignorePlus)
        self._balancing = False
        self._killhistory = []

        try:
            # save original vote settings
            self._origvote = self.console.getCvar('g_allowvote').getInt()
        except ValueError, e:
            self.warning("could not retrieve g_allowvote CVAR value: %s" % e)
            self._origvote = 0  # no votes

        # if by any chance on botstart g_allowvote is 0
        # we'll use the default UrT value
        if self._origvote == 0:
            self._origvote = 536871039

        self._lastvote = self._origvote

        # how many players are allowed and if g_maxGameClients != 0 we will disable specchecking
        self._sv_maxclients = self.console.getCvar('sv_maxclients').getInt()
        self._g_maxGameClients = self.console.getCvar('g_maxGameClients').getInt()

        try:
            # save original gear settings
            self._origgear = self.console.getCvar('g_gear').getInt()
        except ValueError, e:
            if self.console.gameName == 'iourt41':
                # if the game is iourt42 don't log since the above cvar retrieval
                # is going to raise an exception everytime: iourt42 uses a gear
                # string instead of gear bitmask so int casting will raise a ValueError
                self.warning("could not retrieve g_gear CVAR value: %s" % e)
                self._origgear = 0  # allow all weapons

        self.installCrontabs()

        self.debug('Started')

    def registerEvents(self):
        """
        Register events needed
        """
        self.verbose('Registering events')
        self.registerEvent('EVT_GAME_ROUND_START')
        self.registerEvent('EVT_GAME_EXIT')
        self.registerEvent('EVT_CLIENT_AUTH')
        self.registerEvent('EVT_CLIENT_DISCONNECT')
        self.registerEvent('EVT_CLIENT_TEAM_CHANGE')
        self.registerEvent('EVT_CLIENT_DAMAGE')
        self.registerEvent('EVT_CLIENT_NAME_CHANGE')
        self.registerEvent('EVT_CLIENT_KILL')
        self.registerEvent('EVT_CLIENT_KILL_TEAM')
        self.registerEvent('EVT_CLIENT_ACTION')
        self.registerEvent('EVT_GAME_MAP_CHANGE')

    def onLoadConfig(self):
        """
        Load the plugin configuration
        """
        self.loadNameChecker()
        self.loadTeamBalancer()
        self.loadVoteDelayer()
        self.loadSpecChecker()
        self.loadSkillBalancer()
        self.loadMoonMode()
        self.loadPublicMode()
        self.loadMatchMode()
        self.loadBotSupport()
        self.loadHeadshotCounter()
        self.loadRotationManager()
        self.loadSpecial()

    def loadNameChecker(self):
        """
        Setup the name checker
        """
        try:
            self._ninterval = self.config.getint('namechecker', 'ninterval')
        except ConfigParser.NoOptionError:
            self.warning('Could not find namechecker/ninterval in config file, using default: %s' % self._ninterval)
        except ValueError, e:
            self.error('Could not load namechecker/ninterval config value: %s' % e)
            self.debug('Using default value (%s) for namechecker/ninterval' % self._ninterval)

        # clamp name checker interval
        if self._ninterval > 59:
            self._ninterval = 59

        try:
            self._checkdupes = self.config.getboolean('namechecker', 'checkdupes')
        except ConfigParser.NoOptionError:
            self.warning('Could not find namechecker/checkdupes in config file, using default: %s' % self._checkdupes)
        except ValueError, e:
            self.error('Could not load namechecker/checkdupes config value: %s' % e)
            self.debug('Using default value (%s) for namechecker/checkdupes' % self._checkdupes)

        try:
            self._checkunknown = self.config.getboolean('namechecker', 'checkunknown')
        except ConfigParser.NoOptionError:
            self.warning('Could not find namechecker/checkunknown in config file, using default: %s' %
                         self._checkunknown)
        except ValueError, e:
            self.error('Could not load namechecker/checkunknown config value: %s' % e)
            self.debug('Using default value (%s) for namechecker/checkunknown' % self._checkunknown)

        try:
            self._checkbadnames = self.config.getboolean('namechecker', 'checkbadnames')
        except ConfigParser.NoOptionError:
            self.warning('Could not find namechecker/checkbadnames in config file, using default: %s' %
                         self._checkbadnames)
        except ValueError, e:
            self.error('Could not load namechecker/checkbadnames config value: %s' % e)
            self.debug('Using default value (%s) for namechecker/checkbadnames' % self._checkbadnames)

        try:
            self._checkchanges = self.config.getboolean('namechecker', 'checkchanges')
        except ConfigParser.NoOptionError:
            self.warning('Could not find namechecker/checkchanges in config file, using default: %s' %
                         self._checkchanges)
        except ValueError, e:
            self.error('Could not load namechecker/checkchanges config value: %s' % e)
            self.debug('Using default value (%s) for namechecker/checkchanges' % self._checkchanges)

        try:
            self._checkallowedchanges = self.config.getint('namechecker', 'checkallowedchanges')
        except ConfigParser.NoOptionError:
            self.warning('Could not find namechecker/checkallowedchanges in config file, using default: %s' %
                         self._checkallowedchanges)
        except ValueError, e:
            self.error('Could not load namechecker/checkallowedchanges config value: %s' % e)
            self.debug('Using default value (%s) for namechecker/checkallowedchanges' % self._checkallowedchanges)

        self.debug('Name checker interval: %s' % self._ninterval)
        self.debug('Check bad names: %s' % self._checkbadnames)
        self.debug('Check duplicate names: %s' % self._checkdupes)
        self.debug('Check unknown names: %s' % self._checkunknown)
        self.debug('Check name changes: %s' % self._checkchanges)
        self.debug('Max. allowed name changes per game: %s' % self._checkallowedchanges)

    def loadTeamBalancer(self):
        """
        Setup the teambalancer
        """
        try:
            self._tinterval = self.config.getint('teambalancer', 'tinterval')
        except ConfigParser.NoOptionError:
            self.warning('Could not find teambalancer/tinterval in config file, using default: %s' % self._tinterval)
        except ValueError, e:
            self.error('Could not load teambalancer/tinterval config value: %s' % e)
            self.debug('Using default value (%s) for teambalancer/tinterval' % self._tinterval)

        # clamp team balancer interval
        if self._tinterval > 59:
            self._tinterval = 59

        try:
            self._teamdiff = self.config.getint('teambalancer', 'teamdifference')
        except ConfigParser.NoOptionError:
            self.warning('Could not find teambalancer/teamdifference in config file, using default: %s' %
                         self._teamdiff)
        except ValueError, e:
            self.error('Could not load teambalancer/teamdifference config value: %s' % e)
            self.debug('Using default value (%s) for teambalancer/teamdifference' % self._teamdiff)

        # set a minimum/maximum teamdifference
        if self._teamdiff < 1:
            self._teamdiff = 1
        elif self._teamdiff > 9:
            self._teamdiff = 9

        try:
            self._tmaxlevel = self.config.getint('teambalancer', 'maxlevel')
        except ConfigParser.NoOptionError:
            self.warning('Could not find teambalancer/maxlevel in config file, using default: %s' % self._tmaxlevel)
        except ValueError, e:
            self.error('Could not load teambalancer/maxlevel config value: %s' % e)
            self.debug('Using default value (%s) for teambalancer/maxlevel' % self._tmaxlevel)

        try:
            self._announce = self.config.getint('teambalancer', 'announce')
        except ConfigParser.NoOptionError:
            self.warning('Could not find teambalancer/announce in config file, using default: %s' % self._announce)
        except ValueError, e:
            self.error('Could not load teambalancer/announce config value: %s' % e)
            self.debug('Using default value (%s) for teambalancer/announce' % self._announce)

        try:
            # 10/21/2008 - 1.4.0b9 - mindriot
            self._team_change_force_balance_enable = self.config.getboolean('teambalancer',
                                                                            'team_change_force_balance_enable')
        except ConfigParser.NoOptionError:
            self.warning('Could not find teambalancer/team_change_force_balance_enable in config file, \
                          using default: %s' % self._team_change_force_balance_enable)
        except ValueError, e:
            self.error('Could not load teambalancer/team_change_force_balance_enable config value: %s' % e)
            self.debug('Using default value (%s) for teambalancer/team_change_force_balance_enable' %
                       self._team_change_force_balance_enable)

        try:
            # 10/22/2008 - 1.4.0b10 - mindriot
            self._autobalance_gametypes = self.config.get('teambalancer', 'autobalance_gametypes')
        except ConfigParser.NoOptionError:
            self.warning('Could not find teambalancer/autobalance_gametypes in config file, '
                         'using default: %s' % self._autobalance_gametypes)

        self._autobalance_gametypes = self._autobalance_gametypes.lower()
        self._autobalance_gametypes_array = re.split(r'[\s,]+', self._autobalance_gametypes)

        try:
            self._teamLocksPermanent = self.config.getboolean('teambalancer', 'teamLocksPermanent')
        except ConfigParser.NoOptionError:
            self.warning('Could not find teambalancer/teamLocksPermanent in config file, '
                         'using default: %s' % self._teamLocksPermanent)
        except ValueError, e:
            self.error('Could not load teambalancer/teamLocksPermanent config value: %s' % e)
            self.debug('Using default value (%s) for teambalancer/teamLocksPermanent' % self._teamLocksPermanent)

        try:
            self._ignorePlus = self.config.getint('teambalancer', 'timedelay')
        except ConfigParser.NoOptionError:
            self.warning('Could not find teambalancer/timedelay in config file, using default: %s' % self._ignorePlus)
        except ValueError, e:
            self.warning('Could not load teambalancer/timedelay config value: %s' % e)
            self.debug('Using default value (%s) for teambalancer/timedelay' % self._ignorePlus)

        self.debug('Teambalance interval: %s' % self._tinterval)
        self.debug('Teambalance difference: %s' % self._teamdiff)
        self.debug('Teambalance max level: %s' % self._tmaxlevel)
        self.debug('Teambalance announce: %s' % self._announce)
        self.debug('Team change force balance enable: %s' % self._team_change_force_balance_enable)
        self.debug('Team locks permanent: %s' % self._teamLocksPermanent)
        self.debug('Time delay: %s' % self._ignorePlus)
        self.debug('Autobalance gametypes: %s' % self._autobalance_gametypes)

    def loadSkillBalancer(self):
        """
        Setup the skill balancer
        """
        try:
            self._skinterval = self.config.getint('skillbalancer', 'interval')
        except ConfigParser.NoOptionError:
            self.warning('Could not find skillbalancer/interval in config file, using default: %s' % self._skinterval)
        except ValueError, e:
            self.error('Could not load skillbalancer/interval config value: %s' % e)
            self.debug('Using default value (%s) for skillbalancer/interval' % self._skinterval)

        # clamp skill balancer interval
        if self._skinterval > 59:
            self._skinterval = 59

        try:
            self._skilldiff = self.config.getfloat('skillbalancer', 'difference')
        except ConfigParser.NoOptionError:
            self.warning('Could not find skillbalancer/difference in config file, using default: %s' % self._skilldiff)
        except ValueError, e:
            self.error('Could not load skillbalancer/difference config value: %s' % e)
            self.debug('Using default value (%s) for skillbalancer/difference' % self._skilldiff)

        # clamp skill difference
        if self._skilldiff < 0.1:
            self._skilldiff = 0.1
        elif self._skilldiff > 9:
            self._skilldiff = 9

        try:
            self._skill_balance_mode = self.config.getint('skillbalancer', 'mode')
        except ConfigParser.NoOptionError:
            self.warning('Could not find skillbalancer/mode in config file, using default: %s' %
                         self._skill_balance_mode)
        except ValueError, e:
            self.error('Could not load skillbalancer/mode config value: %s' % e)
            self.debug('Using default value (%s) for skillbalancer/mode' % self._skill_balance_mode)

        try:
            self._minbalinterval = self.config.getint('skillbalancer', 'min_bal_interval')
        except ConfigParser.NoOptionError:
            self.warning('Could not find skillbalancer/min_bal_interval in config file, using default: %s' %
                         self._minbalinterval)
        except ValueError, e:
            self.warning('Could not load skillbalancer/min_bal_interval config value: %s' % e)
            self.debug('Using default value (%s) for skillbalancer/min_bal_interval' % self._minbalinterval)

        self.debug('Skillbalance interval: %s' % self._skinterval)
        self.debug('Skillbalance difference: %s' % self._skilldiff)
        self.debug('Skillbalance mode: %s' % self._skill_balance_mode)
        self.debug('Minimum skillbalance interval: %s' % self._minbalinterval)

    def loadVoteDelayer(self):
        """
        Setup the vote delayer
        """
        try:
            self._votedelay = self.config.getint('votedelay', 'votedelay')
        except ConfigParser.NoOptionError:
            self.warning('Could not find votedelay/votedelay in config file, using default: %s' % self._votedelay)
        except ValueError, e:
            self.warning('Could not load votedelay/votedelay config value: %s' % e)
            self.debug('Using default value (%s) for votedelay/votedelay' % self._votedelay)

        # set a max delay, setting it larger than timelimit would be foolish
        timelimit = self.console.getCvar('timelimit').getInt()

        if timelimit == 0 and self._votedelay != 0:
            # endless map or frag limited settings
            self._votedelay = 10
        elif self._votedelay >= timelimit - 1:
            # don't overlap rounds
            self._votedelay = timelimit - 1

        self.debug('Vote delay: %s' % self._votedelay)

    def loadSpecChecker(self):
        """
        Setup the spec checker
        """
        try:
            self._sinterval = self.config.getint('speccheck', 'sinterval')
        except ConfigParser.NoOptionError:
            self.warning('Could not find speccheck/sinterval in config file, using default: %s' % self._sinterval)
        except ValueError, e:
            self.error('Could not load speccheck/sinterval config value: %s' % e)
            self.debug('Using default value (%s) for speccheck/sinterval' % self._sinterval)

        try:
            self._smaxspectime = self.config.getint('speccheck', 'maxspectime')
        except ConfigParser.NoOptionError:
            self.warning('Could not find speccheck/maxspectime in config file, using default: %s' % self._smaxspectime)
        except ValueError, e:
            self.error('Could not load speccheck/maxspectime e config value: %s' % e)
            self.debug('Using default value (%s) for speccheck/maxspectime ' % self._smaxspectime)

        try:
            # loading spec max level configuration value
            self._smaxlevel = self.config.getint('speccheck', 'maxlevel')
        except ConfigParser.NoOptionError:
            self.warning('Could not find speccheck/maxlevel in config file, using default: %s' % self._smaxlevel)
        except ValueError, e:
            self.error('Could not load speccheck/maxlevel config value: %s' % e)
            self.debug('Using default value (%s) for speccheck/maxlevel' % self._smaxlevel)

        try:
            self._smaxplayers = self.config.getint('speccheck', 'maxplayers')
        except (ConfigParser.NoOptionError, ValueError), e:
            if isinstance(e, ConfigParser.NoOptionError):
                self.warning('Could not find speccheck/maxplayers in config file')
            elif isinstance(e, ValueError):
                self.error('Could not load speccheck/maxplayers config value: %s' % e)

            # load default value according to server configuration
            maxclients = self.console.getCvar('sv_maxclients').getInt()
            pvtclients = self.console.getCvar('sv_privateClients').getInt()
            self._smaxplayers = maxclients - pvtclients
            self.debug('using default server value (sv_maxclients - sv_privateClients = %s) for \
                        speccheck/maxplayers' % self._smaxplayers)

        self.debug('Speccheck interval: %s' % self._sinterval)
        self.debug('Max spec time: %s' % self._smaxspectime)
        self.debug('Speccheck max level: %s' % self._smaxlevel)
        self.debug('Spec max players: %s' % self._smaxplayers)

    def loadMoonMode(self):
        """
        Setup the moon mode
        """
        try:
            self._moon_on_gravity = self.config.getint('moonmode', 'gravity_on')
        except ConfigParser.NoOptionError:
            self.warning('Could not find moonmode/gravity_on in config file, using default: %s' % self._moon_on_gravity)
        except ValueError, e:
            self.error('Could not load moonmode/gravity_on config value: %s' % e)
            self.debug('Using default value (%s) for moonmode/gravity_on' % self._moon_on_gravity)

        try:
            self._moon_off_gravity = self.config.getint('moonmode', 'gravity_off')
        except ConfigParser.NoOptionError:
            self.warning('Could not find moonmode/gravity_off in config file, using default: %s' %
                         self._moon_off_gravity)
        except ValueError, e:
            self.error('Could not load moonmode/gravity_off config value: %s' % e)
            self.debug('Using default value (%s) for moonmode/gravity_off' % self._moon_off_gravity)

        self.debug('Moon ON gravity: %s' % self._moon_on_gravity)
        self.debug('Moon OFF gravity: %s' % self._moon_off_gravity)

    def loadPublicMode(self):
        """
        Setup the public mode
        """
        try:
            self._randnum = self.config.getint('publicmode', 'randnum')
        except ConfigParser.NoOptionError:
            self.warning('Could not find publicmode/randnum in config file, using default: %s' % self._randnum)
        except ValueError, e:
            self.error('Could not load publicmode/randnum config value: %s' % e)
            self.debug('Using default value (%s) for publicmode/randnum' % self._randnum)

        try:

            try:
                padic = self.config.getboolean('publicmode', 'usedic')
            except ConfigParser.NoOptionError:
                padic = False
                self.warning('Could not find publicmode/usedic in config file, using default: %s' % padic)
            except ValueError, e:
                padic = False
                self.error('Could not load publicmode/usedic config value: %s' % e)
                self.debug('Using default value (%s) for publicmode/usedic' % padic)

            if padic:

                padicfile = self.config.getpath('publicmode', 'dicfile')
                self.debug('trying to use password dictionnary %s' % padicfile)
                if os.path.exists(padicfile):
                    stinfo = os.stat(padicfile)
                    if stinfo.st_size > self._max_dic_size:
                        self.warning('dictionary file is too big: switching to default')
                    else:
                        dicfile = open(padicfile)
                        text = dicfile.read().strip()
                        dicfile.close()
                        if text == "":
                            self.warning('dictionary file is empty: switching to default')
                        else:
                            self._pass_lines = text.splitlines()

                    self.debug('using dictionary password')

                else:
                    self.warning('dictionary is enabled but the file doesn\'t exists: switching to default')

        except Exception, e:
            self.error('Could not load dictionary config: %s' % e)
            self.debug('using default dictionary')

        try:

            self._papublic_password = self.config.get('publicmode', 'g_password')
            if self._papublic_password is None:
                self.warning('could not setup papublic command because there is no password set in config')

        except ConfigParser.NoOptionError:
            self.debug('could not setup papublic command because there is no password set in config')

        self.debug('papublic password set to : %s' % self._papublic_password)

    def loadMatchMode(self):
        """
        Setup the match mode
        """
        try:
            # load a list of plugins to be disabled/enabled upon match mode enabled/disabled
            self.debug('matchmode/plugins_disable : %s' % self.config.get('matchmode', 'plugins_disable'))
            self._match_plugin_disable = [x for x in re.split('\W+',
                                                              self.config.get('matchmode', 'plugins_disable')) if x]
        except ConfigParser.NoOptionError:
            self.warning('Could not find matchmode/plugins_disable in config file')

        try:

            # load all the configuration files into a dict
            for key, value in self.config.items('matchmode_configs'):
                self._gameconfig[key] = value

        except (ConfigParser.NoSectionError, ConfigParser.NoOptionError, KeyError), e:
            self.warning('could not read matchmode configs: %s' % e)

    def loadBotSupport(self):
        """
        Setup the bot support
        """
        try:
            self._botenable = self.config.getboolean('botsupport', 'bot_enable')
        except ConfigParser.NoOptionError:
            self.warning('Could not find botsupport/bot_enable in config file, using default: %s' % self._botenable)
        except ValueError, e:
            self.error('Could not load botsupport/bot_enable config value: %s' % e)
            self.debug('Using default value (%s) for botsupport/bot_enable' % self._botenable)

        try:
            self._botskill = self.config.getint('botsupport', 'bot_skill')
        except ConfigParser.NoOptionError:
            self.warning('Could not find botsupport/bot_skill in config file, using default: %s' % self._botskill)
        except ValueError, e:
            self.error('Could not load botsupport/bot_skill config value: %s' % e)
            self.debug('Using default value (%s) for botsupport/bot_skill' % self._botskill)

        # clamp botskill value
        if self._botskill > 5:
            self._botskill = 5
        elif self._botskill < 1:
            self._botskill = 1

        try:
            self._botminplayers = self.config.getint('botsupport', 'bot_minplayers')
        except ConfigParser.NoOptionError:
            self.warning('Could not find botsupport/bot_minplayers in config file, '
                         'using default: %s' % self._botminplayers)
        except ValueError, e:
            self.error('Could not load botsupport/bot_minplayers config value: %s' % e)
            self.debug('Using default value (%s) for botsupport/bot_minplayers' % self._botminplayers)

        # clamp botminplayers value
        if self._botminplayers > 16:
            self._botminplayers = 16
        elif self._botminplayers < 0:
            self._botminplayers = 0

        try:
            maps = self.config.get('botsupport', 'bot_maps')
            maps = maps.split(' ')
            self._botmaps = maps
        except ConfigParser.NoOptionError:
            self.debug('no map specified for botsupport...')

        if self._botenable:
            # if it isn't enabled already it takes a mapchange to activate
            self.console.write('set bot_enable 1')

        # set the correct botskill anyway
        self.console.write('set g_spskill %s' % self._botskill)

        self.debug('Bot enable: %s' % self._botenable)
        self.debug('Bot skill: %s' % self._botskill)
        self.debug('Bot minplayers: %s' % self._botminplayers)
        self.debug('Bot maps: %s' % self._botmaps)

        # first check for botsupport
        self.botsupport()

    def loadHeadshotCounter(self):
        """
        Setup the headshot counter
        """
        try:
            self._hsenable = self.config.getboolean('headshotcounter', 'hs_enable')
        except ConfigParser.NoOptionError:
            self.warning('Could not find headshotcounter/hs_enable in config file, using default: %s' % self._hsenable)
        except ValueError, e:
            self.error('Could not load headshotcounter/hs_enable config value: %s' % e)
            self.debug('Using default value (%s) for headshotcounter/hs_enable' % self._hsenable)

        try:
            self._hsresetvars = self.config.get('headshotcounter', 'reset_vars')
            if not self._hsresetvars in ['no', 'map', 'round']:
                raise KeyError('configuration setting not valid')
        except ConfigParser.NoOptionError:
            self.warning('Could not find headshotcounter/reset_vars in config file, using default: %s' %
                         self._hsresetvars)
        except KeyError, e:
            self.error('Could not load headshotcounter/reset_vars config value: %s' % e)
            self.debug('Using default value (%s) for headshotcounter/reset_vars' % self._hsresetvars)

        try:
            self._hsbroadcast = self.config.getboolean('headshotcounter', 'broadcast')
        except ConfigParser.NoOptionError:
            self.warning('Could not find headshotcounter/broadcast in config file, using default: %s' %
                         self._hsbroadcast)
        except ValueError, e:
            self.error('Could not load headshotcounter/broadcast config value: %s' % e)
            self.debug('Using default value (%s) for headshotcounter/broadcast' % self._hsbroadcast)

        try:
            self._hsall = self.config.getboolean('headshotcounter', 'announce_all')
        except ConfigParser.NoOptionError:
            self.warning('Could not find headshotcounter/announce_all in config file, using default: %s' % self._hsall)
        except ValueError, e:
            self.error('Could not load headshotcounter/announce_all config value: %s' % e)
            self.debug('Using default value (%s) for headshotcounter/announce_all' % self._hsall)

        try:
            self._hspercent = self.config.getboolean('headshotcounter', 'announce_percentages')
        except ConfigParser.NoOptionError:
            self.warning('Could not find headshotcounter/announce_percentages in config file, using default: %s' %
                         self._hspercent)
        except ValueError, e:
            self.error('Could not load headshotcounter/announce_percentages config value: %s' % e)
            self.debug('Using default value (%s) for headshotcounter/announce_percentages' % self._hspercent)

        try:
            self._hspercentmin = self.config.getint('headshotcounter', 'percent_min')
        except ConfigParser.NoOptionError:
            self.warning('Could not find headshotcounter/percent_min in config file, using default: %s' %
                         self._hspercentmin)
        except ValueError, e:
            self.error('Could not load headshotcounter/percent_min config value: %s' % e)
            self.debug('Using default value (%s) for headshotcounter/percent_min' % self._hspercentmin)

        try:
            self._hswarnhelmet = self.config.getboolean('headshotcounter', 'warn_helmet')
        except ConfigParser.NoOptionError:
            self.warning('Could not find headshotcounter/warn_helmet in config file, using default: %s' %
                         self._hswarnhelmet)
        except ValueError, e:
            self.error('Could not load headshotcounter/warn_helmet config value: %s' % e)
            self.debug('Using default value (%s) for headshotcounter/warn_helmet' % self._hswarnhelmet)

        try:
            self._hswarnhelmetnr = self.config.getint('headshotcounter', 'warn_helmet_nr')
        except ConfigParser.NoOptionError:
            self.warning('Could not find headshotcounter/warn_helmet_nr in config file, using default: %s' %
                         self._hswarnhelmetnr)
        except ValueError, e:
            self.error('Could not load headshotcounter/warn_helmet_nr config value: %s' % e)
            self.debug('Using default value (%s) for headshotcounter/warn_helmet_nr' % self._hswarnhelmetnr)

        try:
            self._hswarnkevlar = self.config.getboolean('headshotcounter', 'warn_kevlar')
        except ConfigParser.NoOptionError:
            self.warning('Could not find headshotcounter/warn_kevlar in config file, using default: %s' %
                         self._hswarnkevlar)
        except ValueError, e:
            self.error('Could not load headshotcounter/warn_kevlar config value: %s' % e)
            self.debug('Using default value (%s) for headshotcounter/warn_kevlar' % self._hswarnkevlar)

        try:
            self._hswarnkevlarnr = self.config.getint('headshotcounter', 'warn_kevlar_nr')
        except ConfigParser.NoOptionError:
            self.warning('Could not find headshotcounter/warn_kevlar_nr in config file, using default: %s' %
                         self._hswarnkevlarnr)
        except ValueError, e:
            self.error('Could not load headshotcounter/warn_kevlar_nr config value: %s' % e)
            self.debug('Using default value (%s) for headshotcounter/warn_kevlar_nr' % self._hswarnkevlarnr)

        # making shure loghits is enabled to count headshots
        if self._hsenable:
            self.console.write('set g_loghits 1')

        self.debug('Headshotcounter enable: %s' % self._hsenable)
        self.debug('Broadcasting: %s' % self._hsbroadcast)
        self.debug('Announce all: %s' % self._hsall)
        self.debug('Announce percentages: %s' % self._hspercent)
        self.debug('Minimum percentage: %s' % self._hspercentmin)
        self.debug('Warn to use helmet: %s' % self._hswarnhelmet)
        self.debug('Warn after nr of hits in the head: %s' % self._hswarnhelmetnr)
        self.debug('Warn to use kevlar: %s' % self._hswarnkevlar)
        self.debug('Warn after nr of hits in the torso: %s' % self._hswarnkevlarnr)

    def loadRotationManager(self):
        """
        Setup the rotation manager
        """
        try:
            self._rmenable = self.config.getboolean('rotationmanager', 'rm_enable')
        except ConfigParser.NoOptionError:
            self.warning('Could not find rotationmanager/rm_enable in config file, using default: %s' % self._rmenable)
        except ValueError, e:
            self.error('Could not load rotationmanager/rm_enable config value: %s' % e)
            self.debug('Using default value (%s) for rotationmanager/rm_enable' % self._rmenable)

        if self._rmenable:

            try:
                self._switchcount1 = self.config.getint('rotationmanager', 'switchcount1')
            except ConfigParser.NoOptionError:
                self.warning('Could not find rotationmanager/switchcount1 in config file, using default: %s' %
                             self._switchcount1)
            except ValueError, e:
                self.error('Could not load rotationmanager/switchcount1 config value: %s' % e)
                self.debug('Using default value (%s) for rotationmanager/switchcount1' % self._switchcount1)

            try:
                self._switchcount2 = self.config.getint('rotationmanager', 'switchcount3')
            except ConfigParser.NoOptionError:
                self.warning('Could not find rotationmanager/switchcount2 in config file, using default: %s' %
                             self._switchcount2)
            except ValueError, e:
                self.error('Could not load rotationmanager/switchcount2 config value: %s' % e)
                self.debug('Using default value (%s) for rotationmanager/switchcount2' % self._switchcount2)

            try:
                self._hysteresis = self.config.getint('rotationmanager', 'hysteresis')
            except ConfigParser.NoOptionError:
                self.warning('Could not find rotationmanager/hysteresis in config file, using default: %s' %
                             self._hysteresis)
            except ValueError, e:
                self.error('Could not load rotationmanager/hysteresis config value: %s' % e)
                self.debug('Using default value (%s) for rotationmanager/hysteresis' % self._hysteresis)

            try:
                self._rotation_small = self.config.get('rotationmanager', 'smallrotation')
            except ConfigParser.NoOptionError:
                self.warning('Could not find rotationmanager/smallrotation in config file')

            try:
                self._rotation_medium = self.config.get('rotationmanager', 'mediumrotation')
            except ConfigParser.NoOptionError:
                self.warning('Could not find rotationmanager/mediumrotation in config file')

            try:
                self._rotation_large = self.config.get('rotationmanager', 'largerotation')
            except ConfigParser.NoOptionError:
                self.warning('Could not find rotationmanager/largerotation in config file')

            try:
                self._gamepath = self.config.get('rotationmanager', 'gamepath')
            except ConfigParser.NoOptionError:
                self.warning('Could not find rotationmanager/gamepath in config file')

            self.debug('Rotation Manager is enabled')
            self.debug('Switchcount 1: %s' % self._switchcount1)
            self.debug('Switchcount 2: %s' % self._switchcount2)
            self.debug('Hysteresis: %s' % self._hysteresis)
            self.debug('Rotation small: %s' % self._rotation_small)
            self.debug('Rotation medium: %s' % self._rotation_medium)
            self.debug('Rotation large: %s' % self._rotation_large)
            self.debug('Game path: %s' % self._gamepath)
        else:
            self.debug('Rotation Manager is disabled')

    def loadSpecial(self):
        """
        Setup special configs
        """
        try:
            self._slapSafeLevel = self.config.getint('special', 'slap_safe_level')
        except ConfigParser.NoOptionError:
            self.warning('Could not find special/slap_safe_level in config file, using default: %s' %
                         self._slapSafeLevel)
        except ValueError, e:
            self.error('Could not load special/slap_safe_level config value: %s' % e)
            self.debug('Using default value (%s) for special/slap_safe_level' % self._slapSafeLevel)

        try:
            self._full_ident_level = self.config.getint('special', 'paident_full_level')
        except ConfigParser.NoOptionError:
            self.warning('Could not find special/paident_full_level in config file, using default: %s' %
                         self._full_ident_level)
        except ValueError, e:
            self.error('Could not load special/paident_full_level config value: %s' % e)
            self.debug('Using default value (%s) for special/paident_full_level' % self._full_ident_level)

    def installCrontabs(self):
        """
        CRONTABS INSTALLATION
        Cleanup and Create the crontabs
        """
        if self._ncronTab:
            # remove existing crontab
            self.console.cron - self._ncronTab
        if self._tcronTab:
            # remove existing crontab
            self.console.cron - self._tcronTab
        if self._scronTab:
            # remove existing crontab
            self.console.cron - self._scronTab
        if self._skcronTab:
            # remove existing crontab
            self.console.cron - self._skcronTab
        if self._ninterval > 0:
            self._ncronTab = b3.cron.PluginCronTab(self, self.namecheck, 0, '*/%s' % self._ninterval)
            self.console.cron + self._ncronTab
        if self._tinterval > 0:
            self._tcronTab = b3.cron.PluginCronTab(self, self.teamcheck, 0, '*/%s' % self._tinterval)
            self.console.cron + self._tcronTab
        if self._sinterval > 0:
            self._scronTab = b3.cron.PluginCronTab(self, self.speccheck, 0, '*/%s' % self._sinterval)
            self.console.cron + self._scronTab
        if self._skinterval > 0:
            self._skcronTab = b3.cron.PluginCronTab(self, self.skillcheck, 0, '*/%s' % self._skinterval)
            self.console.cron + self._skcronTab

    def getCmd(self, cmd):
        cmd = 'cmd_%s' % cmd
        if hasattr(self, cmd):
            func = getattr(self, cmd)
            return func

        return None

    def onEvent(self, event):
        """
        Handle intercepted events
        """
        if event.type == self.console.getEventID('EVT_CLIENT_DISCONNECT'):
            if self._rmenable and self.console.time() > self._dontcount and self._mapchanged:
                self._playercount -= 1
                self.debug('PlayerCount: %s' % self._playercount)
                self.adjustrotation(-1)

        elif event.type ==  self.console.getEventID('EVT_CLIENT_AUTH'):
            if self._hsenable:
                self.setupVars(event.client)
            if self._rmenable and self.console.time() > self._dontcount and self._mapchanged:
                self._playercount += 1
                self.debug('PlayerCount: %s' % self._playercount)
                self.adjustrotation(+1)

        elif event.type ==  self.console.getEventID('EVT_CLIENT_TEAM_CHANGE'):
            self.onTeamChange(event.data, event.client)

        elif event.type ==  self.console.getEventID('EVT_CLIENT_DAMAGE'):
            self.headshotcounter(event.client, event.target, event.data)

        elif event.type ==  self.console.getEventID('EVT_GAME_EXIT'):
            self._mapchanged = True
            if self._botenable:
                self.botsdisable()

            self.ignoreSet(self._ignorePlus)

            # reset headshotcounter (per map) if applicable
            if self._hsresetvars == 'map':
                self.resetVars()

            # reset number of name changes per client
            self.resetNameChanges()
            if not self._teamLocksPermanent:
                # release TeamLocks
                self.resetTeamLocks()

            # setup timer for recounting players
            if self._rmenable:
                tm = 60
                self._dontcount = self.console.time() + tm
                t2 = threading.Timer(tm, self.recountplayers)
                self.debug('Starting RecountPlayers Timer: %s seconds' % tm)
                t2.start()

        elif event.type ==  self.console.getEventID('EVT_GAME_ROUND_START'):
            self._forgetTeamContrib()
            self._killhistory = []
            self._lastbal = self.console.time()

            # check for botsupport
            if self._botenable:
                self.botsdisable()
                self.botsupport()

            # reset headshotcounter (per round) if applicable
            if self._hsresetvars == 'round':
                self.resetVars()

            # ignore teambalance checking for 1 minute
            self.ignoreSet(self._ignorePlus)
            self._teamred = 0
            self._teamblue = 0

            # vote delay init
            if self._votedelay > 0 and self.console.getCvar('g_allowvote').getInt() != 0:
                # delay voting
                data = 'off'
                self.votedelay(data)
                # re-enable voting
                tm = self._votedelay * 60
                t1 = threading.Timer(tm, self.votedelay)
                self.debug('Starting Vote delay Timer: %s seconds' % tm)
                t1.start()

        elif event.type ==  self.console.getEventID('EVT_CLIENT_NAME_CHANGE'):
            self.onNameChange(event.data, event.client)

        elif event.type ==  self.console.getEventID('EVT_CLIENT_KILL'):
            self.onKill(event.client, event.target, int(event.data[0]))

        elif event.type ==  self.console.getEventID('EVT_CLIENT_KILL_TEAM'):
            self.onKillTeam(event.client, event.target, int(event.data[0]))

        elif event.type ==  self.console.getEventID('EVT_CLIENT_ACTION'):
            self.onAction(event.client, event.data)

        elif event.type == self.console.getEventID('EVT_GAME_MAP_CHANGE'):
            self._matchmode = self.console.getCvar('g_matchmode').getBoolean()

        else:
            self.dumpEvent(event)

    def onKill(self, killer, victim, points):
        killer.var(self, 'kills', 0).value += 1
        victim.var(self, 'deaths', 0).value += 1
        now = self.console.time()
        killer.var(self, 'teamcontribhist', []).value.append((now, 1))
        victim.var(self, 'teamcontribhist', []).value.append((now, -1))
        self._killhistory.append((now, killer.team))

    def onKillTeam(self, killer, victim, points):
        killer.var(self, 'teamkills', 0).value += 1

    def onAction(self, client, actiontype):
        if actiontype in ('flag_captured', 'flag_dropped', 'flag_returned', 'bomb_planted', 'bomb_defused'):
            client.var(self, actiontype, 0).value += 1
        if actiontype in ('team_CTF_redflag', 'team_CTF_blueflag'):
            client.var(self, 'flag_taken', 0).value += 1

    def dumpEvent(self, event):
        self.debug('poweradminurt.dumpEvent -- Type %s, Client %s, Target %s, Data %s',
                   event.type, event.client, event.target, event.data)

    def _teamvar(self, client, var):
        """
        Return how much variable has changed
        since player joined its team
        """
        old = client.var(self, 'prev_' + var, 0).value
        new = client.var(self, var, 0).value
        return new - old

    def _saveTeamvars(self, client):
        for var in ('kills', 'deaths', 'teamkills', 'headhits', 'helmethits',
                    'flag_captured', 'flag_returned', 'bomb_planted', 'bomb_defused'):
            old = client.var(self, var, 0).value
            client.setvar(self, "prev_" + var, old)

    def _getScores(self, clients, usexlrstats=True):
        xlrstats = usexlrstats and self.console.getPlugin('xlrstats')
        playerstats = {}
        maxstats = {}
        minstats = {}
        keys = 'hsratio', 'killratio', 'teamcontrib', 'xhsratio', 'xkillratio', 'flagperf', 'bombperf'
        now = self.console.time()
        for c in clients:
            if not c.isvar(self, 'teamtime'):
                c.setvar(self, 'teamtime', now)
            age = (now - c.var(self, 'teamtime', 0).value) / 60.0
            kills = max(0, self._teamvar(c, 'kills'))
            deaths = max(0, self._teamvar(c, 'deaths'))
            teamkills = max(0, self._teamvar(c, 'teamkills'))
            hs = self._teamvar(c, 'headhits') + self._teamvar(c, 'helmethits')
            hsratio = min(1.0, hs / (1.0 + kills))  # hs can be greater than kills
            killratio = kills / (1.0 + deaths + teamkills)
            teamcontrib = (kills - deaths - teamkills) / (age + 1.0)
            flag_taken = int(bool(c.var(self, 'flag_taken', 0).value))  # one-time bonus
            flag_captured = self._teamvar(c, 'flag_captured')
            flag_returned = self._teamvar(c, 'flag_returned')
            flagperf = 10 * flag_taken + 20 * flag_captured + flag_returned
            bomb_planted = self._teamvar(c, 'bomb_planted')
            bomb_defused = self._teamvar(c, 'bomb_defused')
            bombperf = bomb_planted + bomb_defused

            playerstats[c.id] = {
                'age': age,
                'hsratio': hsratio,
                'killratio': killratio,
                'teamcontrib': teamcontrib,
                'flagperf': flagperf,
                'bombperf': bombperf,
            }

            stats = xlrstats.get_PlayerStats(c) if xlrstats else None
            if stats:
                playerstats[c.id]['xkillratio'] = stats.ratio
                head = xlrstats.get_PlayerBody(playerid=c.cid, bodypartid=0).kills
                helmet = xlrstats.get_PlayerBody(playerid=c.cid, bodypartid=1).kills
                xhsratio = min(1.0, (head + helmet) / (1.0 + kills))
                playerstats[c.id]['xhsratio'] = xhsratio
            else:
                playerstats[c.id]['xhsratio'] = 0.0
                playerstats[c.id]['xkillratio'] = 0.8
            for key in keys:
                if key not in maxstats or maxstats[key] < playerstats[c.id][key]:
                    maxstats[key] = playerstats[c.id][key]
                if key not in minstats or minstats[key] > playerstats[c.id][key]:
                    minstats[key] = playerstats[c.id][key]

        scores = {}
        weights = {
            'killratio': 1.0,
            'teamcontrib': 0.5,
            'hsratio': 0.3,
            'xkillratio': 1.0,
            'xhsratio': 0.5,
            # weight score for mission objectives higher
            'flagperf': 3.0,
            'bombperf': 3.0,
        }

        weightsum = sum(weights[key] for key in keys)
        self.debug("score: maxstats=%s" % str(maxstats))
        self.debug("score: minstats=%s" % str(minstats))
        for c in clients:
            score = 0.0
            tm = min(1.0, playerstats[c.id]['age'] / 5.0)  # reduce score for players who just joined
            msg = []
            for key in keys:
                denom = maxstats[key] - minstats[key]
                if denom < 0.0001:  # accurate at ne nimis
                    continue
                msg.append("%s=%.3f" % (key, playerstats[c.id][key]))
                keyscore = weights[key] * (playerstats[c.id][key] - minstats[key]) / denom
                if key in ('killratio', 'teamcontrib', 'hsratio'):
                    score += tm * keyscore
                else:
                    score += keyscore

            score /= weightsum
            self.debug('score: %s %s score=%.3f age=%.2f %s' % (c.team, c.name, score,
                                                                playerstats[c.id]['age'], ' '.join(msg)))
            scores[c.id] = score

        return scores

    def _getRandomTeams(self, clients, checkforced=False):
        blue = []
        red = []
        nonforced = []
        for c in clients:
            # ignore spectators
            if c.team in (b3.TEAM_BLUE, b3.TEAM_RED):
                if checkforced and c.isvar(self, 'paforced'):
                    if c.team == b3.TEAM_BLUE:
                        blue.append(c)
                    else:
                        red.append(c)
                else:
                    nonforced.append(c)

        # distribute nonforced players
        random.shuffle(nonforced)
        n = (len(nonforced) + len(blue) + len(red)) / 2 - len(blue)
        blue.extend(nonforced[:n])
        red.extend(nonforced[n:])
        return blue, red

    def _getTeamScore(self, team, scores):
        return sum(scores.get(c.id, 0.0) for c in team)

    def _getTeamScoreDiff(self, blue, red, scores):
        bluescore = self._getTeamScore(blue, scores)
        redscore = self._getTeamScore(red, scores)
        return bluescore - redscore

    def _getTeamScoreDiffForAdvise(self, minplayers=None):
        clients = self.console.clients.getList()
        gametype = self._getGameType()
        tdm = (gametype == 'tdm')
        scores = self._getScores(clients, usexlrstats=tdm)
        blue = [c for c in clients if c.team == b3.TEAM_BLUE]
        red = [c for c in clients if c.team == b3.TEAM_RED]
        self.debug("advise: numblue=%d numred=%d" % (len(blue), len(red)))

        if minplayers and len(blue) + len(red) < minplayers:
            self.debug('advise: too few players')
            return None, None

        diff = self._getTeamScoreDiff(blue, red, scores)

        if tdm:
            bs, rs = self._getAvgKillsRatios(blue, red)
            avgdiff = bs - rs
            self.debug('advise: TDM blue=%.2f red=%.2f avgdiff=%.2f skilldiff=%.2f' % (bs, rs, avgdiff, diff))
        else:
            # just looking at kill ratios doesn't work well for CTF, so we base
            # the balance diff on the skill diff for now
            sincelast = self.console.time() - self._lastbal
            damping = min(1.0, sincelast / (1.0 + 60.0 * self._minbalinterval))
            avgdiff = 1.21*diff*damping
            self.debug('advise: CTF/BOMB avgdiff=%.2f skilldiff=%.2f damping=%.2f' % (avgdiff, diff, damping))

        return avgdiff, diff

    def _getRecentKills(self, tm):
        t0 = self.console.time() - tm
        i = len(self._killhistory) - 1
        while i >= 0:
            t, team = self._killhistory[i]
            if t < t0:
                break

            i -= 1
            yield t, team

    def _getAvgKillsRatios(self, blue, red):
        if not blue or not red:
            return 0.0, 0.0

        tmin = 2.0
        tmax = 4.0
        totkpm = len(list((self._getRecentKills(60))))
        tm = max(tmin, tmax - 0.1 * totkpm)
        self.debug('recent: totkpm=%d tm=%.2f' % (totkpm, tm))
        recentcontrib = {}
        t0 = self.console.time() - tm * 60
        for c in blue + red:
            hist = c.var(self, 'teamcontribhist', []).value
            k = 0
            d = 0
            for t, s in hist:
                if t0 < t:
                    if s > 0:
                        k += 1
                    elif s < 0:
                        d += 1
            recentcontrib[c.id] = k/(1.0+d)

        self.debug('recent: %s' % str(recentcontrib))

        def contribcmp(a, b):
            return cmp(recentcontrib[b.id], recentcontrib[a.id])

        blue = sorted(blue, cmp=contribcmp)
        red = sorted(red, cmp=contribcmp)
        n = min(len(blue), len(red))
        if n > 3:
            n = 3 + int((n-3)/2)

        bs = float(sum(recentcontrib[c.id] for c in blue[:n])) / n / tm
        rs = float(sum(recentcontrib[c.id] for c in red[:n])) / n / tm
        self.debug('recent: n=%d tm=%.2f %.2f %.2f' % (n, tm, bs, rs))
        return bs, rs

    def _forgetTeamContrib(self):
        self._oldadv = (None, None, None)
        clients = self.console.clients.getList()
        for c in clients:
            c.setvar(self, 'teamcontribhist', [])
            self._saveTeamvars(c)

    def _countSnipers(self, team):
        n = 0
        for c in team:
            kills = max(0, c.var(self, 'kills', 0).value)
            deaths = max(0, c.var(self, 'deaths', 0).value)
            ratio = kills / (1.0 + deaths)
            if ratio < 1.2:
                # Ignore sniper noobs
                continue
                # Count players with SR8 and PSG1
            gear = getattr(c, 'gear', '')
            if 'Z' in gear or 'N' in gear:
                n += 1

        return n

    def _move(self, blue, red, scores=None):
        self.debug('move: final blue team: ' + ' '.join(c.name for c in blue))
        self.debug('move: final red team: ' + ' '.join(c.name for c in red))

        # Filter out players already in correct team
        blue = [c for c in blue if c.team != b3.TEAM_BLUE]
        red = [c for c in red if c.team != b3.TEAM_RED]

        if not blue and not red:
            return 0

        bestscore = None

        if scores:
            bestscore = max(scores[c.id] for c in blue + red)

        clients = self.console.clients.getList()
        numblue = len([c for c in clients if c.team == b3.TEAM_BLUE])
        numred = len([c for c in clients if c.team == b3.TEAM_RED])
        self.debug('move: num players: blue=%d red=%d' % (numblue, numred))
        self.ignoreSet(30)

        # We have to make sure we don't get a "too many players" error from the
        # server when we move the players. Start moving from the team with most
        # players. If the teams are equal in numbers, temporarily put one player in
        # spec mode.
        moves = len(blue) + len(red)
        spec = None
        self.debug('move: need to do %d moves' % moves)
        self.debug('move: will go to blue team: ' + ' '.join(c.name for c in blue))
        self.debug('move: will go to red team: ' + ' '.join(c.name for c in red))

        if blue and numblue == numred:
            random.shuffle(blue)
            spec = blue.pop()
            self.console.write('forceteam %s spectator' % spec.cid)
            numred -= 1
            moves -= 1
            self.debug('move: moved %s from red to spec' % spec.name)

        queue = []

        for _ in xrange(moves):
            newteam = None

            if (blue and numblue < numred) or (blue and not red):
                c = blue.pop()
                newteam = 'blue'
                self.console.write('forceteam %s %s' % (c.cid, newteam))
                numblue += 1
                numred -= 1
                self.debug('move: moved %s to blue' % c.name)
            elif red:
                c = red.pop()
                newteam = 'red'
                self.console.write('forceteam %s %s' % (c.cid, newteam))
                numblue -= 1
                numred += 1
                self.debug('move: moved %s to red' % c.name)

            if newteam and scores:
                if newteam == "red":
                    colorpfx = '^1'
                    oldteam = "blue"
                else:
                    colorpfx = '^4'
                    oldteam = "red"
                if scores[c.id] == bestscore:
                    messages = [
                        "You were moved because %n team needs more noobs.",
                        "I wanted to move the best player but settled for you instead.",
                        "If you learnt to aim before you shoot I wouldn't have to move you!",
                    ]
                else:
                    messages = [
                        "%n team needs your help! Try not to die too many times...",
                        "You have new friends now. Try not to kill them...",
                        "You have no friends now but try to kill %o team anyway...",
                        "You were moved to %n team for balance.",
                    ]

                msg = random.choice(messages)
                team = None

                if '%n' in msg:
                    team = newteam
                    msg = msg.replace('%n', '%s')

                if '%o' in msg:
                    team = oldteam
                    msg = msg.replace('%o', '%s')

                if msg.startswith('%'):
                    team = team.capitalize()

                if '%s' in msg:
                    msg = msg % team

                # send priv msg after all joins, seem like we can lose the msg
                # otherwise...
                queue.append((c, colorpfx + msg))

        if spec:
            self.console.write('forceteam %s blue' % spec.cid)
            self.debug('move: moved %s from spec to blue' % spec.name)

        for c, msg in queue:
            c.message(msg)

        return moves

    def _randTeams(self, times, slack, maxmovesperc=None):
        """
        Randomize teams a few times and pick the most balanced
        """
        clients = self.console.clients.getList()
        scores = self._getScores(clients)
        oldblue = [c for c in clients if c.team == b3.TEAM_BLUE]
        oldred = [c for c in clients if c.team == b3.TEAM_RED]
        n = len(oldblue) + len(oldred)
        olddiff = self._getTeamScoreDiff(oldblue, oldred, scores)
        self.debug('rand: n=%s' % n)
        self.debug('rand: olddiff=%.2f' % olddiff)
        bestdiff = None  # best balance diff so far when diff > slack
        sbestdiff = None  # best balance diff so far when diff < slack
        bestnumdiff = None  # best difference in number of snipers so far
        bestblue = bestred = None  # best teams so far when diff > slack
        sbestblue = sbestred = None  # new teams so far when diff < slack
        epsilon = 0.0001

        if not maxmovesperc and abs(len(oldblue) - len(oldred)) > 1:
            # Teams are unbalanced by count, force both teams two have equal number
            # of players
            self.debug('rand: force new teams')
            bestblue, bestred = self._getRandomTeams(clients, checkforced=True)
            bestdiff = self._getTeamScoreDiff(bestblue, bestred, scores)

        for _ in xrange(times):
            blue, red = self._getRandomTeams(clients, checkforced=True)
            m = self._countMoves(oldblue, blue) + self._countMoves(oldred, red)
            if maxmovesperc and m > max(2, int(round(maxmovesperc * n))):
                continue

            diff = self._getTeamScoreDiff(blue, red, scores)

            if abs(diff) <= slack:
                # balance below slack threshold, try to distribute the snipers instead
                numdiff = abs(self._countSnipers(blue) - self._countSnipers(red))
                if bestnumdiff is None or numdiff < bestnumdiff:
                    # got better sniper num diff
                    if bestnumdiff is None:
                        self.debug('rand: first numdiff %d (sdiff=%.2f)' % (numdiff, diff))
                    else:
                        self.debug('rand: found better numdiff %d < %d (sdiff=%.2f)' % (numdiff, bestnumdiff, diff))

                    sbestblue, sbestred = blue, red
                    sbestdiff, bestnumdiff = diff, numdiff

                elif numdiff == bestnumdiff and abs(diff) < abs(sbestdiff) - epsilon:
                    # same number of snipers but better balance diff
                    self.debug('rand: found better sdiff %.2f < %.2f (numdiff=%d bestnumdiff=%d)' % (
                        abs(diff), abs(sbestdiff), numdiff, bestnumdiff))
                    sbestblue, sbestred = blue, red
                    sbestdiff = diff

            elif bestdiff is None or abs(diff) < abs(bestdiff) - epsilon:
                # balance above slack threshold
                if bestdiff is None:
                    self.debug('rand: first diff %.2f' % abs(diff))
                else:
                    self.debug('rand: found better diff %.2f < %.2f' % (abs(diff), abs(bestdiff)))

                bestblue, bestred = blue, red
                bestdiff = diff

        if bestdiff is not None:
            self.debug('rand: bestdiff=%.2f' % bestdiff)

        if sbestdiff is not None:
            self.debug('rand: sbestdiff=%.2f bestnumdiff=%d' % (sbestdiff, bestnumdiff))
            self.debug('rand: snipers: blue=%d red=%d' % (self._countSnipers(sbestblue), self._countSnipers(sbestred)))
            return olddiff, sbestdiff, sbestblue, sbestred, scores

        return olddiff, bestdiff, bestblue, bestred, scores

    def _countMoves(self, old, new):
        i = 0
        newnames = [c.name for c in new]
        for c in old:
            if c.name not in newnames:
                i += 1

        return i

    def skillcheck(self):
        if self._balancing or self.ignoreCheck():
            return

        gametype = self._getGameType()

        # run skillbalancer only if current
        # gametype is in autobalance_gametypes list
        if not gametype in self._autobalance_gametypes_array:
            self.debug('Current gametype (%s) is not specified in autobalance_gametypes - skillbalancer disabled',
                       self.console.game.gameType)
            return None

        if self._skill_balance_mode == 0:
            # disabled
            return

        avgdiff, diff = self._getTeamScoreDiffForAdvise(minplayers=3)

        if avgdiff is None:
            return None

        absdiff = abs(avgdiff)
        unbalanced = False

        if absdiff >= self._skilldiff:
            unbalanced = True

        if unbalanced or self._skill_balance_mode == 1:
            if absdiff > 0.2:
                self.console.say('Avg kill ratio diff is %.2f, skill diff is %.2f' %\
                                 (avgdiff, diff))
                if self._skill_balance_mode == 1:
                    # Give advice if teams are unfair
                    self._advise(avgdiff, 2)
                else:
                    # Only report stronger team, we will balance/skuffle below
                    self._advise(avgdiff, 0)

        if unbalanced:
            if self._skill_balance_mode == 2:
                self.cmd_pabalance()
            if self._skill_balance_mode == 3:
                self.cmd_paskuffle()

        return None

    def _advise(self, avgdiff, mode):
        # mode 0: no advice
        # mode 1: give advice
        # mode 2: give advice if teams are unfair
        absdiff = 5 * abs(avgdiff)
        unfair = absdiff > 2.31  # constant carefully reviewed by an eminent team of trained Swedish scientistians :)
        word = None
        same = 'remains '
        stronger = 'has become '
        if 1 <= absdiff < 2:
            word = 'stronger'
        elif 2 <= absdiff < 4:
            word = 'dominating'
        elif 4 <= absdiff < 6:
            word = 'overpowering'
        elif 6 <= absdiff < 8:
            word = 'supreme'
        elif 8 <= absdiff < 10:
            word = 'Godlike!'
        elif 10 <= absdiff:
            word = 'probably cheating :P'
            same = 'is '
            stronger = 'is '

        if word:
            oldteam, oldword, oldabsdiff = self._oldadv
            self.debug('advise: oldteam=%s oldword=%s oldabsdiff=%s' % (oldteam, oldword, oldabsdiff))
            team = avgdiff < 0 and 'Red' or 'Blue'
            if team == oldteam:
                if word == oldword:
                    msg = '%s team %s%s' % (team, same, word)
                elif absdiff > oldabsdiff:
                    # stronger team is becoming even stronger
                    msg = '%s team %s%s' % (team, stronger, word)
                elif absdiff < oldabsdiff:
                    # stronger team is becoming weaker
                    msg = '%s team is just %s' % (team, word)
                    if absdiff < 4:
                        # difference not too big, teams may soon be fair
                        unfair = False
                else:
                    # FIXME (Fenix): here 'msg' is not initialized thus it produces a warning
                    return
            else:
                msg = '%s team is now %s' % (team, word)

            if unfair and (mode == 1 or mode == 2):
                msg += ', use !bal to balance the teams'

            if not unfair and mode == 1:
                msg += ', but no action necessary yet'

            self.debug('advise: team=%s word=%s absdiff=%s' % (team, word, absdiff))
            self._oldadv = (team, word, absdiff)

        else:
            msg = 'Teams seem fair'
            self._oldadv = (None, None, None)

        self.console.say(msg)

########################################################################################################################
#---COMMANDS IMPLEMENTATION---------------------------------------------------------------------------------------------
#
#   /rcon commands:
#   slap <clientnum>
#   nuke <clientnum>
#   forceteam <clientnum> <red/blue/s>
#   veto (vote cancellen)
#   mute <clientnum> <seconds>
#   pause
#   swapteams
#   shuffleteams

    def cmd_paadvise(self, data, client, cmd=None):
        """
        Report team skill balance, and give advice if teams are unfair
        """
        avgdiff, diff = self._getTeamScoreDiffForAdvise()
        self.console.say('Avg kill ratio diff is %.2f, skill diff is %.2f' % (avgdiff, diff))
        self._advise(avgdiff, 1)

    def cmd_paunskuffle(self, data, client, cmd=None):
        """
        Create unbalanced teams. Used to test !paskuffle and !pabalance.
        """
        self._balancing = True
        clients = self.console.clients.getList()
        scores = self._getScores(clients)
        decorated = [(scores.get(c.id, 0), c) for c in clients
                     if c.team in (b3.TEAM_BLUE, b3.TEAM_RED)]

        decorated.sort()
        players = [c for score, c in decorated]
        n = len(players) / 2
        blue = players[:n]
        red = players[n:]
        self.console.write('bigtext "Unskuffling! Noobs beware!"')
        self._move(blue, red)
        self._forgetTeamContrib()
        self._balancing = False

    def cmd_paskuffle(self, data=None, client=None, cmd=None):
        """
        Skill shuffle. Shuffle players to balanced teams by numbers and skill.
        Locked players are also moved.
        """
        now = self.console.time()
        sincelast = now - self._lastbal
        if client and client.maxLevel < 20 and self.ignoreCheck() and sincelast < 60 * self._minbalinterval:
            client.message('Teams changed recently, please wait a while')
            return

        self._balancing = True
        olddiff, bestdiff, blue, red, scores = self._randTeams(100, 0.1)
        if client:
            if (client.team == b3.TEAM_BLUE and client.cid not in [c.cid for c in blue]) or \
               (client.team == b3.TEAM_RED and client.cid not in [c.cid for c in red]):
                # don't move player who initiated skuffle
                blue, red = red, blue

        moves = 0
        if bestdiff is not None:
            self.console.write('bigtext "Skill Shuffle in Progress!"')
            moves = self._move(blue, red, scores)

        if moves:
            self.console.say('^4Team skill difference was ^1%.2f^4, is now ^1%.2f' % (olddiff, bestdiff))
        else:
            self.console.say('^1Cannot improve team balance!')

        self._forgetTeamContrib()
        self._balancing = False
        self._lastbal = now

    def cmd_pabalance(self, data=None, client=None, cmd=None):
        """
        Move as few players as needed to create teams balanced by numbers AND skill.
        Locked players are not moved.
        """
        now = self.console.time()
        sincelast = now - self._lastbal
        if client and client.maxLevel < 20 and self.ignoreCheck() and sincelast < 60 * self._minbalinterval:
            client.message('Teams changed recently, please wait a while')
            return

        self._balancing = True
        # always allow at least 2 moves, but don't move more than 30% of the players
        olddiff, bestdiff, bestblue, bestred, scores = self._randTeams(100, 0.1, 0.3)
        if bestdiff is not None:
            self.console.write('bigtext "Balancing teams!"')
            self._move(bestblue, bestred, scores)
            self.console.say('^4Team skill difference was ^1%.2f^4, is now ^1%.2f' % (olddiff, bestdiff))
        else:
            # we couldn't beat the previous diff by moving only a few players, do a full skuffle
            self.cmd_paskuffle(data, client, cmd)

        self._forgetTeamContrib()
        self._balancing = False
        self._lastbal = now

    def cmd_paautoskuffle(self, data, client, cmd=None):
        """
        [<mode>] - Set the skill balancer mode.
        """
        modes = ["0-none", "1-advise", "2-autobalance", "3-autoskuffle"]
        if not data:
            mode = modes[self._skill_balance_mode]
            self.console.say("Skill balancer mode is '%s'" % mode)
            self.console.say("Options are %s" % ', '.join(modes))
            return

        mode = None

        try:
            mode = int(data)
        except ValueError:
            for i, m in enumerate(modes):
                if data in m:
                    mode = i

        if mode is not None and 0 <= mode <= 3:
            self._skill_balance_mode = mode
            self.console.say("Skill balancer mode is now '%s'" % modes[mode])
            self.skillcheck()
        else:
            self.console.say("Valid options are %s" % ', '.join(modes))

    def cmd_paswap(self, data, client, cmd=None):
        """
        <player1> [player2] - Swap two teams for 2 clients. If player2 is not specified, the admin
        using the command is swapped with player1. Doesn't work with spectators (exception for calling admin).
        """
        # check the input
        args = self._adminPlugin.parseUserCmd(data)
        # check for input. If none, exist with a message.
        if args:
            # check if the first player exists. If none, exit.
            client1 = self._adminPlugin.findClientPrompt(args[0], client)
            if not client1:
                return
        else:
            client.message("Invalid parameters, try !help paswap")
            return

        # if the specified player doesn't exist, exit.
        if args[1] is not None:
            client2 = self._adminPlugin.findClientPrompt(args[1], client)
            if not client2:
                return
        else:
            client2 = client

        if client1.team == b3.TEAM_SPEC:
            client.message("%s is a spectator! - Can't be swapped" % client1.name)
            return

        if client2.team == b3.TEAM_SPEC:
            client.message("%s is a spectator! - Can't be swapped" % client2.name)
            return

        if client1.team == client2.team:
            client.message("%s and %s are on the same team! - Swapped them anyway :p" % (client1.name, client2.name))
            return

        if client1.team == b3.TEAM_RED:
            self._move([client1], [client2])
        else:
            self._move([client2], [client1])

        # No need to send the message twice to the switching admin :-)

        if client1 != client:
            client1.message("^4You were swapped with %s by the admin" % client2.name)

        if client2 != client:
            client2.message("^4You were swapped with %s by the admin" % client1.name)

        client.message("^3Successfully swapped %s and %s" % (client1.name, client2.name))


    def cmd_pateams(self, data, client, cmd=None):
        """
        Force teambalancing (all gametypes!)
        The player with the least time in a team will be switched.
        """
        if self.teambalance():

            if self._teamsbalanced:
                client.message('^7Teams are already balanced')
            else:
                client.message('^7Teams are now balanced')
                self._teamsbalanced = True
        else:
            client.message('^7Teambalancing failed, please try a again in a few moments')

    def cmd_pavote(self, data, client=None, cmd=None):
        """
        <on/off/reset> - Set voting on, off or reset to original value at bot start.
        Setting vote on will set the vote back to the value when it was set off.
        """
        if not data:

            if client:
                client.message('^7Invalid or missing data, try !help pavote')
            else:
                self.debug('No data sent to cmd_pavote')

            return

        else:

            if data in ('on', 'off', 'reset'):
                if client:
                    client.message('^7Voting: ^1%s' % data)
                else:
                    self.debug('Voting: %s' % data)
            else:

                if client:
                    client.message('^7Invalid data, try !help pavote')
                else:
                    self.debug('Invalid data sent to cmd_pavote')

                return

        if data == 'off':
            curvalue = self.console.getCvar('g_allowvote').getInt()
            if curvalue != 0:
                self._lastvote = curvalue
            self.console.setCvar('g_allowvote', '0')
        elif data == 'on':
            self.console.setCvar('g_allowvote', '%s' % self._lastvote)
        elif data == 'reset':
            self.console.setCvar('g_allowvote', '%s' % self._origvote)

    def cmd_paversion(self, data, client, cmd=None):
        """
        This command identifies PowerAdminUrt version and creator
        """
        cmd.sayLoudOrPM(client, 'I am PowerAdminUrt version %s by %s' % (__version__, __author__))

    def cmd_paexec(self, data, client, cmd=None):
        """
        <configfile.cfg> - Execute a server configfile.
        (You must use the command exactly as it is!)
        """
        if not data:
            client.message('^7Missing data, try !help paexec')
            return

        if re.match('^[a-z0-9_.]+.cfg$', data, re.I):
            self.debug('executing configfile: %s' % data)
            result = self.console.write('exec %s' % data)
            cmd.sayLoudOrPM(client, result)
        else:
            self.error('%s is not a valid configfile' % data)

    def cmd_pacyclemap(self, data, client, cmd=None):
        """
        Cycle to the next map.
        (You can safely use the command without the 'pa' at the beginning)
        """
        time.sleep(1)
        self.console.write('cyclemap')

    def cmd_pamaprestart(self, data, client, cmd=None):
        """
        Restart the current map.
        (You can safely use the command without the 'pa' at the beginning)
        """
        self.console.write('map_restart')

    def cmd_pamapreload(self, data, client, cmd=None):
        """
        Reload the current map.
        (You can safely use the command without the 'pa' at the beginning)
        """
        self.console.write('reload')

    def cmd_paset(self, data, client, cmd=None):
        """
        <cvar> <value> - Set a server cvar to a certain value.
        (You must use the command exactly as it is!)
        """
        if not data:
            client.message('^7Invalid or missing data, try !help paset')
            return

        # are we still here? Let's write it to console
        args = data.split(' ', 1)
        cvar = args[0]
        value = args[1] if len(args) == 2 else ""
        self.console.setCvar(cvar, value)

    def cmd_paget(self, data, client, cmd=None):
        """
        <cvar> - Returns the value of a servercvar.
        (You must use the command exactly as it is! )
        """
        if not data:
            client.message('^7Invalid or missing data, try !help paget')
            return

        # are we still here? Let's write it to console
        getcvar = data.split(' ')
        getcvarvalue = self.console.getCvar('%s' % getcvar[0])
        cmd.sayLoudOrPM(client, '%s' % getcvarvalue)

    def cmd_pabigtext(self, data, client, cmd=None):
        """
        <message> - Print a Bold message on the center of all screens.
        (You can safely use the command without the 'pa' at the beginning)
        """
        if not data:
            client.message('^7Invalid or missing data, try !help pabigtext')
            return

        # are we still here? Let's write it to console
        self.console.write('bigtext "%s"' % data)

    def cmd_pamute(self, data, client, cmd=None):
        """
        <player> [<duration>] - Mute a player.
        (You can safely use the command without the 'pa' at the beginning)
        """
        # this will split the player name and the message
        args = self._adminPlugin.parseUserCmd(data)
        if args:
            # args[0] is the player id
            sclient = self._adminPlugin.findClientPrompt(args[0], client)
            if not sclient:
                # a player matchin the name was not found, a list of closest matches will be displayed
                # we can exit here and the user will retry with a more specific player
                return
        else:
            client.message('^7Invalid data, try !help pamute')
            return

        if sclient.maxLevel > client.maxLevel:
            client.message("^7You don't have enough privileges to mute this player")
            return

        if args[1] is not None and re.match('^([0-9]+)\s*$', args[1]):
            duration = int(args[1])
        else:
            duration = ''

        # are we still here? Let's write it to console
        self.console.write('mute %s %s' % (sclient.cid, duration))

    def cmd_papause(self, data, client, cmd=None):
        """
        <message> - Pause the game. Type again to resume
        """
        result = self.console.write('pause')
        cmd.sayLoudOrPM(client, result)

    def cmd_paslap(self, data, client, cmd=None):
        """
        <player> [<ammount>] - (multi)Slap a player.
        (You can safely use the command without the 'pa' at the beginning)
        """
        # this will split the player name and the message
        args = self._adminPlugin.parseUserCmd(data)
        if args:
            # args[0] is the player id
            sclient = self._adminPlugin.findClientPrompt(args[0], client)
            if not sclient:
                # a player matchin the name was not found, a list of closest matches will be displayed
                # we can exit here and the user will retry with a more specific player
                return
        else:
            client.message('^7Invalid data, try !help paslap')
            return

        if sclient.maxLevel >= self._slapSafeLevel and client.maxLevel < 90:
            client.message("^7You don't have enough privileges to slap an Admin")
            return

        if args[1]:

            try:
                x = int(args[1])
            except ValueError:
                client.message('^7Invalid data, try !help paslap')
                return

            if x in range(1, 26):
                thread.start_new_thread(self.multipunish, (x, sclient, client, 'slap'))
            else:
                client.message('^7Number of punishments out of range, must be 1 to 25')
        else:
            self.debug('Performing single slap...')
            self.console.write('slap %s' % sclient.cid)

    def cmd_panuke(self, data, client, cmd=None):
        """
        <player> [<ammount>] - (multi)Nuke a player.
        (You can safely use the command without the 'pa' at the beginning)
        """
        # this will split the player name and the message
        args = self._adminPlugin.parseUserCmd(data)
        if args:
            # args[0] is the player id
            sclient = self._adminPlugin.findClientPrompt(args[0], client)
            if not sclient:
                # a player matchin the name was not found, a list of closest matches will be displayed
                # we can exit here and the user will retry with a more specific player
                return
        else:
            client.message('^7Invalid data, try !help panuke')
            return

        if args[1]:

            try:
                x = int(args[1])
            except ValueError:
                client.message('^7Invalid data, try !help panuke')
                return

            if x in range(1, 26):
                thread.start_new_thread(self.multipunish, (x, sclient, client, 'nuke'))
            else:
                client.message('^7Number of punishments out of range, must be 1 to 25')
        else:
            self.debug('Performing single nuke...')
            self.console.write('nuke %s' % sclient.cid)

    def multipunish(self, x, sclient, client, cmd):
        self.debug('Entering multipunish...')
        #self.debug('x: %s, sclient.cid: %s, client.cid: %s, cmd: %s' %(x, sclient.cid, client.cid, cmd))
        c = 0
        while c < x:
            self.console.write('%s %s' % (cmd, sclient.cid))
            time.sleep(1)
            c += 1

    def cmd_paveto(self, data, client, cmd=None):
        """
        Veto current running Vote.
        (You can safely use the command without the 'pa' at the beginning)
        """
        self.console.write('veto')

    def cmd_paforce(self, data, client, cmd=None):
        """
        <player> <red/blue/spec/free> <lock> - Force a client to red/blue/spec or release the force (free)
        adding 'lock' will lock the player where it is forced to, default this is off.
        using 'all free' will release all locks.
        (You can safely use the command without the 'pa' at the beginning)
        """
        # this will split the player name and the message
        args = self._adminPlugin.parseUserCmd(data)
        if args:
            # check if all Locks should be released
            if args[0] == "all" and args[1] == "free":
                self.resetTeamLocks()
                self.console.say('All TeamLocks were released')
                return

            # args[0] is the player id
            sclient = self._adminPlugin.findClientPrompt(args[0], client)
            if not sclient:
                # a player matchin the name was not found, a list of closest matches will be displayed
                # we can exit here and the user will retry with a more specific player
                return
        else:
            client.message('^7Invalid data, try !help paforce')
            return

        if not len(args[1]):
            client.message('^7Missing data, try !help paforce')
            return

        tdata = args[1].split(' ')
        team = tdata[0]

        lock = False
        if len(tdata) > 1 and tdata[1] == 'lock':
            lock = True

        if team == 'spec' or team == 'spectator':
            team = 's'
        if team == 'b':
            team = 'blue'
        if team == 'r':
            team = 'red'

        if team == 's':
            teamname = 'spectator'
        else:
            teamname = team

        if team == 'free':
            if sclient.isvar(self, 'paforced'):
                sclient.message('^3Your have been released by the admin')
                client.message('^7%s ^3has been released' % sclient.name)
                sclient.delvar(self, 'paforced')
                return
            else:
                client.message('^3There was no lock on ^7%s' % sclient.name)

        elif team in ('red', 'blue', 's') and lock:
            sclient.message('^3Your are forced and locked to: ^7%s' % teamname)

        elif team in ('red', 'blue', 's'):
            sclient.message('^3Your are forced to: ^7%s' % teamname)

        else:
            client.message('^7Invalid data, try !help paforce')
            return

        if lock:
            sclient.setvar(self, 'paforced', team)  # s, red or blue
        else:
            sclient.delvar(self, 'paforced')

        # are we still here? Let's write it to console
        self.console.write('forceteam %s %s' % (sclient.cid, team))
        client.message('^3%s ^7forced to ^3%s' % (sclient.name, teamname))

    def cmd_paswapteams(self, data, client, cmd=None):
        """
        Swap current teams.
        (You can safely use the command without the 'pa' at the beginning)
        """
        # ignore automatic checking before giving the command
        self.ignoreSet(30)
        self.console.write('swapteams')

    def cmd_pashuffleteams(self, data, client, cmd=None):
        """
        Shuffle teams.
        (You can safely use the command without the 'pa' at the beginning)
        """
        # Ignore automatic checking before giving the command
        self.ignoreSet(30)
        self.console.write('shuffleteams')

    def cmd_pamoon(self, data, client, cmd=None):
        """
        Set moon mode <on/off>
        (You can safely use the command without the 'pa' at the beginning)
        """
        if not data or data not in ('on', 'off'):
            client.message('^7Invalid or missing data, try !help pamoon')
            return

        if data == 'on':
            self.console.setCvar('g_gravity', self._moon_on_gravity)
            self.console.say('^7Moon mode: ^2ON')
        elif data == 'off':
            self.console.setCvar('g_gravity', self._moon_off_gravity)
            self.console.say('^7Moon mode: ^1OFF')

    def cmd_papublic(self, data, client, cmd=None):
        """
        Set server public mode on/off.
        (You can safely use the command without the 'pa' at the beginning)
        """
        if not data or data not in ('on', 'off'):
            client.message('^7Invalid or missing data, try !help papublic')
            return

        if data == 'on':
            self.console.setCvar('g_password', '')
            self.console.say('^7public mode: ^2ON')
            self.console.queueEvent(self.console.getEvent('EVT_CLIENT_PUBLIC', '', client))

        elif data == 'off':
            newpassword = self._papublic_password
            if self._pass_lines is not None:
                i = random.randint(0, len(self._pass_lines) - 1)
                newpassword = self._pass_lines[i]

            for i in range(0, self._randnum):
                newpassword += str(random.randint(1, 9))

            self.debug('private password set to: %s' % newpassword)

            if newpassword is None:
                client.message('^1ERROR: ^7could not set public mode off because \
                                there is no password specified in the config file')
                return

            self.console.setCvar('g_password', '%s' % newpassword)
            self.console.say('^7public mode: ^1OFF')
            client.message('^7password is \'^4%s^7\'' % newpassword)
            client.message('^7type ^5!mapreload^7 to apply change')
            self.console.write('bigtext "^7Server going ^3PRIVATE ^7soon!!"')
            self.console.queueEvent(self.console.getEvent('EVT_CLIENT_PUBLIC', newpassword, client))

    def cmd_pamatch(self, data, client, cmd=None):
        """
        Set server match mode on/off
        (You can safely use the command without the 'pa' at the beginning)
        """
        if not data or data not in ('on', 'off'):
            client.message('^7Invalid or missing data, try !help pamatch')
            return

        if data == 'on':
            self._matchmode = True
            self.console.setCvar('g_matchmode', '1')
            self.console.say('^7Match mode: ^2ON')
            self.console.write('bigtext "^7MATCH starting soon !!"')
            for e in self._match_plugin_disable:
                self.debug('disabling plugin %s' % e)
                plugin = self.console.getPlugin(e)
                if plugin:
                    plugin.disable()
                    client.message('^7plugin %s disabled' % e)
            client.message('^7type ^5!mapreload^7 to apply change')
            self.console.write('bigtext "^7MATCH starting soon !!"')

        elif data == 'off':
            self._matchmode = False
            self.console.setCvar('g_matchmode', '0')
            self.console.say('^7Match mode: ^1OFF')

            for e in self._match_plugin_disable:
                self.debug('enabling plugin %s' % e)
                plugin = self.console.getPlugin(e)
                if plugin:
                    plugin.enable()
                    client.message('^7plugin %s enabled' % e)
            client.message('^7type ^5!mapreload^7 to apply change')

        self.set_configmode(None)

    def cmd_pagear(self, data, client=None, cmd=None):
        """
        [<all/none/reset/[+-](nade|snipe|spas|pistol|auto|negev)>] - Set allowed weapons.
        """
        cur_gear = self.console.getCvar('g_gear').getInt()
        if not data:

            if client:
                nade = (cur_gear & 1) != 1
                snipe = (cur_gear & 2) != 2
                spas = (cur_gear & 4) != 4
                pist = (cur_gear & 8) != 8
                auto = (cur_gear & 16) != 16
                nege = (cur_gear & 32) != 32

                self.console.write('^7current gear: %s (Nade:%d, Sniper:%d, Spas:%d, Pistol:%d, Auto:%d, Negev:%d)' %
                                   (cur_gear, nade, snipe, spas, pist, auto, nege))
            return

        else:

            if not data[:5] in ('all', 'none', 'reset',
                                '+nade', '+snip', '+spas', '+pist', '+auto', '+nege',
                                '-nade', '-snip', '-spas', '-pist', '-auto', '-nege'):
                if client:
                    client.message('^7Invalid data, try !help pagear')
                else:
                    self.debug('invalid data sent to cmd_pagear')

                return

        if data[:5] == 'all':
            self.console.setCvar('g_gear', '0')
        elif data[:5] == 'none':
            self.console.setCvar('g_gear', '63')
        elif data[:5] == 'reset':
            self.console.setCvar('g_gear', '%s' % self._origgear)
        else:

            if data[1:5] == 'nade':
                bit = 1
            elif data[1:5] == 'snip':
                bit = 2
            elif data[1:5] == 'spas':
                bit = 4
            elif data[1:5] == 'pist':
                bit = 8
            elif data[1:5] == 'auto':
                bit = 16
            elif data[1:5] == 'nege':
                bit = 32
            else:
                return

            if data[:1] == '+':
                self.console.setCvar('g_gear', '%s' % (cur_gear & (63 - bit)))
            elif data[:1] == '-':
                self.console.setCvar('g_gear', '%s' % (cur_gear | bit))

    def cmd_paffa(self, data, client, cmd=None):
        """
        Change game type to Free For All
        (You can safely use the command without the 'pa' at the beginning)
        """
        self.console.setCvar('g_gametype', '0')
        if client:
            client.message('^7game type changed to ^4Free For All')

        self.set_configmode('ffa')

    def cmd_patdm(self, data, client, cmd=None):
        """
        Change game type to Team Death Match
        (You can safely use the command without the 'pa' at the beginning)
        """
        self.console.setCvar('g_gametype', '3')
        if client:
            client.message('^7game type changed to ^4Team Death Match')

        self.set_configmode('tdm')

    def cmd_pats(self, data, client, cmd=None):
        """
        Change game type to Team Survivor
        (You can safely use the command without the 'pa' at the beginning)
        """
        self.console.setCvar('g_gametype', '4')
        if client:
            client.message('^7game type changed to ^4Team Survivor')

        self.set_configmode('ts')

    def cmd_paftl(self, data, client, cmd=None):
        """
        Change game type to Follow The Leader
        (You can safely use the command without the 'pa' at the beginning)
        """
        self.console.setCvar('g_gametype', '5')
        if client:
            client.message('^7game type changed to ^4Follow The Leader')

        self.set_configmode('ftl')

    def cmd_pacah(self, data, client, cmd=None):
        """
        Change game type to Capture And Hold
        (You can safely use the command without the 'pa' at the beginning)
        """
        self.console.setCvar('g_gametype', '6')
        if client:
            client.message('^7game type changed to ^4Capture And Hold')

        self.set_configmode('cah')

    def cmd_pactf(self, data, client, cmd=None):
        """
        Change game type to Capture The Flag
        (You can safely use the command without the 'pa' at the beginning)
        """
        self.console.setCvar('g_gametype', '7')
        if client:
            client.message('^7game type changed to ^4Capture The Flag')

        self.set_configmode('ctf')

    def cmd_pabomb(self, data, client, cmd=None):
        """
        Change game type to Bomb
        (You can safely use the command without the 'pa' at the beginning)
        """
        self.console.setCvar('g_gametype', '8')
        if client:
            client.message('^7game type changed to ^4Bomb')

        self.set_configmode('bomb')

    def cmd_paident(self, data, client=None, cmd=None):
        """
        <name> - show the ip and guid of a player
        (You can safely use the command without the 'pa' at the beginning)
        """
        args = self._adminPlugin.parseUserCmd(data)
        if not args:
            cmd.sayLoudOrPM(client, 'Your id is ^2@%s' % client.id)
            return

        # args[0] is the player id
        sclient = self._adminPlugin.findClientPrompt(args[0], client)
        if not sclient:
            # a player matching the name was not found, a list of closest matches will be displayed
            # we can exit here and the user will retry with a more specific player
            return

        if client.maxLevel < self._full_ident_level:
            cmd.sayLoudOrPM(client, '%s ^4@%s ^2%s' % (self.console.formatTime(self.console.time()),
                                                       sclient.id, sclient.exactName))
        else:
            cmd.sayLoudOrPM(client, '%s ^4@%s ^2%s ^2%s ^2%s' % (self.console.formatTime(self.console.time()),
                                                                 sclient.id, sclient.exactName, sclient.ip,
                                                                 self.console.formatTime(sclient.timeAdd)))

########################################################################################################################
#---Teambalance Mechanism-----------------------------------------------------------------------------------------------
#
#   /g_redteamlist en /g_blueteamlist
#   they return which clients are in the red or blue team
#   not with numbers but characters (clientnum 0 = A, clientnum 1 = B, etc.

    def onTeamChange(self, team, client):
        #store the time of teamjoin for autobalancing purposes
        client.setvar(self, 'teamtime', self.console.time())
        self.verbose('client variable teamtime set to: %s' % client.var(self, 'teamtime').value)
        # remember current stats so we can tell how the player
        # is performing on the new team
        self._saveTeamvars(client)

        if not self._matchmode and client.isvar(self, 'paforced'):
            forcedteam = client.var(self, 'paforced').value
            if team != b3.TEAM_UNKNOWN and team != self.console.getTeam(forcedteam):
                self.console.write('forceteam %s %s' % (client.cid, forcedteam))
                client.message('^1You are LOCKED! You are NOT allowed to switch!')
                self.verbose('%s was locked and forced back to %s' % (client.name, forcedteam))
                # Break out of this function, nothing more to do here
            return None

        # 10/21/2008 - 1.4.0b9 - mindriot
        # 10/23/2008 - 1.4.0b12 - mindriot
        if self._team_change_force_balance_enable and not self._matchmode:

            # if the round just started, don't do anything
            if self.ignoreCheck():
                return None

            if self.isEnabled() and not self._balancing:
                # set balancing flag
                self._balancing = True
                self.verbose('teamchanged cid: %s, name: %s, team: %s' % (client.cid, client.name, team))

                # are we supposed to be balanced?
                if client.maxLevel >= self._tmaxlevel:
                    # done balancing
                    self._balancing = False
                    return None

                # did player join spectators?
                if team == b3.TEAM_SPEC:
                    self.verbose('player joined specs')
                    # done balancing
                    self._balancing = False
                    return None
                elif team == b3.TEAM_UNKNOWN:
                    self.verbose('team is unknown')
                    # done balancing
                    self._balancing = False
                    return None

                # check if player was allowed to join this team
                if not self.countteams():
                    self._balancing = False
                    self.error('aborting teambalance: counting teams failed!')
                    return False
                if abs(self._teamred - self._teamblue) <= self._teamdiff:
                    # teams are balanced
                    self.verbose('teams are balanced, red: %s, blue: %s' % (self._teamred, self._teamblue))
                    # done balancing
                    self._balancing = False
                    return None
                else:
                    # teams are not balanced
                    self.verbose('teams are NOT balanced, red: %s, blue: %s' % (self._teamred, self._teamblue))

                    # switch is not allowed, so this should be a client suicide, not a legit switch.
                    # added as anti stats-harvest-exploit measure. One suicide is added as extra penalty for harvesting.
                    if self.console:

                        self.verbose('Applying Teamswitch penalties')


                        self.console.queueEvent(self.console.getEvent('EVT_CLIENT_SUICIDE',
                                                                      (100, 'penalty', 'body', 'Team_Switch_Penalty'),
                                                                      client,
                                                                      client))

                        self.console.queueEvent(self.console.getEvent('EVT_CLIENT_SUICIDE',
                                                                      (100, 'penalty', 'body', 'Team_Switch_Penalty'),
                                                                      client,
                                                                      client))

                        plugin = self.console.getPlugin('xlrstats')
                        if plugin:
                            client.message('Switching made teams unfair. Points where deducted from your stats \
                                            as a penalty!')

                    if self._teamred > self._teamblue:
                        # join the blue team
                        self.verbose('forcing %s to the Blue team' % client.name)
                        self.console.write('forceteam %s blue' % client.cid)
                    else:
                        # join the red team
                        self.verbose('forcing %s to the Red team' % client.name)
                        self.console.write('forceteam %s red' % client.cid)

                # done balancing
                self._balancing = False

        else:
            self.debug('onTeamChange DISABLED')

        return None

    def countteams(self):
        try:
            self._teamred = len(self.console.getCvar('g_redteamlist').getString())
            self._teamblue = len(self.console.getCvar('g_blueteamlist').getString())
            return True
        except Exception:
            return False

    def _getGameType(self):
        # g_gametype //0 = FreeForAll = dm, 3 = TeamDeathMatch = tdm, 4 = Team Survivor = ts,
        # 5 = Follow the Leader = ftl, 6 = Capture and Hold = cah, 7 = Capture The Flag = ctf, 8 = Bombmode = bm

        # 10/22/2008 - 1.4.0b10 - mindriot
        # if gametype is unknown when B3 is started in the middle of a game
        if self.console.game.gameType is None:
            try:
                # find and set current gametype
                self.console.game.gameType = self.console.defineGameType(self.console.getCvar('g_gametype').getString())
                self.debug('current gametype found - changed to (%s)', self.console.game.gameType)
            except Exception:
                self.debug('unable to determine current gametype - remains at (%s)', self.console.game.gameType)

        return self.console.game.gameType

    def teamcheck(self):
        gametype = self._getGameType()

        # run teambalance only if current gametype
        # is in autobalance_gametypes list
        if not gametype in self._autobalance_gametypes_array:
            self.debug('current gametype (%s) is not specified in autobalance_gametypes - teambalancer disabled',
                       gametype)
            return None

        if self._skill_balance_mode != 0:
            self.debug('skill balancer is active, not performing classic teamcheck')

        if self.console.time() > self._ignoreTill:
            self.teambalance()

        return None

    def teambalance(self):
        if self.isEnabled() and not self._balancing and not self._matchmode:
            # set balancing flag
            self._balancing = True
            self.verbose('checking for balancing')

            if not self.countteams():
                self._balancing = False
                self.warning('aborting teambalance: counting teams failed!')
                return False

            if abs(self._teamred - self._teamblue) <= self._teamdiff:
                # teams are balanced
                self._teamsbalanced = True
                self.verbose('Teambalance: teams are balanced, red: %s, blue: %s (diff: %s)' % (
                             self._teamred, self._teamblue, self._teamdiff))
                # done balancing
                self._balancing = False
                return True
            else:
                #teams are not balanced
                self._teamsbalanced = False
                self.verbose('Teambalance: teams are NOT balanced, red: %s, blue: %s (diff: %s)' % (
                             self._teamred, self._teamblue, self._teamdiff))
                if self._announce == 1:
                    self.console.write('say Autobalancing Teams!')
                elif self._announce == 2:
                    self.console.write('bigtext "Autobalancing Teams!"')

                if self._teamred > self._teamblue:
                    newteam = 'blue'
                    oldteam = b3.TEAM_RED
                else:
                    newteam = 'red'
                    oldteam = b3.TEAM_BLUE

                self.verbose('smaller team is: %s' % newteam)

                # endless loop protection
                count = 25
                while abs(self._teamred - self._teamblue) > self._teamdiff and count > 0:
                    stime = self.console.upTime()
                    self.verbose('uptime bot: %s' % stime)
                    forceclient = None
                    clients = self.console.clients.getList()
                    for c in clients:
                        if not c.isvar(self, 'teamtime'):
                            self.debug('client has no variable teamtime')
                            # 10/22/2008 - 1.4.0b11 - mindriot
                            # store the time of teamjoin for autobalancing purposes
                            c.setvar(self, 'teamtime', self.console.time())
                            self.verbose('client variable teamtime set to: %s' % c.var(self, 'teamtime').value)

                        if self.console.time() - c.var(self, 'teamtime').value < stime and \
                           c.team == oldteam and c.maxLevel < self._tmaxlevel and not c.isvar(self, 'paforced'):
                            forceclient = c.cid
                            stime = self.console.time() - c.var(self, 'teamtime').value

                    if forceclient:
                        if newteam:
                            self.verbose('forcing client: %s to team: %s' % (forceclient, newteam))
                            self.console.write('forceteam %s %s' % (forceclient, newteam))
                        else:
                            self.debug('no new team to force to')
                    else:
                        self.debug('No client to force')

                    count -= 1
                    # recount the teams... do we need to balance once more?
                    if not self.countteams():
                        self._balancing = False
                        self.error('aborting teambalance: counting teams failed!')
                        return False

                    # 10/28/2008 - 1.4.0b13 - mindriot
                    self.verbose('Teambalance: red: %s, blue: %s (diff: %s)' %
                                 (self._teamred, self._teamblue, self._teamdiff))

                    if self._teamred > self._teamblue:
                        newteam = 'blue'
                        oldteam = b3.TEAM_RED
                    else:
                        newteam = 'red'
                        oldteam = b3.TEAM_BLUE

                    self.verbose('smaller team is: %s' % newteam)

            # done balancing
            self._balancing = False

        return True

    def resetTeamLocks(self):
        if self.isEnabled():
            clients = self.console.clients.getList()
            for c in clients:
                if c.isvar(self, 'paforced'):
                    c.delvar(self, 'paforced')
            self.debug('TeamLocks Released')
        return None

########################################################################################################################
#---Dupes/Forbidden Names Mechanism-------------------------------------------------------------------------------------

    def namecheck(self):
        if self._matchmode:
            return None

        self.debug('checking names')
        d = {}
        if self.isEnabled() and self.console.time() > self._ignoreTill:
            for player in self.console.clients.getList():
                if not player.name in d.keys():
                    d[player.name] = [player.cid]
                else:
                    #l = d[player.name]
                    #l.append(cid)
                    #d[player.name]=l
                    d[player.name].append(player.cid)

            for pname, cidlist in d.items():
                if self._checkdupes and len(cidlist) > 1:
                    self.info("warning players %s for using the same name" %
                              (", ".join(["%s <%s> @%s" %
                                         (c.exactName, c.cid, c.id) for c in
                                          map(self.console.clients.getByCID, cidlist)])))

                    for cid in cidlist:
                        client = self.console.clients.getByCID(cid)
                        self._adminPlugin.warnClient(client, 'badname')

                if self._checkunknown and pname == self.console.stripColors('New UrT Player'):
                    for cid in cidlist:
                        client = self.console.clients.getByCID(cid)
                        self.info("warning player %s <%s> @%s for using forbidden name 'New UrT Player'" %
                                  (client.exactName, client.cid, client.id))
                        self._adminPlugin.warnClient(client, 'badname')

                if self._checkbadnames and pname == 'all':
                    for cid in cidlist:
                        client = self.console.clients.getByCID(cid)
                        self.info("warning player %s <%s> @%s for using forbidden name 'all'" %
                                  (client.exactName, client.cid, client.id))
                        self._adminPlugin.warnClient(client, 'badname')

        return None

    def onNameChange(self, name, client):
        if self.isEnabled() and self._checkchanges and client.maxLevel < 9:
            if not client.isvar(self, 'namechanges'):
                client.setvar(self, 'namechanges', 0)
                client.setvar(self, 'savedname', self.clean(client.exactName))

            cleanedname = self.clean(client.exactName)
            ## also check if the name is ending with '_<slot num>' (happens with clients having deconnections)
            if cleanedname.endswith('_' + str(client.cid)):
                cleanedname = cleanedname[:-len('_' + str(client.cid))]

            if cleanedname != client.var(self, 'savedname').value:
                n = client.var(self, 'namechanges').value + 1
                oldname = client.var(self, 'savedname').value
                client.setvar(self, 'savedname', cleanedname)
                self.debug('%s changed name %s times. His name was %s' % (cleanedname, n, oldname))
                if n > self._checkallowedchanges:
                    client.kick('Too many namechanges!')
                else:
                    client.setvar(self, 'namechanges', n)
                    if self._checkallowedchanges - n < 4:
                        r = self._checkallowedchanges - n
                        client.message('^1WARNING:^7 ^2%s^7 more namechanges allowed during this map!' % r)

        return None

    def resetNameChanges(self):
        if self.isEnabled() and self._checkchanges:
            clients = self.console.clients.getList()
            for c in clients:
                if c.isvar(self, 'namechanges'):
                    c.setvar(self, 'namechanges', 0)
            self.debug('Namechanges Reset')
        return None


########################################################################################################################
#---Vote delayer at round start-----------------------------------------------------------------------------------------

    def votedelay(self, data=None):
        if not data:
            data = 'on'
        self.cmd_pavote(data)

########################################################################################################################
#---Spectator Checking--------------------------------------------------------------------------------------------------

    def speccheck(self):
        if self.isEnabled() and self._g_maxGameClients == 0 and not self._matchmode:
            self.debug('checking for idle spectators')
            clients = self.console.clients.getList()
            if len(clients) < self._smaxplayers:
                self.verbose('clients online (%s) < maxplayers (%s), ignoring' % (len(clients), self._smaxplayers))
                return None

            for c in clients:
                if not c.isvar(self, 'teamtime'):
                    self.debug('client %s has no variable teamtime' % c)
                    # 10/22/2008 - 1.4.0b11 - mindriot
                    # store the time of teamjoin for autobalancing purposes
                    c.setvar(self, 'teamtime', self.console.time())
                    self.verbose('client variable teamtime set to: %s' % c.var(self, 'teamtime').value)

                if c.maxLevel >= self._smaxlevel:
                    self.debug('%s is allowed to idle in spec' % c.name)
                    continue
                elif c.isvar(self, 'paforced'):
                    self.debug('%s is forced by an admin' % c.name)
                    continue
                elif c.team == b3.TEAM_SPEC and (self.console.time() - c.var(self, 'teamtime').value) > \
                        (self._smaxspectime * 60):
                    self.debug('warning %s for speccing on full server' % c.name)
                    self._adminPlugin.warnClient(c, 'spec')

        return None

########################################################################################################################
#---Bot support---------------------------------------------------------------------------------------------------------

    def botsupport(self, data=None):
        self.debug('checking for bot support')
        if self.isEnabled() and not self._matchmode:

            try:
                test = self.console.game.mapName
            except AttributeError:
                self.debug('mapName not yet available')
                return None

            if not self._botenable:
                return None

            for m in self._botmaps:
                if m == self.console.game.mapName:
                    # we got ourselves a winner
                    self.debug('enabling bots for this map: %s' % self.console.game.mapName)
                    self.botsenable()

        return None

    def botsdisable(self):
        self.debug('disabling the bots')
        self.console.write('set bot_minplayers 0')

    def botsenable(self):
        self.debug('enabling the bots')
        self.console.write('set bot_minplayers %s' % self._botminplayers)

########################################################################################################################
#---Headshot Counter----------------------------------------------------------------------------------------------------

    def setupVars(self, client):
        if not client.isvar(self, 'totalhits'):
            client.setvar(self, 'totalhits', 0.00)
        if not client.isvar(self, 'totalhitted'):
            client.setvar(self, 'totalhitted', 0.00)
        if not client.isvar(self, 'headhits'):
            client.setvar(self, 'headhits', 0.00)
        if not client.isvar(self, 'headhitted'):
            client.setvar(self, 'headhitted', 0.00)
        if not client.isvar(self, 'helmethits'):
            client.setvar(self, 'helmethits', 0.00)
        if not client.isvar(self, 'torsohitted'):
            client.setvar(self, 'torsohitted', 0.00)

        client.setvar(self, 'hitvars', True)
        self.debug('ClientVars set up for %s' % client.name)

    def resetVars(self):
        if self.isEnabled() and self._hsenable:
            clients = self.console.clients.getList()
            for c in clients:
                if c.isvar(self, 'hitvars'):
                    c.setvar(self, 'totalhits', 0.00)
                    c.setvar(self, 'totalhitted', 0.00)
                    c.setvar(self, 'headhits', 0.00)
                    c.setvar(self, 'headhitted', 0.00)
                    c.setvar(self, 'helmethits', 0.00)
                    c.setvar(self, 'torsohitted', 0.00)

            self.debug('ClientVars Reset')
        return None

    def headshotcounter(self, attacker, victim, data):
        if self.isEnabled() and self._hsenable and attacker.isvar(self, 'hitvars') and \
           victim.isvar(self, 'hitvars') and not self._matchmode:
            headshots = 0
            #damage = int(data[0])
            weapon = data[1]
            hitloc = data[2]

            # set totals
            t = attacker.var(self, 'totalhits').value + 1
            attacker.setvar(self, 'totalhits', t)
            t = victim.var(self, 'totalhitted').value + 1
            victim.setvar(self, 'totalhitted', t)

            # headshots... no helmet!
            if hitloc == self._hitlocations['HL_HEAD']:
                t = attacker.var(self, 'headhits').value + 1
                attacker.setvar(self, 'headhits', t)
                t = victim.var(self, 'headhitted').value + 1
                victim.setvar(self, 'headhitted', t)

            # helmethits
            elif hitloc == self._hitlocations['HL_HELMET']:
                t = attacker.var(self, 'helmethits').value + 1
                attacker.setvar(self, 'helmethits', t)

            # torso... no kevlar!
            elif hitloc == self._hitlocations['HL_TORSO']:
                t = victim.var(self, 'torsohitted').value + 1
                victim.setvar(self, 'torsohitted', t)

            # announce headshots
            if self._hsall and hitloc in (self._hitlocations['HL_HEAD'], self._hitlocations['HL_HELMET']):
                headshots = attacker.var(self, 'headhits').value + attacker.var(self, 'helmethits').value
                hstext = 'headshots'
                if headshots == 1:
                    hstext = 'headshot'

                percentage = int(headshots / attacker.var(self, 'totalhits').value * 100)
                if self._hspercent and headshots > 5 and percentage > self._hspercentmin:
                    message = ('^2%s^7: %s %s! ^7(%s percent)' % (attacker.name, int(headshots), hstext, percentage))
                else:
                    message = ('^2%s^7: %s %s!' % (attacker.name, int(headshots), hstext))

                if self._hsbroadcast:
                    self.console.write(message)
                else:
                    self.console.say(message)

            # wear a helmet!
            if self._hswarnhelmet and \
                    victim.connections < 20 and \
                    victim.var(self, 'headhitted').value == self._hswarnhelmetnr and \
                    hitloc == 0:
                victim.message('You were hit in the head %s times! Consider wearing a helmet!' % self._hswarnhelmetnr)

            # wear kevlar!
            if self._hswarnkevlar and \
                    victim.connections < 20 and \
                    victim.var(self, 'torsohitted').value == self._hswarnkevlarnr and \
                    hitloc == 2:
                victim.message('You were hit in the torso %s times! Wearing kevlar will reduce \
                                your number of deaths!' % self._hswarnkevlarnr)

        return None


########################################################################################################################
#---Rotation Manager----------------------------------------------------------------------------------------------------

    def adjustrotation(self, delta):
        # if the round just started, don't do anything
        if self.console.time() < self._dontcount:
            return None

        if delta == +1:
            if self._playercount > (self._switchcount2 + self._hysteresis):
                self.setrotation(3)
            elif self._playercount > (self._switchcount1 + self._hysteresis):
                self.setrotation(2)
            else:
                self.setrotation(1)

        elif delta == -1 or delta == 0:
            if self._playercount < (self._switchcount1 + (delta * self._hysteresis)):
                self.setrotation(1)
            elif self._playercount < (self._switchcount2 + (delta * self._hysteresis)):
                self.setrotation(2)
            else:
                self.setrotation(3)

        else:
            self.error('invalid delta passed to adjustrotation')

        return None

    def setrotation(self, newrotation):
        if not self._gamepath or \
                not self._rotation_small or \
                not self._rotation_medium or \
                not self._rotation_large or \
                not self._mapchanged:
            return None

        if newrotation == self._currentrotation:
            return None

        if newrotation == 1:
            rotname = "small"
            rotation = self._rotation_small
        elif newrotation == 2:
            rotname = "medium"
            rotation = self._rotation_medium
        elif newrotation == 3:
            rotname = "large"
            rotation = self._rotation_large
        else:
            self.error('Error: Invalid newrotation passed to setrotation.')
            return None

        self.debug('Adjusting to %s mapRotation' % rotname)
        self.console.setCvar('g_mapcycle', rotation)
        self._currentrotation = newrotation

    def recountplayers(self):
        # reset, recount and set a rotation
        self._oldplayercount = self._playercount
        self._playercount = 0

        for p in self.console.clients.getList():
            self._playercount += 1

        self.debug('Initial PlayerCount: %s' % self._playercount)

        if self._oldplayercount == -1:
            self.adjustrotation(0)
        elif self._playercount > self._oldplayercount:
            self.adjustrotation(+1)
        elif self._playercount < self._oldplayercount:
            self.adjustrotation(-1)

########################################################################################################################
#--Support Functions----------------------------------------------------------------------------------------------------

    def clean(self, data):
        return re.sub(self._reClean, '', data)[:20]

    def ignoreSet(self, data=60):
        """
        Sets the ignoreflag for an amount of seconds
        self._ignoreTill is a plugin flag that holds a time which ignoreCheck checks against
        """
        self._ignoreTill = self.console.time() + data
        return None

    def ignoreDel(self):
        self._ignoreTill = 0
        return None

    def ignoreCheck(self):
        """
        Tests if the ignore flag is set, to disable certain automatic functions when unwanted
        Returns True if the functionality should be ignored
        """
        if self._ignoreTill - self.console.time() > 0:
            return True
        else:
            return False

########################################################################################################################
#---Rcon commands------by:FSK405|Fear-----------------------------------------------------------------------------------
#   setnextmap <mapname>
#   respawngod <seconds>
#   respawndelay <seconds>
#   caplimit <caps>
#   fraglimit <frags>
#   waverespawns <on/off>
#   bluewave <seconds>
#   redwave <seconds>
#   timelimit <minutes>
#   hotpotato <minutes>

    def cmd_pawaverespawns(self, data, client, cmd=None):
        """
        <on/off> - Set waverespawns on, or off.
        """
        if not data or data not in ('on', 'off'):
            client.message('^7Invalid or missing data, try !help pawaverespawns')
            return

        if data == 'on':
            self.console.setCvar('g_waverespawns', '1')
            self.console.say('^7Wave Respawns: ^2ON')
        elif data == 'off':
            self.console.setCvar('g_waverespawns', '0')
            self.console.say('^7Wave Respawns: ^1OFF')

    def cmd_pasetnextmap(self, data, client=None, cmd=None):
        """
        <mapname> - Set the nextmap (partial map name works)
        """
        if not data:
            client.message('^7Invalid or missing data, try !help pasetnextmap')
            return

        match = self.console.getMapsSoundingLike(data)
        if isinstance(match, basestring):
            mapname = match
            self.console.setCvar('g_nextmap', mapname)
            if client:
                client.message('^7nextmap set to %s' % mapname)
        elif isinstance(match, list):
            client.message('do you mean : %s ?' % string.join(match[:5], ', '))
        else:
            client.message('^7cannot find any map like [^4%s^7]' % data)

    def cmd_parespawngod(self, data, client, cmd=None):
        """
        <seconds> - Set the respawn protection in seconds.
        """
        if not data:
            client.message('^7Missing data, try !help parespawngod')
            return

        self.console.setCvar('g_respawnProtection', data)

    def cmd_parespawndelay(self, data, client, cmd=None):
        """
        <seconds> - Set the respawn delay in seconds.
        """
        if not data:
            client.message('^7Missing data, try !help parespawndelay')
            return

        self.console.setCvar('g_respawnDelay', data)

    def cmd_pacaplimit(self, data, client, cmd=None):
        """
        <caps> - Set the ammount of flagcaps before map is over.
        """
        if not data:
            client.message('^7Missing data, try !help pacaplimit')
            return

        self.console.setCvar('capturelimit', data)

    def cmd_patimelimit(self, data, client, cmd=None):
        """
        <minutes> - Set the minutes before map is over.
        """
        if not data:
            client.message('^7Missing data, try !help patimelimit')
            return

        self.console.setCvar('timelimit', data)

    def cmd_pafraglimit(self, data, client, cmd=None):
        """
        <frags> - Set the ammount of points to be scored before map is over.
        """
        if not data:
            client.message('^7Missing data, try !help pafraglimit')
            return

        self.console.setCvar('fraglimit', data)

    def cmd_pabluewave(self, data, client, cmd=None):
        """
        <seconds> - Set the blue wave respawn time.
        """
        if not data:
            client.message('^7Missing data, try !help pabluewave')
            return False

        self.console.setCvar('g_bluewave', data)

    def cmd_paredwave(self, data, client, cmd=None):
        """
        <seconds> - Set the red wave respawn time.
        """
        if not data:
            client.message('^7Missing data, try !help paredwave')
            return False

        self.console.setCvar('g_redwave', data)

    def cmd_pahotpotato(self, data, client, cmd=None):
        """
        <minutes> - Set the flag explode time.
        """
        if not data:
            client.message('^7Missing data, try !help pahotpotato')
            return False

        self.console.setCvar('g_hotpotato', data)

#------------- SGT --------------------------------------------

    def cmd_pasetwave(self, data, client, cmd=None):
        """
        <seconds> - Set the wave respawn time for both teams.
        """
        if not data:
            client.message('^7Missing data, try !help pasetwave')
            return

        self.console.setCvar('g_bluewave', data)
        self.console.setCvar('g_redwave', data)

    def cmd_pasetgravity(self, data, client, cmd=None):
        """
        <value> - Set the gravity value. default = 800 (less means less gravity)
        """
        if not data:
            client.message('^7Missing data, try !help pasetgravity')
            return

        if data == 'def':
            data = 800

        self.console.setCvar('g_gravity', data)
        client.message('^7Gravity: %s' % data)

    def set_configmode(self, mode=None):
        if mode:
            modestring = 'mode_%s' % mode
            if modestring in self._gameconfig:
                cfgfile = self._gameconfig.get(modestring)
                filename = os.path.join(self.console.game.fs_homepath, self.console.game.fs_game, cfgfile)
                if os.path.isfile(filename):
                    self.debug('executing config file: %s', cfgfile)
                    self.console.write('exec %s' % cfgfile)

        if self._matchmode:
            cfgfile = self._gameconfig.get('matchon', None)
        else:
            cfgfile = self._gameconfig.get('matchoff', None)

        if cfgfile:
            filename = os.path.join(self.console.game.fs_homepath, self.console.game.fs_game, cfgfile)
            if os.path.isfile(filename):
                self.debug('executing configfile: %s', cfgfile)
                self.console.write('exec %s' % cfgfile)