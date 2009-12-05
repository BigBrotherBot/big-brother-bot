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
__version__ = '0.1.0'

import platform, shutil, time
import os.path
from lib.elementtree.SimpleXMLWriter import XMLWriter

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
        self._outputFile = self.raw_default("Location and name of the configfile", self._config)
        #Creating Backup
        self.backupFile(self._outputFile)
        self.runSetup()
        raise SystemExit('Restart B3 or reconfigure B3 using option: -s')

    def runSetup(self):
        global xml
        xml = XMLWriter(self._outputFile)

        # first level
        configuration = xml.start("configuration")
        xml.data("\n    ")

        # B3 settings
        self.add_buffer('--B3 SETTINGS---------------------------------------------------\n')
        xml.start("settings", name="b3")
        self.add_set("parser", "cod", "Define your game: cod/cod2/cod4/cod5/iourt41/etpro/wop/smg")
        self.add_set("database", "mysql://b3:password@localhost/b3", "Your database info: [mysql]://[db-user]:[db-password]@[db-server]/[db-name]")
        self.add_set("bot_name", "b3", "Name of the bot")
        self.add_set("bot_prefix", "^0(^2b3^0)^7:", "Ingame messages are prefixed with this code, you can use colorcodes")
        self.add_set("time_format", "%I:%M%p %Z %m/%d/%y")
        self.add_set("time_zone", "CST", "The timezone your bot is in")
        self.add_set("log_level", "9", "How much detail in the logfile: 9 = verbose, 10 = debug, 21 = bot, 22 = console")
        self.add_set("logfile", "b3.log", "Name of the logfile the bot will generate")
        xml.data("\n    ")
        xml.end()
        xml.data("\n    ")

        # server settings
        self.add_buffer('\n--GAME SERVER SETTINGS------------------------------------------\n')
        xml.start("settings", name="server")
        self.add_set("rcon_password", "", "The RCON pass of your gameserver")
        self.add_set("port", "28960", "The port the server is running on")
        self.add_set("game_log", "games_mp.log", "The gameserver generates a logfile, put the path and name here")
        self.add_set("public_ip", "127.0.0.1", "The public IP your gameserver is residing on")
        self.add_set("rcon_ip", "127.0.0.1", "The IP the bot can use to send RCON commands to (127.0.0.1 when on the same box)")
        self.add_set("punkbuster", "on", "Is the gameserver running PunkBuster Anticheat: on/off")
        xml.data("\n    ")
        xml.end()
        xml.data("\n    ")

        # messages settings
        self.add_buffer('\n--MESSAGES------------------------------------------------------\n')
        xml.start("settings", name="messages")
        self.add_set("kicked_by", "%s^7 was kicked by %s^7 %s")
        self.add_set("kicked", "%s^7 was kicked %s")
        self.add_set("banned_by", "%s^7 was banned by %s^7 %s")
        self.add_set("banned", "%s^7 was banned %s")
        self.add_set("temp_banned_by", "%s^7 was temp banned by %s^7 for %s^7 %s")
        self.add_set("temp_banned", "%s^7 was temp banned for %s^7 %s")
        self.add_set("unbanned_by", "%s^7 was un-banned by %s^7 %s")
        self.add_set("unbanned", "%s^7 was un-banned %s")
        xml.data("\n    ")
        xml.end()
        xml.data("\n    ")

        # plugins settings
        self.add_buffer('\n--PLUGIN CONFIG PATH--------------------------------------------\n')
        xml.start("settings", name="plugins")
        self.add_set("external_dir", "@b3/extplugins")
        xml.data("\n    ")
        xml.end()
        xml.data("\n    ")

        # plugins
        self.add_buffer('\n--INSTALLING PLUGINS--------------------------------------------\n')
        xml.start("plugins")
        self.add_plugin("censor", "@b3/conf/plugin_censor.xml")
        self.add_plugin("spamcontrol", "@b3/conf/plugin_spamcontrol.xml")
        self.add_plugin("tk", "@b3/conf/plugin_tk.xml")
        self.add_plugin("stats", "@b3/conf/plugin_stats.xml")
        self.add_plugin("pingwatch", "@b3/conf/plugin_pingwatch.xml")
        self.add_plugin("adv", "@b3/conf/plugin_adv.xml")
        self.add_plugin("status", "@b3/conf/plugin_status.xml")
        self.add_plugin("welcome", "@b3/conf/plugin_welcome.xml")
        #<plugin name="punkbuster" priority="11" config="@b3/conf/plugin_punkbuster.xml" />
        self.add_plugin("punkbuster", "@b3/conf/plugin_punkbuster.xml")
        xml.data("\n        ")
        xml.comment("You can add new/custom plugins to this list using the same form as above.")
        xml.data("        ")
        xml.comment("Just make sure you don't have any duplicate priority values!")
        xml.data("    ")
        xml.end()

        xml.data("\n")
        xml.close(configuration)
        self.add_buffer('\n--FINISHED CONFIGURATION----------------------------------------\n')

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

    def add_set(self, sname, sdflt, explanation=""):
        """
        A routine to add a setting with a textnode to the config
        Usage: self.add_set(name, default value optional-explanation)
        """
        xml.data("\n        ")
        if explanation != "":
            self.add_explanation(explanation)
            xml.comment(explanation)
            xml.data("        ")
        _value = self.raw_default(sname, sdflt)
        xml.element("set", _value, name=sname)
        self.add_buffer(str(sname)+self.equaLize(sname)+": "+str(_value)+"\n")

    def add_plugin(self, sname, sconfig, explanation=""):
        """
        A routine to add a plugin to the config
        Usage: self.add_plugin(pluginname, default-configfile, optional-explanation)
        Priority is increased automatically.
        """
        _q = "Install "+sname+" plugin? (yes/no)"
        _test = self.raw_default(_q, "yes")
        if _test == "no":
            return None
        if explanation != "":
            self.add_explanation(explanation)
        _config = self.raw_default("config", sconfig)
        xml.data("\n        ")
        xml.element("plugin", name=sname, priority=str(self._priority), config=_config)
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

    # funtion not longer needed when using ElementTree
    def writeXML(self, xml):
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
        print "\n--BACKUP/CREATE CONFIGFILE--------------------------------------\n"
        print "    Trying to backup the original "+_file+"..."
        try:
            _stamp = time.strftime("-%d_%b_%Y_%H.%M.%S", time.gmtime())
            _fname = _file+_stamp+".xml"
            shutil.copy(_file, _fname)
            print "    Backup success, "+_file+" copied to : %s" % _fname
            print "    If you need to abort setup, you can restore by renaming the backup file."
            self.testExit()
        except:
            print "    A file with this location/name does not yet exist,\n    I'm about to generate it...\n"
            self.testExit()

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
    #dom.Element.writexml = fixed_writexml


if __name__ == '__main__':
    #from b3.fake import fakeConsole
    #from b3.fake import joe
    #from b3.fake import simon
    
    Setup('test.xml')