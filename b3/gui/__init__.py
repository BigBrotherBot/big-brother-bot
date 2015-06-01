# -*- coding: utf-8 -*-
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
# 16/04/2015 - 0.1  - initial release
# 05/05/2015 - 0.2  - changed GUI application to use QProcess instead of QThreads
#                   - reimplemented STDOut redirection into QTextEdit widget
#                   - changed MessageBox to use Button class instead of the default StandardButton: this enable
#                     the mouse cursor transition upon MessageBox button enterEvent and leaveEvent
#                   - added update check feature
# 07/05/2015 - 0.3  - added loggin facility
#                   - moved database file into user HOME folder (will survive updates)
#                   - implement B3 log open through UI
# 11/05/2015 - 0.4  - win32 graphic adjustment
#                   - implemented process refresh feature: refresh a B3 configuration file without the need of
#                     rebooting the application completely
#                   - implemented plugin install feature: will deploy the plugin in the B3 default extplugins folder
# 13/05/2015 - 0.5  - linux graphic changes
# 18/05/2015 - 0.6  - fixed B3 process status flag (CONFIG_READY) not being refreshed correctly
#                   - make use of properties in B3 QProcess instead of normal attributes
# 18/05/2015 - 0.7  - added system tray icon
#                   - remove MessageBox class: make use of the default QMessageBox one which seems to be working better
#                   - correctly space buttons in about dialog window
#                   - make sure to have a visible MainWindow when a MenuBar action is triggered: on OS X the menubar
#                     is visible even though the MainWindow is hidden, so it's possible to launch Dialogs (if such
#                     dialogs gets closed while the MainWindow is hidden, the application terminate)
# 19/05/2015 - 0.8  - activate back application close button
#                   - make sure MainWindow is visible when triggering stop_all and start_all
#                   - handle double click event in system tray icon
#                   - added Tools menu entry and moved check update submenu to Tools menu
#                   - rework plugin installation algorithm: make use of tempfile.mkdtemp and check if the plugin is already
#                     installed before copying the plugin directory inside the B3 extplugins folder (will also make sure that
#                     the user didn't delete the extplugins folder manually)
# 22/05/2015 - 0.9  - allow the user to terminate B3 application by closing the main window (only windows system)
#                   - simulate application minimize into tray icon (windows only)
# 23/05/2015 - 0.10 - make sure that the MainWindow is displayed and focused when restoring it from system tray
#                   - make sure to properly shutdown B3 when closing the application from OSX dock icon
# 26/05/2015 - 0.11 - split module into separate submodules
#                   - implement B3 database update dialog (available from Menu::Tools)
#                   - implement drag&drop in MainTable: add new B3 by simply dropping the configuration file on it
# 01/06/2015 - 0.12 - minor adjustments for win32 platform
#                   - support multi-drag/drop in main table (create multiple B3 processes)

__author__ = 'Fenix'
__version__ = '0.12'


import b3
import bisect
import os
import re
import sys
import logging
import sqlite3

## USER PATHS
B3_STORAGE = b3.getWritableFilePath(os.path.join(b3.HOMEDIR, 'app.db'), True)
B3_LOG = b3.getWritableFilePath(os.path.join(b3.HOMEDIR, 'app.log'), True)

## RESOURCE PATHS
B3_BANNER = b3.getAbsolutePath('@b3/gui/assets/main.png', True)
B3_ICON = b3.getAbsolutePath('@b3/gui/assets/icon.png', True)
B3_ICON_SMALL = b3.getAbsolutePath('@b3/gui/assets/icon-small.png', True)
B3_SPLASH = b3.getAbsolutePath('@b3/gui/assets/splash.png', True)
B3_SQL = b3.getAbsolutePath('@b3/sql/sqlite/b3-gui.sql', True)
ICON_DEL = b3.getAbsolutePath('@b3/gui/assets/del.png', True)
ICON_CONSOLE = b3.getAbsolutePath('@b3/gui/assets/console.png', True)
ICON_LOG = b3.getAbsolutePath('@b3/gui/assets/log.png', True)
ICON_REFRESH = b3.getAbsolutePath('@b3/gui/assets/refresh.png', True)
ICON_START = b3.getAbsolutePath('@b3/gui/assets/start.png', True)
ICON_STOP = b3.getAbsolutePath('@b3/gui/assets/stop.png', True)

## STATUS FLAGS
CONFIG_FOUND = 0b0001   # configuration file has been found
CONFIG_VALID = 0b0010   # configuration file has been parsed correctly
CONFIG_READY = 0b0100   # configuration file is ready for deploy

## OTHERS
LOG = None
RE_COLOR = re.compile(r'(\^\d)')

from b3.config import MainConfig, load as load_config
from b3.decorators import Singleton
from b3.exceptions import ConfigFileNotValid
from b3.functions import main_is_frozen
from PyQt5.QtCore import QProcess, QEvent
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication,  QMessageBox

@Singleton
class B3App(QApplication):
    """
    This class implements the main Qt application.
    The @Singleton decorator ease the QApplication subclass retrieval from within widgets.
    """
    processes = []  # list of B3 processes
    main_window = None  # main application window
    shutdown_requested = False  # set it to true when a shutdown is requested
    storage = None  # connection with the SQLite database

    def __init__(self, *args, **kwargs):
        """
        Initialize a new application.
        """
        QApplication.__init__(self, *args, **kwargs)

    def init(self):
        """
        Initialize the application.
        :return MainWindow: the reference to the main window object
        """
        self.__init_home()
        self.__init_log()
        self.__init_storage()
        self.__init_os_specific()
        self.__init_processes()
        self.__init_main_window()
        return self.main_window

    @staticmethod
    def __init_home():
        """
        Initialize B3 HOME directory.
        """
        if not os.path.isdir(b3.HOMEDIR):
            os.mkdir(b3.HOMEDIR)

    @staticmethod
    def __init_log():
        """
        Initialize the GUI log.
        """
        global LOG

        class CustomHandler(logging.Logger):

            def __init__(self, name, level=logging.NOTSET):
                """
                Object constructor.
                :param name: The logger name
                :param level: The default logging level
                """
                logging.Logger.__init__(self, name, level)

            def critical(self, msg, *args, **kwargs):
                """
                Log 'msg % args' with severity 'CRITICAL' and raise an Exception.
                """
                logging.Logger.critical(self, msg, *args, **kwargs)
                raise Exception(msg % args)

        logging.setLoggerClass(CustomHandler)

        LOG = logging.getLogger('B3')
        handler = logging.FileHandler(B3_LOG, mode='w')
        handler.setFormatter(logging.Formatter('%(asctime)s\t%(levelname)s\t%(message)r', '%y%m%d %H:%M:%S'))
        LOG.addHandler(handler)
        LOG.setLevel(logging.DEBUG)

    def __init_storage(self):
        """
        Initialize the connection with the SQLite database.
        :raise DatabaseError: if the database schema is not consistent.
        """
        is_new_database = not os.path.isfile(B3_STORAGE)
        self.storage = sqlite3.connect(B3_STORAGE, check_same_thread=False)
        self.storage.isolation_level = None  # set autocommit mode
        self.storage.row_factory = sqlite3.Row  # allow row index by name
        if is_new_database:
            # create new schema
            self.__build_schema()
        else:
            # check database schema
            LOG.debug('checking database schema')
            cursor = self.storage.cursor()
            cursor.execute("""SELECT * FROM sqlite_master WHERE type='table'""")
            tables = [row[1] for row in cursor.fetchall()]
            cursor.close()

            if 'b3' not in tables:
                LOG.debug('database schema is corrupted: asking the user if he wants to rebuild it')

                msgbox = QMessageBox()
                msgbox.setIcon(QMessageBox.Critical)
                msgbox.setText('The database schema is corrupted and must be rebuilt. Do you want to proceed?')
                msgbox.setInformativeText('NOTE: all the previously saved data will be lost!')
                msgbox.setStandardButtons(QMessageBox.No | QMessageBox.Yes)
                msgbox.setDefaultButton(QMessageBox.No)
                msgbox.exec_()

                if msgbox.result() == QMessageBox.No:
                    # critical will raise an exception which will terminate the QApplication
                    LOG.critical('could not start B3: database schema is corrupted!')

                try:
                    os.remove(B3_STORAGE)
                    self.__build_schema()
                except Exception, err:
                    raise LOG.critical('could initialize SQLite database: %s (%s): make sure B3 has permissions to '
                                       'operate on this file, or remove it manually', B3_STORAGE, err)

    def __init_os_specific(self):
        """
        Initialize OS specific features.
        """
        if b3.getPlatform() == 'darwin':
            self.setQuitOnLastWindowClosed(False)

    def __init_processes(self):
        """
        Load available B3 processes from the database.
        """
        LOG.debug('loading process instances from the storage')
        self.processes = B3.get_list_from_storage()
        self.processes.sort()
        LOG.info('%s processes available', len(self.processes))
        for proc in self.processes:
            LOG.debug('%s: @%s:%s', proc.name, proc.id, proc.config_path)

    def __init_main_window(self):
        """
        Initialize the QApplication main window.
        """
        # set the icon here so it's global
        self.setWindowIcon(QIcon(B3_ICON_SMALL))
        self.main_window = MainWindow()

    def __build_schema(self):
        """
        Build the database schema.
        Will import the B3 schema SQL script into the database, to create missing tables.
        """
        with open(B3_SQL, 'r') as schema:
            LOG.debug('initializing database schema')
            self.storage.executescript(schema.read())

    ############################################## EVENT HANDLERS ######################################################

    def event(self, event):
        """
        Handle global application events.
        """
        if b3.getPlatform() == 'darwin':
            # when the dock icon is clicked make sure that the main window is visible
            if event.type() == QEvent.ApplicationActivate and self.main_window:
                self.main_window.make_visible()
            elif event.type() == QEvent.Close:
                event.ignore()
                self.shutdown()

        if event.isAccepted():
            return QApplication.event(self, event)
        return 0

    ############################################# ACTION HANDLERS ######################################################

    def start_all(self):
        """
        Start all the available B3 processes.
        """
        self.main_window.show()
        main_table = self.main_window.centralWidget().main_table
        for process in self.processes:
            main_table.process_start(row=self.processes.index(process), process=process, warn=False)

    def stop_all(self):
        """
        Stop all the available B3 processes.
        """
        self.main_window.show()
        main_table = self.main_window.centralWidget().main_table
        for process in self.processes:
            main_table.process_shutdown(process)

    def shutdown(self):
        """
        Perform cleanup operation before the application exits.
        This is executed when the `aboutToQuit` signal is emitted, before `quit()
        or when the user shutdown the Desktop session`.
        """
        LOG.debug('shutdown requested')
        is_something_running = False
        for process in self.processes:
            if process.state() == QProcess.Running:
                is_something_running = True
                break

        if is_something_running:
            # ask the use if he wants to quit for real
            LOG.debug('some processes are still running: asking the user if he wants to terminate them...')
            msgbox = QMessageBox()
            msgbox.setIcon(QMessageBox.Question)
            msgbox.setText('Are you sure you want to quit?')
            msgbox.setInformativeText('NOTE: all the running B3 will be stopped!')
            msgbox.setStandardButtons(QMessageBox.No | QMessageBox.Yes)
            msgbox.setDefaultButton(QMessageBox.No)
            msgbox.exec_()

            if msgbox.result() == QMessageBox.Yes:
                LOG.debug('user agreed to terminate all the running processes and quit the application')
            else:
                LOG.debug('shutdown aborted')
                return

        self.shutdown_requested = True
        self.stop_all()
        ## REMOVE LOG HANDLERS
        for handler in LOG.handlers:
            handler.close()
            LOG.removeHandler(handler)
        ## HIDE SYSTEM TRAY (ON WINDOWS IT STAYS VISIBLE SOMETIME)
        self.main_window.system_tray.hide()
        ## QUIT THE APPLICATION
        self.quit()


class B3(QProcess):

    _config = None
    _config_path = None
    _name = 'N/A'
    _status = 0

    stdout = None

    def __init__(self, id=None, config=None):
        """
        Initialize a new B3 instance.
        :param id: the B3 instance id :type int:
        :param config: the B3 configuration file path :type MainConfig: || :type str:
        """
        QProcess.__init__(self)
        self.id = id
        self.config = config

    ############################################### PROPERTIES #########################################################

    def __get_config(self):
        """
        Return the B3 process configuration instance.
        """
        return self._config

    def __set_config(self, config):
        """
        Load the B3 process configuration instance.
        :param config: the MainConfig instance ot the configuration file path
        """
        if isinstance(config, MainConfig):
            self._config = config
            self._config_path = config.fileName
            self.setFlag(CONFIG_VALID)
            self.setFlag(CONFIG_FOUND)
        else:

            try:
                self._config_path = config
                if not os.path.isfile(self._config_path):
                    raise OSError('configuration file (%s) could not be found' % self._config_path)
                self._config = MainConfig(load_config(self._config_path))
            except OSError:
                self.delFlag(CONFIG_FOUND)
                self.delFlag(CONFIG_VALID)
                self.delFlag(CONFIG_READY)
            except ConfigFileNotValid:
                self.setFlag(CONFIG_FOUND)
                self.delFlag(CONFIG_VALID)
                self.delFlag(CONFIG_READY)
            else:
                self.setFlag(CONFIG_FOUND)
                self.setFlag(CONFIG_VALID)
                self.delFlag(CONFIG_READY)

        if self.isFlag(CONFIG_VALID):

            # RUN ANALYSIS
            if self.config.analyze():
                self.delFlag(CONFIG_READY)
            else:
                self.setFlag(CONFIG_READY)

            # PARSE B3 NAME FOR QUICK ACCESS
            if self.config.has_option('b3', 'bot_name'):
                self._name = re.sub(RE_COLOR, '', self.config.get('b3', 'bot_name')).strip()

    config = property(__get_config, __set_config)

    def __get_config_path(self):
        """
        Return the configuration file path.
        """
        if not self._config_path and self._config:
            self._config_path = self._config.fileName
        return self._config_path

    config_path = property(__get_config_path)

    def __get_name(self):
        """
        Return the B3 process name.
        """
        if self._name == 'N/A' and self._config:
            if self.config.has_option('b3', 'bot_name'):
                self._name = re.sub(RE_COLOR, '', self.config.get('b3', 'bot_name')).strip()
        return self._name

    name = property(__get_name)

    ########################################### STATUS FLAG METHODS ####################################################

    def setFlag(self, flag):
        """Set the given status flag"""
        self._status |= flag

    def delFlag(self, flag):
        """Remove the given status flag"""
        self._status &= ~flag

    def isFlag(self, flag):
        """Check whether the given flag is set"""
        return self._status & flag

    ############################################# PROCESS STARTUP ######################################################

    def start(self):
        """
        Start the B3 process.
        Will lookup the correct entry point (b3_run.py if running from sources,
        otherwise the Frozen executable) handing over necessary startup parameters.
        """
        if not main_is_frozen():
            # if we are running b3 from sources identify the entry point
            entry_point = os.path.join(b3.getB3Path(True), '..', 'b3_run.py')
            if not os.path.isfile(entry_point):
                # must be running from wheel distribution
                entry_point = os.path.join(b3.getB3Path(True), 'run.py')
            # prefer compiled python instance
            if os.path.isfile(entry_point + 'c'):
                entry_point += 'c'
            program = '%s %s --config %s --console' % (sys.executable, entry_point, self.config_path)
        else:
            if b3.getPlatform() == 'darwin':
                program = '"%s" --config "%s" --console' % (sys.executable, self.config_path)
            else:
                program = '%s --config %s --console' % (sys.executable, self.config_path)

        LOG.info('starting %s process: %s', self.name, program)

        # create the console window (hidden by default)
        self.stdout = STDOutDialog(process=self)
        self.setProcessChannelMode(QProcess.MergedChannels)
        self.readyReadStandardOutput.connect(self.stdout.read_stdout)

        # configure signal handlers
        self.finished.connect(self.process_finished)

        # start the program
        QProcess.start(self, program)

    ############################################# STORAGE METHODS ######################################################                                                                                              #

    def insert(self):
        """
        Insert the current B3 instance in the database.
        Will also store the B3 instance reference in the QApplication.
        """
        # store it in the database first so we get the id
        cursor = B3App.Instance().storage.cursor()
        cursor.execute("INSERT INTO b3 (config) VALUES (?)", (self.config_path,))
        self.id = cursor.lastrowid
        LOG.debug('stored new process in the database: @%s:%s', self.id, self.config_path)
        cursor.close()
        # store in the QApplication
        if self not in B3App.Instance().processes:
            bisect.insort_left(B3App.Instance().processes, self)

    def update(self):
        """
        Update the current B3 instance in the database.
        """
        cursor = B3App.Instance().storage.cursor()
        cursor.execute("UPDATE b3 SET config=? WHERE id=?", (self.config_path, self.id))
        LOG.debug('updated process in the database: @%s:%s', self.id, self.config_path)
        cursor.close()

    def delete(self):
        """
        Delete the current B3 instance from the database.
        Will also delete the B3 instance reference from the QApplication.
        """
        # remove from the storage
        cursor = B3App.Instance().storage.cursor()
        cursor.execute("DELETE FROM b3 WHERE id=?", (self.id,))
        LOG.debug('removed process from the database: @%s:%s', self.id, self.config_path)
        cursor.close()
        # remove QApplication reference
        if self in B3App.Instance().processes:
            B3App.Instance().processes.remove(self)

    ############################################## STATIC METHODS  #####################################################

    @staticmethod
    def exists(config):
        """
        Checks whether a B3 with this config is already stored in the database.
        :param config: the configuration file path.
        :return: :type bool
        """
        # check in the QApplication first
        for process in B3App.Instance().processes:
            if process.config_path == config:
                return True
        # search also in the database
        cursor = B3App.Instance().storage.cursor()
        cursor.execute("""SELECT * FROM b3 WHERE config=?""", (b3.getAbsolutePath(config),))
        row = cursor.fetchone()
        cursor.close()
        return True if row else False

    @staticmethod
    def get_by_id(id):
        """
        Retrieve a B3 instance given its configuration file.
        :param id: the B3 entry id.
        """
        # search in the QApplication first
        for process in B3App.Instance().processes:
            if process.id == id:
                return process
        # search also in the database
        cursor = B3App.Instance().storage.cursor()
        cursor.execute("SELECT * FROM b3 WHERE id=?", (id,))
        row = cursor.fetchone()
        cursor.close()
        return B3.__get_b3_instance_from_row(row)

    @staticmethod
    def get_by_config(config):
        """
        Retrieve a B3 instance given its configuration file.
        :param config: the configuration file path.
        :return: :type B3 or None.
        """
        # search in the QApplication first
        for process in B3App.Instance().processes:
            if process.config_path == config:
                return process
        # search also in the database
        cursor = B3App.Instance().storage.cursor()
        cursor.execute("""SELECT * FROM b3 WHERE config=?""", (b3.getAbsolutePath(config),))
        row = cursor.fetchone()
        cursor.close()
        return B3.__get_b3_instance_from_row(row)

    @staticmethod
    def get_list_from_storage():
        """
        Return a list of available B3 entries fetching data form the database.
        :return: :type list:
        """
        cursor = B3App.Instance().storage.cursor()
        values = [B3.__get_b3_instance_from_row(row) for row in cursor.execute("""SELECT * FROM b3""")]
        cursor.close()
        return values

    @staticmethod
    def __get_b3_instance_from_row(row):
        """
        Construct a B3 instance from a database row.
        :param row: the database row as dict.
        :return: :type B3.
        """
        return B3(row['id'], row['config'])

    ############################################# SIGNAL HANDLERS ######################################################

    def process_finished(self, exit_code, exit_status):
        """
        Executed when the process terminate
        :param exit_code: the process exit code
        :param exit_status: the process exit status
        """
        if self.stdout:
            self.stdout.hide()
            self.stdout = None

    ############################################## MAGIC METHODS  ######################################################

    def __lt__(self, other):
        """Comparison used by bisect.insort"""
        if self.name == 'N/A' and other.name != 'N/A':
            return False
        if self.name != 'N/A' and other.name == 'N/A':
            return True
        return self.name < other.name


from b3.gui.dialogs import STDOutDialog
from b3.gui.widgets import MainWindow