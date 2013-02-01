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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
# CHANGELOG:
# 2010/03/21 - 0.2.1 - Courgette
#    * fix bug on config path which showed up only when run as a .exe
# 2010/03/27 - 0.2.2 - xlr8or
#    * minor improvements, added port to db-conn, default value for yes/no in add_plugin()
# 2010/04/17 - 0.3 -Courgette
#    * remove plugin priority related code to follow with parser.py v1.16 changes
# 2010/04/27 - 0.4 - Bakes
#    * added proper BC2 support to the setup wizard.
#    * changed censor and spamcontrol plugins to be added before admin.
#      this means that people who spam or swear in admin commands are
#      warned, rather than the event just being handled in the admin
#      plugin and veto'd elsewhere.
# 2010/10/11 - 0.5 - xlr8or
#    * added MOH support
# 2010/11/07 - 0.5.1 - GrosBedo
#    * edited default messages settings
# 2010/11/07 - 0.5.2 - GrosBedo
#    * added default values of lines_per_second and delay
#    * added more infos about the http access for gamelog
# 2011/02/06 - 0.6 - xlr8or
#    * setup now reads values from an existing config or a distribution example
#    * added COD7 support
# 2011/03/10 - 0.7 - xlr8or
#    * Don't let setup fail when SQL file cannot be opened
# 2011/03/12 - 0.8 - xlr8or
#    * Better handling of execution of b3.sql
#    * Bugfix in message section
#    * use tempfile until setup is completed
# 2011/05/19 - 1.0 - xlr8or
#    * Added Update class
#    * Version 1.0 merged into master branch (for B3 v1.6.0 release)
# 2011/11/12 - 1.1 - courgette
#    * can install external plugins having a module defined as a directory instead as as a python file
# 2012/01/08 - 1.2 - xlr8or
#    * Added: xlrstats-update-2.6.1.sql
#    * Fixed bug that would not update the xlrstats tables
# 2012/10/19 - 1.3 - courgette
#    * Added: Ravaged game
# 2012/10/24 - 1.4 - courgette
#   * Added: iourt42 custom settings
# 2012/10/31 - 1.5 - courgette
#   * Added: arma2 support
#
# This section is DoxuGen information. More information on how to comment your code
# is available at http://wiki.bigbrotherbot.net/doku.php/customize:doxygen_rules
## @file
# The setup procedure, to create a new configuration file (b3.xml)

__author__ = 'xlr8or'
__version__ = '1.5'

import platform
import urllib2
import shutil
import os
import sys
import time
import zipfile
import glob
import pkg_handler
import functions
import tempfile
from lib.elementtree.ElementTree import ElementTree
from lib.elementtree.SimpleXMLWriter import XMLWriter
from distutils import version
from urlparse import urlsplit

__version__ = pkg_handler.version(__name__)
modulePath = pkg_handler.resource_directory(__name__)

_buffer = ''
_equaLength = 15
_indentation = '    '


class Setup:
    _pver = sys.version.split()[0]
    _indentation = '    '
    _config = r'b3/conf/b3.xml'
    _template = ''
    _templatevar = ''
    _buffer = ''
    _equaLength = 15
    ## @todo bfbc2 and moh need to be added later when parsers correctly implemented pb.
    _PBSupportedParsers = ['cod', 'cod2', 'cod4', 'cod5', 'cod6', 'cod7', 'cod8']
    _frostBite = ['bfbc2', 'moh', 'bf3']

    def __init__(self, config=None):
        if config:
            self._config = config
        elif self.getB3Path() != "":
            self._config = self.getB3Path() + r'/conf/b3.xml'
        print self._config
        self.introduction()
        self.clearscreen()
        self._outputFile = self.raw_default("Location and name of the new configfile", self._config)
        self._outputTempFile = tempfile.NamedTemporaryFile(delete=False)
        #Creating Backup
        self.backupFile(self._outputFile)
        self.runSetup()
        # copy the config to it's final version
        shutil.copy(self._outputTempFile.name, self._outputFile)
        try:
            # try to delete the tempfile. this fails on Windows in some cases
            os.unlink(self._outputTempFile.name)
        except:
            pass
        raise SystemExit('Restart B3 or reconfigure B3 using option: -s')

    def runSetup(self):
        """ The main function that handles the setup steps """
        global xml
        xml = XMLWriter(self._outputTempFile, "UTF-8")

        # write appropriate header
        xml.declaration()
        xml.comment("\n This file is generated by the B3 setup Procedure.\n\
 If you want to regenerate this file and make sure the format is\n\
 correct, you can invoke the setup procedure with the\n\
 command : b3_run -s b3.xml\n\n\
 This is B3 main config file (the one you specify when you run B3 with the\n\
 command : b3_run -c b3.xml)\n\n\
 For any change made in this config file, you have to restart the bot.\n\
 Whenever you can specify a file/directory path, the following shortcuts\n\
 can be used :\n\
  @b3 : the folder where B3 code is installed in\n\
  @conf : the folder containing this config file\n")

        # first level
        configuration = xml.start("configuration")
        xml.data("\n\t")

        # B3 settings
        self.add_buffer('--B3 SETTINGS---------------------------------------------------\n')
        xml.start("settings", name="b3")
        self.add_set("parser", "",
                     """\
Define your game: cod/cod2/cod4/cod5/cod6/cod7/cod8
                  iourt41/iourt42
                  bfbc2/bf3/moh
                  etpro/altitude/oa081/smg/sof2/wop/wop15
                  homefront/ro2/csgo/ravaged/arma2""")

        # set a template xml file to read existing settings from
        _result = False
        while not _result:
            _result = self.load_template()
            if _result:
                self.add_buffer('Configuration values from [%s] loaded successfully\n' % (self._template))
                break

        # getting database info, test it and set up the tables
        self.add_set("database", self.read_element('b3', 'database', 'mysql://b3:password@localhost/b3'),
                     "Your database info: [mysql]://[db-user]:[db-password]@[db-server[:port]]/[db-name]")
        self.add_buffer('Testing and Setting Up Database...\n')
        # try to install the tables if they do not exist
        _sqlfiles = ['@b3/sql/b3.sql', 'b3/sql/b3.sql', 'sql/b3.sql']
        _sqlc = 0
        _sqlresult = 'notfound'
        while _sqlresult == 'notfound' and _sqlc < len(_sqlfiles):
            _sqlresult = self.executeSql(_sqlfiles[_sqlc], self._set_database)
            _sqlc += 1
        if _sqlresult == 'notfound':
            # still not found? prompt for the complete path and filename
            _sqlfile = self.raw_default('I could not find b3/sql/b3.sql. Please provide the full path and filename.')
            _sqlresult = self.executeSql(_sqlfile, self._set_database)
        if _sqlresult in ['notfound', 'couldnotopen']:
            # still no luck? giving up...
            self.add_buffer(
                'I give up, I could not find or open SQL file, you will need to import the database tables manually')

        self.add_set("bot_name", self.read_element('b3', 'bot_name', 'b3'), "Name of the bot")
        self.add_set("bot_prefix", self.read_element('b3', 'bot_prefix', '^0(^2b3^0)^7:'),
                     "Ingame messages are prefixed with this code, you can use colorcodes", allow_blank=True)
        self.add_set("time_format", self.read_element('b3', 'time_format', '%I:%M%p %Z %m/%d/%y'))
        self.add_set("time_zone", self.read_element('b3', 'time_zone', 'CST'),
                     "The timezone your bot is in")
        self.add_set("log_level", self.read_element('b3', 'log_level', '9'),
                     "How much detail in the logfile: 9 = verbose, 10 = debug, 21 = bot, 22 = console")
        self.add_set("logfile", self.read_element('b3', 'logfile', 'b3.log'),
                     "Name of the logfile the bot will generate")
        xml.data("\n\t")
        xml.end()
        xml.data("\n\t")

        # BFBC2 specific settings
        if self._set_parser == 'bfbc2':
            self.add_buffer('\n--BFBC2 SPECIFIC SETTINGS---------------------------------------\n')
            xml.start("settings", name="bfbc2")
            self.add_set("max_say_line_length", self.read_element('bfbc2', 'max_say_line_length', '100'),
                         "how long do you want the lines to be restricted to in the chat zone. (maximum length is 100)")
            xml.data("\n\t")
            xml.end()
            xml.data("\n\t")

        # MOH specific settings
        if self._set_parser == 'moh':
            self.add_buffer('\n--MOH SPECIFIC SETTINGS-----------------------------------------\n')
            xml.start("settings", name="moh")
            self.add_set("max_say_line_length", self.read_element('moh', 'max_say_line_length', '100'),
                         "how long do you want the lines to be restricted to in the chat zone. (maximum length is 100)")
            xml.data("\n\t")
            xml.end()
            xml.data("\n\t")

        # server settings
        self.add_buffer('\n--GAME SERVER SETTINGS------------------------------------------\n')
        xml.start("settings", name="server")

        # Frostbite specific
        if self._set_parser in self._frostBite:
            self.add_set("public_ip", self.read_element('server', 'public_ip', ''),
                         "The IP address of your gameserver")
            self.add_set("port", self.read_element('server', 'port', ''),
                         "The port people use to connect to your gameserver")
            self.add_set("rcon_ip", self.read_element('server', 'rcon_ip', ''),
                         "The IP of your gameserver B3 will connect to in order to send RCON commands. Usually the same as the public_ip")
            self.add_set("rcon_port", self.read_element('server', 'rcon_port', ''),
                         "The port of your gameserver that B3 will connect to in order to send RCON commands. NOT the same as the normal port.")
            self.add_set("rcon_password", self.read_element('server', 'rcon_password', ''),
                         "The RCON password of your gameserver.")
            self.add_set("timeout", self.read_element('server', 'timeout', '3'),
                         "RCON timeout", silent=True)

        # Ravaged specific
        elif self._set_parser == 'ravaged':
            self.add_set("public_ip", self.read_element('server', 'public_ip', ''),
                         "The IP address of your gameserver")
            self.add_set("port", self.read_element('server', 'port', '27015'),
                         "The query port of your gameserver (see SteamQueryPort in your Ravaged server config file)")
            self.add_set("rcon_ip", self.read_element('server', 'rcon_ip', ''),
                         "The IP of your gameserver B3 will connect to in order to send RCON commands. Usually the same as the public_ip")
            self.add_set("rcon_port", self.read_element('server', 'rcon_port', '13550'),
                         "The port of your gameserver that B3 will connect to in order to send RCON commands. (see RConPort in your Ravaged server config file)")
            self.add_set("rcon_password", self.read_element('server', 'rcon_password', ''),
                         "The RCON password of your gameserver. (see AdminPassword in your Ravaged server config file)")

        # Homefront specific
        elif self._set_parser == 'homefront':
            self.add_set("public_ip", self.read_element('server', 'public_ip', ''),
                         "The IP address of your gameserver")
            self.add_set("port", self.read_element('server', 'port', ''),
                         "The port people use to connect to your gameserver")
            self.add_set("rcon_ip", self.read_element('server', 'rcon_ip', ''),
                         "The IP of your gameserver B3 will connect to in order to send RCON commands. Usually the same as the public_ip")
            self.add_set("rcon_port", self.read_element('server', 'rcon_port', ''),
                         "The port of your gameserver that B3 will connect to in order to send RCON commands. NOT the same as the normal port.")
            self.add_set("rcon_password", self.read_element('server', 'rcon_password', ''),
                         "The RCON password of your gameserver.")

        # Arma2 specific
        elif self._set_parser == 'arma2':
            self.add_set("public_ip", self.read_element('server', 'public_ip', ''),
                         "The IP address of your gameserver")
            self.add_set("port", self.read_element('server', 'port', ''),
                         "The ArmA2 game network communication port")
            self.add_set("rcon_ip", self.read_element('server', 'rcon_ip', ''),
                         "The IP of your gameserver B3 will connect to in order to send RCON commands. Usually the same as the public_ip")
            self.add_set("rcon_password", self.read_element('server', 'rcon_password', ''),
                         "The RCON password of your gameserver.")

        # Urban Terror specific
        elif self._set_parser == 'iourt42':
            self.add_set("game_log", self.read_element('server', 'game_log', ''),
                "The gameserver generates a logfile, put the path and name here")
            self.add_set("public_ip", self.read_element('server', 'public_ip', ''),
                "The public IP your gameserver is residing on")
            self.add_set("port", self.read_element('server', 'port', ''),
                "The port the server is running on")
            self.add_set("rcon_ip", self.read_element('server', 'rcon_ip', ''),
                "The IP the bot can use to send RCON commands to (127.0.0.1 when on the same box)")
            self.add_set("rcon_password", self.read_element('server', 'rcon_password', ''),
                "The RCON pass of your gameserver")
            self.add_set("permban_with_frozensand", self.read_element('server', 'permban_with_frozensand', 'no'),
                         "Permban with Frozen Sand auth system")
            self.add_set("tempban_with_frozensand", self.read_element('server', 'tempban_with_frozensand', 'no'),
                         "Tempban with Frozen Sand auth system")

        # Q3A specific
        else:
            self.add_set("rcon_password", self.read_element('server', 'rcon_password', ''),
                         "The RCON pass of your gameserver")
            self.add_set("port", self.read_element('server', 'port', ''),
                         "The port the server is running on")
            # check if we can run cod7 remote gamelog retrieval
            if version.LooseVersion(self._pver) < version.LooseVersion('2.6.0') and self._set_parser == 'cod7':
                self.add_buffer('\nERROR:\n  You are running python ' + self._pver +
                                ', remote log functionality\n  is not available prior to python version 2.6.0\nYou need to update to python version 2.6+ before you can run B3 for CoD7!')
                self.testExit()
            elif self._set_parser == 'cod7':
                self.add_buffer(
                    '\nNOTE: You\'re gamelog must be set to this format:\nhttp://logs.gameservers.com/127.0.0.1:1024/xxxxx-1234-5678-9012-xxxxx')
            # determine if ftp functionality is available
            elif version.LooseVersion(self._pver) < version.LooseVersion('2.6.0'):
                self.add_buffer('\n  NOTE for game_log:\n  You are running python ' + self._pver +
                                ', ftp functionality\n  is not available prior to python version 2.6.0\n')
            else:
                self.add_buffer('\n  NOTE for game_log:\n  You are running python ' + self._pver +
                                ', the gamelog may also be\n  ftp-ed or http-ed in.\n  Define game_log like this:\n   ftp://[ftp-user]:[ftp-password]@[ftp-server]/path/to/games_mp.log\n  Or for web access (you can use htaccess to secure):\n   http://serverhost/path/to/games_mp.log\n')
            self.add_set("game_log", self.read_element('server', 'game_log', ''),
                         "The gameserver generates a logfile, put the path and name here")
            self.add_set("public_ip", self.read_element('server', 'public_ip', ''),
                         "The public IP your gameserver is residing on")
            self.add_set("rcon_ip", self.read_element('server', 'rcon_ip', ''),
                         "The IP the bot can use to send RCON commands to (127.0.0.1 when on the same box)")
            # configure default performances parameters
            self.add_set("delay", self.read_element('server', 'delay', '0.33'),
                         "Delay between each log reading. Set a higher value to consume less disk resources or bandwidth if you remotely connect (ftp or http remote log access)"
                         , silent=True)
            self.add_set("lines_per_second", self.read_element('server', 'lines_per_second', '50'),
                         "Number of lines to process per second. Set a lower value to consume less CPU resources",
                         silent=True)

        # determine if PunkBuster is supported
        if self._set_parser in self._PBSupportedParsers:
            self.add_set("punkbuster", "on", "Is the gameserver running PunkBuster Anticheat: on/off")
        else:
            self.add_set("punkbuster", "off", "Is the gameserver running PunkBuster Anticheat: on/off", silent=True)

        xml.data("\n\t")
        xml.end()
        xml.data("\n\t")

        # update channel settings
        self.add_buffer('\n--UPDATE CHANNEL-------------------------------------------------\n')
        self.add_buffer("""
  B3 checks if a new version is available at startup against 3 different channels. Choose the
  channel you want to check against.

  Available channels are :
    stable : will only show stable releases of B3
    beta : will also check if a beta release is available
    dev : will also check if a development release is available

""")
        xml.start("settings", name="update")
        xml.data("\n\t\t")
        xml.comment("""B3 checks if a new version is available at startup. Choose here what channel you want to check against.
            Available channels are :
                stable : will only show stable releases of B3
                beta   : will also check if a beta release is available
                dev    : will also check if a development release is available
            If you don't know what channel to use, use 'stable'
        """)
        xml.data("\t\t")
        self.add_set("channel", self.read_element('update', 'channel', 'stable'), "stable, beta or dev")
        xml.data("\n\t")
        xml.end()
        xml.data("\n\t")

        # autodoc settings
        self.add_buffer('\n--AUTODOC-------------------------------------------------------\n')
        xml.start("settings", name="autodoc")
        xml.data("\n\t\t")
        xml.comment("Autodoc will generate a user documentation for all B3 commands")
        xml.data("\t\t")
        xml.comment("by default, a html documentation is created in your conf folder")
        self.add_set("type", self.read_element('autodoc', 'type', 'html'), "html, htmltable or xml")
        self.add_set("maxlevel", self.read_element('autodoc', 'maxlevel', '100'),
                     "if you want to exclude commands reserved for higher levels")
        self.add_set("destination", self.read_element('autodoc', 'destination', ''),
                     "Destination can be a file or a ftp url")
        xml.data("\n\t")
        xml.end()
        xml.data("\n\t")

        # messages settings
        self.add_buffer('\n--MESSAGES------------------------------------------------------\n')
        xml.start("settings", name="messages")
        # in this section we also need to check if we have old version messages! they contain: %s
        if '%s' in self.read_element('messages', 'kicked_by', '%s'):
            self.add_set("kicked_by", "$clientname^7 was kicked by $adminname^7 $reason")
        else:
            self.add_set("kicked_by",
                         self.read_element('messages', 'kicked_by', '$clientname^7 was kicked by $adminname^7 $reason'))

        if '%s' in self.read_element('messages', 'kicked', '%s'):
            self.add_set("kicked", "$clientname^7 was kicked $reason")
        else:
            self.add_set("kicked", self.read_element('messages', 'kicked', '$clientname^7 was kicked $reason'))

        if '%s' in self.read_element('messages', 'banned_by', '%s'):
            self.add_set("banned_by", "$clientname^7 was banned by $adminname^7 $reason")
        else:
            self.add_set("banned_by",
                         self.read_element('messages', 'banned_by', '$clientname^7 was banned by $adminname^7 $reason'))

        if '%s' in self.read_element('messages', 'banned', '%s'):
            self.add_set("banned", "$clientname^7 was banned $reason")
        else:
            self.add_set("banned", self.read_element('messages', 'banned', '$clientname^7 was banned $reason'))

        if '%s' in self.read_element('messages', 'temp_banned_by', '%s'):
            self.add_set("temp_banned_by", "$clientname^7 was temp banned by $adminname^7 for $banduration^7 $reason")
        else:
            self.add_set("temp_banned_by", self.read_element('messages', 'temp_banned_by',
                                                             '$clientname^7 was temp banned by $adminname^7 for $banduration^7 $reason'))

        if '%s' in self.read_element('messages', 'temp_banned', '%s'):
            self.add_set("temp_banned", "$clientname^7 was temp banned for $banduration^7 $reason")
        else:
            self.add_set("temp_banned", self.read_element('messages', 'temp_banned',
                                                          '$clientname^7 was temp banned for $banduration^7 $reason'))

        if '%s' in self.read_element('messages', 'unbanned_by', '%s'):
            self.add_set("unbanned_by", "$clientname^7 was un-banned by $adminname^7 $reason")
        else:
            self.add_set("unbanned_by", self.read_element('messages', 'unbanned_by',
                                                          '$clientname^7 was un-banned by $adminname^7 $reason'))

        if '%s' in self.read_element('messages', 'unbanned', '%s'):
            self.add_set("unbanned", "$clientname^7 was un-banned $reason")
        else:
            self.add_set("unbanned", self.read_element('messages', 'unbanned', '$clientname^7 was un-banned $reason'))

        xml.data("\n\t")
        xml.end()
        xml.data("\n\t")

        # plugins settings
        self.add_buffer('\n--PLUGIN CONFIG PATH--------------------------------------------\n')
        xml.start("settings", name="plugins")
        self.add_set("external_dir", self.read_element('plugins', 'external_dir', '@b3/extplugins'))
        xml.data("\n\t")
        xml.end()
        xml.data("\n\t")

        # plugins
        self.add_buffer('\n--INSTALLING PLUGINS--------------------------------------------\n')
        xml.start("plugins")
        xml.data("\n\t\t")
        xml.comment(
            "plugin order is important. Plugins that add new in-game commands all depend on the admin plugin. Make sure to have the admin plugin before them.")
        self.autoinstallplugins = self.raw_default("Do you want to (auto)install all plugins?", "yes")
        if self.autoinstallplugins == 'yes':
            self.read_plugins('plugins')
            # check if we are using a template
            if self._templatevar == 'template':
                self.installextplugins = self.raw_default(
                    "Would you like me to download and install extra, game specific plugins?", "no")
                if self.installextplugins == 'yes':
                    self.read_plugins('extplugins')
        else:
            self.add_plugin("censor", "@conf/plugin_censor.xml")
            self.add_plugin("spamcontrol", "@conf/plugin_spamcontrol.xml")
            self.add_plugin("admin", "@conf/plugin_admin.xml", explanation="the admin plugin is compulsory.",
                            prompt=False)
            self.add_plugin("tk", "@conf/plugin_tk.xml")
            self.add_plugin("stats", "@conf/plugin_stats.xml")
            self.add_plugin("pingwatch", "@conf/plugin_pingwatch.xml")
            self.add_plugin("adv", "@conf/plugin_adv.xml")
            self.add_plugin("status", "@conf/plugin_status.xml")
            self.add_plugin("welcome", "@conf/plugin_welcome.xml")
            if self._set_punkbuster == "on":
                self.add_plugin("punkbuster", "@conf/plugin_punkbuster.xml")
                xml.data("\n\t\t")
            else:
                xml.data("\n\t\t")
                xml.comment("The punkbuster plugin was not installed since punkbuster is not supported or disabled.")
                xml.data("\t\t")

            # ext plugins
            xml.comment(
                "The next plugins are external, 3rd party plugins and should reside in the external_dir. Example:")
            xml.data("\t\t")
            xml.comment("plugin config=\"@b3/extplugins/conf/newplugin.xml\" name=\"newplugin\"")
            _result = self.add_plugin("xlrstats", self._set_external_dir + "/conf/xlrstats.xml", default="no")
            if _result:
                self.executeSql('@b3/sql/xlrstats.sql', self._set_database)

        # final comments
        xml.data("\n\t\t")
        xml.comment("You can add new/custom plugins to this list using the same form as above.")
        xml.data("\t")
        xml.end()

        xml.data("\n")
        xml.close(configuration)
        xml.flush()
        self.add_buffer('\n--FINISHED CONFIGURATION----------------------------------------\n')
        self.testExit(_question='Done, [Enter] to finish setup')


    def load_template(self):
        """ Load an existing config file or use the packaged examples"""
        if os.path.exists('b3/conf'):
            self._configpath = 'b3/'
        # perhaps setup is executed directly
        elif os.path.exists('conf/'):
            self._configpath = ''
        elif functions.main_is_frozen():
            self._configpath = os.environ['ALLUSERSPROFILE'] + '/BigBrotherBot/'
        else:
            self._configpath = self.raw_default(
                "Could not locate the config folder, please provide the full path (using /)").rstrip('/') + '/'

        # load the template based on the parser the user just chose
        _dflttemplate = self._configpath + 'conf/templates/b3.' + self._set_parser + '.tpl'
        self._templatevar = 'template'
        if not os.path.exists(_dflttemplate):
            _dflttemplate = self._configpath + 'conf/b3.distribution.xml'
            self._templatevar = 'distribution'

        if self._template != '':
            # means we just backed-up an old config with the same name
            _result = self.raw_default("Do you want to use the values from the backed-up config (%s)?"
                                       % (self._template), "yes")
            if _result != 'yes':
                self._template = self.raw_default("Load values from a template", _dflttemplate)
            else:
                self._templatevar = 'backup'
        else:
            self._template = self.raw_default("Load values from a template", _dflttemplate)

        self._template = self.getAbsolutePath(self._template)
        self.tree = ElementTree()
        try:
            self.tree.parse(self._template)
            return True
        except Exception, msg:
            self.add_buffer('Could not parse xml file: %s\n' % msg)
            # backed up config file must be corrupt or not completed last setup, reset it to the default
            self.add_buffer('Your previous config file was either empty, corrupt or not finished.\
             I Suggest we load the default...\n')
            self._template = ''
            return False

    def read_element(self, _set, _value, _default=''):
        """ Returns a config value in _set with attribute _value """
        l = list(self.tree.findall('settings'))
        for s in l:
            if s.attrib['name'] == _set:
                i = list(s.findall('set'))
                for v in i:
                    if v.attrib['name'] == _value:
                        return v.text
        return _default

    def read_plugins(self, _psection='plugins'):
        """ Writes plugins to the config read from a template """
        l = list(self.tree.findall(_psection))
        for s in l:
            plugins = list(s.findall('plugin'))
            for p in plugins:
                _name = p.attrib['name']
                try:
                    _config = p.attrib['config']
                    if _config[:12] == 'external_dir':
                        _config = ''.join((self._set_external_dir, _config[12:]))
                except:
                    _config = None
                try:
                    # do we need to install database tables?
                    _sql = p.attrib['sql']
                except:
                    _sql = None
                try:
                    # lets see if there is a plugin to download
                    _dl = p.attrib['dlocation']
                except:
                    _dl = None
                self.add_plugin(_name, _config, downlURL=_dl, sql=_sql, prompt=False)
        return None

    def add_explanation(self, etext):
        """ Add an explanation to the question asked by the setup procedure """
        _prechar = "> "
        print _prechar + etext

    def add_buffer(self, addition, autowrite=True):
        """ Add a line to the output buffer """
        self._buffer += addition
        if autowrite:
            self.writebuffer()

    def writebuffer(self):
        """ Clear the screen and write the output buffer to the screen """
        self.clearscreen()
        print self._buffer

    def equaLize(self, _string):
        """ Make the setup questions same length for prettier formatting """
        return (self._equaLength - len(unicode(_string))) * " "

    def add_set(self, sname, sdflt, explanation="", silent=False, allow_blank=None):
        """
        A routine to add a setting with a textnode to the config
        Usage: self.add_set(name, default value optional-explanation)
        """
        xml.data("\n\t\t")
        if explanation != "":
            self.add_explanation(explanation)
            xml.comment(explanation)
            xml.data("\t\t")
        if not silent:
            _value = self.raw_default(sname, sdflt, allow_blank)
        else:
            _value = sdflt
        xml.element("set", _value, name=sname)
        #store values into a variable for later use ie. enabling the punkbuster plugin.
        exec("self._set_" + str(sname) + " = \"" + unicode(_value) + "\"")
        if not silent:
            self.add_buffer(str(sname) + self.equaLize(sname) + ": " + unicode(_value) + "\n")

    def add_plugin(self, sname, sconfig=None, explanation=None, default="yes", downlURL=None, sql=None, prompt=True):
        """
        A routine to add a plugin to the config
        Usage: self.add_plugin(pluginname, default-configfile, optional-explanation, default-entry, optional-downloadlocation, optional-prompt)
        """
        if prompt:
            _q = "Install %s plugin? (yes/no)" % sname
            _test = self.raw_default(_q, default)
            if _test != "yes":
                return False

        if downlURL:
            self.add_buffer('  ... getting external plugin %s:\n' % sname)
            try:
                self.download(sname, downlURL)
            except:
                self.add_buffer("Couldn't get remote plugin %s, please install it manually.\n" % sname)

        if sql:
            self.add_buffer('  ... installing databasetables (%s)\n' % sql)
            _result = self.executeSql('@b3/sql/%s' % sql, self._set_database)
            if _result == 'notfound':
                self.add_buffer('  ... %s not found! Install database tables manually!\n' % sql)
            elif _result == 'couldnotopen':
                self.add_buffer('  ... unable to open %s! Install database tables manually!\n' % sql)
            elif not _result:
                self.add_buffer('  ... cannot execute %s! Install database tables manually!\n' % sql)

        if explanation:
            self.add_explanation(explanation)

        if self.autoinstallplugins:
            _config = sconfig
        else:
            _config = self.raw_default("config", sconfig)

        xml.data("\n\t\t")
        if not _config:
            xml.element("plugin", name=sname)
            self.add_buffer("plugin: " + str(sname) + "\n")
        else:
            xml.element("plugin", name=sname, config=_config)
            self.add_buffer("plugin: " + str(sname) + ", config: " + str(_config) + "\n")
        return True

    def raw_default(self, prompt, dflt=None, allow_blank=None):
        """ Prompt user for input and don't accept an empty value"""
        if dflt:
            prompt = "%s [%s]" % (prompt, dflt)
        else:
            prompt = "%s" % (prompt)
        res = raw_input(prompt + self.equaLize(prompt) + ": ")
        if not res and dflt:
            res = dflt
        if res == "":
            if allow_blank:
                #print "ERROR: No value was entered! Would you leave this value blank?"
                _yntest = self.raw_default("No value was entered! Would you leave this value blank?", "no")
                if _yntest != 'yes':
                    res = self.raw_default(prompt, dflt, allow_blank=True)
            else:
                print "ERROR: No value was entered! Give it another try!"
                res = self.raw_default(prompt, dflt)
        if not allow_blank: self.testExit(res)
        return res

    def clearscreen(self):
        if platform.system() in ('Windows', 'Microsoft'):
            os.system('cls')
        else:
            os.system('clear')

    def backupFile(self, _file):
        """ Create a backup of an existing config file """
        print "\n--BACKUP/CREATE CONFIGFILE--------------------------------------"
        print "    Trying to backup the original " + _file + "..."
        if not os.path.exists(_file):
            print "    No backup needed."
            print "    A file with this location/name does not yet exist,"
            print "    I'm about to generate a new config file!"
            self.testExit()
        else:
            try:
                _stamp = time.strftime("-%d_%b_%Y_%H.%M.%S", time.gmtime())
                _fname = _file.rstrip(".xml") + _stamp + ".xml"
                shutil.copy(_file, _fname)
                print "    Backup success, " + _file + " copied to : %s" % _fname
                print "    If you need to abort setup, you can restore by renaming the backup file."
                # a config with this name already exists, use it as a template
                self._template = _fname
                self.testExit()
            except OSError, why:
                print "\n    Error : %s\n" % str(why)
                self.testExit()

    def introduction(self):
        try:
            _uname = platform.uname()[1] + ", "
        except:
            _uname = "admin, "
        self.clearscreen()
        print "    WELCOME " + _uname + "TO THE B3 SETUP PROCEDURE"
        print "----------------------------------------------------------------"
        print "We're about to generate a main configuration file for "
        print "BigBrotherBot. This procedure is initiated when:\n"
        print " 1. you run B3 with the option --setup or -s"
        print " 2. the config you're trying to run does not exist"
        print "    (" + self._config + ")"
        print " 3. you did not modify the distributed b3.xml prior to"
        print "    starting B3."
        self.testExit()
        print "We will prompt you for each setting. We'll also provide default"
        print "values inside [] if applicable. When you want to accept a"
        print "default value you will only need to press Enter."
        print ""
        print "If you make an error at any stage, you can abort the setup"
        print "procedure by typing \'abort\' at the prompt. You can start"
        print "over by running B3 with the setup option: python b3_run.py -s"
        self.testExit()
        print "First you will be prompted for a location and name for this"
        print "configuration file. This is for multiple server setups, or"
        print "if you want to run B3 from a different setup file for your own"
        print "reasons. In a basic single instance install you will not have to"
        print "change this location and/or name. If a configuration file exists"
        print "we will make a backup first and tag it with date and time, so"
        print "you can always revert to a previous version of the config file."
        print ""
        print "This procedure is new, bugs may be reported on our forums at"
        print "www.bigbrotherbot.net"
        self.testExit(_question='[Enter] to continue to generate the configfile...')

    def testExit(self, _key='', _question='[Enter] to continue, \'abort\' to abort Setup: ',
                 _exitmessage='Setup aborted, run python b3_run.py -s to restart the procedure.'):
        """ Test the input for an exit code, give the user an option to abort setup """
        if _key == '':
            _key = raw_input('\n' + _question)
        if _key != 'abort':
            print "\n"
            return
        else:
            raise SystemExit(_exitmessage)

    def connectToDatabase(self, dbString):
        _db = None
        _dsnDict = functions.splitDSN(dbString)
        if _dsnDict['protocol'] == 'mysql':
            try:
                import MySQLdb

                _db = MySQLdb.connect(host=_dsnDict['host'], port=_dsnDict['port'], user=_dsnDict['user'],
                                      passwd=_dsnDict['password'], db=_dsnDict['path'][1:])
            except ImportError:
                self.add_buffer("You need to install python-mysqldb. Look for 'dependencies' in B3 documentation.\n")
                raise SystemExit()
            except Exception:
                try:
                    _db.close()
                except Exception:
                    pass
        else:
            self.add_buffer("%s protocol is not supported. Use mysql instead\n" % _dsnDict['protocol'])
            self.testExit(_question='Do you still want to continue? [Enter] to continue, \'abort\' to abort Setup: ')
        return _db

    def executeSql(self, file, dbString):
        """This method executes an external sql file on the current database"""
        self.db = self.connectToDatabase(dbString)
        sqlFile = file
        if self.db:
            self.add_buffer('Connected to the database. Executing sql.\n')
            sqlFile = self.getAbsolutePath(file)
            if os.path.exists(sqlFile):
                try:
                    f = open(sqlFile, 'r')
                except Exception:
                    self.db.close()
                    return 'couldnotopen'
                sql_text = f.read()
                f.close()
                sql_statements = sql_text.split(';')
                for s in sql_statements:
                    try:
                        self.db.query(s)
                    except Exception:
                        pass
                self.db.close()
            else:
                self.db.close()
                return 'notfound'
        else:
            self.add_buffer(
                'Connection to the database failed. Check the documentation how to add the database tables from %s manually.\n' % sqlFile)
            self.testExit(_question='Do you still want to continue? [Enter] to continue, \'abort\' to abort Setup: ')
        return 'success'

    def getB3Path(self):
        if functions.main_is_frozen():
            # which happens when running from the py2exe build
            return os.path.dirname(sys.executable)
        return modulePath

    def getAbsolutePath(self, path):
        """Return an absolute path name and expand the user prefix (~)"""
        if path[0:4] == '@b3/':
            path = os.path.join(self.getB3Path(), path[4:])
        return os.path.normpath(os.path.expanduser(path))

    def url2name(self, url):
        return os.path.basename(urlsplit(url)[2])

    def download(self, plugin_name, url, localFileName=None):
        absPath = self.getAbsolutePath(self._set_external_dir)
        localName = self.url2name(url)
        req = urllib2.Request(url)
        try:
            r = urllib2.urlopen(req)
            self.add_buffer('  ... downloading %s ...\n' % url)
        except Exception, msg:
            self.add_buffer('  ... download failed: %s\n' % msg)
            return None
        if r.info().has_key('Content-Disposition'):
            # If the response has Content-Disposition, we take file name from it
            localName = r.info()['Content-Disposition'].split('filename=')[1]
            if localName[0] == '"' or localName[0] == "'":
                localName = localName[1:-1]
        elif r.url != url:
        # if we were redirected, the real file name we take from the final URL
            localName = self.url2name(r.url)
        if localFileName:
        # we can force to save the file as specified name
            localName = localFileName

        packageLocation = absPath + "/packages/"
        localName = packageLocation + localName
        if not os.path.isdir(packageLocation):
            os.mkdir(packageLocation)
        f = open(localName, 'wb')
        f.write(r.read())
        f.close()
        tempExtractDir = packageLocation + "/temp/"
        self.extract(localName, tempExtractDir)
        # move the appropriate files to the correct folders
        for root, dirs, files in os.walk(tempExtractDir):
            # move all available .py files to the extplugins folder
            if root[-10:] == 'extplugins':
                for data in glob.glob(root + '/*.py'):
                    shutil.copy2(data, absPath)
            if root.endswith(os.path.join('extplugins', plugin_name)):
                # some plugin have a directory as the plugin module
                os.mkdir(os.path.join(absPath, plugin_name))
                for data in glob.glob(root + '/*.py'):
                    shutil.copy2(data, os.path.join(absPath, plugin_name))
            # move the config files to the extplugins/conf folder
            if root[-4:] == 'conf':
                for data in glob.glob(root + '/*.xml'):
                    ## @todo: downloading an extplugin for the second time will overwrite the existing extplugins config.
                    shutil.copy2(data, absPath + '/conf/')
            # check for .sql files and move them to the global sql folder
            for data in glob.glob(root + '/*.sql'):
                shutil.copy2(data, self.getAbsolutePath('@b3/sql/'))
        # remove the tempdir and its content
        shutil.rmtree(tempExtractDir)
        #os.remove(localName)

    def extract(self, file, dir):
        if not dir.endswith(':') and not os.path.exists(dir):
            os.mkdir(dir)
        zf = zipfile.ZipFile(file)
        zf.extractall(path=dir)
        

class Update(Setup):
    """ This class holds all update methods for the database"""

    def __init__(self, config=None):

        self.add_buffer('Updating the B3 database\n')
        self.add_buffer('------------------------\n')
        if config:
            self._config = config
        elif self.getB3Path() != "":
            self._config = self.getB3Path() + r'/conf/b3.xml'
        if os.path.exists(self._config):
            self.add_buffer('Using configfile: %s\n' % self._config)
            import config
            _conf = config.load(self._config)
        else:
            raise SystemExit('Configfile not found, create one first (run setup) or correct the startup parameter.')

        _dbstring = _conf.get('b3', 'database')
        _currentversion = version.LooseVersion(__version__)
        self.add_buffer('Current B3 version: %s\n' % _currentversion )

        # update to v1.3.0
        if _currentversion >= '1.3.0':
            self.executeSql('@b3/sql/b3-update-1.3.0.sql', _dbstring)
            self.add_buffer('Updating database to version 1.3.0...\n')
        else:
            self.add_buffer('Version older than 1.3.0...\n')

        # update to v1.6.0
        if _currentversion >= '1.6.0':
            self.executeSql('@b3/sql/b3-update-1.6.0.sql', _dbstring)
            self.add_buffer('Updating database to version 1.6.0...\n')
        else:
            self.add_buffer('Version older than 1.6.0...\n')

        # update to v1.7.0
        if _currentversion >= '1.7.0':
            self.executeSql('@b3/sql/b3-update-1.7.0.sql', _dbstring)
            self.add_buffer('Updating database to version 1.7.0...\n')
        else:
            self.add_buffer('Version older than 1.7.0...\n')

        # update to v1.8.1
        if _currentversion >= '1.8.1':
            self.executeSql('@b3/sql/b3-update-1.8.1.sql', _dbstring)
            self.add_buffer('Updating database to version 1.8.1...\n')
        else:
            self.add_buffer('Version older than 1.8.1...\n')

        # update to v1.9.0
        if _currentversion >= '1.9.0':
            self.executeSql('@b3/sql/b3-update-1.9.0.sql', _dbstring)
            self.add_buffer('Updating database to version 1.9.0...\n')
        else:
            self.add_buffer('Version older than 1.9.0...\n')

        # need to update xlrstats?
        #_result = self.raw_default('Do you have xlrstats installed (with default table names)?', 'yes')
        #if _result == 'yes':
        #    self.executeSql('@b3/sql/xlrstats-update-2.0.0.sql', _dbstring)
        #    self.executeSql('@b3/sql/xlrstats-update-2.4.0.sql', _dbstring)
        #    self.executeSql('@b3/sql/xlrstats-update-2.6.1.sql', _dbstring)

        #self.db = self.connectToDatabase(_dbstring)
        #self.optimizeTables()
        #self.db.close()

        raise SystemExit('Update finished, Restart B3 to continue.')

    
    def showTables(self):
        _tables = []
        q = 'SHOW TABLES'
        cursor = self.db.query(q)
        if (cursor and (cursor.rowcount > 0) ):
            while not cursor.EOF:
                r = cursor.getRow()
                n = str(r.values()[0])
                print r
                _tables.append(r.values()[0])
                cursor.moveNext()
        self.add_buffer('Available tables in this database: %s\n' %_tables)
        return _tables

    def optimizeTables(self, t=None):
        if not t:
            t = self.showTables()
        if type(t) == type(''):
            _tables = str(t)
        else:
            _tables = ', '.join(t)
        self.add_buffer('Optimizing Table(s): %s\n' % _tables)
        try:
            self.db.query('OPTIMIZE TABLE %s' % _tables )
            self.add_buffer('Optimize Success\n')
        except Exception, msg:
            self.add_buffer('Optimizing Table(s) Failed: %s, trying to repair...\n' %msg)
            self.repairTables(t)

    def repairTables(self, t=None):
        if not t:
            t = self.showTables()
        if type(t) == type(''):
            _tables = str(t)
        else:
            _tables = ', '.join(t)
        self.add_buffer('Repairing Table(s): %s\n' % _tables)
        try:
            self.db.query('REPAIR TABLE %s' % _tables )
            self.add_buffer('Repair Success\n')
        except Exception, msg:
            self.add_buffer('Repairing Table(s) Failed: %s\n' %msg)


    
    
#-----------------------------------------------------------------------------------------------------------------------
if __name__ == '__main__':
    #from b3.fake import fakeConsole
    #from b3.fake import joe
    #from b3.fake import simon

    #Setup('test.xml')
    Update('test.xml')
