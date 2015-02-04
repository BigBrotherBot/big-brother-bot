#
# BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2005 Michael "ThorN" Thornton
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
# 04/02/2015 - 1.6.1  - Fenix      - fixed exception being generated when not using database to store status information
# 05/01/2014 - 1.6    - Fenix      - PostgreSQl support
# 30/08/2014 - 1.5    - Fenix      - syntax cleanup
#                                  - make use of the new onStop event handler
# 13/03/2014 - 1.4.18 - Fenix      - double check for server and client vars table to exists before attempting to create
#                                  - use the correct data type for 'Updated' column
#                                  - enforce database tables drop->create so we do not have to bother with schema updates
#                                  - minor bugfixes
# 28/23/2013 - 1.4.17 - Courgette  - close ftp connection
# 30/11/2013 - 1.4.16 - Courgette  - save status info to database by default
# 24/11/2013 - 1.4.15 - Fenix      - improved plugin configuration file loading
#                                  - PEP8 coding standards
# 22/02/2013 - 1.4.14 - Courgette  - fix the sanitize bug
# 10/02/2013 - 1.4.13 - Courgette  - add log message with more precise info when failing to sanitize data
# 26/10/2012 - 1.4.12 - Courgette  - makes sure 'Client' tags have a 'score' attribute
#                                  - better sync of DB and XML saving for XLRstats v3 webfront
# 12/08/2012 - 1.4.11 - Courgette  - will provide more debugging info about errors while generating the XML document
# 05/05/2012 - 1.4.10 - Courgette  - fixes reading config options 'svar_table' and 'client_table'
# 19/07/2011 - 1.4.9  - Freelander - fix errors during map change
# 25/04/2011 - 1.4.8  - Courgette  - in config file, settings/output_file can now use shortcuts such as @b3 and @conf
# 17/04/2011 - 1.4.7  - Courgette  - XML file generated is now using UTF-8 encoding
# 17/04/2011 - 1.4.6  - Courgette  - unicode compliant
# 30/03/2011 - 1.4.5 - SGT         - bugfix camelCasing timeLimit and fragLimit
# 06/01/2011 - 1.4.4 - Gammelbob   - additionally stores current svars and clients in database
# 13/08/2010 - 1.4.3 - xlr8or      - added running roundtime and maptime
# 08/08/2010 - 1.4.2 - xlr8or      - moved 'Game section' before 'Clients section', XLRstats needs gameinfo before it
#                                    adds clients to the playerlist
# 21/03/2010 - 1.4.1 - Courgette   - does not fail if there is no player score available
#                                  - make errors more verbose
# 23/11/2009 - 1.4.0 - Courgette   - on bot shutdown, write an empty status.xml document
#                                  - add tests
# 03/11/2009 - 1.3.1 - Bakes       - XML code is now produced through xml.dom.minidocument rather than concatenation.
#                                    This has a number of advantages.
# 03/11/2009 - 1.3.0 - Bakes       - combined statusftp and status. Use syntax ftp://user:password@host/path/to/status.xml
# 02/11/2009 - 1.2.7 - xlr8or      - if masked show masked level instead of real level
# 02/11/2009 - 1.2.6 - xlr8or      - sanitized xml data, cleaning ascii < 32 and > 126 (func is in functions.py)
# 21/11/2008 - 1.2.5 - Anubis      - added PlayerScores
# 12/03/2008 - 1.2.4 - Courgette   - properly escape strings to ensure valid xml
# 30/11/2005 - 1.2.3 - ThorN       - use PluginCronTab instead of CronTab
# 29/08/2005 - 1.2.0 - ThorN       - converted to use new event handlers

__author__ = 'ThorN'
__version__ = '1.6'

import b3
import b3.cron
import b3.plugin
import b3.events
import os
import re
import StringIO
import time

from b3 import functions
from b3.functions import sanitizeMe
from ConfigParser import NoOptionError
from ftplib import FTP
from xml.dom.minidom import Document


class StatusPlugin(b3.plugin.Plugin):

    _tkPlugin = None
    _cronTab = None
    _ftpstatus = False
    _ftpinfo = None
    _interval = 60
    _outputFile = '~/status.xml'
    _enableDBsvarSaving = True
    _enableDBclientSaving = True

    _tables = {
        'svars': 'current_svars',
        'cvars': 'current_clients',
    }

    _schema = {

        'mysql': {

            'svars': """CREATE TABLE IF NOT EXISTS `%(svars)s` (
                            `id` INT(11) NOT NULL AUTO_INCREMENT,
                            `name` VARCHAR(255) NOT NULL,
                            `value` VARCHAR(255) NOT NULL,
                            PRIMARY KEY (`id`), UNIQUE KEY `name` (`name`)
                         ) ENGINE=MyISAM DEFAULT CHARSET=utf8 AUTO_INCREMENT=1;""",

            'cvars': """CREATE TABLE IF NOT EXISTS `%(cvars)s` (
                            `id` INT(3) NOT NULL AUTO_INCREMENT,
                            `Updated` VARCHAR(25) NOT NULL ,
                            `Name` VARCHAR(32) NOT NULL ,
                            `Level` INT(10) NOT NULL ,
                            `DBID` INT(10) NOT NULL ,
                            `CID` INT(3) NOT NULL ,
                            `Joined` VARCHAR(25) NOT NULL ,
                            `Connections` INT(11) NOT NULL ,
                            `State` INT(1) NOT NULL ,
                            `Score` INT(10) NOT NULL ,
                            `IP` VARCHAR(16) NOT NULL ,
                            `GUID` VARCHAR(36) NOT NULL ,
                            `PBID` VARCHAR(32) NOT NULL ,
                            `Team` INT(1) NOT NULL ,
                            `ColorName` VARCHAR(32) NOT NULL,
                            PRIMARY KEY (`id`)
                         ) ENGINE = MYISAM DEFAULT CHARSET=utf8 AUTO_INCREMENT=1;"""
        },
        'postgresql': {

            'svars': """CREATE TABLE IF NOT EXISTS %(svars)s (
                            id SERIAL PRIMARY KEY,
                            name VARCHAR(255) NOT NULL,
                            value VARCHAR(255) NOT NULL,
                            CONSTRAINT %(svars)s_name UNIQUE (name));""",

            'cvars': """CREATE TABLE IF NOT EXISTS %(cvars)s (
                            id SERIAL PRIMARY KEY,
                            Updated VARCHAR(25) NOT NULL,
                            Name VARCHAR(32) NOT NULL,
                            Level INTEGER NOT NULL,
                            DBID INTEGER NOT NULL,
                            CID SMALLINT NOT NULL,
                            Joined VARCHAR(25) NOT NULL,
                            Connections INTEGER NOT NULL,
                            State SMALLINT NOT NULL,
                            Score INTEGER NOT NULL,
                            IP VARCHAR(16) NOT NULL,
                            GUID VARCHAR(36) NOT NULL,
                            PBID VARCHAR(32) NOT NULL,
                            Team SMALLINT NOT NULL,
                            ColorName VARCHAR(32) NOT NULL);""",
        },
        'sqlite': {

            'svars': """CREATE TABLE IF NOT EXISTS `%(svars)s` (
                            `id` INTEGER PRIMARY KEY AUTOINCREMENT,
                            `name` VARCHAR(255) NOT NULL,
                            `value` VARCHAR(255) NOT NULL,
                            CONSTRAINT %(svars)s_name UNIQUE (name));""",

            'cvars': """CREATE TABLE IF NOT EXISTS `%(cvars)s` (
                            `id` INTEGER PRIMARY KEY AUTOINCREMENT,
                            `Updated` VARCHAR(25) NOT NULL ,
                            `Name` VARCHAR(32) NOT NULL ,
                            `Level` INTEGER NOT NULL ,
                            `DBID` INTEGER NOT NULL ,
                            `CID` SMALLINT NOT NULL ,
                            `Joined` VARCHAR(25) NOT NULL ,
                            `Connections` INTEGER NOT NULL ,
                            `State` SMALLINT NOT NULL ,
                            `Score` INTEGER NOT NULL ,
                            `IP` VARCHAR(16) NOT NULL ,
                            `GUID` VARCHAR(36) NOT NULL ,
                            `PBID` VARCHAR(32) NOT NULL ,
                            `Team` SMALLINT NOT NULL ,
                            `ColorName` VARCHAR(32) NOT NULL);""",
        }

    }

    ####################################################################################################################
    ##                                                                                                                ##
    ##   STARTUP                                                                                                      ##
    ##                                                                                                                ##
    ####################################################################################################################

    def onLoadConfig(self):
        """
        Load plugin configuration.
        """
        try:

            if self.config.get('settings', 'output_file')[0:6] == 'ftp://':
                self._ftpstatus = True
                self._ftpinfo = functions.splitDSN(self.config.get('settings', 'output_file'))
                self.debug('using custom remote path for settings/output_file: %s/%s' % (self._ftpinfo['host'], self._ftpinfo['path']))
            else:
                self._outputFile = self.config.getpath('settings', 'output_file')
                self.debug('using custom local path for settings/output_file: %s' % self._outputFile)

        except NoOptionError:
            self._outputFile = os.path.normpath(os.path.expanduser(self._outputFile))
            self.warning('could not find settings/output_file in config file, using default: %s' % self._outputFile)

        self._tkPlugin = self.console.getPlugin('tk')

        try:
            self._interval = self.config.getint('settings', 'interval')
            self.debug('using custom value for settings/interval: %s' % self._interval)
        except NoOptionError:
            self.warning('could not find settings/interval in config file, using default: %s' % self._interval)
        except ValueError, e:
            self.error('could not load settings/interval config value: %s' % e)
            self.debug('using default value (%s) for settings/interval' % self._interval)

        try:
            self._enableDBsvarSaving = self.config.getboolean('settings', 'enableDBsvarSaving')
            self.debug('using custom value for settings/enableDBsvarSaving: %s' % self._enableDBsvarSaving)
        except NoOptionError:
            self.warning('could not find settings/enableDBsvarSaving in config file, using default: %s' % self._enableDBsvarSaving)
        except ValueError, e:
            self.error('could not load settings/enableDBsvarSaving config value: %s' % e)
            self.debug('using default value (%s) for settings/enableDBsvarSaving' % self._enableDBsvarSaving)

        try:
            self._enableDBclientSaving = self.config.getboolean('settings', 'enableDBclientSaving')
            self.debug('using custom value for settings/enableDBclientSaving: %s' % self._enableDBclientSaving)
        except NoOptionError:
            self.warning('could not find settings/enableDBclientSaving in config file, using default: %s' % self._enableDBclientSaving)
        except ValueError, e:
            self.error('could not load settings/enableDBclientSaving config value: %s' % e)
            self.debug('using default value (%s) for settings/enableDBclientSaving' % self._enableDBclientSaving)

        if self._enableDBsvarSaving:
            try:
                self._tables['svars'] = self.config.get('settings', 'svar_table')
                self.debug('using custom table for saving server svars: %s' % self._tables['svars'])
            except NoOptionError:
                self.debug('using default table for saving server svars: %s' % self._tables['svars'])

        if self._enableDBclientSaving:
            try:
                self._tables['cvars'] = self.config.get('settings', 'client_table')
                self.debug('using custom table for saving current clients: %s' % self._tables['cvars'])
            except NoOptionError:
                self.debug('using default table for saving current clients: %s' % self._tables['cvars'])

        self.build_schema()

        if self._cronTab:
            # remove existing crontab
            self.console.cron - self._cronTab

        self._cronTab = b3.cron.PluginCronTab(self, self.update, '*/%s' % self._interval)
        self.console.cron + self._cronTab

    ####################################################################################################################
    ##                                                                                                                ##
    ##   EVENTS                                                                                                       ##
    ##                                                                                                                ##
    ####################################################################################################################

    def onStop(self, event):
        self.info('B3 stop/exit.. updating status')
        # create an empty status document
        xml = Document()
        b3status = xml.createElement("B3Status")
        b3status.setAttribute("Time", time.asctime())
        xml.appendChild(b3status)
        self.writeXML(xml.toprettyxml(indent="        "))

    ####################################################################################################################
    ##                                                                                                                ##
    ##   OTHER METHODS                                                                                                ##
    ##                                                                                                                ##
    ####################################################################################################################

    def build_schema(self):
        """
        Create the necessary tables for storing status information in the database
        """
        if not self._enableDBsvarSaving and not self._enableDBclientSaving:
            self.debug('not building database schema')
            return

        current_tables = self.console.storage.getTables()

        if self._enableDBsvarSaving:
            if self._tables['svars'] in current_tables:
                self.bot('removing outdated %s database table...' % self._tables['svars'])
                self.console.storage.query("""DROP TABLE IF EXISTS %s""" % self._tables['svars'])

            self.bot('creating table to store server information: %s' % self._tables['svars'])
            self.console.storage.query(self._schema[self.console.storage.dsnDict['protocol']]['svars'] % self._tables)

        if self._enableDBclientSaving:
            if self._tables['cvars'] in current_tables:
                self.bot('removing outdated %s database table...' % self._tables['cvars'])
                self.console.storage.query("""DROP TABLE IF EXISTS %s""" % self._tables['cvars'])

            self.bot('creating table to store client information: %s' % self._tables['cvars'])
            self.console.storage.query(self._schema[self.console.storage.dsnDict['protocol']]['cvars'] % self._tables)

    def update(self):
        """
        Update XML/DB status.
        """
        clients = self.console.clients.getList()
        score_list = self.console.getPlayerScores()
                 
        self.verbose('building XML status')
        xml = Document()

        # --- Main section
        b3status = xml.createElement("B3Status")
        b3status.setAttribute("Time", time.asctime())
        xml.appendChild(b3status)

        # --- Game section
        c = self.console.game
        gamename = ''
        gametype = ''
        mapname = ''
        timelimit = ''
        fraglimit = ''
        capturelimit = ''
        rounds = ''
        round_time = ''
        map_time = ''

        if c.gameName:
            gamename = c.gameName
        if c.gameType:
            gametype = c.gameType
        if c.mapName:
            mapname = c.mapName
        if c.timeLimit:
            timelimit = c.timeLimit
        if c.fragLimit:
            fraglimit = c.fragLimit
        if c.captureLimit:
            capturelimit = c.captureLimit
        if c.rounds:
            rounds = c.rounds
        if c.roundTime:
            round_time = c.roundTime()
        if c.mapTime():
            map_time = c.mapTime()

        # For XML:
        game = xml.createElement("Game")
        game.setAttribute("Ip", str(self.console._publicIp))
        game.setAttribute("Port", str(self.console._port))
        game.setAttribute("Name", str(gamename))
        game.setAttribute("Type", str(gametype))
        game.setAttribute("Map", str(mapname))
        game.setAttribute("TimeLimit", str(timelimit))
        game.setAttribute("FragLimit", str(fraglimit))
        game.setAttribute("CaptureLimit", str(capturelimit))
        game.setAttribute("Rounds", str(rounds))
        game.setAttribute("RoundTime", str(round_time))
        game.setAttribute("MapTime", str(map_time))
        game.setAttribute("OnlinePlayers", str(len(clients)))
        b3status.appendChild(game)

        # For DB:
        if self._enableDBsvarSaving:
            # EMPTY DB SVARS TABLE
            self.verbose('cleaning database table: %s...' % self._tables['svars'])
            self.console.storage.truncateTable(self._tables['svars'])
            # ADD NEW DATA
            self.storeServerinfo("Ip", str(self.console._publicIp))
            self.storeServerinfo("Port", str(self.console._port))
            self.storeServerinfo("Name", str(gamename))
            self.storeServerinfo("Type", str(gametype))
            self.storeServerinfo("Map", str(mapname))
            self.storeServerinfo("TimeLimit", str(timelimit))
            self.storeServerinfo("FragLimit", str(fraglimit))
            self.storeServerinfo("CaptureLimit",str(capturelimit) )
            self.storeServerinfo("Rounds", str(rounds))
            self.storeServerinfo("RoundTime", str(round_time))
            self.storeServerinfo("MapTime", str(map_time))
            self.storeServerinfo("OnlinePlayers", str(len(clients)))
            self.storeServerinfo("lastupdate", str(int(time.time())))

        for k, v in self.console.game.__dict__.items():
            data = xml.createElement("Data")
            data.setAttribute("Name", str(k))
            data.setAttribute("Value", str(v))
            game.appendChild(data)
            self.storeServerinfo(k, v)

        # --- End Game section        

        # --- Clients section
        b3clients = xml.createElement("Clients")
        b3clients.setAttribute("Total", str(len(clients)))
        b3status.appendChild(b3clients)

        if self._enableDBclientSaving:
            # EMPTY DB CVARS TABLE
            self.verbose('cleaning database table: %s...' % self._tables['cvars'])
            self.console.storage.truncateTable(self._tables['cvars'])

        for c in clients:

            if not c.name:
                c.name = "@" + str(c.id)

            if c.exactName == "^7":
                c.exactName = "@" + str(c.id) + "^7"

            if not c.maskedLevel:
                level = c.maxLevel
            else:
                level = c.maskedLevel
            try:
                client = xml.createElement("Client")
                client.setAttribute("Name", sanitizeMe(c.name))
                client.setAttribute("ColorName", sanitizeMe(c.exactName))
                client.setAttribute("DBID", str(c.id))
                client.setAttribute("Connections", str(c.connections))
                client.setAttribute("CID", c.cid)
                client.setAttribute("Level", str(level))

                if c.guid:
                    client.setAttribute("GUID", c.guid)
                else:
                    client.setAttribute("GUID", '')
                if c.pbid:
                    client.setAttribute("PBID", c.pbid)
                else:
                    client.setAttribute("PBID", '')

                client.setAttribute("IP", c.ip)
                client.setAttribute("Team", str(c.team))
                client.setAttribute("Joined", str(time.ctime(c.timeAdd)))
                client.setAttribute("Updated", str(time.ctime(c.timeEdit)))

                if score_list and c.cid in score_list:
                    client.setAttribute("Score", str(score_list[c.cid]))
                else:
                    client.setAttribute("Score", "")

                client.setAttribute("State", str(c.state))

                if self._enableDBclientSaving:
                    builder_key = ""
                    builder_value = ""
                    # get our attributes
                    for k, v in client.attributes.items():
                        # build the qrystring
                        builder_key = "%s%s," % (builder_key, k)
                        builder_value = "%s'%s'," % (builder_value, v)
                    # cut last ,
                    builder_key = builder_key[:-1]
                    builder_value = builder_value[:-1]

                    try:
                        self.console.storage.query("""INSERT INTO %s (%s) VALUES (%s);""" % (self._tables['cvars'], builder_key, builder_value))
                    except Exception:
                        # exception is already logged, just don't raise it again
                        pass

                b3clients.appendChild(client)

                for k, v in c.data.iteritems():
                    data = xml.createElement("Data")
                    data.setAttribute("Name", "%s" % k)

                    try:
                        clean_data = sanitizeMe(str(v))
                    except Exception, err:
                        self.error("could not sanitize %r" % v, exc_info=err)
                        data.setAttribute("Value", "")
                    else:
                        data.setAttribute("Value", clean_data)

                    client.appendChild(data)
                        
                if self._tkPlugin:
                    if hasattr(c, 'tkplugin_points'):
                        tkplugin = xml.createElement("TkPlugin")
                        tkplugin.setAttribute("Points", str(c.var(self, 'points')))
                        client.appendChild(tkplugin)            
                        if hasattr(c, 'tkplugin_attackers'):
                            for acid, points in c.var(self, 'attackers').value.items():
                                try:
                                    attacker = xml.createElement("Attacker")
                                    attacker.setAttribute("Name", sanitizeMe(self.console.clients[acid].name))
                                    attacker.setAttribute("CID", str(acid))
                                    attacker.setAttribute("Points", str(points))
                                    tkplugin.appendChild(attacker)
                                except Exception, e:
                                    self.warning('could not append child node in XML tree: %s' % e)
                                    pass
                                
            except Exception, err:
                self.error('XML Failed: %r' % err, exc_info=err)
                pass

        # --- End Clients section

        self.writeXML(xml.toprettyxml(encoding="UTF-8", indent="        "))

    def storeServerinfo(self, k, v):
        """
        Store server information in the database.
        """
        if self._enableDBsvarSaving:
            # remove forbidden sql characters
            k = re.sub("'", "", str(k))
            v = re.sub("'", "", str(v))[:255]  # length of the database varchar field
            try:
                if self.console.storage.dsnDict['protocol'] == 'postgresql':
                    self.console.storage.query("""UPDATE %s SET value='%s' WHERE name='%s';""" % (self._tables['svars'], v, k))
                    self.console.storage.query("""INSERT INTO %s (name, value) SELECT '%s', '%s' WHERE NOT EXISTS (
                                                  SELECT 1 FROM %s WHERE name='%s');""" % (self._tables['svars'], k, v,
                                                                                           self._tables['svars'], k))
                else:
                    self.console.storage.query("""INSERT INTO %s (name, value) VALUES ('%s','%s') ON DUPLICATE KEY
                                                  UPDATE value = VALUES(value);""" % (self._tables['svars'], k, v))
            except Exception:
                # exception is already logged, just don't raise it again
                pass

    def writeXML(self, xml):
        """
        Store server information in the XML file.
        """
        if self._ftpstatus:
            self.debug('uploading XML status to FTP server')
            ftp_file = StringIO.StringIO()
            ftp_file.write(xml)
            ftp_file.seek(0)
            ftp = FTP(self._ftpinfo['host'], self._ftpinfo['user'], passwd=self._ftpinfo['password'])
            ftp.cwd(os.path.dirname(self._ftpinfo['path']))
            ftp.storbinary('STOR ' + os.path.basename(self._ftpinfo['path']), ftp_file)
            ftp.quit()
        else:
            self.debug('writing XML status to %s', self._outputFile)
            with open(self._outputFile, 'w') as f:
                f.write(xml)

if __name__ == '__main__':
    from b3.fake import fakeConsole
    p = StatusPlugin(fakeConsole, "@b3/conf/plugin_status.ini")
    p.onStartup()
    p.update()
    
    while True:
        pass