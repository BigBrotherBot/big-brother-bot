#!/usr/bin/env python
#
# BigBrotherBot(B3) (www.bigbrotherbot.com)
# Copyright (C) 2009 Mark "xlr8or" Weirath
# 
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

__author__  = 'xlr8or'
__version__ = '0.0.1'

import b3, platform
import os.path
from xml.dom.minidom import Document

class Setup:
    _indentation = "    "
    _priority = 1

    def __init__(self):
        if platform.system() != 'Windows':
            os.system('clear')
        self.runSetup()

    def runSetup(self):
        global xml
        xml = Document()

        # first level
        _configuration = xml.createElement("configuration")
        xml.appendChild(_configuration)

        # B3 settings
        _section = xml.createElement("settings") 
        _section.setAttribute("name", "b3")
        _configuration.appendChild(_section)
        #<set name="parser">changeme</set>
        self.add_set(_section, "parser", "cod", "Define your game: cod/cod2/cod4/cod5/iourt41/etpro/wop/smg")
        #<set name="parser">changeme</set>
        self.add_set(_section, "database", "mysql://b3:password@localhost/b3", "Your database info: <mysql>://<db-user>:<db-password>@<db-server>/<db-name>")
        #<set name="bot_name">b3</set>
        self.add_set(_section, "bot_name", "b3")
        #<set name="bot_prefix">^0(^2b3^0)^7:</set>
        self.add_set(_section, "bot_prefix", "^0(^2b3^0)^7:")
        #<set name="time_format">%I:%M%p %Z %m/%d/%y</set>
        self.add_set(_section, "time_format", "%I:%M%p %Z %m/%d/%y")
        #<set name="time_zone">CST</set>
        self.add_set(_section, "time_zone", "CST")
        #<!-- 9 = verbose, 10 = debug, 21 = bot, 22 = console -->
        #<set name="log_level">9</set>
        self.add_set(_section, "log_level", "9", "How much detail in the logfile: 9 = verbose, 10 = debug, 21 = bot, 22 = console")
        #<set name="logfile">b3.log</set>
        self.add_set(_section, "logfile", "b3.log")

        # server settings
        _section = xml.createElement("settings") 
        _section.setAttribute("name", "server")
        _configuration.appendChild(_section)
        #<set name="rcon_password">password</set>
        self.add_set(_section, "rcon_password", "")
        #<set name="port">28960</set>
        self.add_set(_section, "port", "28960")
        #<set name="game_log">games_mp.log</set>
        self.add_set(_section, "game_log", "games_mp.log")
        #<set name="public_ip">127.0.0.1</set>
        self.add_set(_section, "public_ip", "127.0.0.1")
        #<set name="rcon_ip">127.0.0.1</set>
        self.add_set(_section, "rcon_ip", "127.0.0.1")
        #<set name="punkbuster">on</set>
        self.add_set(_section, "punkbuster", "on", "Punkbuster: on / off")

        # messages settings
        _section = xml.createElement("settings") 
        _section.setAttribute("name", "messages")
        _configuration.appendChild(_section)
        #<set name="kicked_by">%s^7 was kicked by %s^7 %s</set>
        self.add_set(_section, "kicked_by", "%s^7 was kicked by %s^7 %s")
        #<set name="kicked">%s^7 was kicked %s</set>
        self.add_set(_section, "kicked", "%s^7 was kicked %s")
        #<set name="banned_by">%s^7 was banned by %s^7 %s</set>
        self.add_set(_section, "banned_by", "%s^7 was banned by %s^7 %s")
        #<set name="banned">%s^7 was banned %s</set>
        self.add_set(_section, "banned", "%s^7 was banned %s")
        #<set name="temp_banned_by">%s^7 was temp banned by %s^7 for %s^7 %s</set>
        self.add_set(_section, "temp_banned_by", "%s^7 was temp banned by %s^7 for %s^7 %s")
        #<set name="temp_banned">%s^7 was temp banned for %s^7 %s</set>
        self.add_set(_section, "temp_banned", "%s^7 was temp banned for %s^7 %s")
        #<set name="unbanned_by">%s^7 was un-banned by %s^7 %s</set>
        self.add_set(_section, "unbanned_by", "%s^7 was un-banned by %s^7 %s")
        #<set name="unbanned">%s^7 was un-banned %s</set>
        self.add_set(_section, "unbanned", "%s^7 was un-banned %s")

        # plugins settings
        _section = xml.createElement("settings") 
        _section.setAttribute("name", "plugins")
        _configuration.appendChild(_section)
        #<set name="external_dir">@b3/extplugins</set>
        self.add_set(_section, "external_dir", "@b3/extplugins")

        # plugins
        _section = xml.createElement("plugins") 
        _configuration.appendChild(_section)
        #<plugin name="censor" priority="1" config="@b3/conf/plugin_censor.xml" />
        self.add_plugin(_section, "censor", "@b3/conf/plugin_censor.xml")
        #<plugin name="spamcontrol" priority="2" config="@b3/conf/plugin_spamcontrol.xml" />
        self.add_plugin(_section, "spamcontrol", "@b3/conf/plugin_spamcontrol.xml")
        #<plugin name="admin" priority="3" config="@b3/conf/plugin_admin.xml" />
        self.add_plugin(_section, "admin", "@b3/conf/plugin_admin.xml")
        #<plugin name="tk" priority="4" config="@b3/conf/plugin_tk.xml" />
        self.add_plugin(_section, "tk", "@b3/conf/plugin_tk.xml")
        #<plugin name="stats" priority="5" config="@b3/conf/plugin_stats.xml" />
        self.add_plugin(_section, "stats", "@b3/conf/plugin_stats.xml")
        #<plugin name="pingwatch" priority="6" config="@b3/conf/plugin_pingwatch.xml" />
        self.add_plugin(_section, "pingwatch", "@b3/conf/plugin_pingwatch.xml")
        #<plugin name="adv" priority="7" config="@b3/conf/plugin_adv.xml" />
        self.add_plugin(_section, "adv", "@b3/conf/plugin_adv.xml")
        #<plugin name="status" priority="8" config="@b3/conf/plugin_status.xml" />
        self.add_plugin(_section, "status", "@b3/conf/plugin_status.xml")
        #<plugin name="welcome" priority="9" config="@b3/conf/plugin_welcome.xml" />
        self.add_plugin(_section, "welcome", "@b3/conf/plugin_welcome.xml")
        #<plugin name="punkbuster" priority="11" config="@b3/conf/plugin_punkbuster.xml" />
        self.add_plugin(_section, "punkbuster", "@b3/conf/plugin_punkbuster.xml")


        #self.writeXML(xml.toxml())
        self.writeXML(xml.toprettyxml(indent=self._indentation))
        
    def add_explanation(self, etext):
        _prechar = "> "
        print _prechar+etext

    def add_set(self, ssection, sname, sdflt, explanation=""):
        """
        A routine to add a setting with a textnode to the config
        Usage: self.add_set(section, name, default value optional-explanation)
        """
        if explanation != "":
            self.add_explanation(explanation)
        _value = self.raw_default(sname, sdflt)
        _set = xml.createElement("set")
        _set.setAttribute("name", sname)
        _text = xml.createTextNode(_value)
        _set.appendChild(_text)
        ssection.appendChild(_set)

    def add_plugin(self, ssection, sname, sconfig, explanation=""):
         """
        A routine to add a plugin to the config
        Usage: self.add_plugin(section, pluginname, default-configfile, optional-explanation)
        Priority is increased automatically.
        """
       _q = "Install "+sname+" plugin? (yes/no)"
        _test = self.raw_default(_q, "yes")
        if _test == "no":
            return None
        if explanation != "":
            self.add_explanation(explanation)
        _set = xml.createElement("plugin")
        _set.setAttribute("name", sname)
        _set.setAttribute("priority", str(self._priority))
        _config = self.raw_default("config", sconfig)
        _set.setAttribute("config", _config)
        ssection.appendChild(_set)
        self._priority += 1

    def raw_default(self, prompt, dflt=None):
        if dflt: 
            prompt = "%s [%s]: " % (prompt, dflt)
        else:
            prompt = "%s: " % (prompt)
        res = raw_input(prompt)
        if not res and dflt:
            return dflt
        if res == "":
            print "ERROR: No value was entered! Check your config file later!"
        return res         

    def writeXML(self, xml):
        try:
            self._outputFile = "b3-conf.xml"
            #self.debug('Writing XML status to %s', _outputFile)
            f = file(self._outputFile, 'w')
            f.write(xml)
            f.close()
            print self._outputFile+" written."
        except:
            print "ERROR: There was an error writing the file: "+self._outputFile+"!"

if __name__ == '__main__':
    from b3.fake import fakeConsole
    from b3.fake import joe
    from b3.fake import simon
    
    Setup()