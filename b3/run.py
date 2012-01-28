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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
# CHANGELOG:
#
# 2010/02/24 - 1.2 - Courgette
#    * uniformize SystemExit and uncatched exception handling between
#      bot running as a win32 standalone and running as a python script
# 2010/03/20 - 1.3 -  xlr8or
#    * finished options -s --setup and -n, --nosetup
#      where setup launches setup procedure and nosetup prevents bot from entering setup procedure.
# 2010/08/05 - 1.3.1 -  xlr8or
#    * Fixing broken --restart mode
# 2010/10/22 - 1.3.3 -  xlr8or
#    * Restart counter
# 2011/05/19 - 1.4.0 -  xlr8or
#    * Added --update -u arg
# 2011/12/03 - 1.4.1 -  courgette
#    * fix crash at bot start in restart mode when installed from egg

__author__  = 'ThorN'
__version__ = '1.4.1'

import b3, sys, os, time
import traceback
from b3.functions import main_is_frozen
from b3.setup import Setup
from b3.setup import Update
from optparse import OptionParser
import pkg_handler


modulePath = pkg_handler.resource_directory(__name__)

def run_autorestart(args=None):
    _restarts = 0

    if main_is_frozen():
        script = ''
    else:
        script = os.path.join(modulePath[:-3], 'b3_run.py')
        if not os.path.isfile(script):
            # must be running from the egg
            script = os.path.join(modulePath[:-3], 'b3', 'run.py')
        if os.path.isfile(script + 'c'):
            script += 'c'

    if args:
        script = '%s %s %s' % (sys.executable, script, ' '.join(args))
    else:
        script = '%s %s' % (sys.executable, script)

    while True:
        try:
            print 'Running in auto-restart mode...'
            if _restarts > 0:
                print 'Bot restarted %s times.' %_restarts
            time.sleep(1)

            try:
                import subprocess
                status = subprocess.call(script, shell=True)
            except ImportError:
                #for Python versions < 2.5
                #status = os.system(script)
                print 'Restart mode not fully supported!\nUse B3 without the -r (--restart) option or update your python installation!'
                break

            print 'Exited with status %s' % status

            if status == 221:
                # restart
                print 'Restart requested...'
            elif status == 222:
                # stop
                print 'Shutdown requested.'
                break
            elif status == 220:
                # stop
                print 'B3 Error, check log file.'
                break
            elif status == 223:
                # stop
                print 'B3 Error Restart, check log file.'
                break
            elif status == 224:
                # stop
                print 'B3 Error, check console.'
                break
            elif status == 256:
                # stop
                print 'Python error, stopping, check log file.'
                break
            elif status == 0:
                # stop
                print 'Normal shutdown, stopping.'
                break
            elif status == 1:
                # stop
                print 'Error, stopping, check console.'
                break
            else:
                print 'Unknown shutdown status (%s), restarting...' % status
        
            _restarts += 1
            time.sleep(4)
        except KeyboardInterrupt:
            print 'Quit'
            break

def run(config=None, nosetup=False):
    if config:
        config = b3.getAbsolutePath(config)
    else:
        # search for the config file
        config = None
        for p in ('b3.xml', 'conf/b3.xml', 'b3/conf/b3.xml', '~/b3.xml', '~/conf/b3.xml', '~/b3/conf/b3.xml', '@b3/conf/b3.xml'):
            path = b3.getAbsolutePath(p)
            print 'Searching for config file: %s' % path
            if os.path.isfile(path):
                config = path
                break

    if not config:
        # This happens when no config was specified on the commandline and the default configs are missing! 
        if nosetup:
            raise SystemExit('ERROR: Could not find config file, Please run B3 with option: --setup or -s')
        else:
            Setup(config)

    b3.start(config, nosetup)

def run_setup(config=None):
    Setup(config)

def run_update(config=None):
    Update(config)

def main():
    parser = OptionParser(version=b3.getB3versionString())
    parser.add_option('-c', '--config', dest='config', default=None,
                      help='B3 config file. Example: -c b3.xml')
    parser.add_option('-r', '--restart',
                      action='store_true', dest='restart', default=False,
                      help='Auto-restart B3 on crash')
    parser.add_option('-s', '--setup',
                      action='store_true', dest='setup', default=False,
                      help='Setup main b3.xml config file')
    parser.add_option('-u', '--update',
                      action='store_true', dest='update', default=False,
                      help='Update B3 database to latest version')
    parser.add_option('-n', '--nosetup',
                      action="store_true", dest='nosetup', default=False,
                      help='Do not enter setup mode when config is missing')


    (options, args) = parser.parse_args()

    if not options.config and len(args) == 1:
        options.config = args[0]

    if options.setup:
        run_setup(config=options.config)

    if options.update:
        run_update(config=options.config)

    if options.restart:
        if options.config:
            run_autorestart(['--config', options.config] + args)
        else:
            run_autorestart([])
    else:
        try:
            run(config=options.config, nosetup=options.nosetup)
        except SystemExit, msg:
            # This needs some work, is ugly a.t.m. but works... kinda
            if main_is_frozen():
                if sys.stdout != sys.__stdout__:
                    # make sure we are not writing to the log:
                    sys.stdout = sys.__stdout__
                    sys.stderr = sys.__stderr__
                print msg
                raw_input("Press the [ENTER] key")
            raise
        except:
            if sys.stdout != sys.__stdout__:
                # make sure we are not writing to the log:
                sys.stdout = sys.__stdout__
                sys.stderr = sys.__stderr__
            traceback.print_exc()
        if main_is_frozen():
            # which happens when running from the py2exe build
            # we wait for keyboad keypress to give a chance to the 
            # user to see the error message
            if sys.stdout != sys.__stdout__:
                # make sure we are not writing to the log:
                sys.stdout = sys.__stdout__
                sys.stderr = sys.__stderr__
            raw_input("Press the [ENTER] key")
     
    
if __name__ == '__main__':
    main()
