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
# 2010/02/24 - 1.2   - Courgette     - uniformize SystemExit and uncatched exception handling between bot running
#                                      as a win32 standalone and running as a python script
# 2010/03/20 - 1.3   - xlr8or        - finished options -s --setup and -n, --nosetup where setup launches setup
#                                      procedure and nosetup prevents bot from entering setup procedure.
# 2010/08/05 - 1.3.1 - xlr8or        - fixing broken --restart mode
# 2010/10/22 - 1.3.3 - xlr8or        - restart counter
# 2011/05/19 - 1.4.0 - xlr8or        - added --update -u arg
# 2011/12/03 - 1.4.1 - Courgette     - fix crash at bot start in restart mode when installed from egg
# 2014/07/21 - 1.5   - Fenix         - syntax cleanup
# 2014/12/15 - 1.5.1 - Fenix         - let the parser know if we are running B3 in auto-restart mode or not
# 2015/02/02 - 1.5.2 - Fenix         - keep looking for xml configuration files if ini/cfg are not found
# 2015/02/14 - 1.5.3 - Fenix         - removed _check_arg_configfile in favor of configuration file lookup
# 2015/05/07 - 1.6   - Fenix         - add GUI startup
# 2015/05/26 - 1.7   - Fenix         - reworked B3 startup routine
#                                    - removed B3 setup procedure: display B3 configuration generator webtool url instead
# 2015/06/21 - 1.7.1 - Fenix         - fixed console startup not working properly
# 2015/07/29 - 1.8   - Thomas LEVEIL - by default, run in console mode and remove the --console option

__author__  = 'ThorN'
__version__ = '1.8'

import b3
import b3.config
import os
import sys
import argparse
import pkg_handler
import traceback

from b3 import HOMEDIR, B3_CONFIG_GENERATOR
from b3.functions import main_is_frozen, console_exit
from b3.update import DBUpdate
from time import sleep

modulePath = pkg_handler.resource_directory(__name__)


def run_autorestart(args=None):
    """
    Run B3 in auto-restart mode.
    """
    restart_num = 0

    if main_is_frozen():
        # if we are running the frozen application we do not
        # need to run any script, just the executable itself
        script = ''
    else:
        # if we are running from sources, then sys.executable is set to `python`
        script = os.path.join(modulePath[:-3], 'b3_run.py')
        if not os.path.isfile(script):
            # must be running from the wheel, so there is no b3_run
            script = os.path.join(modulePath[:-3], 'b3', 'run.py')
        if os.path.isfile(script + 'c'):
            script += 'c'

    if args:
        script = '%s %s %s --autorestart' % (sys.executable, script, ' '.join(args))
    else:
        script = '%s %s --autorestart' % (sys.executable, script)

    while True:

        try:

            try:
                import subprocess32 as subprocess
            except ImportError:
                import subprocess

            status = subprocess.call(script, shell=True)

            sys.stdout.write('Exited with status: %s ... ' % status)
            sys.stdout.flush()
            sleep(2)

            if status == 221:
                restart_num += 1
                sys.stdout.write('restart requested (%s)\n' % restart_num)
                sys.stdout.flush()
            elif status == 222:
                sys.stdout.write('shutdown requested!\n')
                sys.stdout.flush()
                break
            elif status == 220 or status == 223:
                sys.stdout.write('B3 error (check log file)\n')
                sys.stdout.flush()
                break
            elif status == 224:
                sys.stdout.write('B3 error (check console)\n')
                sys.stdout.flush()
                break
            elif status == 256:
                sys.stdout.write('python error, (check log file)\n')
                sys.stdout.flush()
                break
            elif status == 0:
                sys.stdout.write('normal shutdown\n')
                sys.stdout.flush()
                break
            elif status == 1:
                sys.stdout.write('general error (check console)\n')
                sys.stdout.flush()
                break
            else:
                restart_num += 1
                sys.stdout.write('unknown exit code (%s), restarting (%s)...\n' % (status, restart_num))
                sys.stdout.flush()

            sleep(4)

        except KeyboardInterrupt:
            print 'Quit'
            break


def run_update(config=None):
    """
    Run the B3 update.
    :param config: The B3 configuration file instance
    """
    update = DBUpdate(config)
    update.run()


def run_gui():
    """
    Run B3 graphical user interface.
    Will raise an exception if the GUI cannot be initialized.
    """
    from b3.gui import B3App
    from b3.gui.misc import SplashScreen
    from PyQt5.QtWidgets import QMessageBox
    from PyQt5.QtWidgets import QSpacerItem, QSizePolicy

    # initialize outside try/except so if PyQt5 is not avaiable or there is
    # no display adapter available, this will raise an exception and we can
    # fallback into console mode
    app = B3App.Instance(sys.argv)

    try:
        with SplashScreen(min_splash_time=2):
            mainwindow = app.init()
    except Exception, e:
        box = QMessageBox()
        box.setIcon(QMessageBox.Critical)
        box.setWindowTitle('CRITICAL')
        box.setText('CRITICAL: B3 FAILED TO START!')
        box.setInformativeText('ERROR: %s' % e)
        box.setDetailedText(traceback.format_exc())
        box.setStandardButtons(QMessageBox.Ok)

        # this will trick Qt and resize a bit the QMessageBox to the exception stack trace is printed nice
        box.layout().addItem(QSpacerItem(400, 0, QSizePolicy.Minimum, QSizePolicy.Expanding),
                             box.layout().rowCount(), 0, 1, box.layout().columnCount())
        box.exec_()
        sys.exit(127)
    else:
        mainwindow.make_visible()
        sys.exit(app.exec_())


def run_console(options):
    """
    Run B3 in console mode.
    :param options: command line options
    """
    analysis = None     # main config analysis result
    printexit = False   # whether the exit message has been printed alreadty or not

    try:

        if options.config:
            config = b3.getAbsolutePath(options.config, True)
            if not os.path.isfile(config):
                printexit = True
                console_exit('ERROR: configuration file not found (%s).\n'
                             'Please visit %s to create one.' % (config, B3_CONFIG_GENERATOR))
        else:
            config = None
            for p in ('b3.%s', 'conf/b3.%s', 'b3/conf/b3.%s',
                      os.path.join(HOMEDIR, 'b3.%s'), os.path.join(HOMEDIR, 'conf', 'b3.%s'),
                      os.path.join(HOMEDIR, 'b3', 'conf', 'b3.%s'), '@b3/conf/b3.%s'):
                for e in ('ini', 'cfg', 'xml'):
                    path = b3.getAbsolutePath(p % e, True)
                    if os.path.isfile(path):
                        print "Using configuration file: %s" % path
                        config = path
                        sleep(3)
                        break

            if not config:
                printexit = True
                console_exit('ERROR: could not find any valid configuration file.\n'
                             'Please visit %s to create one.' % B3_CONFIG_GENERATOR)

        # LOADING MAIN CONFIGURATION
        main_config = b3.config.MainConfig(b3.config.load(config))
        analysis = main_config.analyze()
        if analysis:
            raise b3.config.ConfigFileNotValid('invalid configuration file specified')

        # START B3
        b3.start(main_config, options)

    except b3.config.ConfigFileNotValid:
        if analysis:
            print 'CRITICAL: invalid configuration file specified:\n'
            for problem in analysis:
                print"  >>> %s\n" % problem
        else:
            print 'CRITICAL: invalid configuration file specified!'
        raise SystemExit(1)
    except SystemExit, msg:
        if not printexit and main_is_frozen():
            if sys.stdout != sys.__stdout__:
                sys.stdout = sys.__stdout__
                sys.stderr = sys.__stderr__
            print msg
            raw_input("press any key to continue...")
        raise
    except:
        if sys.stdout != sys.__stdout__:
            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__
        traceback.print_exc()
        raw_input("press any key to continue...")


def main():
    """
    Main execution.
    """
    p = argparse.ArgumentParser()
    p.add_argument('-c', '--config', dest='config', default=None, metavar='b3.ini', help='B3 config file. Example: -c b3.ini')
    p.add_argument('-r', '--restart', action='store_true', dest='restart', default=False, help='Auto-restart B3 on crash')
    p.add_argument('-s', '--setup',  action='store_true', dest='setup', default=False, help='Setup main b3.ini config file')
    p.add_argument('-u', '--update', action='store_true', dest='update', default=False, help='Update B3 database to latest version')
    p.add_argument('-v', '--version', action='version', default=False, version=b3.getB3versionString(), help='Show B3 version and exit')
    p.add_argument('-a', '--autorestart', action='store_true', dest='autorestart', default=False, help=argparse.SUPPRESS)

    (options, args) = p.parse_known_args()

    if not options.config and len(args) == 1:
        options.config = args[0]

    if options.setup:
        # setup procedure is deprecated: show configuration file generator web tool url instead
        sys.stdout.write('\n')
        console_exit("  *** NOTICE: the console setup procedure is deprecated!\n" \
                     "  *** Please visit %s to generate a new B3 configuration file.\n" % B3_CONFIG_GENERATOR)

    if options.update:
        ## UPDATE => CONSOLE
        run_update(config=options.config)

    if options.restart:
        ## AUTORESTART => CONSOLE
        if options.config:
            run_autorestart(['--config', options.config] + args)
        else:
            run_autorestart([])
    else:
        run_console(options)

if __name__ == '__main__':
    main()
