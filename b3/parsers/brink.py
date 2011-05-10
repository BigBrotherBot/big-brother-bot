# encoding: utf-8
#
# BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2011 
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
#
__author__  = 'Courgette'
__version__ = '0.0'

import b3.parsers
from b3.parser import Parser
from b3.parsers.q3a.rcon import Rcon as Q3Rcon


"""
 TIPS FOR CONTRIBUTORS :
 =======================

  * In your main config file, set log level down to 8 to see log message of
    type VERBOS2.  <set name="log_level">8</set>

  * You can add the section below in your b3.xml in order to display the log
    file on your console :
        <settings name="devmode">
            <set name="log2console">true</set>
        </settings>

"""


class BrinkParser(Parser):
    gameName = 'brink'
    OutputClass = b3.parsers.brink.Rcon
    rconTest = True
        
    def startup(self):
        pass



class Rcon(Q3Rcon):
    rconsendstring = '\377\377\377\377rcon\377%s\377%s\377'
    rconreplystring = '\377\377\377\377print\377'
    qserversendstring = '\377\377\377\377%s\377'
