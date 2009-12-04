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
__version__ = '0.0.4'

import platform, shutil, time
import os.path
from xml.dom.minidom import Document


class Setup:
    _indentation = "    "
    _priority = 1
    _config = "b3/conf/b3.xml"
    _buffer = ''
    _equaLength = 15

    def __init__(self, config=None):
        if config:
            self._config = config
        self.introduction()
        self.clearscreen()
        self.runSetup()
        raise SystemExit('Restart B3 or reconfigure B3 using option: -s')

    def runSetup(self):
        global xml
        xml = Document()

        # first level
        _configuration = xml.createElement("configuration")
        xml.appendChild(_configuration)

        # B3 settings
        self.add_buffer('--B3 SETTINGS---------------------------------------------------\n')
        _section = xml.createElement("settings") 
        _section.setAttribute("name", "b3")
        _configuration.appendChild(_section)
        #<set name="parser">changeme</set>
        self.add_set(_section, "parser", "cod", "Define your game: cod/cod2/cod4/cod5/iourt41/etpro/wop/smg")
        #<set name="parser">changeme</set>
        self.add_set(_section, "database", "mysql://b3:password@localhost/b3", "Your database info: <mysql>://<db-user>:<db-password>@<db-server>/<db-name>")
        #<set name="bot_name">b3</set>
        self.add_set(_section, "bot_name", "b3", "Name of the bot")
        #<set name="bot_prefix">^0(^2b3^0)^7:</set>
        self.add_set(_section, "bot_prefix", "^0(^2b3^0)^7:", "Ingame messages are prefixed with this code, you can use colorcodes")
        #<set name="time_format">%I:%M%p %Z %m/%d/%y</set>
        self.add_set(_section, "time_format", "%I:%M%p %Z %m/%d/%y")
        #<set name="time_zone">CST</set>
        self.add_set(_section, "time_zone", "CST", "The timezone your bot is in")
        #<!-- 9 = verbose, 10 = debug, 21 = bot, 22 = console -->
        #<set name="log_level">9</set>
        self.add_set(_section, "log_level", "9", "How much detail in the logfile: 9 = verbose, 10 = debug, 21 = bot, 22 = console")
        #<set name="logfile">b3.log</set>
        self.add_set(_section, "logfile", "b3.log", "Name of the logfile the bot will generate")

        # server settings
        self.add_buffer('\n--GAME SERVER SETTINGS------------------------------------------\n')
        _section = xml.createElement("settings") 
        _section.setAttribute("name", "server")
        _configuration.appendChild(_section)
        #<set name="rcon_password">password</set>
        self.add_set(_section, "rcon_password", "", "The RCON pass of your gameserver")
        #<set name="port">28960</set>
        self.add_set(_section, "port", "28960", "The port the server is running on")
        #<set name="game_log">games_mp.log</set>
        self.add_set(_section, "game_log", "games_mp.log", "The gameserver generates a logfile, put the path and name here")
        #<set name="public_ip">127.0.0.1</set>
        self.add_set(_section, "public_ip", "127.0.0.1", "The public IP your gameserver is residing on")
        #<set name="rcon_ip">127.0.0.1</set>
        self.add_set(_section, "rcon_ip", "127.0.0.1", "The IP the bot can use to send RCON commands to (127.0.0.1 when on the same box)")
        #<set name="punkbuster">on</set>
        self.add_set(_section, "punkbuster", "on", "Punkbuster: on / off", "Is the gameserver running PunkBuster Anticheat?")

        # messages settings
        self.add_buffer('\n--MESSAGES------------------------------------------------------\n')
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
        self.add_buffer('\n--PLUGIN CONFIG PATH--------------------------------------------\n')
        _section = xml.createElement("settings") 
        _section.setAttribute("name", "plugins")
        _configuration.appendChild(_section)
        #<set name="external_dir">@b3/extplugins</set>
        self.add_set(_section, "external_dir", "@b3/extplugins")

        # plugins
        self.add_buffer('\n--INSTALLING PLUGINS--------------------------------------------\n')
        _section = xml.createElement("plugins") 
        _configuration.appendChild(_section)
        #<plugin name="censor" priority="1" config="@b3/conf/plugin_censor.xml" />
        self.add_plugin(_section, "censor", "@b3/conf/plugin_censor.xml")
        #<plugin name="spamcontrol" priority="2" config="@b3/conf/plugin_spamcontrol.xml" />
        self.add_plugin(_section, "spamcontrol", "@b3/conf/plugin_spamcontrol.xml")
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

        self.add_buffer('\n--BACKUP/WRITE CONFIG-------------------------------------------\n')
        self.writeXML(xml.toxml())
        #self.writeXML(xml.toprettyxml(indent=self._indentation))
        
    def add_explanation(self, etext):
        _prechar = "> "
        print _prechar+etext

    def add_buffer(self, addition, autowrite=True):
        self._buffer += addition
        if autowrite:
            self.writebuffer()

    def writebuffer(self):
        self.clearscreen()
        print self._buffer

    def equaLize(self, _string):
        return (self._equaLength-len(str(_string)))*" "

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
        self.add_buffer(str(sname)+self.equaLize(sname)+": "+str(_value)+"\n")

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
        self.add_buffer("plugin: "+str(sname)+", priority: "+str(self._priority)+", config: "+str(_config)+"\n")
        self._priority += 1

    def raw_default(self, prompt, dflt=None):
        res = None
        if dflt: 
            prompt = "%s [%s]" % (prompt, dflt)
        else:
            prompt = "%s" % (prompt)
        res = raw_input(prompt+self.equaLize(prompt)+": ")
        if not res and dflt:
            res = dflt
        if res == "":
            print "ERROR: No value was entered! Give it another try!"
            res = self.raw_default(prompt, dflt)
        self.testExit(res)
        return res         

    def writeXML(self, xml):
        self._outputFile = self.raw_default("Location and name of the configfile", self._config)
        #Creating Backup
        self.backupFile(self._outputFile)
        self.clearscreen()
        try:
            f = file(self._outputFile, 'w')
            f.write(xml)
            f.close()
            print self._outputFile+" written."
        except:
            print "ERROR: There was an error writing the file: "+self._outputFile+"!"

    def clearscreen(self):
        if platform.system() != 'Windows':
            os.system('clear')
        else:
            os.system('cls')

    def backupFile(self, _file):
        print "    Trying to backup the original "+_file+"..."
        try:
            _stamp = time.strftime("-%d_%b_%Y_%H.%M.%S", time.gmtime())
            _fname = _file+_stamp+".xml"
            shutil.copy(_file, _fname)
            print "    Backup success, "+_file+" copied to : %s" % _fname
            self.testExit(_question='[Enter] to write %s, \'abort\' to abort Setup: ' %(_file))
        except:
            print "    A file with this location/name does not yet exist,\n    I'm about to generate it...\n"
            self.testExit(_question='[Enter] to write %s, \'abort\' to abort Setup: ' %(_file))

    def introduction(self):
        self.clearscreen()
        print "                WELCOME TO B3 SETUP PROCEDURE"
        print "----------------------------------------------------------------"
        print "We're about to generate a main configuration file for "
        print "BigBrotherBot. This procedure is initiated when:\n"
        print " 1. you run B3 with the option --setup or -s"
        print " 2. the config you're trying to run does not exist"
        print "    ("+self._config+")"
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
        print "At the end of setup you are prompted for a location and name for"
        print "this configuration file. This is for multiple server setups, or"
        print "if you want to run B3 from a different setup file for your own."
        print "reasons. In a basic single instance install you will not have to"
        print "change this location and/or name. If a configuration file exists"
        print "we will make a backup first and tag it with date and time, so"
        print "you can always revert to a previous version of the config file."
        print ""
        print "This procedure is new, bugs may be reported on our forums at"
        print "www.bigbrotherbot.com"
        self.testExit(_question='[Enter] to continue to generate the configfile...')

    def testExit(self, _key='', _question='[Enter] to continue, \'abort\' to abort Setup: ', _exitmessage='Setup aborted, run python b3_run.py -s to restart the procedure.'):
        if _key == '':
            _key = raw_input('\n'+_question)
        if _key != 'abort':
            print "\n"
            return
        else:
            raise SystemExit(_exitmessage)

    #code not implemented
    def fixed_writexml(self, writer, indent="", addindent="", newl=""):
        # indent = current indentation
        # addindent = indentation to add to higher levels
        # newl = newline string
        writer.write(indent+"<" + self.tagName)
    
        attrs = self._get_attributes()
        a_names = attrs.keys()
        a_names.sort()
    
        for a_name in a_names:
            writer.write(" %s=\"" % a_name)
            xml.dom.minidom._write_data(writer, attrs[a_name].value)
            writer.write("\"")
        if self.childNodes:
            if len(self.childNodes) == 1 \
              and self.childNodes[0].nodeType == xml.dom.minidom.Node.TEXT_NODE:
                writer.write(">")
                self.childNodes[0].writexml(writer, "", "", "")
                writer.write("</%s>%s" % (self.tagName, newl))
                return
            writer.write(">%s"%(newl))
            for node in self.childNodes:
                node.writexml(writer,indent+addindent,addindent,newl)
            writer.write("%s</%s>%s" % (indent,self.tagName,newl))
        else:
            writer.write("/>%s"%(newl))
    # replace minidom's function with ours
    #xml.dom.minidom.Element.writexml = fixed_writexml


if __name__ == '__main__':
    from b3.fake import fakeConsole
    from b3.fake import joe
    from b3.fake import simon
    
    Setup()