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
__version__ = '0.10'

import b3
import bisect
import os
import re
import glob
import imp
import json
import logging
import shutil
import sqlite3
import sys
import tempfile
import urllib2
import webbrowser

from b3 import HOMEDIR
from b3 import __version__ as b3_version
from b3.config import MainConfig, load as load_config
from b3.decorators import Singleton
from b3.exceptions import ConfigFileNotValid, ConfigFileNotFound
from b3.functions import main_is_frozen, unzip
from b3.update import getDefaultChannel, B3version, URL_B3_LATEST_VERSION
from functools import partial
from time import time, sleep
from PyQt5.QtCore import Qt, QSize, QProcess, pyqtSlot, QThread, QEvent, pyqtSignal
from PyQt5.QtGui import QCursor, QTextCursor
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import QPushButton, QApplication, QMainWindow, QAction, QDesktopWidget, QFileDialog, \
                            QMessageBox, QDialog, QWidget, QVBoxLayout, QLabel, QHBoxLayout, QSplashScreen, \
                            QTableWidget, QAbstractItemView, QTableWidgetItem, QHeaderView, QStatusBar, QTextEdit, \
                            QProgressBar, QMenuBar, QSystemTrayIcon, QMenu

## STRINGS
B3_TITLE = 'BigBrotherBot (B3) %s' % b3_version
B3_TITLE_SHORT = 'B3 %s' % b3_version
B3_COPYRIGHT = 'Copyright © 2005 Michael "ThorN" Thornton'
B3_LICENSE = 'GNU General Public License v2'
B3_FORUM = 'http://forum.bigbrotherbot.net/'
B3_WEBSITE = 'http://www.bigbrotherbot.net'
B3_WIKI = 'http://wiki.bigbrotherbot.net/'
B3_CONFIG_GENERATOR = 'http://config.bigbrotherbot.net/'
B3_DOCUMENTATION = 'http://doc.bigbrotherbot.net/'
B3_DONATE = 'http://www.bigbrotherbot.net/donate'
B3_PLUGIN_REPOSITORY = 'http://forum.bigbrotherbot.net/downloads/?cat=4'

## USER PATHS
B3_STORAGE = b3.getWritableFilePath(os.path.join(HOMEDIR, 'app.db'), True)
B3_LOG = b3.getWritableFilePath(os.path.join(HOMEDIR, 'app.log'), True)

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

## OS DEPENDENT GEOMETRY
GEOMETRY = {
    'win32': {
        'MAIN_TABLE_HEIGHT': 260,
        'MAIN_WINDOW_BOTTOM_LAYOUT_MARGIN_RIGHT': 11,
        'MAIN_WINDOW_BOTTOM_LAYOUT_MARGIN_BOTTOM': 52,
        'BUTTONS_SPACING': 10,
    },
    'darwin': {
        'MAIN_TABLE_HEIGHT': 280,
        'MAIN_WINDOW_BOTTOM_LAYOUT_MARGIN_RIGHT': 16,
        'MAIN_WINDOW_BOTTOM_LAYOUT_MARGIN_BOTTOM': 40,
        'BUTTONS_SPACING': 20,
    },
    'linux': {
        'MAIN_TABLE_HEIGHT': 280,
        'MAIN_WINDOW_BOTTOM_LAYOUT_MARGIN_RIGHT': 11,
        'MAIN_WINDOW_BOTTOM_LAYOUT_MARGIN_BOTTOM': 32,
        'BUTTONS_SPACING': 10,
    }
}

## FIXED GEOMETRY
ABOUT_DIALOG_WIDTH = 400
ABOUT_DIALOG_HEIGHT = 520
B3_WIDTH = 520
B3_HEIGHT = 512
BTN_WIDTH = 70
BTN_HEIGHT = 40
BTN_ICON_WIDTH = 20
BTN_ICON_HEIGHT = 20
LICENSE_DIALOG_WIDTH = 400
LICENSE_DIALOG_HEIGHT = 320
CONSOLE_DIALOG_WIDTH = 800
CONSOLE_DIALOG_HEIGHT = 300
CONSOLE_STDOUT_WIDTH = 660
CONSOLE_STDOUT_HEIGHT = 200
MAIN_TABLE_WIDTH = 500
MAIN_TABLE_HEIGHT = GEOMETRY[b3.getPlatform()]['MAIN_TABLE_HEIGHT']
MAIN_TABLE_VERTICAL_SPACING = 4
MAIN_TABLE_COLUMN_NAME_WIDTH = 200
MAIN_TABLE_COLUMN_STATUS_WIDTH = 180
MAIN_TABLE_COLUMN_TOOLBAR_WIDTH = 118
PROGRESS_WIDTH = 240
PROGRESS_HEIGHT = 20
UPDATE_DIALOG_WIDTH = 400
UPDATE_DIALOG_HEIGHT = 120
PLUGIN_INSTALL_DIALOG_WIDTH = 500
PLUGIN_INSTALL_DIALOG_HEIGHT = 140

STYLE_BUTTON = """
  QPushButton {
    background: #B7B7B7;
    border: 0;
    color: #484848;
    min-width: 70px;
    min-height: 40px;
  }
  QPushButton:hover {
    background: #C2C2C2;
  }
"""
STYLE_BUTTON_LARGE = """
  QPushButton {
    background: #B7B7B7;
    border: 0;
    color: #484848;
    min-width: 100px;
    min-height: 40px;
  }
  QPushButton:hover {
    background: #C2C2C2;
  }
"""
STYLE_BUTTON_ICON = """
  QPushButton {
    border: 0;
  }
"""
STYLE_WIDGET_GENERAL = """
  QWidget, QDialog, QMessageBox {
    background: #F2F2F2;
  }
"""
STYLE_WIDGET_TABLE_ITEM = """
  QWidget, QDialog, QMessageBox {
    background: #FFFFFF;
    border: 0;
  }
"""
STYLE_TABLE = """
  QTableWidget {
    background: #FFFFFF;
    border: 1px solid #B7B7B7;
    color: #484848;
  }
"""
STYLE_STATUS_BAR = """
  QStatusBar {
     background: #B7B7B7;
     border: 0;
     color: #484848;
  }
"""
STYLE_STDOUT = """
  QTextEdit {
    background: #000000;
    border: 0;
    color: #F2F2F2;
    font-family: Courier, sans-serif;
    }
"""
STYLE_PROGRESS_BAR = """
  QProgressBar {
    border: 1px solid #484848;
    border-radius: 0;
    background: #484848;
  }
  QProgressBar::chunk {
    background: qlineargradient(x1: 0, y1: 0.5, x2: 1, y2: 0.5, stop: 0 #484848, stop: 1 #F2F2F2);
    width: 100px;
  }
"""
STYLE_PROGRESS_BAR_STOPPED = """
  QProgressBar {
    border: 1px solid #484848;
    border-radius: 0;
    background: #484848;
  }
  QProgressBar::chunk {
    background: #484848;
    width: 100px;
  }
"""

## STATUS FLAGS
CONFIG_FOUND = 0b0001   # configuration file has been found
CONFIG_VALID = 0b0010   # configuration file has been parsed correctly
CONFIG_READY = 0b0100   # configuration file is ready for deploy

## OTHERS
RE_COLOR = re.compile(r'(\^\d)')
LOG = None


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
            program = 'python %s --config %s --console' % (os.path.join(b3.getB3Path(True), '..', 'b3_run.py'), self.config_path)
        else:
            if b3.getPlatform() == 'darwin':
                # treat osx separately since the command line terms need some extra quotes
                program = '"%s" --config "%s" --console' % (os.path.join(b3.getB3Path(True), 'b3_run'), self.config_path)
            else:
                executable = 'b3_run.exe' if b3.getPlatform() == 'win32' else 'b3_run.x86'
                program = '%s --config %s --console' % (os.path.join(b3.getB3Path(True), executable), self.config_path)

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


class SplashScreen(QSplashScreen):
    """
    This class implements the splash screen.
    It can be used with the context manager, i.e:

    >>> from PyQt5.QtWidgets import QApplication, QSplashScreen
    >>> app = QApplication(sys.argv)
    >>> with SplashScreen(min_splash_time=5):
    >>>     pass

    In the Example above a 5 seconds (at least) splash screen is drawn on the screen.
    The with statement body can be used to initialize the main widget and process heavy stuff.
    """
    def __init__(self, min_splash_time=2):
        """
        Initialize the B3 splash screen.
        :param min_splash_time: the minimum amount of seconds the splash screen should be drawn.
        """
        self.splash_pix = QPixmap(B3_SPLASH)
        self.min_splash_time = time() + min_splash_time
        QSplashScreen.__init__(self, self.splash_pix, Qt.WindowStaysOnTopHint)
        self.setMask(self.splash_pix.mask())

    def __enter__(self):
        """
        Draw the splash screen.
        """
        self.show()

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Remove the splash screen from the screen.
        This will make sure that the splash screen is displayed for at least min_splash_time seconds.
        """
        now = time()
        if now < self.min_splash_time:
            sleep(self.min_splash_time - now)
        self.close()


class Button(QPushButton):
    """
    This class implements a custom button.
    """
    def __init__(self, parent=None, text='', shortcut='', width=BTN_WIDTH, height=BTN_HEIGHT):
        """
        Initialize a Button object.
        :param parent: the widget this QPushButton is connected to :type QObject:
        :param text: the text to be displayed in the button :type str:
        :param shortcut: the keyboard sequence to be used as button shortcut :type str:
        :param width: the button width :type numeric:
        :param height: the button height :type numeric:
        """
        QPushButton.__init__(self, text, parent)
        self.setContentsMargins(0, 0, 0, 0)
        self.setFixedSize(width, height)
        self.setShortcut(shortcut)
        self.setStyleSheet(STYLE_BUTTON)

    def enterEvent(self, _):
        """
        Executed when the mouse enter the Button.
        """
        B3App.Instance().setOverrideCursor(QCursor(Qt.PointingHandCursor))

    def leaveEvent(self, _):
        """
        Executed when the mouse leave the Button.
        """
        B3App.Instance().setOverrideCursor(QCursor(Qt.ArrowCursor))


class IconButton(QPushButton):
    """
    This class implements an icon button.
    """

    def __init__(self, parent=None, icon=None):
        """
        Initialize a IconButton object.
        :param parent: the widget this QButton is connected to :type QObject:
        :param icon: the icon to be displayed in the button :type QIcon:
        """
        QPushButton.__init__(self, parent)
        self.setContentsMargins(0, 0, 0, 0)
        self.setStyleSheet(STYLE_BUTTON_ICON)
        self.setFixedSize(BTN_ICON_WIDTH, BTN_ICON_HEIGHT)
        self.setIconSize(QSize(BTN_ICON_WIDTH, BTN_ICON_HEIGHT))
        self.setIcon(icon)

    def enterEvent(self, _):
        """
        Executed when the mouse enter the Button.
        """
        B3App.Instance().setOverrideCursor(QCursor(Qt.PointingHandCursor))

    def leaveEvent(self, _):
        """
        Executed when the mouse leave the Button.
        """
        B3App.Instance().setOverrideCursor(QCursor(Qt.ArrowCursor))


class ImageWidget(QLabel):
    """
    This class can be used to render images inside widgets.
    By the default the image is placed on the top left corner of the parent widget.
    """
    def __init__(self, parent=None, image=None):
        """
        :param parent: the parent widget
        :param image: the image to display
        """
        QLabel.__init__(self, parent)
        self.setPixmap(QPixmap(image))
        self.setGeometry(0, 0, self.pixmap().width(), self.pixmap().height())


class AboutDialog(QDialog):
    """
    This class is used to display the 'About' dialog.
    """
    def __init__(self, parent=None):
        """
        Initialize the 'About' dialog window.
        :param parent: the parent widget
        """
        QDialog.__init__(self, parent)
        self.initUI()

    def initUI(self):
        """
        Initialize the About Dialog layout.
        """
        self.setWindowTitle(B3_TITLE_SHORT)
        self.setFixedSize(ABOUT_DIALOG_WIDTH, ABOUT_DIALOG_HEIGHT)
        self.setStyleSheet(STYLE_WIDGET_GENERAL)

        def __get_top_layout(parent):
            image = ImageWidget(parent, B3_ICON)
            image_pos_x = (parent.geometry().width() - image.geometry().width()) / 2
            image_pos_y = 30
            layout = QHBoxLayout()
            layout.addWidget(image)
            layout.setAlignment(Qt.AlignTop)
            layout.setContentsMargins(image_pos_x, image_pos_y, 0, 0)
            return layout

        def __get_middle_layout(parent):
            message = """
            %(TITLE)s<br/>
            %(COPYRIGHT)s<br/>
            <br/>
            Michael Thornton (ThorN)<br/>
            Tim ter Laak (ttlogic)<br/>
            Mark Weirath (xlr8or)<br/>
            Thomas Leveil (Courgette)<br/>
            Daniele Pantaleone (Fenix)<br/>
            <br/>
            <a href="%(WEBSITE)s">%(WEBSITE)s</a>
            """ % dict(TITLE=B3_TITLE, COPYRIGHT=B3_COPYRIGHT, WEBSITE=B3_WEBSITE)
            label = QLabel(message, parent)
            label.setWordWrap(True)
            label.setOpenExternalLinks(True)
            label.setAlignment(Qt.AlignHCenter)
            layout = QHBoxLayout()
            layout.addWidget(label)
            layout.setAlignment(Qt.AlignTop)
            layout.setContentsMargins(0, 20, 0, 0)
            return layout

        def __get_bottom_layout(parent):
            btn_license = Button(parent=parent, text='License')
            btn_license.clicked.connect(self.show_license)
            btn_license.setVisible(True)
            btn_close = Button(parent=parent, text='Close')
            btn_close.clicked.connect(parent.close)
            btn_close.setVisible(True)
            layout = QHBoxLayout()
            layout.addWidget(btn_license)
            layout.addWidget(btn_close)
            layout.setAlignment(Qt.AlignHCenter)
            layout.setSpacing(GEOMETRY[b3.getPlatform()]['BUTTONS_SPACING'])
            return layout

        main_layout = QVBoxLayout()
        main_layout.addLayout(__get_top_layout(self))
        main_layout.addLayout(__get_middle_layout(self))
        main_layout.addLayout(__get_bottom_layout(self))
        self.setLayout(main_layout)
        self.setModal(True)

    def show_license(self):
        """
        Open the license dialog window.
        """
        dialog = LicenseDialog(self)
        dialog.show()


class LicenseDialog(QDialog):
    """
    This class is used to display the 'License' dialog.
    """
    def __init__(self, parent=None):
        """
        Initialize the 'License' dialog window
        :param parent: the parent widget
        """
        QDialog.__init__(self, parent)
        self.initUI()

    def initUI(self):
        """
        Initialize the Dialog layout.
        """
        self.setWindowTitle(B3_LICENSE)
        self.setFixedSize(LICENSE_DIALOG_WIDTH, LICENSE_DIALOG_HEIGHT)
        self.setStyleSheet(STYLE_WIDGET_GENERAL)

        def __get_top_layout(parent):
            message = """
            %(COPYRIGHT)s<br/>
            <br/>
            This program is free software; you can redistribute it and/or modify
            it under the terms of the GNU General Public License as published by
            the Free Software Foundation; either version 2 of the License, or
            (at your option) any later version.<br/>
            <br/>
            This program is distributed in the hope that it will be useful,
            but WITHOUT ANY WARRANTY; without even the implied warranty of
            MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
            GNU General Public License for more details.<br/>
            <br/>
            You should have received a copy of the GNU General Public License along
            with this program; if not, write to the Free Software Foundation, Inc.,
            51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
            """ % dict(COPYRIGHT=B3_COPYRIGHT)
            label = QLabel(message, parent)
            label.setWordWrap(True)
            label.setOpenExternalLinks(True)
            label.setAlignment(Qt.AlignLeft)
            layout = QHBoxLayout()
            layout.addWidget(label)
            layout.setAlignment(Qt.AlignTop)
            layout.setContentsMargins(0, 0, 0, 0)
            return layout

        def __get_bottom_layout(parent):
            btn_close = Button(parent=parent, text='Close')
            btn_close.clicked.connect(parent.close)
            btn_close.setVisible(True)
            layout = QHBoxLayout()
            layout.addWidget(btn_close)
            layout.setAlignment(Qt.AlignHCenter)
            return layout

        main_layout = QVBoxLayout()
        main_layout.addLayout(__get_top_layout(self))
        main_layout.addLayout(__get_bottom_layout(self))
        self.setLayout(main_layout)
        self.setModal(True)


class BusyProgressBar(QProgressBar):
    """
    This class implements a progress bar (busy indicator)
    """
    def __init__(self, parent=None):
        """
        Initialize the progress bar.
        :param parent: the parent widget
        """
        QProgressBar.__init__(self, parent)
        self.setFixedSize(PROGRESS_WIDTH, PROGRESS_HEIGHT)
        self.setStyleSheet(STYLE_PROGRESS_BAR)

    def start(self):
        """
        Start the progressbar animation.
        """
        self.setRange(0, 0)
        self.setValue(-1)

    def stop(self):
        """
        Stop the progress bar.
        """
        self.setStyleSheet(STYLE_PROGRESS_BAR_STOPPED)
        self.setTextVisible(False)
        self.setRange(0, 100)
        self.setValue(100)


class UpdateDialog(QDialog):
    """
    This class is used to display the 'update check' dialog.
    """
    layout = None
    message = None
    progress = None
    updatecheckthread = None

    def __init__(self, parent=None):
        """
        Initialize the 'update check' dialog window
        :param parent: the parent widget
        """
        QDialog.__init__(self, parent)
        self.initUI()
        self.checkupdate()

    def initUI(self):
        """
        Initialize the Dialog layout.
        """
        self.setWindowTitle('Checking for updates...')
        self.setFixedSize(UPDATE_DIALOG_WIDTH, UPDATE_DIALOG_HEIGHT)
        self.setStyleSheet(STYLE_WIDGET_GENERAL)
        self.progress = BusyProgressBar(self)
        self.progress.start()
        self.message = QLabel('contacting update server...', self)
        self.message.setAlignment(Qt.AlignHCenter)
        self.message.setWordWrap(True)
        self.message.setOpenExternalLinks(True)
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.progress)
        self.layout.addWidget(self.message)
        self.layout.setAlignment(Qt.AlignCenter)
        self.setLayout(self.layout)
        self.setModal(True)

    def checkupdate(self):
        """
        Initialize a Thread which deals with the update check.
        UI updates is then handled through signals.
        """
        class UpdateCheck(QThread):

            messagesignal = pyqtSignal(str)

            def run(self):
                """
                Threaded code.
                """
                sleep(.5)
                LOG.info('checking for updates...')

                try:
                    channel = getDefaultChannel(b3_version)
                    jsondata = urllib2.urlopen(URL_B3_LATEST_VERSION, timeout=4).read()
                    versioninfo = json.loads(jsondata)
                except urllib2.URLError, err:
                    self.messagesignal.emit('ERROR: could not connect to the update server: %s' % err.reason)
                    LOG.error('could not connect to the update server: %s', err.reason)
                except IOError, err:
                    self.messagesignal.emit('ERROR: could not read data: %s' % err)
                    LOG.error('could not read data: %s', err)
                except Exception, err:
                    self.messagesignal.emit('ERROR: unknown error: %s' % err)
                    LOG.error('ERROR: unknown error: %s', err)
                else:
                    self.messagesignal.emit('parsing data...')
                    sleep(.5)

                    channels = versioninfo['B3']['channels']
                    if channel not in channels:
                        self.messagesignal.emit('ERROR: unknown channel \'%s\': expecting (%s)' % (channel, ', '.join(channels.keys())))
                        LOG.error('unknown channel \'%s\': expecting (%s)', channel, ', '.join(channels.keys()))
                    else:
                        try:
                            latestversion = channels[channel]['latest-version']
                        except KeyError:
                            self.messagesignal.emit('ERROR: could not get latest B3 version for channel: %s' % channel)
                            LOG.error('could not get latest B3 version for channel: %s', channel)
                        else:
                            if B3version(b3_version) < B3version(latestversion):
                                try:
                                    url = versioninfo['B3']['channels'][channel]['url']
                                except KeyError:
                                    url = B3_WEBSITE

                                self.messagesignal.emit('update available: <a href="%s">%s</a>' % (url, latestversion))
                                LOG.info('update available: %s - %s', url, latestversion)
                            else:
                                self.messagesignal.emit('no update available')
                                LOG.info('no update available')

        self.updatecheckthread = UpdateCheck(self)
        self.updatecheckthread.messagesignal.connect(self.update_message)
        self.updatecheckthread.finished.connect(self.finished)
        self.updatecheckthread.start()

    @pyqtSlot(str)
    def update_message(self, message):
        """
        Update the status message
        """
        self.message.setText(message)

    def finished(self):
        """
        Execute when the QThread emits the finished signal.
        """
        self.progress.stop()


class PluginInstallDialog(QDialog):
    """
    This class can be used to initialize the 'install plugin' dialog window.
    """
    archive = None
    installthread = None
    layout = None
    message = None
    progress = None

    def __init__(self, parent=None, archive=None):
        """
        Initialize the 'install plugin' dialog window
        :param parent: the parent widget
        :param archive: the plugin archive filepath
        """
        QDialog.__init__(self, parent)
        self.archive = archive
        self.initUI()
        self.install()

    def initUI(self):
        """
        Initialize the Dialog layout.
        """
        self.setWindowTitle('Installing plugin...')
        self.setFixedSize(PLUGIN_INSTALL_DIALOG_WIDTH, PLUGIN_INSTALL_DIALOG_HEIGHT)
        self.setStyleSheet(STYLE_WIDGET_GENERAL)
        self.progress = BusyProgressBar(self)
        self.progress.start()
        self.message = QLabel('initializing plugin install...', self)
        self.message.setAlignment(Qt.AlignHCenter)
        self.message.setWordWrap(True)
        self.message.setOpenExternalLinks(True)
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.progress)
        self.layout.addWidget(self.message)
        self.layout.setAlignment(Qt.AlignCenter)
        self.setLayout(self.layout)
        self.setModal(True)

    def install(self):
        """
        Initialize a QThread which deals with the plugin installation.
        UI updates is then handled through signals.
        """
        class PluginInstaller(QThread):

            messagesignal = pyqtSignal(str)

            def __init__(self, parent=None, archive=None):
                """
                Initialize the QThread.
                :param parent: the parent widget
                :param archive: the plugin archive filepath
                """
                QThread.__init__(self, parent)
                self.archive = archive

            def run(self):
                """
                Threaded code.
                """
                sleep(.5)

                def plugin_import(directory):
                    """
                    Import a plugin module: will import the first valid module found in the directory tree.
                    It will only lookup modules composed of a directory with inside __init__.py (B3 plugins
                    should be composed of a single module directory with inside everything needed by the plugin to work.
                    :param directory: the source directory from where to start the module search
                    :raise ImportError: if the plugin module is not found
                    :return tuple(name, path, module, clazz)
                    """
                    fp = None
                    clazz = None
                    module = None
                    module_name = None
                    module_path = None
                    for k in os.walk(directory):
                        module_name = os.path.basename(k[0])
                        module_path = k[0]
                        try:
                            LOG.debug('searching for python module in %s', module_path)
                            fp, pathname, description = imp.find_module(module_name, [os.path.join(k[0], '..')])
                            module = imp.load_module(module_name, fp, pathname, description)
                        except ImportError:
                            module_name = module_path = module = clazz = None
                        else:
                            try:
                                LOG.debug('python module found (%s) in %s : looking for plugin class', module_name, module_path)
                                clazz = getattr(module, '%sPlugin' % module_name.title())
                            except AttributeError:
                                LOG.debug('no valid plugin class found in %s module', module_name)
                                module_name = module_path = module = clazz = None
                            else:
                                LOG.debug('plugin class found (%s) in %s module', clazz.__name__, module_name)
                                break
                        finally:
                            if fp:
                                fp.close()

                    if not module:
                        raise ImportError('no valid plugin module found')

                    return module_name, module_path, module, clazz

                LOG.debug('plugin installation started')
                extplugins_dir = b3.getAbsolutePath('@b3/extplugins')
                tmp_dir = tempfile.mkdtemp()

                if not os.path.isdir(extplugins_dir):

                    try:
                        LOG.warning('missing %s directory: attempt to create it' % extplugins_dir)
                        os.mkdir(extplugins_dir)
                    except Exception, err:
                        LOG.error('could create default extplugins directory: %s', err)
                        self.messagesignal.emit('ERROR: could not create extplugins directory!')
                        return
                    else:
                        LOG.debug('created directory %s: resuming plugin installation' % extplugins_dir)

                self.messagesignal.emit('uncompressing plugin archive')
                LOG.debug('uncompressing plugin archive: %s', self.archive)
                sleep(.5)

                try:
                    unzip(self.archive, tmp_dir)
                except Exception, err:
                    LOG.error('could not uncompress plugin archive: %s', err)
                    self.messagesignal.emit('ERROR: plugin installation failed!')
                    shutil.rmtree(tmp_dir, True)
                else:
                    self.messagesignal.emit('searching plugin')
                    LOG.debug('searching plugin')
                    sleep(.5)

                    try:
                        name, path, mod, clz = plugin_import(tmp_dir)
                    except ImportError:
                        self.messagesignal.emit('ERROR: no valid plugin module found!')
                        LOG.warning('no valid plugin module found')
                        shutil.rmtree(tmp_dir, True)
                    else:
                        self.messagesignal.emit('plugin found: %s...' % name)

                        x = None
                        LOG.debug('checking if plugin %s is already installed', name)

                        try:
                            # check if the plugin is already installed (built-in plugins directory)
                            x, y, z = imp.find_module(name, [b3.getAbsolutePath('@b3/plugins')])
                            imp.load_module(name, x, y, z)
                        except ImportError:

                            try:
                                # check if the plugin is already installed (extplugins directory)
                                x, y, z = imp.find_module(name, [extplugins_dir])
                                imp.load_module(name, x, y, z)
                            except ImportError:
                                pass
                            else:
                                self.messagesignal.emit('NOTICE: plugin %s is already installed!' % name)
                                LOG.info('plugin %s is already installed' % name)
                                shutil.rmtree(tmp_dir, True)
                                return
                            finally:
                                if x:
                                    x.close()

                        else:

                            self.messagesignal.emit('NOTICE: %s is built-in plugin!' % name)
                            LOG.info('%s is built-in plugin' % name)
                            shutil.rmtree(tmp_dir, True)
                            return

                        finally:
                            if x:
                                x.close()

                        if clz.requiresConfigFile:
                            self.messagesignal.emit('searching plugin %s configuration file' % name)
                            LOG.debug('searching plugin %s configuration file', name)
                            sleep(.5)

                            collection = glob.glob('%s%s*%s*' % (os.path.join(path, 'conf'), os.path.sep, name))
                            if len(collection) == 0:
                                self.messagesignal.emit('ERROR: no configuration file found for plugin %s' % name)
                                LOG.warning('no configuration file found for plugin %s', name)
                                shutil.rmtree(tmp_dir, True)
                                return

                            # suppose there are multiple configuration files: we'll try all of them
                            # till a valid one is loaded, so we can prompt the user a correct plugin
                            # configuration file path (if no valid is found, installation is aborted)
                            loaded = None
                            for entry in collection:
                                try:
                                    loaded = b3.config.load(entry)
                                except Exception:
                                    pass
                                else:
                                    break

                            if not loaded:
                                self.messagesignal.emit('ERROR: no valid configuration file found for plugin %s' % name)
                                LOG.warning('no valid configuration file found for plugin %s', name)
                                shutil.rmtree(tmp_dir, True)
                                return

                        # move into extplugins folder and remove temp directory
                        shutil.move(path, extplugins_dir)
                        shutil.rmtree(tmp_dir, True)

                        self.messagesignal.emit('plugin %s installed' % name)
                        LOG.info('plugin %s installed successfully', name)

        self.installthread = PluginInstaller(self, self.archive)
        self.installthread.messagesignal.connect(self.update_message)
        self.installthread.finished.connect(self.finished)
        self.installthread.start()

    @pyqtSlot(str)
    def update_message(self, message):
        """
        Update the status message
        """
        self.message.setText(message)

    def finished(self):
        """
        Execute when the QThread emits the finished signal.
        """
        self.progress.stop()


class STDOutText(QTextEdit):
    """
    This class can be used to display console text within a Widget.
    """
    def __init__(self, parent=None):
        """
        Initialize the STDOutText object.
        :param parent: the parent widget
        """
        QTextEdit.__init__(self, parent)
        self.setStyleSheet(STYLE_STDOUT)
        self.setReadOnly(True)


class STDOutDialog(QDialog):
    """
    This class is used to display the 'B3 console output' dialog.
    """
    stdout = None

    def __init__(self, parent=None, process=None):
        """
        Initialize the 'Launch' dialog window.
        :param parent: the parent widget
        """
        QDialog.__init__(self, parent)
        self.process = process
        self.initUI()

    def initUI(self):
        """
        Initialize the STDOutDialog layout.
        """
        self.setWindowTitle('%s console' % self.process.name)
        self.setFixedSize(CONSOLE_DIALOG_WIDTH, CONSOLE_DIALOG_HEIGHT)
        self.setStyleSheet(STYLE_WIDGET_GENERAL)
        self.stdout = STDOutText(self)
        layout = QVBoxLayout(self)
        layout.addWidget(self.stdout)
        layout.setAlignment(Qt.AlignCenter)
        self.setLayout(layout)
        self.setModal(True)
        self.hide()

    @pyqtSlot()
    def read_stdout(self):
        """
        Read STDout and append it to the QTextEdit
        """
        self.stdout.moveCursor(QTextCursor.End)
        self.stdout.insertPlainText(str(self.process.readAllStandardOutput()))


class MainTable(QTableWidget):
    """
    This class implements the main table widget where B3 processes are being displayed.
    """
    def __init__(self, parent):
        """
        Initialize the main table widget.
        """
        QTableWidget.__init__(self, parent)
        self.initUI()
        self.paint()
        self.show()

    def initUI(self):
        """
        Initialize the MainTable layout.
        """
        self.setFixedSize(MAIN_TABLE_WIDTH, MAIN_TABLE_HEIGHT)
        self.setStyleSheet(STYLE_TABLE)
        self.setShowGrid(False)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setSelectionMode(QAbstractItemView.NoSelection)
        self.horizontalHeader().setVisible(False)
        self.verticalHeader().setVisible(False)
        self.verticalHeader().sectionResizeMode(QHeaderView.Fixed)
        self.verticalHeader().setDefaultSectionSize(BTN_ICON_HEIGHT + MAIN_TABLE_VERTICAL_SPACING)

    def paint(self):
        """
        Paint table contents.
        """
        self.setRowCount(len(B3App.Instance().processes))
        self.setColumnCount(3)
        self.setColumnWidth(0, MAIN_TABLE_COLUMN_NAME_WIDTH)
        self.setColumnWidth(1, MAIN_TABLE_COLUMN_STATUS_WIDTH)
        self.setColumnWidth(2, MAIN_TABLE_COLUMN_TOOLBAR_WIDTH)
        for i in range(len(B3App.Instance().processes)):
            self.paint_row(i)

    def repaint(self):
        """
        Repaint table contents.
        """
        self.clear()
        self.paint()

    def paint_row(self, row):
        """
        Fills a QTableWidget row.
        :param row: the row number
        """
        process = B3App.Instance().processes[row]

        def __paint_column_name(parent, numrow, proc):
            """
            Paint the B3 instance name in the 1st column.
            """
            name = re.sub(RE_COLOR, '', proc.name).strip()
            parent.setItem(numrow, 0, QTableWidgetItem(name))

        def __paint_column_status(parent, numrow, proc):
            """
            Paint the B3 instance status in the 2nd column.
            """
            if proc.state() == QProcess.Running:
                value, background, foregound = 'RUNNING', Qt.green, Qt.white
            else:
                if proc.isFlag(CONFIG_READY):
                    value, background, foregound = 'IDLE', Qt.yellow, Qt.black
                else:
                    background, foregound = Qt.red, Qt.white
                    value = 'INVALID CONFIG' if proc.isFlag(CONFIG_FOUND) else 'MISSING CONFIG'

            value = QTableWidgetItem(value)
            value.setTextAlignment(Qt.AlignCenter)
            parent.setItem(numrow, 1, value)
            parent.item(numrow, 1).setBackground(background)
            parent.item(numrow, 1).setForeground(foregound)

        def __paint_column_toolbar(parent, numrow, proc):
            """
            Paint the B3 instance toolbar in the 3rd column.
            """
            ## DELETE BUTTON
            btn_del = IconButton(parent=parent, icon=QIcon(ICON_DEL))
            btn_del.setStatusTip('Remove %s' % proc.name)
            btn_del.setVisible(True)
            btn_del.clicked.connect(partial(parent.process_delete, process=proc))
            ## REFRESH BUTTON
            btn_refresh = IconButton(parent=parent, icon=QIcon(ICON_REFRESH))
            btn_refresh.setStatusTip('Refresh %s configuration' % proc.name)
            btn_refresh.setVisible(True)
            btn_refresh.clicked.connect(partial(parent.process_refresh, process=proc))
            ## CONSOLE BUTTON
            btn_console = IconButton(parent=parent, icon=QIcon(ICON_CONSOLE))
            btn_console.setStatusTip('Show %s console output' % proc.name)
            btn_console.setVisible(True)
            btn_console.clicked.connect(partial(parent.process_console, process=proc))
            ## LOGFILE BUTTON
            btn_log = IconButton(parent=parent, icon=QIcon(ICON_LOG))
            btn_log.setStatusTip('Show %s log' % proc.name)
            btn_log.setVisible(True)
            btn_log.clicked.connect(partial(parent.process_log, process=proc))
            if proc.state() == QProcess.Running:
                ## SHUTDOWN BUTTON
                btn_ctrl = IconButton(parent=parent, icon=QIcon(ICON_STOP))
                btn_ctrl.setStatusTip('Shutdown %s' % proc.name)
                btn_ctrl.setVisible(True)
                btn_ctrl.clicked.connect(partial(parent.process_shutdown, process=proc))
            else:
                ## STARTUP BUTTON
                btn_ctrl = IconButton(parent=parent, icon=QIcon(ICON_START))
                btn_ctrl.setStatusTip('Run %s' % proc.name)
                btn_ctrl.setVisible(True)
                btn_ctrl.clicked.connect(partial(parent.process_start, row=numrow, process=proc, warn=False))

            layout = QHBoxLayout()
            layout.addWidget(btn_del)
            layout.addWidget(btn_refresh)
            layout.addWidget(btn_log)
            layout.addWidget(btn_console)
            layout.addWidget(btn_ctrl)
            layout.setAlignment(Qt.AlignCenter)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(2)
            widget = QWidget(parent)
            widget.setLayout(layout)
            widget.setStyleSheet(STYLE_WIDGET_TABLE_ITEM)
            parent.setCellWidget(numrow, 2, widget)

        __paint_column_name(self, row, process)
        __paint_column_status(self, row, process)
        __paint_column_toolbar(self, row, process)

    ############################################ TOOLBAR HANDLERS  #####################################################

    def process_start(self, row, process, warn=True):
        """
        Handle the startup of a B3 process.
        :param row: the number of the row displaying the process state
        :param process: the QProcess instance to start
        :param warn: whether to warn the user of a startup failure or not
        """
        if process.state() != QProcess.Running:
            # refresh the config before running
            process.config = process.config_path
            self.repaint()
            if process.isFlag(CONFIG_READY):
                process.stateChanged.connect(partial(self.paint_row, row=row))
                process.start()
            else:
                if warn:
                    suffix = 'not found' if process.isFlag(CONFIG_FOUND) else 'not valid'
                    reason = 'configuration file %s: %s' % (suffix, process.config_path)
                    msgbox = QMessageBox()
                    msgbox.setIcon(QMessageBox.Warning)
                    msgbox.setText('%s startup failure: %s' % (process.name, reason))
                    msgbox.setStandardButtons(QMessageBox.Ok)
                    msgbox.exec_()

    def process_shutdown(self, process):
        """
        Handle the shutdown of a B3 process.
        :param process: the QProcess instance to shutdown
        """
        if process.state() != QProcess.NotRunning:
            # will emit stateChanged signal and row repaint will be triggered already
            LOG.info('shutting down %s process', process.name)
            process.close()

    def process_delete(self, process):
        """
        Handle the removal of a B3 process.
        """
        if process.state() != QProcess.NotRunning:
            # make sure to stop the running process before removing the B3 entry
            self.process_shutdown(process)
        process.delete()
        self.repaint()

    def process_refresh(self, process):
        """
        Refresh a process configuration file
        """
        if process.state() == QProcess.Running:
            msgbox = QMessageBox()
            msgbox.setIcon(QMessageBox.Information)
            msgbox.setText('%s is currently running: you need to stop it to refresh the configuration file.' % process.name)
            msgbox.setStandardButtons(QMessageBox.Ok)
            msgbox.exec_()
        else:
            process.config = process.config_path
            self.repaint()

    def process_console(self, process):
        """
        Display the STDOut console of a process.
        """
        if process.state() == QProcess.NotRunning:
            msgbox = QMessageBox()
            msgbox.setIcon(QMessageBox.Information)
            msgbox.setText('%s is not running' % process.name)
            msgbox.setStandardButtons(QMessageBox.Ok)
            msgbox.exec_()
        else:
            if not process.stdout:
                msgbox = QMessageBox()
                msgbox.setIcon(QMessageBox.Warning)
                msgbox.setText('%s console initialization failed' % process.name)
                msgbox.setStandardButtons(QMessageBox.Ok)
                msgbox.exec_()
            else:
                process.stdout.show()

    def process_log(self, process):
        """
        Open the B3 instance log file.
        """
        try:

            if not process.isFlag(CONFIG_FOUND):
                raise ConfigFileNotFound('missing configuration file (%s)' % process.config_path)
            elif not process.isFlag(CONFIG_VALID):
                raise ConfigFileNotValid('invalid configuration file (%s)' % process.config_path)

            if not process.config.has_option('b3', 'logfile'):
                raise Exception('missing b3::logfile option in %s configuration file' % process.name)

            path = process.config.getpath('b3', 'logfile')
            if not os.path.isfile(path):
                message = '- missing: %s' % path
                path = os.path.join(HOMEDIR, os.path.basename(path))
                if not os.path.isfile(path):
                    raise Exception(message + '\n- missing: %s' % path)

        except Exception, err:
            msgbox = QMessageBox()
            msgbox.setIcon(QMessageBox.Warning)
            msgbox.setText('Could not find %s log file' % process.name)
            msgbox.setDetailedText(err.message)
            msgbox.setStandardButtons(QMessageBox.Ok)
            msgbox.exec_()
        else:
            if b3.getPlatform() == 'win32':
                os.system('start %s' % path)
            elif b3.getPlatform() == 'darwin':
                os.system('open "%s"' % path)
            else:
                os.system('xdg-open "%s"' % path)


class CentralWidget(QWidget):
    """
    This class implements the central widget.
    """
    # keep main table reference for repainting
    main_table = None

    def __init__(self, parent=None):
        """
        :param parent: the parent widget
        """
        QWidget.__init__(self, parent)
        self.setWindowTitle(B3_TITLE)
        self.setFixedSize(B3_WIDTH, B3_HEIGHT)
        self.setStyleSheet(STYLE_WIDGET_GENERAL)
        self.initUI()

    def initUI(self):
        """
        Initialize the Central Widget user interface.
        """
        def __get_top_layout(parent):
            image = ImageWidget(parent, B3_BANNER)
            layout = QHBoxLayout()
            layout.addWidget(image)
            layout.setAlignment(Qt.AlignTop)
            layout.setContentsMargins(0, 0, 0, 0)
            return layout

        def __get_middle_layout(parent):
            parent.main_table = MainTable(parent)
            layout = QVBoxLayout()
            layout.addWidget(parent.main_table)
            layout.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
            layout.setContentsMargins(0, 2, 0, 0)
            return layout

        def __get_bottom_layout(parent):
            btn_new = Button(parent=parent, text='Add', shortcut='Ctrl+N')
            btn_new.clicked.connect(self.parent().new_process)
            btn_new.setStatusTip('Add a new B3')
            btn_new.setVisible(True)
            btn_quit = Button(parent=parent, text='Quit', shortcut='Ctrl+Q')
            btn_quit.clicked.connect(B3App.Instance().shutdown)
            btn_quit.setStatusTip('Shutdown B3')
            btn_quit.setVisible(True)
            layout = QHBoxLayout()
            layout.addWidget(btn_new)
            layout.addWidget(btn_quit)
            layout.setAlignment(Qt.AlignBottom | Qt.AlignRight)
            layout.setContentsMargins(0, 0, GEOMETRY[b3.getPlatform()]['MAIN_WINDOW_BOTTOM_LAYOUT_MARGIN_RIGHT'],
                                            GEOMETRY[b3.getPlatform()]['MAIN_WINDOW_BOTTOM_LAYOUT_MARGIN_BOTTOM'])
            layout.setSpacing(GEOMETRY[b3.getPlatform()]['BUTTONS_SPACING'])
            return layout

        main_layout = QVBoxLayout()
        main_layout.addLayout(__get_top_layout(self))
        main_layout.addLayout(__get_middle_layout(self))
        main_layout.addLayout(__get_bottom_layout(self))
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(main_layout)
        self.setFocus()


class StatusBar(QStatusBar):
    """
    This class implements the MainWindow status bar.
    """
    def __init__(self, parent=None):
        """
        Initialize the status bar.
        """
        QStatusBar.__init__(self, parent)
        self.initUI()

    def initUI(self):
        """
        Initialize the statusbar user interface.
        """
        self.setStyleSheet(STYLE_STATUS_BAR)
        self.setSizeGripEnabled(False)


class MainMenuBar(QMenuBar):
    """
    This class implements the main menu bar.
    """
    def __init__(self, parent=None):
        """
        Initialize the menubar.
        :param parent: the parent widget
        """
        QMenuBar.__init__(self, parent)
        self.initUI()

    def initUI(self):
        """
        Initialize the menu user interface.
        """
        self.__init_menu_file()
        self.__init_menu_tools()
        self.__init_menu_help()

    def __init_menu_file(self):
        """
        Initialize the 'File' menu.
        """
        ####  NEW B3 INSTANCE SUBMENU ENTRY
        new_process = QAction('Add B3', self.parent())
        new_process.setShortcut('Ctrl+N')
        new_process.setStatusTip('Add a new B3')
        new_process.triggered.connect(self.parent().new_process)
        new_process.setVisible(True)
        ### INSTALL PLUGIN SUBMENU ENTRY
        install_plugin = QAction('Add Plugin', self.parent())
        install_plugin.setShortcut('Ctrl+P')
        install_plugin.setStatusTip('Install a new B3 plugin')
        install_plugin.triggered.connect(self.parent().install_plugin)
        install_plugin.setVisible(True)
        ####  QUIT SUBMENU ENTRY
        quit_btn = QAction('Quit', self.parent())
        quit_btn.setShortcut('Ctrl+Q')
        quit_btn.setStatusTip('Shutdown B3')
        quit_btn.triggered.connect(B3App.Instance().shutdown)
        quit_btn.setVisible(True)
        ## FILE MENU ENTRY
        file_menu = self.addMenu('&File')
        file_menu.addAction(new_process)
        file_menu.addAction(install_plugin)
        file_menu.addAction(quit_btn)

    def __init_menu_tools(self):
        """
        Initialize the 'Tools' menu.
        """
        #### UPDATE CHECK SUBMENU ENTRY
        update_check = QAction('Check For Updates', self.parent())
        update_check.setStatusTip('Check if a newer version of B3 is available')
        update_check.triggered.connect(self.parent().check_update)
        #### B3 PLUGIN ARCHIVE SUBMENU ENTRY
        plugin_repository = QAction('Plugins Repository', self.parent())
        plugin_repository.setStatusTip('Browse all the available B3 plugins')
        plugin_repository.triggered.connect(lambda: webbrowser.open(B3_PLUGIN_REPOSITORY))
        ## TOOLS MENU ENTRY
        tools_menu = self.addMenu('&Tools')
        tools_menu.addAction(update_check)
        tools_menu.addAction(plugin_repository)

    def __init_menu_help(self):
        """
        Initialize the 'Help' menu.
        """
        #### ABOUT SUBMENU ENTRY
        about = QAction('About', self.parent())
        about.setStatusTip('Display information about B3')
        about.triggered.connect(self.parent().show_about)
        #### B3 DONATION SUBMENU ENTRY
        donate = QAction('Donate to B3', self.parent())
        donate.setStatusTip('Donate to the BigBrotherBot project')
        donate.triggered.connect(lambda: webbrowser.open(B3_DONATE))
        #### B3 WIKI SUBMENU ENTRY
        wiki = QAction('B3 Wiki', self.parent())
        wiki.setStatusTip('Visit the B3 documentation wiki')
        wiki.triggered.connect(lambda: webbrowser.open(B3_WIKI))
        #### B3 CONFIG GENERATOR SUBMENU ENTRY
        code = QAction('B3 Code Reference', self.parent())
        code.setStatusTip('Open the B3 code reference')
        code.triggered.connect(lambda: webbrowser.open(B3_DOCUMENTATION))
        #### B3 CONFIG GENERATOR SUBMENU ENTRY
        config = QAction('B3 Configuration File Generator', self.parent())
        config.setStatusTip('Open the B3 configuration file generator web tool')
        config.triggered.connect(lambda: webbrowser.open(B3_CONFIG_GENERATOR))
        #### B3 FORUM LINK SUBMENU ENTRY
        forum = QAction('B3 Forum', self.parent())
        forum.setStatusTip('Visit the B3 forums to request support')
        forum.triggered.connect(lambda: webbrowser.open(B3_FORUM))
        #### B3 HOMEPAGE LINK SUBMENU ENTRY
        website = QAction('B3 Website', self.parent())
        website.setStatusTip('Visit the B3 website')
        website.triggered.connect(lambda: webbrowser.open(B3_WEBSITE))
        ## HELP MENU ENTRY
        help_menu = self.addMenu('&Help')
        help_menu.addAction(about)
        if b3.getPlatform() != 'darwin':
            help_menu.addSeparator()
        help_menu.addAction(donate)
        help_menu.addSeparator()
        help_menu.addAction(code)
        help_menu.addAction(config)
        help_menu.addAction(forum)
        help_menu.addAction(website)
        help_menu.addAction(wiki)


class SystemTrayIcon(QSystemTrayIcon):
    """
    This class implements the B3 application system tray icon.
    """
    def __init__(self, parent=None):
        """
        Initialize the system tray icon.
        """
        QSystemTrayIcon.__init__(self, parent)
        self.initUI()

    def initUI(self):
        """
        Initialize the System Tray Icon user interface.
        """
        self.setIcon(QIcon(B3_ICON_SMALL))
        #### SHOW ACTION
        show = QAction('Show', self.parent())
        show.triggered.connect(self.showMainWindow)
        show.setVisible(True)
        #### START ALL ACTION
        start = QAction('Start all', self.parent())
        start.triggered.connect(B3App.Instance().start_all)
        start.setVisible(True)
        #### STOP ALL ACTION
        stop = QAction('Stop all', self.parent())
        stop.triggered.connect(B3App.Instance().stop_all)
        stop.setVisible(True)
        #### QUIT ACTION
        terminate = QAction('Quit', self.parent())
        terminate.triggered.connect(B3App.Instance().shutdown)
        terminate.setVisible(True)
        ## CREATE THE MENU
        menu = QMenu(self.parent())
        menu.addAction(show)
        menu.addSeparator()
        menu.addAction(start)
        menu.addAction(stop)
        menu.addSeparator()
        menu.addAction(terminate)
        ## ADD THE MENU
        self.setContextMenu(menu)
        self.activated.connect(self.onActivated)

    def onActivated(self, reason):
        """
        Handle the System Tray icon activation
        """
        if reason == QSystemTrayIcon.DoubleClick:
            self.showMainWindow()

    def showMainWindow(self):
        """
        Show the main Window making sure it's visible.
        """
        self.parent().setWindowState((self.parent().windowState() & ~Qt.WindowMinimized) | Qt.WindowActive)
        self.parent().activateWindow()
        self.parent().raise_()
        self.parent().show()


class MainWindow(QMainWindow):
    """
    This class implements the main application window.
    """
    system_tray = None
    system_tray_minimized = False # this will be set to True after the first minimization

    def __init__(self):
        """
        Initialize the MainWindow.
        """
        QMainWindow.__init__(self)
        self.initUI()

    def initUI(self):
        """
        Initialize the MainWindow layout.
        """
        self.setWindowTitle(B3_TITLE)
        self.setFixedSize(B3_WIDTH, B3_HEIGHT)
        ## INIT SUBCOMPONENTS
        self.setStatusBar(StatusBar(self))
        self.setMenuBar(MainMenuBar(self))
        self.setCentralWidget(CentralWidget(self))
        ## INIT SYSTEM TRAY ICON
        self.system_tray = SystemTrayIcon(self)
        self.system_tray.show()
        ## MOVE TO CENTER SCREEN
        screen = QDesktopWidget().screenGeometry()
        position_x = (screen.width() - self.geometry().width()) / 2
        position_y = (screen.height() - self.geometry().height()) / 2
        self.move(position_x, position_y)

    ############################################# EVENTS HANDLERS  #####################################################

    def closeEvent(self, event):
        """
        Executed when the main window is closed.
        """
        if b3.getPlatform() == 'win32':
            # always shutdown on windows
            B3App.Instance().shutdown()
        else:
            if B3App.Instance().shutdown_requested:
                B3App.Instance().shutdown()
            else:
                event.ignore()
                self.minimize_in_system_tray()

    def changeEvent(self, event):
        """
        Executed when the main window is modified.
        """
        QMainWindow.changeEvent(self, event)
        if b3.getPlatform() == 'win32':
            if event.type() == QEvent.WindowStateChange:
                if event.oldState() != Qt.WindowMinimized and self.isMinimized():
                    # make sure we do this only for minimize events
                    self.minimize_in_system_tray()

    def minimize_in_system_tray(self):
        """
        Minimize B3 in system tray icon
        """
        self.hide()
        if not self.system_tray_minimized:
            self.system_tray_minimized = True
            self.system_tray.showMessage("B3 is still running!",
                                         "B3 will continue to run so that all your B3 processes will stay alive. "
                                         "If you really want to quit right click this icon and select 'Quit'.",
                                         QSystemTrayIcon.Information, 20000)

    ############################################# ACTION HANDLERS  #####################################################

    def new_process(self):
        """
        Create a new B3 entry in the database.
        NOTE: this actually handle also the repainting of the main table but
        since it's not a toolbar button handler it has been implemented here instead.
        """
        self.show()
        init = b3.getAbsolutePath('@b3/conf')
        extensions = ['INI (*.ini)', 'XML (*.xml)', 'All Files (*.*)']
        path, _ = QFileDialog.getOpenFileName(self.centralWidget(), 'Select configuration file', init, ';;'.join(extensions))

        if path:

            try:
                abspath = b3.getAbsolutePath(path)
                config = MainConfig(load_config(abspath))
            except ConfigFileNotValid:
                msgbox = QMessageBox()
                msgbox.setIcon(QMessageBox.Critical)
                msgbox.setText('You selected an invalid configuration file')
                msgbox.setStandardButtons(QMessageBox.Ok)
                msgbox.exec_()
            else:
                analysis = config.analyze()
                if analysis:
                    msgbox = QMessageBox()
                    msgbox.setIcon(QMessageBox.Critical)
                    msgbox.setText('One or more problems have been detected in your configuration file')
                    msgbox.setDetailedText('\n'.join(analysis))
                    msgbox.setStandardButtons(QMessageBox.Ok)
                    msgbox.exec_()
                else:
                    if not B3.exists(config.fileName):
                        process = B3(config=config)
                        process.insert()
                        main_table = self.centralWidget().main_table
                        main_table.repaint()

    def install_plugin(self):
        """
        Handle the install of a new B3 plugin
        """
        self.show()
        init = b3.getAbsolutePath('~')
        path, _ = QFileDialog.getOpenFileName(self.centralWidget(), 'Select plugin package', init, 'ZIP (*.zip)')
        if path:
            install = PluginInstallDialog(self.centralWidget(), path)
            install.show()

    def show_about(self):
        """
        Display the 'about' dialog.
        """
        self.show()
        about = AboutDialog(self.centralWidget())
        about.show()

    def check_update(self):
        """
        Display the 'update check' dialog
        """
        self.show()
        update = UpdateDialog(self.centralWidget())
        update.show()


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
        self.__init_processes()
        self.__init_main_window()
        return self.main_window

    @staticmethod
    def __init_home():
        """
        Initialize B3 HOME directory.
        """
        if not os.path.isdir(HOMEDIR):
            os.mkdir(HOMEDIR)

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

        LOG = logging.getLogger(__name__)
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

if __name__ == "__main__":

    try:
        main = B3App.Instance(sys.argv)
        with SplashScreen(min_splash_time=0):
            main.init()
    except Exception, e:
        box = QMessageBox()
        box.setIcon(QMessageBox.Critical)
        box.setText(e.message)
        box.setStandardButtons(QMessageBox.Ok)
        box.exec_()
        sys.exit(127)
    else:
        sys.exit(main.exec_())