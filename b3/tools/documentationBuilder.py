# -*- coding: utf-8 -*-
#
# BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2010 BigBrotherBot
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
# CHANGELOG:
# 2010/02/20 - 1.1 - Courgette
#    * fix convertion from level to group name for unexpected level numbers
#    * cosmetics to the html export
#    * add maxlevel setting to hide commands reserved to high levels
# 2010/02/23 - 1.2 - Courgette
#    * make the html export validate the W3C test
#    * hide the maxLevel column on the html export
# 2010/02/25 - 1.2.1 - Courgette
#    * fix Internet Explorer issues with logo in html export
#    * remove any use the sets module
# 2010/02/26 - 1.2.2 - Courgette
#    * fix bug making commands with alias appear twice in the results
# 2010/03/07 - 1.2.3 - Courgette
#   * make the html export pass the W3C tests
# 2010/08/25 - 1.2.4 - Courgette
#   * do not fail if 'destination' is found in config but empty
# 2011/05/11 - 1.2.5 - Courgette
#   * update B3 website URL
# 2014/01/20 - 1.2.6 - ozon
#   * add json output

""" 
This module will generate a user documentation depending
on current config
"""

__author__ = 'Courgette, ozon'
__version__ = '1.2.6'

import time
import os
import StringIO
import string
import re
from xml.dom.minidom import Document
from ftplib import FTP
from cgi import escape
import datetime
from b3 import getConfPath
from b3.functions import splitDSN


class DocBuilder:
    _supportedExportType = ['xml', 'html', 'htmltable', 'json']
    _console = None
    _adminPlugin = None
    _outputType = 'html'
    _outputUrl = 'file://' + getConfPath() + '/b3doc.html'
    _maxlevel = None
    _template_path = getConfPath() + '/templates/autodoc/'
    
    def __init__(self, console):
        self._console = console
        self._outputDir = getConfPath()
        self._adminPlugin = self._console.getPlugin('admin')
        if self._adminPlugin is None:
            raise Exception('AUTODOC: cannot generate documentation without the admin plugin')
                
        if self._console.config.has_section('autodoc'):
            if self._console.config.has_option('autodoc', 'destination'):
                dest = self._console.config.get('autodoc', 'destination')
                if dest is None:
                    self._console.warning('AUTODOC: destination found but empty. using default')
                else:
                    if dest.startswith('ftp://') or dest.startswith('file://'):
                        self._outputUrl = dest
                    else:
                        # assume file
                        self._outputUrl = 'file://' + self._console.config.getpath('autodoc', 'destination')
        
            if self._console.config.has_option('autodoc', 'type'):
                self._outputType = self._console.config.get('autodoc', 'type')
    
            if self._console.config.has_option('autodoc', 'maxlevel'):
                self._maxlevel = self._console.config.getint('autodoc', 'maxlevel')

    def save(self):
        if self._outputType not in self._supportedExportType:
            self._console.error('AUTODOC: %s type of doc unsupported' % self._outputType)
            self._console.info('AUTODOC: supported doc types are : %s' % ", ".join(self._supportedExportType))
        else:
            self._console.debug('AUTODOC: saving %s documentation' % self._outputType)
            if self._outputType == 'xml':
                self._write(self.getXml())
            elif self._outputType == 'html':
                from string import Template
                doc_template = Template(self.load_html_template(template=self._template_path+'b3doc_template.html'))
                self._write(doc_template.safe_substitute(
                    commandsTable=self.getHtmlTable(),
                    dateUpdated=time.asctime(),
                    server=self._console._publicIp + ':' + str(self._console._port)
                ))
            elif self._outputType == 'htmltable':
                self._write(self.getHtmlTable())
            elif self._outputType == 'json':
                self._write(self.get_json())

    def load_html_template(self, template):
        """Loads template file from the file system"""
        with open(template, 'r') as template_file:
                    template_data = template_file.read()

        return template_data

    def get_json(self):
        import json

        output = {
            'commands': self._getCommandsDict(),
            'updated': datetime.datetime.now().isoformat(),
            'level_info': {},
            'server_info': {
                'ip': self._console._publicIp,
                'port': self._console._port,
            }
        }

        # add group level info to output
        for g in self._console.storage.getGroups():
            output['level_info'].update({
                g.level: {
                    'name': g.name,
                    'keyword': g.keyword,
                    'level': g.level
                }
            })

        return json.dumps(output, indent=4)

    def getXml(self):
        xml = Document()
        xDoc = xml.createElement("b3doc")
        xDoc.setAttribute("time", time.asctime())
        xDoc.setAttribute("game", self._console.game.gameName)
        xDoc.setAttribute("address", self._console._publicIp + ':' + str(self._console._port))
        
        xCommands = xml.createElement("b3commands")
        for cmd in self._getCommandsDict():
            xCommand = xml.createElement("b3command")
            xCommand.setAttribute("name", cmd['name'])
            if 'alias' in cmd and cmd['alias'] != '' :
                xCommand.setAttribute("alias", cmd['alias'])
            xCommand.setAttribute("plugin", cmd['plugin'])
            xCommand.setAttribute("help", cmd['description'])
            xCommand.setAttribute("minlevel", cmd['minlevel'])
            xCommand.setAttribute("maxlevel", cmd['maxlevel'])
            xCommands.appendChild(xCommand)
        xDoc.appendChild(xCommands)
        xml.appendChild(xDoc)
        return xml.toprettyxml(indent="\t")

    def getHtmlTable(self):
        text = """
            <table id="b3commands">
                <thead>
                    <tr>
                        <th class="b3Plugin">plugin</th>
                        <th class="b3MinLevel">min level</th>
                        <th class="b3MaxLevel">max level</th>
                        <th class="b3Name">command</th>
                        <th class="b3Alias">alias</th>
                        <th class="b3Desc">description</th>
                    </tr>
                </thead>
                <tbody>
                %(commandsTablerow)s
                </tbody>
            </table>
        """
        
        def friendlyLevel(level):
            try:
                intlevel = int(level)
                if intlevel <= 0:
                    return '<span title="%s - Everyone">All</span>' % level
                elif intlevel == 1:
                    return '<span title="%s - Registered players">user</span>' % level
                elif intlevel < 20:
                    return '<span title="%s - Regular players">reg</span>' % level
                elif intlevel < 40:
                    return '<span title="%s - Moderators">mod</span>' % level
                elif intlevel < 60:
                    return '<span title="%s - Admins">admin</span>' % level
                elif intlevel < 80:
                    return '<span title="%s - Full admins">fulladmin</span>' % level
                elif intlevel < 100:
                    return '<span title="%s - Senior admins">senioradmin</span>' % level
                elif intlevel >= 100:
                    return '<span title="%s - Super admins">superadmin</span>' % level
                else:
                    return level
            except:
                return level
        
        htmlCommands = ""
        for cmd in self._getCommandsDict():
            html = """<tr class="b3command">
                <td class="b3Plugin">%(plugin)s</td>
                <td class="b3MinLevel">%(minlevel)s</td>
                <td class="b3MaxLevel">%(maxlevel)s</td>
                <td class="b3Name">%(name)s</td>
                <td class="b3Alias">%(alias)s</td>
                <td class="b3Desc">%(description)s</td>
                </tr>
                """
            cmd['minlevel'] = friendlyLevel(cmd['minlevel'])
            cmd['maxlevel'] = friendlyLevel(cmd['maxlevel'])
            htmlCommands += html % cmd
        return text % {'commandsTablerow': htmlCommands}
    
    def _getCommandsDict(self):
        if self._maxlevel is not None:
            self._console.debug('AUTODOC: get commands with level <= %s' % self._maxlevel)
        commands = {}
        for cmd in self._adminPlugin._commands.values():
            if cmd in commands or \
                cmd.level is None:
                continue
            if self._maxlevel is not None and cmd.level[0] > self._maxlevel:
                continue
            
            #self._console.debug('AUTODOC: making command doc for %s'%cmd.command)
            tmp = {}
            tmp['name'] = cmd.prefix + cmd.command
            tmp['alias'] = ""
            if cmd.alias is not None and cmd.alias != '' :
                tmp['alias'] = cmd.prefix + cmd.alias
            tmp['plugin'] = re.sub('Plugin$', '', cmd.plugin.__class__.__name__) 
            tmp['description'] = escape(cmd.help)
            tmp['minlevel'] = str(cmd.level[0]) if self._outputType != 'json' else cmd.level[0]
            tmp['maxlevel'] = str(cmd.level[1]) if self._outputType != 'json' else cmd.level[1]
            commands[cmd] = tmp

        def commands_compare(x, y):
            if x['plugin'] < y['plugin']: return -1
            elif x['plugin'] > y['plugin']: return 1

            elif int(x['minlevel']) < int(y['minlevel']): return -1
            elif int(x['minlevel']) > int(y['minlevel']): return 1

            elif x['name'] < y['name']: return -1
            elif x['name'] > y['name']: return 1

            else:
                return 0

        listCommands = commands.values()
        listCommands.sort(commands_compare)
        return listCommands
    
    def _write(self, text):
        
        if text.strip() == '':
            self._console.warning('AUTODOC: nothing to write')
            
        dsn = splitDSN(self._outputUrl)
        
        if dsn['protocol'] == 'ftp':
            self._console.debug('Uploading to FTP server %s' % dsn['host'])
            ftp = FTP(dsn['host'], dsn['user'], passwd=dsn['password'])
            ftp.cwd(os.path.dirname(dsn['path']))
            ftpfile = StringIO.StringIO()
            ftpfile.write(text)
            ftpfile.seek(0)
            ftp.storbinary('STOR '+os.path.basename(dsn['path']), ftpfile)
        elif dsn['protocol'] == 'file':
            self._console.debug('Writing to %s', dsn['path'])
            f = file(dsn['path'], 'w')
            f.write(text)
            f.close()
        else:
            self._console.error('AUTODOC: protocol [%s] is not supported' % dsn['protocol'])
