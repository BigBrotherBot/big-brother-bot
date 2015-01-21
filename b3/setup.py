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
import tempfile
import time

from b3.storage import PROTOCOLS as DB_PROTOCOLS
from b3.lib.SimpleXMLWriter import XMLWriter
from distutils import version
from functions import splitDSN
from timezones import timezones
from urlparse import urlsplit

try:
    from xml.etree import cElementTree as ElementTree
except ImportError:
    from xml.etree import ElementTree

__author__ = 'xlr8or'
__version__ = pkg_handler.version(__name__)
modulePath = pkg_handler.resource_directory(__name__)

_buffer = ''
_equaLength = 15
_indentation = '    '


class Setup(object):

    _pver = sys.version.split()[0]
    _indentation = '    '
    _configpath = ''
    _config = r'b3/conf/b3.xml'
    _template = ''
    _templatevar = ''
    _buffer = ''
    _equalength = 16

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
            self._config = os.path.join(self.getB3Path(), 'conf', 'b3.xml')

        self.introduction()
        self.clearscreen()

        self._output_file = self.raw_default("Location of the new configuration file", self._config)
        self._output_tempfile = tempfile.NamedTemporaryFile(delete=False)

        # creating backup if needed
        self.backup_file(self._output_file)
        self.run_setup()

        # copy the config to it's final version
        functions.copy_file(self._output_tempfile.name, self._output_file)

        try:
            # try to delete the tempfile: this fails on Windows in some cases
            functions.rm_file(self._output_tempfile.name)
        except:
            pass

        raise SystemExit('Restart B3 or reconfigure B3 using option: -s')

    def run_setup(self):
        """
        The main function that handles the setup steps.
        """
        global xml
        xml = XMLWriter(self._output_tempfile, "UTF-8")

        # write appropriate header
        xml.declaration()
        xml.comment("""
This file is generated by the B3 setup procedure.
If you want to regenerate this file and make sure the format is correct,
you can invoke the setup procedure with the command : b3_run -s b3.xml\n
This is B3 main config file (the one you specify when you run B3 with the
command : b3_run.py -c b3.xml)\n
For any change made in this config file, you have to restart B3.
Whenever you can specify a file/directory path, the following shortcuts
can be used :\n
    @b3 : the folder where B3 code is installed in
    @conf : the folder containing this config file\n""")

        # first level
        configuration = xml.start("configuration")
        xml.data("\n\t")

        # B3 settings
        self.add_buffer("""-------------------------- B3 SPECIFIC SETTINGS -------------------------------\n""")

        xml.start("settings", name="b3")
        self.add_set("parser", "", explanation="""Define your game:
                arma2/arma3
                bfbc2/bf3/bf4/moh/mohw
                cod/cod2/cod4/cod5/cod6/cod7/cod8
                iourt41/iourt42
                et/etpro/altitude/oa081/smg/smg11/sof2/sof2pm/wop/wop15
                chiv/csgo/homefront/insurgency/ravaged/ro2/""",
                allow_blank=False,
                validate=lambda x: x in self._supported_parsers)

        # set a template xml file to read existing settings from
        result = False
        while not result:
            result = self.load_template(self._set['parser'])
            if result:
                #self.add_buffer('Configuration values loaded successfully: %s\n' % self._template)
                break

        # getting database info, test it and set up the tables
        self.add_set("database", self.read_element('b3', 'database', 'mysql://b3:password@localhost/b3'),
                     explanation= "Your database info: [protocol]://[db-user]:[db-password]@[db-server[:port]]/[db-name]",
                     allow_blank=False,
                     validate=lambda x: splitDSN(x)['protocol'] in DB_PROTOCOLS)

        self.add_set("bot_name", self.read_element('b3', 'bot_name', 'b3'),
                     explanation="Name of the bot",
                     allow_blank=False)

        self.add_set("bot_prefix", self.read_element('b3', 'bot_prefix', '^0(^2b3^0)^7:'),
                     explanation="Ingame messages are prefixed with this code, you can use colorcodes",
                     allow_blank=True)

        self.add_set("time_format", self.read_element('b3', 'time_format', '%I:%M%p %Z %m/%d/%y'),
                     explanation="Time format to use to format time strings (also used by the !time command of the Admin Plugin",
                     allow_blank=False)

        self.add_set("time_zone", self.read_element('b3', 'time_zone', 'CST'),
                     explanation="The timezone your bot is in (see: http://wiki.bigbrotherbot.net/usage:available_timezones)",
                     allow_blank=False,
                     validate=lambda x: x in timezones)

        self.add_set("log_level", self.read_element('b3', 'log_level', '9'),
                     explanation="How much detail in the log file: 9 = verbose, 10 = debug, 21 = bot, 22 = console",
                     allow_blank=False)

        self.add_set("logfile", self.read_element('b3', 'logfile', 'b3.log'),
                     explanation="Name of the log file B3 will generate",
                     allow_blank=False)

        xml.data("\n\t")
        xml.end()
        xml.data("\n\t")

        # server settings
        self.add_buffer("""\n-------------------------- GAME SERVER SETTINGS -------------------------------\n""")

        xml.start("settings", name="server")

        # Frostbite specific
        if self._set['parser'] in self._frostbite:
            self.add_set("public_ip", self.read_element('server', 'public_ip'),
                         explanation="The IP address of your gameserver",
                         allow_blank=False)
            self.add_set("port", self.read_element('server', 'port'),
                         explanation="The port people use to connect to your gameserver",
                         allow_blank=False,
                         validate=lambda x: 1 <= int(x) <= 65535)
            self.add_set("rcon_ip", self.read_element('server', 'rcon_ip'),
                         explanation="The IP of your gameserver B3 will use to send RCON commands (usually the same as public_ip)",
                         allow_blank=False)
            self.add_set("rcon_port", self.read_element('server', 'rcon_port'),
                         explanation="The port of your gameserver B3 will use to send RCON commands (not the same as the normal port)",
                         allow_blank=False,
                         validate=lambda x: 1 <= int(x) <= 65535)
            self.add_set("rcon_password", self.read_element('server', 'rcon_password'),
                         explanation="The RCON password of your gameserver",
                         allow_blank=False)
            self.add_set("timeout", self.read_element('server', 'timeout', '3'),
                         explanation="RCON timeout",
                         silent=True)

        # Ravaged specific
        elif self._set['parser'] == 'ravaged':
            self.add_set("public_ip", self.read_element('server', 'public_ip'),
                         explanation="The IP address of your gameserver",
                         allow_blank=False)
            self.add_set("port", self.read_element('server', 'port'),
                         explanation="The query port of your gameserver (see SteamQueryPort in your Ravaged server config file)",
                         allow_blank=False,
                         validate=lambda x: 1 <= int(x) <= 65535)
            self.add_set("rcon_ip", self.read_element('server', 'rcon_ip'),
                         explanation="The IP of your gameserver B3 will use to send RCON commands (usually the same as public_ip)",
                         allow_blank=False)
            self.add_set("rcon_port", self.read_element('server', 'rcon_port'),
                         explanation="The port of your gameserver B3 will use to send RCON commands (see RConPort in your Ravaged server config file)",
                         allow_blank=False,
                         validate=lambda x: 1 <= int(x) <= 65535)
            self.add_set("rcon_password", self.read_element('server', 'rcon_password'),
                         explanation="The RCON password of your gameserver (see AdminPassword in your Ravaged server config file)",
                         allow_blank=False)

        # Chivalry specific
        elif self._set['parser'] == 'chiv':
            self.add_set("public_ip", self.read_element('server', 'public_ip'),
                         explanation="The IP address of your gameserver",
                         allow_blank=False)
            self.add_set("port", self.read_element('server', 'port', '27015'),
                         explanation="The query port of your gameserver (see SteamQueryPort in your Chivalry server config file)",
                         allow_blank=False,
                         validate=lambda x: 1 <= int(x) <= 65535)
            self.add_set("rcon_ip", self.read_element('server', 'rcon_ip'),
                         explanation="The IP of your gameserver B3 will use to send RCON commands (usually the same as public_ip)",
                         allow_blank=False)
            self.add_set("rcon_port", self.read_element('server', 'rcon_port'),
                         explanation="The port of your gameserver B3 will use to send RCON commands (see 'RConPort' in section '[AOC.AOCRCon]' of your PCServer-UDKGame.ini server config file)",
                         allow_blank=False,
                         validate=lambda x: 1 <= int(x) <= 65535)
            self.add_set("rcon_password", self.read_element('server', 'rcon_password'),
                         explanation="The RCON password of your gameserver (see AdminPassword in your gameserver config file)",
                         allow_blank=False)

        # Homefront specific
        elif self._set['parser'] == 'homefront':
            self.add_set("public_ip", self.read_element('server', 'public_ip'),
                         explanation="The IP address of your gameserver",
                         allow_blank=False)
            self.add_set("port", self.read_element('server', 'port'),
                         explanation="The port people use to connect to your gameserver",
                         allow_blank=False,
                         validate=lambda x: 1 <= int(x) <= 65535)
            self.add_set("rcon_ip", self.read_element('server', 'rcon_ip'),
                         explanation="The IP of your gameserver B3 will use to send RCON commands (usually the same as public_ip)",
                         allow_blank=False)
            self.add_set("rcon_port", self.read_element('server', 'rcon_port'),
                         explanation="The port of your gameserver B3 will use to send RCON commands (not the same as the normal port)",
                         allow_blank=False,
                         validate=lambda x: 1 <= int(x) <= 65535)
            self.add_set("rcon_password", self.read_element('server', 'rcon_password'),
                         explanation="The RCON password of your gameserver (see AdminPassword in your Ravaged server config file)",
                         allow_blank=False)

        # Arma2 specific
        elif self._set['parser'] == 'arma2':
            self.add_set("public_ip", self.read_element('server', 'public_ip'),
                         explanation="The IP address of your gameserver",
                         allow_blank=False)
            self.add_set("port", self.read_element('server', 'port'),
                         explanation="The ArmA2 game network communication port",
                         allow_blank=False,
                         validate=lambda x: 1 <= int(x) <= 65535)
            self.add_set("rcon_ip", self.read_element('server', 'rcon_ip'),
                         explanation="The IP of your gameserver B3 will use to send RCON commands (usually the same as public_ip)",
                         allow_blank=False)
            self.add_set("rcon_password", self.read_element('server', 'rcon_password'),
                         explanation="The RCON password of your gameserver",
                         allow_blank=False)

        # Arma3 specific
        elif self._set['parser'] == 'arma3':
            self.add_set("public_ip", self.read_element('server', 'public_ip'),
                         explanation="The IP address of your gameserver",
                         allow_blank=False)
            self.add_set("port", self.read_element('server', 'port'),
                         explanation="The ArmA3 game network communication port",
                         allow_blank=False,
                         validate=lambda x: 1 <= int(x) <= 65535)
            self.add_set("rcon_ip", self.read_element('server', 'rcon_ip'),
                         explanation="The IP of your gameserver B3 will use to send RCON commands (usually the same as public_ip)",
                         allow_blank=False)
            self.add_set("rcon_password", self.read_element('server', 'rcon_password'),
                         explanation="The RCON password of your gameserver",
                         allow_blank=False)

        # Q3A specific
        else:
            self.add_set("public_ip", self.read_element('server', 'public_ip'),
                         explanation="The IP address of your gameserver",
                         allow_blank=False)
            self.add_set("rcon_ip", self.read_element('server', 'rcon_ip'),
                         explanation="The IP of your gameserver B3 will use to send RCON commands (127.0.0.1 when on the same box)",
                         allow_blank=False)
            self.add_set("port", self.read_element('server', 'port'),
                         explanation="The port the server is running on",
                         allow_blank=False,
                         validate=lambda x: 1 <= int(x) <= 65535)
            self.add_set("rcon_password", self.read_element('server', 'rcon_password'),
                         explanation="The RCON password of your gameserver",
                         allow_blank=False)

            # Urban Terror 4.2 specific
            if self._set['parser'] == 'iourt42':
                self.add_set("permban_with_frozensand", self.read_element('server', 'permban_with_frozensand', 'no'),
                             explanation="Permban with Frozen Sand auth system",
                             allow_blank=True,
                             validate=lambda x: x.lower() in ('yes', '1', 'on', 'true', 'no', '0', 'off', 'false'))
                self.add_set("tempban_with_frozensand", self.read_element('server', 'tempban_with_frozensand', 'no'),
                             explanation="Tempban with Frozen Sand auth system",
                             allow_blank=True,
                             validate=lambda x: x.lower() in ('yes', '1', 'on', 'true', 'no', '0', 'off', 'false'))

            # CoD7 game log specific
            if self._set['parser'] == 'cod7':
                self.add_set("game_log", self.read_element('server', 'game_log'),
                             allow_blank=False,
                             explanation="The gameserver generates a logfile, put the path here.\n"
                                         "NOTE: must be of this format: http://logs.gameservers.com/127.0.0.1:1024/xxxxx-1234-5678-9012-xxxxx)")
            else:
                self.add_set("game_log", self.read_element('server', 'game_log'),
                             explanation="""The gameserver generates a logfile, put the path and name here
             The logfile logfile may also be accessed using HTTP, SFTP or FTP:
                 HTTP: http://serverhost/path/to/games_mp.log
                 SFTP: sftp://[sftp-user]:[sftp-password]@[sftp-server]/path/to/games_mp.log
                 FTP: ftp://[ftp-user]:[ftp-password]@[ftp-server]/path/to/games_mp.log
             For HTTP access you can use .htaccess to secure the connection""", allow_blank=False)

            # configure default performances parameters
            self.add_set("delay", self.read_element('server', 'delay', '0.33'), silent=True,
                         explanation="Delay between each log reading (set a higher value to consume less disk resources or bandwidth if you remotely connect)")
            self.add_set("lines_per_second", self.read_element('server', 'lines_per_second', '50'), silent=True,
                         explanation="Number of lines to process per second. Set a lower value to consume less CPU resources")

        # determine if PunkBuster is supported
        if self._set['parser'] in self._pb_supported_parsers:
            self.add_set("punkbuster", "on",
                         explanation="Is the gameserver running PunkBuster Anticheat: on/off",
                         allow_blank=False,
                         validate=lambda x: x.lower() in ('yes', '1', 'on', 'true', 'no', '0', 'off', 'false'))
        else:
            self.add_set("punkbuster", "off", silent=True,
                         explanation="Is the gameserver running PunkBuster Anticheat: on/off")

        xml.data("\n\t")
        xml.end()
        xml.data("\n\t")

        # update channel settings
        self.add_buffer("""\n----------------------------- UPDATE CHANNEL ----------------------------------\n""")

        xml.start("settings", name="update")
        self.add_set("channel", self.read_element('update', 'channel', 'stable'),
                     explanation="""B3 checks if a new version is available at startup against 3 different channels
            Choose the channel you want to check against. Available channels are :
                    stable : will only show stable releases of B3
                    beta : will also check if a beta release is available
                    dev : will also check if a development release is available
                    skip: will skip the update check""",
                     allow_blank=False,
                     validate=lambda x: x in ('stable', 'beta', 'dev', 'skip'))

        xml.data("\n\t")
        xml.end()
        xml.data("\n\t")

        # autodoc settings
        self.add_buffer("""\n---------------------------- AUTODOC SETTINGS ---------------------------------\n""")

        xml.start("settings", name="autodoc")

        self.add_set("type", self.read_element('autodoc', 'type', 'html'),
                     explanation="The type of B3 user documentation to generate: html, htmltable, json, xml",
                     allow_blank=False,
                     validate=lambda x: x in ('html', 'htmltable', 'json', 'xml'))
        self.add_set("maxlevel", self.read_element('autodoc', 'maxlevel', '100'),
                     explanation="If you want to exclude commands reserved for higher levels",
                     allow_blank=True)
        self.add_set("destination", self.read_element('autodoc', 'destination'),
                     explanation="Where to store the B3 documentation file: you can use a filepath or an FTP url",
                     allow_blank=True)

        xml.data("\n\t")
        xml.end()
        xml.data("\n\t")

        # messages settings
        self.add_buffer("""\n-------------------------------- MESSAGES -------------------------------------\n""")

        xml.start("settings", name="messages")

        # in this section we also need to check if we have old version messages! they contain: %s
        if '%s' in self.read_element('messages', 'kicked_by', '%s'):
            self.add_set("kicked_by", "$clientname^7 was kicked by $adminname^7 $reason", allow_blank=False)
        else:
            self.add_set("kicked_by", self.read_element('messages', 'kicked_by', '$clientname^7 was kicked by $adminname^7 $reason'), allow_blank=False)

        if '%s' in self.read_element('messages', 'kicked', '%s'):
            self.add_set("kicked", "$clientname^7 was kicked $reason", allow_blank=False)
        else:
            self.add_set("kicked", self.read_element('messages', 'kicked', '$clientname^7 was kicked $reason'), allow_blank=False)

        if '%s' in self.read_element('messages', 'banned_by', '%s'):
            self.add_set("banned_by", "$clientname^7 was banned by $adminname^7 $reason", allow_blank=False)
        else:
            self.add_set("banned_by", self.read_element('messages', 'banned_by', '$clientname^7 was banned by $adminname^7 $reason'), allow_blank=False)

        if '%s' in self.read_element('messages', 'banned', '%s'):
            self.add_set("banned", "$clientname^7 was banned $reason", allow_blank=False)
        else:
            self.add_set("banned", self.read_element('messages', 'banned', '$clientname^7 was banned $reason'), allow_blank=False)

        if '%s' in self.read_element('messages', 'temp_banned_by', '%s'):
            self.add_set("temp_banned_by", "$clientname^7 was temp banned by $adminname^7 for $banduration^7 $reason", allow_blank=False)
        else:
            self.add_set("temp_banned_by", self.read_element('messages', 'temp_banned_by', '$clientname^7 was temp banned by $adminname^7 for $banduration^7 $reason'), allow_blank=False)

        if '%s' in self.read_element('messages', 'temp_banned', '%s'):
            self.add_set("temp_banned", "$clientname^7 was temp banned for $banduration^7 $reason", allow_blank=False)
        else:
            self.add_set("temp_banned", self.read_element('messages', 'temp_banned', '$clientname^7 was temp banned for $banduration^7 $reason'), allow_blank=False)

        if '%s' in self.read_element('messages', 'unbanned_by', '%s'):
            self.add_set("unbanned_by", "$clientname^7 was un-banned by $adminname^7 $reason", allow_blank=False)
        else:
            self.add_set("unbanned_by", self.read_element('messages', 'unbanned_by', '$clientname^7 was un-banned by $adminname^7 $reason'), allow_blank=False)

        if '%s' in self.read_element('messages', 'unbanned', '%s'):
            self.add_set("unbanned", "$clientname^7 was un-banned $reason", allow_blank=False)
        else:
            self.add_set("unbanned", self.read_element('messages', 'unbanned', '$clientname^7 was un-banned $reason'), allow_blank=False)

        xml.data("\n\t")
        xml.end()
        xml.data("\n\t")

        # plugins settings
        self.add_buffer("""\n--------------------------- PLUGIN CONFIG PATH --------------------------------\n""")

        xml.start("settings", name="plugins")
        self.add_set("external_dir", self.read_element('plugins', 'external_dir', '@b3/extplugins'),
                     explanation="The directory where external plugins may be found",
                     allow_blank=False,
                     validate=lambda x: os.path.isdir(self.getAbsolutePath(x)))
        xml.data("\n\t")
        xml.end()
        xml.data("\n\t")

        # plugins
        self.add_buffer("""\n--------------------------- INSTALLING PLUGINS --------------------------------\n""")

        xml.start("plugins")
        xml.data("\n\t\t")
        xml.comment("""
            You can load a plugin but having it disabled by default. This
            allows to later enabled it ingame with the !enable command. To do so use the following syntax:\n
                plugin name=\"adv\" config=\"@conf/plugin_adv.xml\" disabled=\"yes\"\n
            You can override the plugin path (official plugins and extplugins folders)
            by specifying the exact location of the plugin file with the 'path' attribute:\n
                plugin name=\"adv\" config=\"@conf/plugin_adv.xml\" path=\"C:/somewhere/else/\"
        """)

        self.autoinstallplugins = self.raw_default("Do you want to (auto)install all plugins?", "yes")
        if self.autoinstallplugins == 'yes':
            self.read_plugins()
        else:
            self.add_plugin("admin", "@conf/plugin_admin.ini", prompt=False)
            self.add_plugin("adv", "@conf/plugin_adv.xml")
            self.add_plugin("censor", "@conf/plugin_censor.xml")
            self.add_plugin("cmdmanager", "@conf/plugin_cmdmanager.ini")
            self.add_plugin("pingwatch", "@conf/plugin_pingwatch.ini")
            self.add_plugin("spamcontrol", "@conf/plugin_spamcontrol.ini")
            self.add_plugin("stats", "@conf/plugin_stats.ini")
            self.add_plugin("status", "@conf/plugin_status.ini")
            self.add_plugin("tk", "@conf/plugin_tk.ini")
            self.add_plugin("welcome", "@conf/plugin_welcome.ini")

            if self._set['punkbuster'] == "on":
                self.add_plugin("punkbuster", "@conf/plugin_punkbuster.ini")
                xml.data("\n\t\t")
            else:
                xml.data("\n\t\t")
                xml.comment("The punkbuster plugin was not installed since punkbuster is not supported or disabled")
                xml.data("\t\t")

        # install the plugin
        xml.comment("""
            The next plugins are external, 3rd party plugins and should reside in the external_dir. Example:
                plugin name=\"newplugin\" config=\"@b3/extplugins/newplugin/conf/pluigin_newplugin.ini\"
            You can add new/custom plugins to this list using the same form as above
        """)

        test = self.raw_default("Install xlrstats plugin? (yes/no)", 'no', allow_blank=False, validate=lambda x: x.lower() in ('yes', 'y', 'no', 'n'))
        if test.lower() in ('yes', 'y'):
            self.add_plugin("xlrstats", "@b3/extplugins/xlrstats/conf/plugin_xlrstats.ini", prompt=False)

        xml.data("\n\t")
        xml.end()
        xml.data("\n")
        xml.close(configuration)
        xml.flush()

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
            # if there is not a template available, use the distribution xml file
            default_tpl = os.path.join(self._configpath, 'conf', 'b3.distribution.xml')
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
            self.tree = ElementTree.parse(self._template)
        except Exception, msg:
            self.add_buffer('Could not parse XML file: %s\n' % str(msg))
            # backed up config file must be corrupt or not completed last setup, reset it to the default
            self.add_buffer('If you have troubles loading a backup configuration file, try to load the default...\n')
            self._template = ''
            return False
        else:
            return True

    def read_element(self, _set, _value, _default=''):
        """
        Returns a config value in _set with attribute _value.
        """
        l = list(self.tree.findall('settings'))
        for s in l:
            if s.attrib['name'] == _set:
                i = list(s.findall('set'))
                for v in i:
                    if v.attrib['name'] == _value:
                        return v.text
        return _default

    def read_plugins(self):
        """
        Writes plugins to the config read from a template.
        """
        l = list(self.tree.findall('plugins'))
        for s in l:
            plugins = list(s.findall('plugin'))
            for p in plugins:
                name = p.attrib['name']
                try:
                    config = p.attrib['config']
                    if config[:12] == 'external_dir':
                        config = ''.join((self._set['external_dir'], config[12:]))
                except:
                    config = None
                self.add_plugin(name, config, prompt=False)
        return None

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
        return (self._equalength - len(unicode(_string))) * " "

    def add_set(self, sname, sdflt, explanation="", silent=False, allow_blank=None, validate=None):
        """
        A routine to add a setting with a textnode to the config
        :param sname: The set name.
        :param sdflt: The set default value
        :param explanation: An help text to prompt to the user
        :param silent: Whether we have to hide the value entered from the buffer
        :param allow_blank: Whether we can accept an empty value for this set or not
        :param validate: The reference to a function that will validate the correctness of the input value
        """
        xml.data("\n\t\t")
        if explanation != "":
            self.add_explanation(explanation)
            xml.comment(explanation)
            xml.data("\t\t")
        if not silent:
            _value = self.raw_default(prompt=sname, dflt=sdflt, allow_blank=allow_blank, validate=validate)
        else:
            _value = sdflt

        xml.element("set", _value, name=sname)

        # store values for later use ie. enabling the punkbuster plugin
        self._set[str(sname)] = str(_value)

        if not silent:
            self.add_buffer(str(sname) + self.equalize(sname) + ": " + unicode(_value) + "\n")

    def add_plugin(self, sname, sconfig=None, default="yes", prompt=True):
        """
        A routine to add a plugin to the config
        """
        if prompt:
            test = self.raw_default("Install %s plugin? (yes/no)" % sname, default, allow_blank=False, validate=lambda x: x.lower() in ('yes', 'y', 'no', 'n'))
            if test.lower() not in ('yes', 'y'):
                return False

        if self.autoinstallplugins:
            config = sconfig
        else:
            config = self.raw_default("Enter plugin %s configuration file path" % sname, sconfig)

        xml.data("\n\t\t")
        if not config:
            xml.element("plugin", name=sname)
            self.add_buffer("plugin: " + str(sname) + "\n")
        else:
            xml.element("plugin", name=sname, config=config)
            self.add_buffer("plugin: " + str(sname) + ", config: " + str(config) + "\n")
        return True

    def raw_default(self, prompt, dflt=None, allow_blank=None, validate=None):
        """
        Prompt user for input and don't accept an empty value.
        :param prompt: The value to be entered
        :param dflt: An optional default value
        :param allow_blank: Whether to accept blank values or not
        :param validate: The reference to a function that will validate the correctness of the input value
        """
        if dflt:
            newprompt = "%s [%s]" % (prompt, dflt)
        else:
            newprompt = "%s" % prompt

        res = raw_input(newprompt + self.equalize(newprompt) + ": ")

        # backup using default if necessary
        if self.is_empty(res) and dflt:
            res = dflt

        if self.is_empty(res):
            # if we have an empty value check if we actually can accept it
            if not allow_blank:
                # if we can't accept it, keep prompting the same question
                res = self.raw_default(prompt=prompt, dflt=dflt, allow_blank=allow_blank, validate=validate)
            else:
                res = ''
        else:
            if validate and callable(validate):
                if not validate(res):
                    # if we can't accept it, keep prompting the same question
                    res = self.raw_default(prompt=prompt, dflt=dflt, allow_blank=allow_blank, validate=validate)
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
                fname = functions.right_cut(_file, '.xml') + stamp + ".xml"
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
              "  3. You did not modify the distributed b3.xml prior starting B3"
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
            if os.path.isfile(self.getAbsolutePath('@b3/%s/sql/b3-update-1.3.0.sql' % dsndict['protocol'])):
                try:
                    print 'Updating database to version 1.3.0...'
                    database.queryFromFile('@b3/%s/sql/b3-update-1.3.0.sql' % dsndict['protocol'])
                except Exception, msg:
                    print "WARNING: could not update database to version 1.3.0 properly: %s" % str(msg)
                    self.test_exit("[Enter] to continue update procedure, \'abort\' to quit")

        # update to v1.6.0
        if _currentversion >= '1.6.0':
            # update only if SQL file exists (some protocols do not have to update since they are new)
            if os.path.isfile(self.getAbsolutePath('@b3/%s/sql/b3-update-1.6.0.sql' % dsndict['protocol'])):
                try:
                    print 'Updating database to version 1.6.0...'
                    database.queryFromFile('@b3/%s/sql/b3-update-1.6.0.sql' % dsndict['protocol'])
                except Exception, msg:
                    print "WARNING: could not update database to version 1.6.0 properly: %s" % str(msg)
                    self.test_exit("[Enter] to continue update procedure, \'abort\' to quit")

        # update to v1.7.0
        if _currentversion >= '1.7.0':
            # update only if SQL file exists (some protocols do not have to update since they are new)
            if os.path.isfile(self.getAbsolutePath('@b3/%s/sql/b3-update-1.7.0.sql' % dsndict['protocol'])):
                try:
                    print 'Updating database to version 1.7.0...'
                    database.queryFromFile('@b3/%s/sql/b3-update-1.7.0.sql' % dsndict['protocol'])
                except Exception, msg:
                    print "WARNING: could not update database to version 1.7.0 properly: %s" % str(msg)
                    self.test_exit("[Enter] to continue update procedure, \'abort\' to quit")

        # update to v1.8.1
        if _currentversion >= '1.8.1':
            # update only if SQL file exists (some protocols do not have to update since they are new)
            if os.path.isfile(self.getAbsolutePath('@b3/%s/sql/b3-update-1.8.1.sql' % dsndict['protocol'])):
                try:
                    print 'Updating database to version 1.8.1...'
                    database.queryFromFile('@b3/%s/sql/b3-update-1.8.1.sql' % dsndict['protocol'])
                except Exception, msg:
                    print "WARNING: could not update database to version 1.8.1 properly: %s" % str(msg)
                    self.test_exit("[Enter] to continue update procedure, \'abort\' to quit")

        # update to v1.9.0
        if _currentversion >= '1.9.0':
            # update only if SQL file exists (some protocols do not have to update since they are new)
            if os.path.isfile(self.getAbsolutePath('@b3/%s/sql/b3-update-1.9.0.sql' % dsndict['protocol'])):
                try:
                    print 'Updating database to version 1.9.0...'
                    database.queryFromFile('@b3/%s/sql/b3-update-1.9.0.sql' % dsndict['protocol'])
                except Exception, msg:
                    print "WARNING: could not update database to version 1.9.0 properly: %s" % str(msg)
                    self.test_exit("[Enter] to continue update procedure, \'abort\' to quit")

        if _currentversion >= '1.10.0':
            # update only if SQL file exists (some protocols do not have to update since they are new)
            if os.path.isfile(self.getAbsolutePath('@b3/%s/sql/b3-update-1.10.0.sql' % dsndict['protocol'])):
                try:
                    print 'Updating database to version 1.10.0...'
                    database.queryFromFile('@b3/%s/sql/b3-update-1.10.0.sql' % dsndict['protocol'])
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

