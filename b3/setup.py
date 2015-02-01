#!/usr/bin/env python
#
# BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2009 Mark "xlr8or" Weirath
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
# 2010/03/21 - 0.2.1 - Courgette      - fix bug on config path which showed up only when run as a .exe
# 2010/03/27 - 0.2.2 - xlr8or         - minor improvements, added port to db-conn, default value for yes/no in add_plugin
# 2010/04/17 - 0.3   - Courgette      - remove plugin priority related code to follow with parser.py v1.16 changes
# 2010/04/27 - 0.4   - Bakes          - added proper BFBC2 support to the setup wizard
#                                     - changed censor and spamcontrol plugins to be added before admin. This means that
#                                       people who spam or swear in admin commands are warned, rather than the event just
#                                       being handled in the admin plugin and veto'd elsewhere
# 2010/10/11 - 0.5   - xlr8or         - added MOH support
# 2010/11/07 - 0.5.1 - GrosBedo       - edited default messages settings
# 2010/11/07 - 0.5.2 - GrosBedo       - added default values of lines_per_second and delay
#                                     - added more infos about the http access for gamelog
# 2011/02/06 - 0.6   - xlr8or         - setup now reads values from an existing config or a distribution example
#                                     - added COD7 support
# 2011/03/10 - 0.7   - xlr8or         - don't let setup fail when SQL file cannot be opened
# 2011/03/12 - 0.8   - xlr8or         - better handling of execution of b3.sql
#                                     - bugfix in message section
#                                     - use tempfile until setup is completed
# 2011/05/19 - 1.0   - xlr8or         - added Update class
#                                     - version 1.0 merged into master branch (for B3 v1.6.0 release)
# 2011/11/12 - 1.1   - courgette      - can install external plugins having a module defined as a directory instead
#                                       as as a python file
# 2012/01/08 - 1.2   - xlr8or         - added: xlrstats-update-2.6.1.sql
#                                     - fixed bug that would not update the xlrstats tables
# 2012/10/19 - 1.3   - Courgette      - added: Ravaged game
# 2012/10/24 - 1.4   - Courgette      - added: iourt42 custom settings
# 2012/10/31 - 1.5   - Courgette      - added: arma2 support
# 2013/07/17 - 1.6   - 82ndAB.Bravo17 - added: arma3 support
# 2013/08/03 - 1.7   - 82ndAB.Bravo17 - added: Chivalry Medieval Warfare support
# 2014/04/01 - 1.8   - Courgette      - added: Insurgency support
# 2014/07/21 - 1.9   - Fenix          - syntax cleanup
# 2014/12/18 - 1.9.1 - Fenix          - switched from MySQLdb to pymysql
# 2014/12/19 - 1.9.2 - Ansa89         - allow use of python-mysql.connector instead of pymysql for debian wheezy
# 2015/01/20 - 1.10  - Fenix          - removed SQL file import: storage module already provides database table generation
#                                       when they are found to be missing
#                                     - changed add_set and raw_default to accept a reference to a function used to validate
#                                       input data (return True when the value is accepted, false otherwise): raw_default
#                                       will also keep asking for the same value until an acceptable one is inserted by
#                                       the user (also for allow_blank)
#                                     - removed extplugins download: will make a B3 plugin to install third party plugins
#                                     - make use of the shipped storage module to execute SQL queries in Update class
#                                     - revamped setup layout
# 2015/01/22 - 1.11  - Fenix          - generate .ini configuration file instead of .xml

# This section is DoxuGen information. More information on how to comment your code
# is available at http://wiki.bigbrotherbot.net/doku.php/customize:doxygen_rules

# FIXME: UGLY HACK WHICH LET US USE THE STORAGE MODULE SHIPPED WITH B3 INSTEAD OF ADDING DUPLICATED CODE
import b3
b3.TEAM_UNKNOWN = -1

import storage
import functions
import os
import pkg_handler
import platform
import sys
import time

from b3.storage import PROTOCOLS as DB_PROTOCOLS
from config import CfgConfigParser
from distutils import version
from functions import splitDSN
from timezones import timezones
from urlparse import urlsplit


__author__ = 'xlr8or'
__version__ = pkg_handler.version(__name__)
modulePath = pkg_handler.resource_directory(__name__)

_buffer = ''
_indentation = '    '


class Setup(object):

    _pver = sys.version.split()[0]
    _indentation = '    '
    _configpath = ''
    _config = r'b3/conf/b3.ini'
    _template = ''
    _templatevar = ''
    _buffer = ''
    _equalength = 20

    _supported_parsers = ['arma2', 'arma3', 'bfbc2', 'bf3', 'bf4', 'moh', 'mohw', 'cod', 'cod2', 'cod4', 'cod5', 'cod6',
                          'cod7', 'cod8', 'iourt41', 'iourt42', 'et', 'etpro', 'altitude', 'oa081', 'smg', 'smg11',
                          'sof2', 'wop', 'wop15', 'chiv', 'csgo', 'homefront', 'insurgency', 'ravaged', 'ro2']

    _pb_supported_parsers = ['cod', 'cod2', 'cod4', 'cod5', 'cod6', 'cod7', 'cod8']
    _frostbite = ['bfbc2', 'moh', 'bf3', 'bf4']

    # those will be set later when using 'add_set'
    _set = {}

    tree = None
    autoinstallplugins = 'yes'
    installextplugins = 'yes'

    def __init__(self, conf=None):
        """
        Object constructor.
        :param conf: The B3 configuration file instance
        """
        if conf:
            self._config = os.path.normpath(conf)
        elif self.getB3Path() != "":
            self._config = os.path.join(self.getB3Path(), 'conf', 'b3.ini')

        self.introduction()
        self.clearscreen()

        self._output_file = self.raw_default("Location of the new configuration file", self._config)

        # creating backup if needed
        self.backup_file(self._output_file)
        self.run_setup()

        raise SystemExit('Restart B3 or reconfigure B3 using option: -s')

    def run_setup(self):
        """
        The main function that handles the setup steps.
        """
        ini = CfgConfigParser(allow_no_value=True)

        # B3 settings
        self.add_buffer("""-------------------------- B3 SPECIFIC SETTINGS -------------------------------\n""")

        ini.add_section('b3')
        self.add_value(ini=ini, section='b3', option='parser', default='',
                       explanation="Define your game:\n"
                                   "arma2/arma3\n"
                                   "bfbc2/bf3/bf4/moh/mohw\n"
                                   "cod/cod2/cod4/cod5/cod6/cod7/cod8\n"
                                   "iourt41/iourt42\n"
                                   "et/etpro/altitude/oa081/smg/smg11/sof2/sof2pm/wop/wop15\n"
                                   "chiv/csgo/homefront/insurgency/ravaged/ro2/",
                       allow_blank=False,
                       validate=lambda x: x in self._supported_parsers)

        result = False
        while not result:
            result = self.load_template(self._set['parser'])
            if result:
                break

        self.add_value(ini=ini, section='b3', option='database',
                       default=self.read_element('b3', 'database', 'mysql://b3:password@localhost/b3'),
                       explanation= "Your database info: [protocol]://[db-user]:[db-password]@[db-server[:port]]/[db-name]",
                       allow_blank=False,
                       validate=lambda x: splitDSN(x)['protocol'] in DB_PROTOCOLS)

        self.add_value(ini=ini, section='b3', option='bot_name',
                       default=self.read_element('b3', 'bot_name', 'b3'),
                       explanation="Name of the bot",
                       allow_blank=False)

        self.add_value(ini=ini, section='b3', option='bot_prefix',
                       default=self.read_element('b3', 'bot_prefix', '^0(^2b3^0)^7:'),
                       explanation="Ingame messages are prefixed with this code, you can use colorcodes",
                       allow_blank=True)

        self.add_value(ini=ini, section='b3', option='time_format',
                       default=self.read_element('b3', 'time_format', '%I:%M%p %Z %m/%d/%y'),
                       explanation="Time format to use to format time strings (also used by the !time command of the Admin Plugin)",
                       allow_blank=False)

        self.add_value(ini=ini, section='b3', option='time_zone',
                       default=self.read_element('b3', 'time_zone', 'CST'),
                       explanation="The timezone your bot is in (see: http://wiki.bigbrotherbot.net/usage:available_timezones)",
                       allow_blank=False,
                       validate=lambda x: x in timezones)

        self.add_value(ini=ini, section='b3', option='log_level',
                       default=self.read_element('b3', 'log_level', '9'),
                       explanation="How much detail in the log file: 9 = verbose, 10 = debug, 21 = bot, 22 = console",
                       allow_blank=False)

        self.add_value(ini=ini, section='b3', option="logfile",
                       default=self.read_element('b3', 'logfile', 'b3.log'),
                       explanation="Name of the log file B3 will generate",
                       allow_blank=False)

        self.add_value(ini=ini, section='b3', option="disabled_plugins",
                       default=self.read_element('b3', 'disabled_plugins', ''),
                       explanation="Comma separated list of plugin that will be loaded in 'disabled' status.\n"
                                   "Example: if you want b3 to load the 'stats' and 'pingwatch' plugin but not\n"
                                   "to start them at b3 main run you need to write: stats, pingwatch.",
                       allow_blank=True)

        self.add_value(ini=ini, section='b3', option="external_plugins_dir",
                       default=self.read_element('b3', 'external_plugins_dir', '@b3/extplugins'),
                       explanation="The directory where additional plugins can be found",
                       allow_blank=False)

        # server settings
        self.add_buffer("""\n-------------------------- GAME SERVER SETTINGS -------------------------------\n""")

        ini.add_section('server')

        # Frostbite specific
        if self._set['parser'] in self._frostbite:

            self.add_value(ini=ini, section='server', option="public_ip",
                           default=self.read_element('server', 'public_ip'),
                           explanation="The IP address of your gameserver",
                           allow_blank=False)

            self.add_value(ini=ini, section='server', option="port",
                           default=self.read_element('server', 'port'),
                           explanation="The port people use to connect to your gameserver",
                           allow_blank=False,
                           validate=lambda x: 1 <= int(x) <= 65535)

            self.add_value(ini=ini, section='server', option="rcon_ip",
                           default=self.read_element('server', 'rcon_ip'),
                           explanation="The IP of your gameserver B3 will use to send RCON commands (usually the same as public_ip)",
                           allow_blank=False)

            self.add_value(ini=ini, section='server', option="rcon_port",
                           default=self.read_element('server', 'rcon_port'),
                           explanation="The port of your gameserver B3 will use to send RCON commands (not the same as the normal port)",
                           allow_blank=False,
                           validate=lambda x: 1 <= int(x) <= 65535)

            self.add_value(ini=ini, section='server', option="rcon_password",
                           default=self.read_element('server', 'rcon_password'),
                           explanation="The RCON password of your gameserver",
                           allow_blank=False)

            self.add_value(ini=ini, section='server', option="timeout",
                           default=self.read_element('server', 'timeout', '3'),
                           explanation="RCON timeout",
                           silent=True)

        # Ravaged specific
        elif self._set['parser'] == 'ravaged':

            self.add_value(ini=ini, section='server', option="public_ip",
                           default=self.read_element('server', 'public_ip'),
                           explanation="The IP address of your gameserver",
                           allow_blank=False)

            self.add_value(ini=ini, section='server', option="port",
                           default=self.read_element('server', 'port'),
                           explanation="The query port of your gameserver (see SteamQueryPort in your Ravaged server config file)",
                           allow_blank=False,
                           validate=lambda x: 1 <= int(x) <= 65535)

            self.add_value(ini=ini, section='server', option="rcon_ip",
                           default=self.read_element('server', 'rcon_ip'),
                           explanation="The IP of your gameserver B3 will use to send RCON commands (usually the same as public_ip)",
                           allow_blank=False)
            self.add_value(ini=ini, section='server', option="rcon_port",
                           default=self.read_element('server', 'rcon_port'),
                           explanation="The port of your gameserver B3 will use to send RCON commands:\n"
                                       "see RConPort in your Ravaged server config file",
                           allow_blank=False,
                           validate=lambda x: 1 <= int(x) <= 65535)

            self.add_value(ini=ini, section='server', option="rcon_password",
                           default=self.read_element('server', 'rcon_password'),
                           explanation="The RCON password of your gameserver (see AdminPassword in your Ravaged server config file)",
                           allow_blank=False)

        # Chivalry specific
        elif self._set['parser'] == 'chiv':

            self.add_value(ini=ini, section='server', option="public_ip",
                           default=self.read_element('server', 'public_ip'),
                           explanation="The IP address of your gameserver",
                           allow_blank=False)

            self.add_value(ini=ini, section='server', option="port",
                           default=self.read_element('server', 'port', '27015'),
                           explanation="The query port of your gameserver (see SteamQueryPort in your Chivalry server config file)",
                           allow_blank=False,
                           validate=lambda x: 1 <= int(x) <= 65535)

            self.add_value(ini=ini, section='server', option="rcon_ip",
                           default=self.read_element('server', 'rcon_ip'),
                           explanation="The IP of your gameserver B3 will use to send RCON commands (usually the same as public_ip)",
                           allow_blank=False)

            self.add_value(ini=ini, section='server', option="rcon_port",
                           default=self.read_element('server', 'rcon_port'),
                           explanation="The port of your gameserver B3 will use to send RCON commands:\n"
                                       "see 'RConPort' in section '[AOC.AOCRCon]' of your PCServer-UDKGame.ini server config file",
                           allow_blank=False,
                           validate=lambda x: 1 <= int(x) <= 65535)

            self.add_value(ini=ini, section='server', option="rcon_password",
                           default=self.read_element('server', 'rcon_password'),
                           explanation="The RCON password of your gameserver (see AdminPassword in your gameserver config file)",
                           allow_blank=False)

        # Homefront specific
        elif self._set['parser'] == 'homefront':

            self.add_value(ini=ini, section='server', option="public_ip",
                           default=self.read_element('server', 'public_ip'),
                           explanation="The IP address of your gameserver",
                           allow_blank=False)

            self.add_value(ini=ini, section='server', option="port",
                           default=self.read_element('server', 'port'),
                           explanation="The port people use to connect to your gameserver",
                           allow_blank=False,
                           validate=lambda x: 1 <= int(x) <= 65535)

            self.add_value(ini=ini, section='server', option="rcon_ip",
                           default=self.read_element('server', 'rcon_ip'),
                           explanation="The IP of your gameserver B3 will use to send RCON commands (usually the same as public_ip)",
                           allow_blank=False)

            self.add_value(ini=ini, section='server', option="rcon_port",
                           default=self.read_element('server', 'rcon_port'),
                           explanation="The port of your gameserver B3 will use to send RCON commands (not the same as the normal port)",
                           allow_blank=False,
                           validate=lambda x: 1 <= int(x) <= 65535)

            self.add_value(ini=ini, section='server', option="rcon_password",
                           default=self.read_element('server', 'rcon_password'),
                           explanation="The RCON password of your gameserver (see AdminPassword in your Ravaged server config file)",
                           allow_blank=False)

        # Arma2 specific
        elif self._set['parser'] == 'arma2':

            self.add_value(ini=ini, section='server', option="public_ip",
                           default=self.read_element('server', 'public_ip'),
                           explanation="The IP address of your gameserver",
                           allow_blank=False)

            self.add_value(ini=ini, section='server', option="port",
                           default=self.read_element('server', 'port'),
                           explanation="The ArmA2 game network communication port",
                           allow_blank=False,
                           validate=lambda x: 1 <= int(x) <= 65535)

            self.add_value(ini=ini, section='server', option="rcon_ip",
                           default=self.read_element('server', 'rcon_ip'),
                           explanation="The IP of your gameserver B3 will use to send RCON commands (usually the same as public_ip)",
                           allow_blank=False)

            self.add_value(ini=ini, section='server', option="rcon_password",
                           default=self.read_element('server', 'rcon_password'),
                           explanation="The RCON password of your gameserver",
                           allow_blank=False)

        # Arma3 specific
        elif self._set['parser'] == 'arma3':

            self.add_value(ini=ini, section='server', option="public_ip",
                           default=self.read_element('server', 'public_ip'),
                           explanation="The IP address of your gameserver",
                           allow_blank=False)

            self.add_value(ini=ini, section='server', option="port",
                           default=self.read_element('server', 'port'),
                           explanation="The ArmA3 game network communication port",
                           allow_blank=False,
                           validate=lambda x: 1 <= int(x) <= 65535)

            self.add_value(ini=ini, section='server', option="rcon_ip",
                           default=self.read_element('server', 'rcon_ip'),
                           explanation="The IP of your gameserver B3 will use to send RCON commands (usually the same as public_ip)",
                           allow_blank=False)

            self.add_value(ini=ini, section='server', option="rcon_password",
                           default=self.read_element('server', 'rcon_password'),
                           explanation="The RCON password of your gameserver",
                           allow_blank=False)

        # Q3A specific
        else:

            self.add_value(ini=ini, section='server', option="public_ip",
                           default=self.read_element('server', 'public_ip'),
                           explanation="The IP address of your gameserver",
                           allow_blank=False)

            self.add_value(ini=ini, section='server', option="rcon_ip",
                           default=self.read_element('server', 'rcon_ip'),
                           explanation="The IP of your gameserver B3 will use to send RCON commands (127.0.0.1 when on the same box)",
                           allow_blank=False)

            self.add_value(ini=ini, section='server', option="port",
                           default=self.read_element('server', 'port'),
                           explanation="The port the server is running on",
                           allow_blank=False,
                           validate=lambda x: 1 <= int(x) <= 65535)

            self.add_value(ini=ini, section='server', option="rcon_password",
                           default=self.read_element('server', 'rcon_password'),
                           explanation="The RCON password of your gameserver",
                           allow_blank=False)

            # Urban Terror 4.2 specific
            if self._set['parser'] == 'iourt42':

                self.add_value(ini=ini, section='server', option="permban_with_frozensand",
                               default=self.read_element('server', 'permban_with_frozensand', 'no'),
                               explanation="Permban with Frozen Sand auth system",
                               allow_blank=True,
                               validate=lambda x: x.lower() in ('yes', '1', 'on', 'true', 'no', '0', 'off', 'false'))

                self.add_value(ini=ini, section='server', option="tempban_with_frozensand",
                               default=self.read_element('server', 'tempban_with_frozensand', 'no'),
                               explanation="Tempban with Frozen Sand auth system",
                               allow_blank=True,
                               validate=lambda x: x.lower() in ('yes', '1', 'on', 'true', 'no', '0', 'off', 'false'))

            # CoD7 game log specific
            if self._set['parser'] == 'cod7':

                self.add_value(ini=ini, section='server', option="game_log",
                               default=self.read_element('server', 'game_log'),
                               allow_blank=False,
                               explanation="The gameserver generates a logfile, put the path here:\n"
                                           "must be of this format: http://logs.gameservers.com/127.0.0.1:1024/xxxxx-1234-5678-9012-xxxxx)")
            else:

                self.add_value(ini=ini, section='server', option="game_log",
                               default=self.read_element('server', 'game_log'),
                               explanation="The gameserver generates a logfile, put the path and name here\n"
                                           "The logfile logfile may also be accessed using HTTP, SFTP or FTP:\n"
                                           "HTTP: http://serverhost/path/to/games_mp.log\n"
                                           "SFTP: sftp://[sftp-user]:[sftp-password]@[sftp-server]/path/to/games_mp.log\n"
                                           "FTP: ftp://[ftp-user]:[ftp-password]@[ftp-server]/path/to/games_mp.log\n"
                                           "For HTTP access you can use .htaccess to secure the connection", allow_blank=False)

            # configure default performances parameters
            self.add_value(ini=ini, section='server', option="delay", silent=True,
                           default=self.read_element('server', 'delay', '0.33'),
                           explanation="Delay between each log reading (set a higher value to consume less disk\n"
                                       "resources or bandwidth if you remotely connect using HTTP, SFTP or FTP)")

            self.add_value(ini=ini, section='server', option="lines_per_second", silent=True,
                           default=self.read_element('server', 'lines_per_second', '50'),
                           explanation="Number of lines to process per second. Set a lower value to consume less CPU resources")

        # determine if PunkBuster is supported
        if self._set['parser'] in self._pb_supported_parsers:
            self.add_value(ini=ini, section='server', option="punkbuster", default="on",
                         explanation="Is the gameserver running PunkBuster Anticheat: on/off",
                         allow_blank=False,
                         validate=lambda x: x.lower() in ('yes', '1', 'on', 'true', 'no', '0', 'off', 'false'))
        else:
            self.add_value(ini=ini, section='server', option="punkbuster", default="off", silent=True,
                           explanation="Is the gameserver running PunkBuster Anticheat: on/off")

        # update channel settings
        self.add_buffer("""\n----------------------------- UPDATE CHANNEL ----------------------------------\n""")

        ini.add_section('update')

        self.add_value(ini=ini, section='update', option="channel",
                       default=self.read_element('update', 'channel', 'stable'),
                       explanation="B3 checks if a new version is available at startup against 3 different channels\n"
                                   "Choose the channel you want to check against. Available channels are :\n"
                                   "stable : will only show stable releases of B3\n"
                                   "beta : will also check if a beta release is available\n"
                                   "dev : will also check if a development release is available\n"
                                   "skip: will skip the update check",
                       allow_blank=False,
                       validate=lambda x: x in ('stable', 'beta', 'dev', 'skip'))

        # autodoc settings
        self.add_buffer("""\n---------------------------- AUTODOC SETTINGS ---------------------------------\n""")

        ini.add_section('autodoc')

        self.add_value(ini=ini, section='autodoc', option="type",
                       default=self.read_element('autodoc', 'type', 'html'),
                       explanation="The type of B3 user documentation to generate: html, htmltable, json, xml",
                       allow_blank=False,
                       validate=lambda x: x in ('html', 'htmltable', 'json', 'xml'))

        self.add_value(ini=ini, section='autodoc', option="maxlevel",
                       default=self.read_element('autodoc', 'maxlevel', '100'),
                       explanation="If you want to exclude commands reserved for higher levels",
                       allow_blank=True)

        self.add_value(ini=ini, section='autodoc', option="destination",
                       default=self.read_element('autodoc', 'destination'),
                       explanation="Where to store the B3 documentation file: you can use a filepath or an FTP url",
                       allow_blank=True)

        # messages settings
        self.add_buffer("""\n-------------------------------- MESSAGES -------------------------------------\n""")

        ini.add_section('messages')

        # in this section we also need to check if we have old version messages! they contain: %s
        if '%s' in self.read_element('messages', 'kicked_by', '%s'):
            self.add_value(ini=ini, section='messages', option="kicked_by",
                           default="$clientname^7 was kicked by $adminname^7 $reason",
                           allow_blank=False)
        else:
            self.add_value(ini=ini, section='messages', option="kicked_by",
                           default=self.read_element('messages', 'kicked_by', '$clientname^7 was kicked by $adminname^7 $reason'),
                           allow_blank=False)

        if '%s' in self.read_element('messages', 'kicked', '%s'):
            self.add_value(ini=ini, section='messages', option="kicked",
                           default="$clientname^7 was kicked $reason",
                           allow_blank=False)
        else:
            self.add_value(ini=ini, section='messages', option="kicked",
                           default=self.read_element('messages', 'kicked', '$clientname^7 was kicked $reason'),
                           allow_blank=False)

        if '%s' in self.read_element('messages', 'banned_by', '%s'):
            self.add_value(ini=ini, section='messages', option="banned_by",
                           default="$clientname^7 was banned by $adminname^7 $reason",
                           allow_blank=False)
        else:
            self.add_value(ini=ini, section='messages', option="banned_by",
                           default=self.read_element('messages', 'banned_by', '$clientname^7 was banned by $adminname^7 $reason'),
                           allow_blank=False)

        if '%s' in self.read_element('messages', 'banned', '%s'):
            self.add_value(ini=ini, section='messages', option="banned",
                           default="$clientname^7 was banned $reason",
                           allow_blank=False)
        else:
            self.add_value(ini=ini, section='messages', option="banned",
                           default=self.read_element('messages', 'banned', '$clientname^7 was banned $reason'),
                           allow_blank=False)

        if '%s' in self.read_element('messages', 'temp_banned_by', '%s'):
            self.add_value(ini=ini, section='messages', option="temp_banned_by",
                           default="$clientname^7 was temp banned by $adminname^7 for $banduration^7 $reason",
                           allow_blank=False)
        else:
            self.add_value(ini=ini, section='messages', option="temp_banned_by",
                           default=self.read_element('messages', 'temp_banned_by', '$clientname^7 was temp banned by $adminname^7 for $banduration^7 $reason'),
                           allow_blank=False)

        if '%s' in self.read_element('messages', 'temp_banned', '%s'):
            self.add_value(ini=ini, section='messages', option="temp_banned",
                           default="$clientname^7 was temp banned for $banduration^7 $reason",
                           allow_blank=False)
        else:
            self.add_value(ini=ini, section='messages', option="temp_banned",
                           default=self.read_element('messages', 'temp_banned', '$clientname^7 was temp banned for $banduration^7 $reason'),
                           allow_blank=False)

        if '%s' in self.read_element('messages', 'unbanned_by', '%s'):
            self.add_value(ini=ini, section='messages', option="unbanned_by",
                           default="$clientname^7 was un-banned by $adminname^7 $reason",
                           allow_blank=False)
        else:
            self.add_value(ini=ini, section='messages', option="unbanned_by",
                           default=self.read_element('messages', 'unbanned_by', '$clientname^7 was un-banned by $adminname^7 $reason'),
                           allow_blank=False)

        if '%s' in self.read_element('messages', 'unbanned', '%s'):
            self.add_value(ini=ini, section='messages', option="unbanned",
                           default="$clientname^7 was un-banned $reason",
                           allow_blank=False)
        else:
            self.add_value(ini=ini, section='messages', option="unbanned",
                           default=self.read_element('messages', 'unbanned', '$clientname^7 was un-banned $reason'),
                           allow_blank=False)

        # plugins
        self.add_buffer("""\n--------------------------- INSTALLING PLUGINS --------------------------------\n""")

        ini.add_section('plugins')

        self.autoinstallplugins = self.raw_default("Do you want to (auto)install all plugins?", "yes")
        if self.autoinstallplugins == 'yes':
            self.read_plugins(ini=ini)
        else:
            self.add_plugin(ini, "admin", "@conf/plugin_admin.ini", prompt=False)
            self.add_plugin(ini, "adv", "@conf/plugin_adv.xml")
            self.add_plugin(ini, "censor", "@conf/plugin_censor.xml")
            self.add_plugin(ini, "cmdmanager", "@conf/plugin_cmdmanager.ini")
            self.add_plugin(ini, "pingwatch", "@conf/plugin_pingwatch.ini")
            self.add_plugin(ini, "spamcontrol", "@conf/plugin_spamcontrol.ini")
            self.add_plugin(ini, "stats", "@conf/plugin_stats.ini")
            self.add_plugin(ini, "status", "@conf/plugin_status.ini")
            self.add_plugin(ini, "tk", "@conf/plugin_tk.ini")
            self.add_plugin(ini, "welcome", "@conf/plugin_welcome.ini")

            if self._set['punkbuster'] == "on":
                self.add_plugin(ini, "punkbuster", "@conf/plugin_punkbuster.ini")

        ini.add_comment('plugins', "This is a non-standard plugin, and quite resource heavy. Please take\n"
                                   "a look in the B3 forums (look for XLR Extensions) for more\n"
                                   "information before enabling this. Extra database tables are necessary")

        test = self.raw_default("Install xlrstats plugin? (yes/no)", 'no', allow_blank=False, validate=lambda x: x.lower() in ('yes', 'y', 'no', 'n'))
        if test.lower() in ('yes', 'y'):
            self.add_plugin(ini, "xlrstats", "@b3/extplugins/xlrstats/conf/plugin_xlrstats.ini", prompt=False)

        ini.write(open(self._output_file,'w'))
        self.add_buffer("""\n------------------------- FINISHED CONFIGURATION ------------------------------\n""")
        self.test_exit(question='Press [Enter] to finish setup')

    def load_template(self, parser):
        """
        Load an existing config file or use the packaged examples.
        :param parser: The parser being used.
        :return True if we loaded a template, False otherwise
        """
        if os.path.isdir(os.path.join(self.getB3Path(), 'conf')):
            self._configpath = self.getB3Path()
        elif functions.main_is_frozen():
            self._configpath = os.path.join(os.environ['ALLUSERSPROFILE'], 'BigBrotherBot')
        else:
            # we cannot identify the configuration folder so we can't use a template
            self._configpath = self.raw_default("Could not locate the config folder, please provide the full system path")
            self.writebuffer()

        self._configpath = functions.right_cut(self._configpath, os.path.sep)

        # load the template based on the parser the user just selected
        default_tpl = os.path.join(self._configpath, 'conf', 'templates', 'b3.%s.tpl' % parser)
        self._templatevar = 'template'
        if not os.path.isfile(default_tpl):
            # if there is not a template available, use the distribution ini file
            default_tpl = os.path.join(self._configpath, 'conf', 'b3.distribution.ini')
            self._templatevar = 'distribution'

        if self._template != '':
            # means we just backed-up an old config with the same name
            result = self.raw_default("Load values from the backed-up config (%s)?" % self._template, "yes", validate=lambda x: x.lower() in ('yes', 'y', 'no', 'n'))
            if result.lower() != 'yes' and result.lower() != 'y':
                self._template = self.raw_default("Load values from a template", default_tpl)
                self.writebuffer()
            else:
                self._templatevar = 'backup'
                self.writebuffer()
        else:
            self._template = self.raw_default("Load values from a template", default_tpl)
            self.writebuffer()

        self._template = self.getAbsolutePath(self._template)

        try:
            self.tree = CfgConfigParser(allow_no_value=True)
            self.tree.load(self._template)
        except Exception, msg:
            self.add_buffer('Could not parse configuration template: %s\n' % str(msg))
            # backed up config file must be corrupt or not completed last setup, reset it to the default
            self.add_buffer('If you have troubles loading a backup configuration file, try to load the default...\n')
            self._template = ''
            return False
        else:
            return True

    def read_element(self, section, option, default=''):
        """
        Returns a config value from self.tree matching the given section/option.
        """
        try:
            # seek in the loaded template
            return self.tree.get(section, option)
        except:
            # return default when an exception is raised: this means that either we are not using
            # a template file or the given section/option combination doesn't match a config value
            return default

    def read_plugins(self, ini):
        """
        Writes plugins to the config read from a template.
        :param ini: The CfgConfigParser instance of the configuration file we are generating
        """
        for name in self.tree.options('plugins'):
            # handle xlrstats plugin separately
            if name != 'xlrstats':
                config = self.tree.get('plugins', name)
                if config is not None and config[:12] == 'external_plugins_dir':
                    config = ''.join((self._set['external_plugins_dir'], config[12:]))
                self.add_plugin(ini, name, config, prompt=False)

    @staticmethod
    def add_explanation(etext):
        """
        Add an explanation to the question asked by the setup procedure.
        """
        # fix XML formatting which looks weird in console sys.out
        for line in ('%s\n' % etext).split('\n'):
            print line.strip()

    def add_buffer(self, addition, autowrite=True):
        """
        Add a line to the output buffer.
        """
        self._buffer += addition
        if autowrite:
            self.writebuffer()

    def writebuffer(self):
        """
        Clear the screen and write the output buffer to the screen.
        """
        self.clearscreen()
        print self._buffer

    def equalize(self, _string):
        """
        Make the setup questions same length for prettier formatting.
        """
        return (self._equalength - len(_string)) * " "

    def add_value(self, ini, section, option, default, explanation="", silent=False, allow_blank=None, validate=None):
        """
        A routine to add a setting with a textnode to the config
        :param ini: The CfgConfigParser instance of the configuration file we are generating
        :param section: The section where to add the new value
        :param option: The option key.
        :param default: The option default value
        :param explanation: An help text to prompt to the user
        :param silent: Whether we have to hide the value entered from the buffer
        :param allow_blank: Whether we can accept an empty value for this set or not
        :param validate: The reference to a function that will validate the correctness of the input value
        """
        if not self.is_empty(explanation):
            self.add_explanation(explanation)
            ini.add_comment(section=section, comment=explanation)

        if not silent:
            value = self.raw_default(prompt=option, default=default, allow_blank=allow_blank, validate=validate)
        else:
            value = default

        # place none in case of empty string
        if self.is_empty(value):
            value = None

        ini.set(section, option, value)
        self._set[str(option)] = str(value)

        if not silent:
            svalue = '' if not value else str(value)
            self.add_buffer(str(option) + self.equalize(option) + ": " + svalue + "\n")

    def add_plugin(self, ini, name, config=None, default="yes", prompt=True):
        """
        A routine to add a plugin to the config
        :param ini: The CfgConfigParser instance of the configuration file we are generating
        :param name: The plugin name
        :param config: The plugin configuration file path
        :param default: Default answer (install or not
        :param prompt: Whether to ask for installation or not
        """
        if prompt:
            test = self.raw_default("Install %s plugin? (yes/no)" % name, default, allow_blank=False, validate=lambda x: x.lower() in ('yes', 'y', 'no', 'n'))
            if test.lower() not in ('yes', 'y'):
                self.writebuffer()
                return False

        ini.set('plugins', name, config)

        if not config:
            self.add_buffer("plugin: " + str(name) + "\n")
        else:
            self.add_buffer("plugin: " + str(name) + ", config: " + str(config) + "\n")

    def raw_default(self, prompt, default=None, allow_blank=None, validate=None):
        """
        Prompt user for input and don't accept an empty value.
        :param prompt: The value to be entered
        :param default: An optional default value
        :param allow_blank: Whether to accept blank values or not
        :param validate: The reference to a function that will validate the correctness of the input value
        """
        if default:
            newprompt = "%s [%s]" % (prompt, default)
        else:
            newprompt = "%s" % prompt

        res = raw_input(newprompt + self.equalize(newprompt) + ": ")

        # backup using default if necessary
        if self.is_empty(res) and default:
            res = default

        if self.is_empty(res):
            # if we have an empty value check if we actually can accept it
            if not allow_blank:
                # if we can't accept it, keep prompting the same question
                res = self.raw_default(prompt=prompt, default=default, allow_blank=allow_blank, validate=validate)
            else:
                res = ''
        else:
            if validate and callable(validate):
                if not validate(res):
                    # if we can't accept it, keep prompting the same question
                    res = self.raw_default(prompt=prompt, default=default, allow_blank=allow_blank, validate=validate)
        return res

    def backup_file(self, _file):
        """
        Create a backup of an existing config file.
        :param _file: The configuration file to backup
        """
        if os.path.isfile(_file):
            print "File " + _file + " already exists : creating backup..."
            try:
                stamp = time.strftime("-%d_%m_%Y_%H.%M.%S", time.gmtime())
                fname = functions.right_cut(_file, '.ini') + stamp + ".ini"
                functions.copy_file(_file, fname)
                print "Successfully created backup file : " + fname
                print "If you need to abort the setup procedure, you can restore by renaming the backup file."
                self._template = fname
                self.test_exit()
            except Exception, e:
                print "Could not create backup file: %s\n" % str(e)
                self.test_exit()


    def introduction(self):
        """
        Display the setup introduction.
        """
        def print_head():
            self.clearscreen()
            print """
                        _\|/_
                        (o o)    {:>32}
                +----oOO---OOo----------------------------------+
                |                                               |
                |      WELCOME TO THE B3 SETUP PROCEDURE        |
                |                                               |
                +-----------------------------------------------+

            """.format('B3 : %s' % __version__)

        print_head()
        print "We're about to generate a main configuration file for BigBrotherBot (B3).\n" \
              "This procedure is initiated when:\n\n" \
              "  1. You run B3 with the option --setup or -s\n" \
              "  2. The configuration file you're trying to run does not exist\n" \
              "  3. You did not modify the distributed b3.ini prior starting B3"
        self.test_exit()
        print_head()
        print "We will prompt you for each setting.\n" \
              "We'll also provide default values inside [...] if applicable.\n" \
              "When you want to accept default value you will only need to press [Enter].\n" \
              "If you make an error at any stage, you can abort the setup procedure by\n" \
              "typing 'abort' at the prompt. You can start over by running B3 with the\n" \
              "setup option: python b3_run.py --setup"
        self.test_exit()
        print_head()
        print "First you will be prompted for a location and name for this configuration file.\n" \
              "This is for multiple server setups, or if you want to run B3 from a different\n" \
              "setup file for your own reasons. In a basic single instance install you will\n" \
              "not have to change this location and/or name. If a configuration file exists\n" \
              "we will make a backup first and tag it with date and time, so you can always\n" \
              "revert to a previous version of the config file.\n\n" \
              "Bugs and suggestions may be reported on our forums at www.bigbrotherbot.net"
        self.test_exit(question='[Enter] to continue to generate the configuration file...')

    @staticmethod
    def test_exit(key='',
                  question='[Enter] to continue, \'abort\' to abort Setup: ',
                  exitmessage='Setup aborted, run python b3_run.py -s to restart the procedure.'):
        """
        Test the input for an exit code, give the user an option to abort setup.
        """
        if key == '':
            key = raw_input('\n' + question)
        if key != 'abort':
            print "\n"
            return
        else:
            raise SystemExit(exitmessage)

    ####################################################################################################################
    ##                                                                                                                ##
    ##  UTILITIES                                                                                                     ##
    ##                                                                                                                ##
    ####################################################################################################################

    @staticmethod
    def clearscreen():
        """
        Clear the shell screen
        """
        if platform.system() in ('Windows', 'Microsoft'):
            os.system('cls')
        else:
            os.system('clear')

    @staticmethod
    def is_empty(value):
        """
        Test whether an input value is empty
        :param value: The value to test
        """
        return not value or not value.strip()

    @staticmethod
    def getB3Path():
        """
        Return the B3 absolute path.
        """
        if functions.main_is_frozen():
            # which happens when running from the py2exe build
            return os.path.dirname(sys.executable)
        return modulePath

    def getAbsolutePath(self, path):
        """
        Return an absolute path name and expand the user prefix (~).
        """
        if path[0:4] == '@b3/':
            path = os.path.join(self.getB3Path(), path[4:])
        return os.path.normpath(os.path.expanduser(path))

    @staticmethod
    def url2name(url):
        return os.path.basename(urlsplit(url)[2])


class Update(Setup):
    """
    This class holds all update methods for the database.
    """
    def __init__(self, conf=None):
        """
        Object constructor.
        :param conf: The B3 configuration file instance
        """
        print """
                        _\|/_
                        (o o)    {:>32}
                +----oOO---OOo----------------------------------+
                |                                               |
                |             UPDATING B3 DATABASE              |
                |                                               |
                +-----------------------------------------------+

        """.format('B3 : %s' % __version__)

        if conf:
            self._config = os.path.normpath(conf)
        elif self.getB3Path() != "":
            self._config = os.path.join(self.getB3Path(), 'conf', 'b3.xml')

        if os.path.exists(self._config):
            import config
            cfg = config.load(self._config)
            print 'Using configuration file: %s\n' % self._config
        else:
            raise SystemExit('Configuration file not found: please start B3 using "python b3_run.py --setup" to create one')

        dsn = cfg.get('b3', 'database')
        dsndict = splitDSN(dsn)
        database = storage.getStorage(dsn, dsndict, StubConsole())

        _currentversion = version.LooseVersion(__version__)
        print 'Current B3 version: %s\n' % _currentversion

        # update to v1.3.0
        if _currentversion >= '1.3.0':
            # update only if SQL file exists (some protocols do not have to update since they are new)
            if os.path.isfile(self.getAbsolutePath('@b3/sql/%s/b3-update-1.3.0.sql' % dsndict['protocol'])):
                try:
                    print 'Updating database to version 1.3.0...'
                    database.queryFromFile('@b3/sql/%s/b3-update-1.3.0.sql' % dsndict['protocol'])
                except Exception, msg:
                    print "WARNING: could not update database to version 1.3.0 properly: %s" % str(msg)
                    self.test_exit("[Enter] to continue update procedure, \'abort\' to quit")

        # update to v1.6.0
        if _currentversion >= '1.6.0':
            # update only if SQL file exists (some protocols do not have to update since they are new)
            if os.path.isfile(self.getAbsolutePath('@b3/sql/%s/b3-update-1.6.0.sql' % dsndict['protocol'])):
                try:
                    print 'Updating database to version 1.6.0...'
                    database.queryFromFile('@b3/sql/%s/b3-update-1.6.0.sql' % dsndict['protocol'])
                except Exception, msg:
                    print "WARNING: could not update database to version 1.6.0 properly: %s" % str(msg)
                    self.test_exit("[Enter] to continue update procedure, \'abort\' to quit")

        # update to v1.7.0
        if _currentversion >= '1.7.0':
            # update only if SQL file exists (some protocols do not have to update since they are new)
            if os.path.isfile(self.getAbsolutePath('@b3/sql/%s/b3-update-1.7.0.sql' % dsndict['protocol'])):
                try:
                    print 'Updating database to version 1.7.0...'
                    database.queryFromFile('@b3/sql/%s/b3-update-1.7.0.sql' % dsndict['protocol'])
                except Exception, msg:
                    print "WARNING: could not update database to version 1.7.0 properly: %s" % str(msg)
                    self.test_exit("[Enter] to continue update procedure, \'abort\' to quit")

        # update to v1.8.1
        if _currentversion >= '1.8.1':
            # update only if SQL file exists (some protocols do not have to update since they are new)
            if os.path.isfile(self.getAbsolutePath('@b3/sql/%s/b3-update-1.8.1.sql' % dsndict['protocol'])):
                try:
                    print 'Updating database to version 1.8.1...'
                    database.queryFromFile('@b3/sql/%s/b3-update-1.8.1.sql' % dsndict['protocol'])
                except Exception, msg:
                    print "WARNING: could not update database to version 1.8.1 properly: %s" % str(msg)
                    self.test_exit("[Enter] to continue update procedure, \'abort\' to quit")

        # update to v1.9.0
        if _currentversion >= '1.9.0':
            # update only if SQL file exists (some protocols do not have to update since they are new)
            if os.path.isfile(self.getAbsolutePath('@b3/sql/%s/b3-update-1.9.0.sql' % dsndict['protocol'])):
                try:
                    print 'Updating database to version 1.9.0...'
                    database.queryFromFile('@b3/sql/%s/b3-update-1.9.0.sql' % dsndict['protocol'])
                except Exception, msg:
                    print "WARNING: could not update database to version 1.9.0 properly: %s" % str(msg)
                    self.test_exit("[Enter] to continue update procedure, \'abort\' to quit")

        if _currentversion >= '1.10.0':
            # update only if SQL file exists (some protocols do not have to update since they are new)
            if os.path.isfile(self.getAbsolutePath('@b3/sql/%s/b3-update-1.10.0.sql' % dsndict['protocol'])):
                try:
                    print 'Updating database to version 1.10.0...'
                    database.queryFromFile('@b3/sql/%s/b3-update-1.10.0.sql' % dsndict['protocol'])
                except Exception, msg:
                    print "WARNING: could not update database to version 1.10.0 properly: %s" % str(msg)
                    self.test_exit("[Enter] to continue update procedure, \'abort\' to quit")

        raise SystemExit('Update finished: restart B3 to continue')


class StubConsole(object):
    """
    This class is needed to we can make use of the storage module which usually accepts a console in input.
    Since the console object is being used just for logging facilities, we'll create a stub one which fakes log methods
    """
    @staticmethod
    def bot(self, msg, *args, **kwargs):
        pass

    @staticmethod
    def info(self, msg, *args, **kwargs):
        pass

    @staticmethod
    def debug(self, msg, *args, **kwargs):
        pass

    @staticmethod
    def error(self, msg, *args, **kwargs):
        pass

    @staticmethod
    def warning(self, msg, *args, **kwargs):
        pass

    @staticmethod
    def verbose(self, msg, *args, **kwargs):
        pass

    @staticmethod
    def verbose2(self, msg, *args, **kwargs):
        pass

    @staticmethod
    def critical(msg, *args, **kwargs):
        raise SystemExit(msg)

