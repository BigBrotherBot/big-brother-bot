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

__author__ = 'Fenix'
__version__ = '0.21'


import b3
import bisect
import os
import re
import sys
import logging
import sqlite3

## USER PATHS
B3_STORAGE = b3.getWritableFilePath('@home/app.db', True)
B3_LOG = b3.getWritableFilePath('@home/app.log', True)

## RESOURCE PATHS
B3_BANNER = b3.getAbsolutePath('@b3/gui/assets/main.png', True)
B3_ICON = b3.getAbsolutePath('@b3/gui/assets/icons/b3.png', True)
B3_ICON_SMALL = b3.getAbsolutePath('@b3/gui/assets/icons/b3-small.png', True)
B3_SPLASH = b3.getAbsolutePath('@b3/gui/assets/splash.png', True)
B3_SQL = b3.getAbsolutePath('@b3/sql/sqlite/b3-gui.sql', True)
ICON_DEL = b3.getAbsolutePath('@b3/gui/assets/icons/del.png', True)
ICON_CONSOLE = b3.getAbsolutePath('@b3/gui/assets/icons/console.png', True)
ICON_LOG = b3.getAbsolutePath('@b3/gui/assets/icons/log.png', True)
ICON_REFRESH = b3.getAbsolutePath('@b3/gui/assets/icons/refresh.png', True)
ICON_START = b3.getAbsolutePath('@b3/gui/assets/icons/start.png', True)
ICON_STOP = b3.getAbsolutePath('@b3/gui/assets/icons/stop.png', True)
ICON_INI = b3.getAbsolutePath('@b3/gui/assets/icons/ini.png', True)
ICON_XML = b3.getAbsolutePath('@b3/gui/assets/icons/xml.png', True)
ICON_DATABASE = b3.getAbsolutePath('@b3/gui/assets/icons/database.png', True)
ICON_UPDATE = b3.getAbsolutePath('@b3/gui/assets/icons/update.png', True)
ICON_SETTINGS = b3.getAbsolutePath('@b3/gui/assets/icons/settings.png', True)
ICON_PLUGINS = b3.getAbsolutePath('@b3/gui/assets/icons/plugins.png', True)
ICON_QUIT = b3.getAbsolutePath('@b3/gui/assets/icons/quit.png', True)
ICON_GAME = b3.getAbsolutePath('@b3/gui/assets/icons/games/%s.png', True)
ICON_XLRSTATS = b3.getAbsolutePath('@b3/gui/assets/icons/xlrstats.png', True)
ICON_PAYPAL = b3.getAbsolutePath('@b3/gui/assets/icons/paypal.png', True)

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
from b3.update import UPDATE_CHANNEL_STABLE
from time import time
from PyQt5.QtCore import QProcess, QEvent, QSettings
from PyQt5.QtGui import QIcon, QTextCursor
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

    settings = None  # B3 app configuration file
    settings_default = {  # B3 app default settings
        'auto_restart_on_crash': False,
        'show_rss_news': True,
        'update_channel': UPDATE_CHANNEL_STABLE,
    }

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
        self.__init_settings()
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
        b3.getHomePath()

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

    def __init_settings(self):
        """
        Initialize the application configuration file.
        """
        self.settings = QSettings('BigBrotherBot', 'B3')
        for key in self.settings_default:
            if not self.settings.contains(key):
                self.settings.setValue(key, self.settings_default[key])

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
        self.setWindowIcon(QIcon(B3_ICON if b3.getPlatform() == 'linux' else B3_ICON_SMALL))
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
        self.main_window.make_visible()
        main_table = self.main_window.centralWidget().main_table
        for process in self.processes:
            main_table.process_start(row=self.processes.index(process), process=process, warn=False)

    def stop_all(self):
        """
        Stop all the available B3 processes.
        """
        self.main_window.make_visible()
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
        if b3.getPlatform() != 'linux':
            # linux has no system tray
            self.main_window.system_tray.hide()

        ## QUIT THE APPLICATION
        self.quit()

    ############################################## OTHER METHODS #######################################################

    @staticmethod
    def openpath(path):
        """
        Open the given path using the OS default application.
        :param path: the path to be opened
        """
        if os.path.isfile(path) or os.path.isdir(path):
            os_open = {'win32': 'start %s', 'darwin': 'open "%s"', 'linux': 'xdg-open "%s"'}
            os.system(os_open[b3.getPlatform()] % path)


class B3(QProcess):

    _config = None
    _config_path = None
    _name = 'N/A'
    _game = 'default'
    _status = 0
    _lastrun = -1

    stdout = None

    def __init__(self, id=None, config=None, lastrun=-1):
        """
        Initialize a new B3 instance.
        :param id: the B3 instance id :type int:
        :param config: the B3 configuration file path :type MainConfig: || :type str:
        :param lastrun: the B3 last run timestamp :type int:
        """
        QProcess.__init__(self)
        self.id = id
        self.config = config
        self.lastrun = lastrun

        # create the console window (hidden by default)
        self.stdout = STDOutDialog(process=self)
        self.setProcessChannelMode(QProcess.MergedChannels)
        self.readyReadStandardOutput.connect(self.stdout.read_stdout)
        self.readyReadStandardError.connect(self.stdout.read_stdout)
        # configure signal handlers
        self.error.connect(self.process_errored)
        self.finished.connect(self.process_finished)
        self.started.connect(self.process_started)

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

            # PARSE PARSER NAME FOR QUICK ACCESS
            if self.config.has_option('b3', 'parser') and self.config.get('b3', 'parser') != 'changeme':
                self._game = self.config.get('b3', 'parser').strip()

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

    def __get_game(self):
        """
        Return the B3 process name.
        """
        if self._game == 'default' and self._config:
            if self.config.has_option('b3', 'parser') and self.config.get('b3', 'parser') != 'changeme':
                self._game = self.config.get('b3', 'parser').strip()
        return self._game

    game = property(__get_game)

    def __get_lastrun(self):
        """
        Return the timestamp when the process was last executed.
        """
        if self._lastrun == -1:
            return None
        return self._lastrun

    def __set_lastrun(self, value):
        """
        Set the lastrun value.
        """
        if value:
            self._lastrun = int(value)

    lastrun = property(__get_lastrun, __set_lastrun)

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

            # append restart flag if specified in app configuration file
            if B3App.Instance().settings.value('auto_restart_on_crash', type=bool):
                program += ' --restart'

        else:
            executables = {'nt': 'b3_run.exe', 'darwin': 'b3_run', 'linux':'b3_run'}
            if b3.getPlatform() == 'darwin':
                program = '"%s" --config "%s" --console' % (executables[b3.getPlatform()], self.config_path)
            else:
                program = '%s --config %s --console' % (executables[b3.getPlatform()], self.config_path)

        LOG.info('attempt to start %s process: %s', self.name, program)

        self.stdout.stdout.clear()
        self.lastrun = time()
        self.update()

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
        cursor.execute("UPDATE b3 SET config=?, lastrun=? WHERE id=?", (self.config_path, self.lastrun, self.id))
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
        return B3(row['id'], row['config'], row['lastrun'])

    ############################################# SIGNAL HANDLERS ######################################################

    def process_finished(self, exit_code, exit_status):
        """
        Executed when the process terminate
        :param exit_code: the process exit code
        :param exit_status: the process exit status
        """
        LOG.info('process %s terminated (%s)', self.name, exit_code)
        if self.stdout:
            self.stdout.stdout.moveCursor(QTextCursor.End)
            self.stdout.stdout.insertPlainText('>>> PROCESS TERMINATED (%s)\n' % exit_code)

    def process_errored(self, error_code):
        """
        Executed when the process errors.
        :param error_code: the generated error (:type int:
        """
        LOG.error('process %s errored (%s)', self.name, error_code)

    def process_started(self):
        """
        Executed when the process starts.
        """
        LOG.info('process %s started successfully', self.name)

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
