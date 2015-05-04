# coding=utf-8
#
# BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2015 Daniele Pantaleone <fenix@bigbrotherbot.net>
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
# 16/04/2015 - 0.1 - initial release

__author__ = 'Fenix'
__version__ = '0.1'

import b3
import os
import re
import sqlite3
import sys
import bisect
import webbrowser

from b3 import __version__ as b3_version
from b3.config import MainConfig, load as load_config
from b3.decorators import Singleton
from b3.exceptions import DatabaseError, ConfigFileNotValid
from functools import partial
from time import time, sleep
from threading import Thread
from Queue import Queue
from PyQt5.QtCore import Qt, QSize, QObject, pyqtSignal, pyqtSlot, QThread
from PyQt5.QtGui import QCursor, QTextCursor
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import QPushButton, QApplication, QMainWindow, QAction, QDesktopWidget, QFileDialog, \
                            QMessageBox, QDialog, QWidget, QVBoxLayout, QLabel, QHBoxLayout, QSplashScreen, \
                            QTableWidget, QAbstractItemView, QTableWidgetItem, QHeaderView, QProgressBar, QStatusBar, \
                            QTextEdit

PLATFORM = sys.platform
if PLATFORM not in ('win32', 'darwin'):
    PLATFORM = 'linux'

## STRINGS
B3_TITLE = 'BigBrotherBot (B3) %s' % b3_version
B3_TITLE_SHORT = 'B3 %s' % b3_version
B3_COPYRIGHT = 'Copyright © 2005 Michael "ThorN" Thornton'
B3_LICENSE = 'GNU General Public License v2'
B3_FORUM = 'http://forum.bigbrotherbot.net/'
B3_WEBSITE = 'http://www.bigbrotherbot.net'
B3_WIKI = 'http://wiki.bigbrotherbot.net/'
B3_CONFIG_GENERATOR = 'http://config.bigbrotherbot.net/'
B3_NEW_INSTANCE_DIALOG_TITLE = 'Select B3 configuration file'
B3_LAUNCH_INSTANCE_DIALOG_TITLE = 'Starting %s ...'

## PATHS
B3_BANNER = b3.getAbsolutePath('@b3/gui/assets/main.png')
B3_ICON = b3.getAbsolutePath('@b3/gui/assets/icon.png')
B3_SPLASH = b3.getAbsolutePath('@b3/gui/assets/splash.png')
B3_STORAGE = b3.getAbsolutePath('@b3/conf/b3.db')
B3_STORAGE_SQL = b3.getAbsolutePath('@b3/sql/sqlite/b3-gui.sql')
ICON_DEL = b3.getAbsolutePath('@b3/gui/assets/del.png')
ICON_INFO = b3.getAbsolutePath('@b3/gui/assets/info.png')
ICON_LOG = b3.getAbsolutePath('@b3/gui/assets/log.png')
ICON_START = b3.getAbsolutePath('@b3/gui/assets/start.png')
ICON_STOP = b3.getAbsolutePath('@b3/gui/assets/stop.png')

## GEOMETRY
ABOUT_DIALOG_WIDTH = 400
ABOUT_DIALOG_HEIGHT = 500
B3_WIDTH = 520  # MAIN FRAME
B3_HEIGHT = 512  # MAIN FRAME
BTN_WIDTH = 70
BTN_HEIGHT = 40
BTN_ICON_WIDTH = 20
BTN_ICON_HEIGHT = 20
LICENSE_DIALOG_WIDTH = 400
LICENSE_DIALOG_HEIGHT = 320
LAUNCH_DIALOG_WIDTH = 600
LAUNCH_DIALOG_HEIGHT = 300
LAUNCH_PROGRESS_WIDTH = 300
LAUNCH_PROGRESS_HEIGHT = 20
LAUNCH_STDOUT_WIDTH = 360
LAUNCH_STDOUT_HEIGHT = 200
MAIN_TABLE_WIDTH = 500
MAIN_TABLE_HEIGHT = 280
MAIN_TABLE_VERTICAL_SPACING = 4
MAIN_TABLE_COLUMN_NAME_WIDTH = 220
MAIN_TABLE_COLUMN_STATUS_WIDTH = 139
MAIN_TABLE_COLUMN_TOOLBAR_WIDTH = 139

## STYLESHEETS
STYLE_ABOUT_DIALOG = 'background: #F2F2F2;'
STYLE_BUTTON = 'background: #B7B7B7; color: #484848; border: 0;'
STYLE_BUTTON_HOVER = 'background: #C2C2C2; color: #484848; border: 0;'
STYLE_BUTTON_ICON = 'border: 0;'
STYLE_CENTRAL_WIDGET = 'background: #F2F2F2;'
STYLE_LICENSE_DIALOG = 'background: #F2F2F2;'
STYLE_LAUNCH_DIALOG = 'background: #F2F2F2;'
STYLE_MAIN_TABLE = 'background: #FFFFFF; color: #484848; border: 1px solid #B7B7B7;'
STYLE_STATUS_BAR = 'background: #B7B7B7; color: #484848; border: 0;'
STYLE_STDOUT = 'background: #000000; color: #F2F2F2; border: 0; font-family: Courier, sans-serif;'
STYLE_PROGRESS_BAR = """
 QProgressBar {
     border: 1px solid #484848;
     border-radius: 0;
     background: #484848;
 }
 QProgressBar::chunk {
     background: qlineargradient(x1: 0, y1: 0.5, x2: 1, y2: 0.5, stop: 0 #484848, stop: 1 #F2F2F2);
     width: 100px;
 }"""

## BIT FLAGS
CONFIG_FOUND = 0b01
CONFIG_VALID = 0b10

## OTHERS
RE_COLOR = re.compile(r'(\^\d)')


class B3(QThread):

    console = None

    def __init__(self, id=None, config=None):
        """
        Initialize a new B3 instance.
        :param id: the B3 instance id :type int:
        :param config: the B3 configuration file path :type MainConfig: || :type str:
        """
        QThread.__init__(self)
        self.id = id
        self.status = 0

        if isinstance(config, MainConfig):
            self.config = config
            self.config_path = config.fileName
            self.status |= CONFIG_VALID
            self.status |= CONFIG_FOUND
        else:
            try:
                if not os.path.isfile(config):
                    raise OSError('configuration file (%s) could not be found' % config)
                self.config = MainConfig(load_config(config))
                self.config_path = config
            except OSError:
                self.status &= ~CONFIG_FOUND
                self.status &= ~CONFIG_VALID
            except ConfigFileNotValid:
                self.status |= CONFIG_FOUND
                self.status &= ~CONFIG_VALID
            else:
                self.status |= CONFIG_VALID
                self.status |= CONFIG_FOUND

        if self.status & CONFIG_VALID:
            # run again the config analysis (we run it when creating the new instance
            # to display information messages to the user, but it's needed also upon
            # construction, since the user can modify the configuration file (which will
            # be loaded by a B3 instance) and then run the application.
            if self.config.analyze():
                self.status &= ~CONFIG_VALID

        self.name = 'N/A'
        if self.status & CONFIG_VALID:
            if self.config.has_option('b3', 'bot_name'):
                self.name = re.sub(RE_COLOR, '', self.config.get('b3', 'bot_name')).strip()

    ################################################# B3 RUN ###########################################################

    @pyqtSlot()
    def run(self):
        """
        Start B3.
        """
        try:
            parser = b3.loadParser(self.config.get('b3', 'parser'), self.config)
            self.console = parser(conf=self.config, autorestart=False)
            self.console.start()
        except:
            (type, value, traceback) = sys.exc_info()
            sys.excepthook(type, value, traceback)

    ############################################# STORAGE METHODS ######################################################                                                                                              #

    def insert(self):
        """
        Insert the current B3 instance in the database.
        Will also store the B3 instance reference in the QApplication.
        """
        # store it in the database first so we get the id
        cursor = B3App.Instance().storage.cursor()
        cursor.execute("INSERT INTO b3 (config) VALUES (?)", (self.config.fileName,))
        self.id = cursor.lastrowid
        cursor.close()
        # store in the QApplication
        if self not in B3App.Instance().instances:
            bisect.insort_left(B3App.Instance().instances, self)

    def update(self):
        """
        Update the current B3 instance in the database.
        """
        cursor = B3App.Instance().storage.cursor()
        cursor.execute("UPDATE b3 SET config=? WHERE id=?", (self.config.fileName, self.id))
        cursor.close()

    def delete(self):
        """
        Delete the current B3 instance from the database.
        Will also delete the B3 instance reference from the QApplication.
        """
        # remove from the storage
        cursor = B3App.Instance().storage.cursor()
        cursor.execute("DELETE FROM b3 WHERE id=?", (self.id,))
        cursor.close()
        # remove QApplication reference
        if self in B3App.Instance().instances:
            B3App.Instance().instances.remove(self)

    ############################################## STATIC METHODS  #####################################################

    @staticmethod
    def exists(config):
        """
        Checks whether a B3 with this config is already stored in the database.
        :param config: the configuration file path.
        :return: :type bool
        """
        # check in the QApplication first
        for instance in B3App.Instance().instances:
            if instance.config_path == config:
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
        for instance in B3App.Instance().instances:
            if instance.config.id == id:
                return instance
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
        for instance in B3App.Instance().instances:
            if instance.config_path == config:
                return instance
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
        if row:
            return B3(row['id'], row['config'])
        return None

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

    def enterEvent(self, QEvent):
        """
        Executed when the mouse enter the Button.
        """
        self.setStyleSheet(STYLE_BUTTON_HOVER)
        B3App.Instance().setOverrideCursor(QCursor(Qt.PointingHandCursor))

    def leaveEvent(self, QEvent):
        """
        Executed when the mouse leave the Button.
        """
        self.setStyleSheet(STYLE_BUTTON)
        B3App.Instance().restoreOverrideCursor()


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

    def enterEvent(self, QEvent):
        """
        Executed when the mouse enter the Button.
        """
        B3App.Instance().setOverrideCursor(QCursor(Qt.PointingHandCursor))

    def leaveEvent(self, QEvent):
        """
        Executed when the mouse leave the Button.
        """
        B3App.Instance().restoreOverrideCursor()


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
        Initialize the Dialog layout.
        """
        self.setWindowTitle(B3_TITLE_SHORT)
        self.setFixedSize(ABOUT_DIALOG_WIDTH, ABOUT_DIALOG_HEIGHT)
        self.setStyleSheet(STYLE_ABOUT_DIALOG)

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
        self.setStyleSheet(STYLE_LICENSE_DIALOG)

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
        self.setFixedSize(LAUNCH_PROGRESS_WIDTH, LAUNCH_PROGRESS_HEIGHT)
        self.setStyleSheet(STYLE_PROGRESS_BAR)
        self.setRange(0, 0)
        self.setValue(-1)


class STDOutText(QTextEdit):
    """
    This class can be used to display console text within a Widget.
    """
    queue = None
    outputstream = None
    inputstream = None
    inputstreamthread = None

    class OutputStream(object):
        """
        The new Stream Object which replaces the default stream associated with sys.stdout
        This object just puts data in a queue!
        """
        def __init__(self, queue):
            self.queue = queue
            self.flush = lambda *args, **kwargs: None

        def write(self, text):
            """
            Write a string into the Queue.
            """
            self.queue.put(text)

    class InputStream(QObject):
        """
        A QObject (to be run in a QThread) which sits waiting for data to come through a Queue.Queue().
        It blocks until data is available, and one it has got something from the queue, it sends
        it to the "MainThread" by emitting a Qt Signal
        """
        signal = pyqtSignal(str)

        def __init__(self, queue, *args, **kwargs):
            QObject.__init__(self, *args, **kwargs)
            self.queue = queue

        @pyqtSlot()
        def run(self):
            """
            Fetch data from the Queue and emit a signal with the extracted text.
            """
            while True:
                text = self.queue.get()
                self.signal.emit(text)

    def __init__(self, parent=None):
        """
        Initialize the STDOutText object.
        :param parent: the parent widget
        """
        QTextEdit.__init__(self, parent)
        self.setStyleSheet(STYLE_STDOUT)
        self.setReadOnly(True)
        self.initUI()

    def __del__(self):
        """
        Restore sys.stdout
        """
        sys.stdout = sys.__stdout__

    def initUI(self):
        """
        Initialize needed input/output streams.
        """
        ## OUTPUT STREAM
        self.queue = Queue()
        self.outputstream = STDOutText.OutputStream(self.queue)
        sys.stdout = self.outputstream
        sys.stderr = self.outputstream
        ## INPUT STREAM
        self.inputstreamthread = QThread()
        self.inputstream = STDOutText.InputStream(self.queue)
        self.inputstream.signal.connect(self.append_text)
        self.inputstream.moveToThread(self.inputstreamthread)
        self.inputstreamthread.started.connect(self.inputstream.run)
        self.inputstreamthread.start()

    @pyqtSlot(str)
    def append_text(self, text):
        self.moveCursor(QTextCursor.End)
        self.insertPlainText(text)


class ThreadedStartup(QObject):
    """
    A QOject (to be run in a QThread) which handles the startup of a B3 instance.
    """
    def __init__(self, instance, *args, **kwargs):
        QObject.__init__(self, *args, **kwargs)
        self.instance = instance

    @pyqtSlot()
    def run(self):
        """
        Handle the B3 instance startup in a separate thread.
        """
        self.instance.start()


class LaunchDialog(QDialog):
    """
    This class is used to display the 'B3 launch action' dialog.
    """
    mainthread = None
    progress = None
    startupthread = None
    stdout = None

    def __init__(self, parent=None, instance=None):
        """
        Initialize the 'Launch' dialog window.
        :param parent: the parent widget
        """
        QDialog.__init__(self, parent)
        self.instance = instance
        self.initUI()
        self.start()

    def initUI(self):
        """
        Initialize the LaunchDialog layout.
        """
        self.setWindowTitle(B3_LAUNCH_INSTANCE_DIALOG_TITLE % self.instance.name)
        self.setFixedSize(LAUNCH_DIALOG_WIDTH, LAUNCH_DIALOG_HEIGHT)
        self.setStyleSheet(STYLE_LAUNCH_DIALOG)

        def __get_top_layout(parent):
            parent.progress = BusyProgressBar(parent)
            layout = QHBoxLayout()
            layout.addWidget(parent.progress)
            layout.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
            return layout

        def __get_middle_layout(parent):
            parent.stdout = STDOutText(parent)
            layout = QHBoxLayout()
            layout.addWidget(parent.stdout)
            layout.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
            return layout

        main_layout = QVBoxLayout(self)
        main_layout.addLayout(__get_top_layout(self))
        main_layout.addLayout(__get_middle_layout(self))
        self.setLayout(main_layout)
        self.setModal(True)

    @pyqtSlot()
    def start(self):
        """
        Invoke B3 startup.
        """
        self.instance.start()


class MainTable(QTableWidget):
    """
    This class implements the main table widget where B3 instances are being displayed.
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
        self.setStyleSheet(STYLE_MAIN_TABLE)
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
        self.setRowCount(len(B3App.Instance().instances))
        self.setColumnCount(3)
        self.setColumnWidth(0, MAIN_TABLE_COLUMN_NAME_WIDTH)
        self.setColumnWidth(1, MAIN_TABLE_COLUMN_STATUS_WIDTH)
        self.setColumnWidth(2, MAIN_TABLE_COLUMN_TOOLBAR_WIDTH)
        for i in range(len(B3App.Instance().instances)):
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
        instance = B3App.Instance().instances[row]

        def __paint_column_name(parent_table, current_row, current_instance):
            """
            Paint the B3 instance name in the 1st column.
            """
            name = re.sub(RE_COLOR, '', current_instance.config.get('b3', 'bot_name')).strip()
            parent_table.setItem(current_row, 0, QTableWidgetItem(name))

        def __paint_column_status(parent_table, current_row, current_instance):
            """
            Paint the B3 instance status in the 2nd column.
            """
            if current_instance.isRunning():
                value, color = 'RUNNING', Qt.green
            elif current_instance.status & CONFIG_FOUND and current_instance.status & CONFIG_VALID:
                value, color = 'IDLE', Qt.yellow
            else:
                value, color = 'ERROR', Qt.red

            status = QTableWidgetItem(value)
            status.setTextAlignment(Qt.AlignCenter)
            parent_table.setItem(current_row, 1, status)
            parent_table.item(current_row, 1).setBackground(color)

        def __paint_column_toolbar(parent_table, current_row, current_instance):
            """
            Paint the B3 instance toolbar in the 3rd column.
            """
            ## DELETE BUTTON
            btn_del = IconButton(parent=parent_table, icon=QIcon(ICON_DEL))
            btn_del.setStatusTip('Remove %s' % current_instance.name)
            btn_del.setVisible(True)
            btn_del.clicked.connect(partial(self.delete_instance, instance=current_instance))
            ## INFORMATION BUTTON
            btn_info = IconButton(parent=parent_table, icon=QIcon(ICON_INFO))
            btn_info.setStatusTip('Show %s information' % current_instance.name)
            btn_info.setVisible(True)
            ## LOGFILE BUTTON
            btn_log = IconButton(parent=parent_table, icon=QIcon(ICON_LOG))
            btn_log.setStatusTip('Open %s log' % current_instance.name)
            btn_log.setVisible(True)
            btn_log.clicked.connect(partial(self.open_log, instance=current_instance))
            ## STARTUP BUTTON
            btn_start = IconButton(parent=parent_table, icon=QIcon(ICON_START))
            btn_start.setStatusTip('Launch %s' % current_instance.name)
            btn_start.setVisible(True)
            btn_start.clicked.connect(partial(self.launch_instance, instance=current_instance))

            layout = QHBoxLayout()
            layout.addWidget(btn_del)
            layout.addWidget(btn_info)
            layout.addWidget(btn_log)
            layout.addWidget(btn_start)
            layout.setAlignment(Qt.AlignCenter)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(2)
            widget = QWidget(parent_table)
            widget.setLayout(layout)
            widget.setStyleSheet('border: 0;')
            parent_table.setCellWidget(current_row, 2, widget)

        __paint_column_name(self, row, instance)
        __paint_column_status(self, row, instance)
        __paint_column_toolbar(self, row, instance)

    ############################################ TOOLBAR HANDLERS  #####################################################

    def launch_instance(self, instance):
        """
        Handle the startup of a B3 instance.
        Will prompt a dialog window with information on the startup sequence.
        """
        start = LaunchDialog(self.parent(), instance)
        start.show()

    def delete_instance(self, instance):
        """
        Handle the startup of a B3 instance.
        Will prompt a dialog window with information on the startup sequence.
        """
        instance.delete()
        self.repaint()

    def open_log(self, instance):
        """
        Open the B3 instance log file.
        """
        try:
            if not instance.config.has_option('b3', 'logfile'):
                raise Exception('missing b3::logfile option in %s configuration file' % instance.name)

            path = instance.config.get('b3', 'logfile')
            if len([x for x in os.path.split(path) if x]) == 1:
                # if not path is specified but just a filename then look for the
                # file in the main b3 folder (namely outside the @b3 directory)
                path = os.path.join(b3.getAbsolutePath('@b3'), '..', path)

            path = b3.getAbsolutePath(path)
            if not os.path.isfile(path):
                raise Exception('file not found (%s)' % path)

        except Exception, err:
            msgbox = QMessageBox()
            msgbox.setIcon(QMessageBox.Warning)
            msgbox.setWindowTitle('WARNING')
            msgbox.setText('Could not open %s log file: %s' % (instance.name, err.message))
            msgbox.setStandardButtons(QMessageBox.Ok)
            msgbox.exec_()
        else:
            # open in a web browser so it works if the .log extension is not associated
            print path
            webbrowser.open_new_tab(path)


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
        self.setStyleSheet(STYLE_CENTRAL_WIDGET)
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
            btn_new.clicked.connect(self.parent().new_instance)
            btn_new.setStatusTip('Add a new B3')
            btn_new.setVisible(True)
            btn_quit = Button(parent=parent, text='Quit', shortcut='Ctrl+Q')
            btn_quit.clicked.connect(B3App.Instance().quit)
            btn_quit.setStatusTip('Shutdown B3')
            btn_quit.setVisible(True)
            layout = QHBoxLayout()
            layout.addWidget(btn_new)
            layout.addWidget(btn_quit)
            layout.setAlignment(Qt.AlignBottom | Qt.AlignRight)
            layout.setContentsMargins(0, 0, 16, 40)
            layout.setSpacing(20)
            return layout

        main_layout = QVBoxLayout()
        main_layout.addLayout(__get_top_layout(self))
        main_layout.addLayout(__get_middle_layout(self))
        main_layout.addLayout(__get_bottom_layout(self))
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(main_layout)


class StatusBar(QStatusBar):
    """
    This class implements the MainWindow status bar.
    """
    def __init__(self, parent=None):
        """
        Initialize the status bar.
        """
        QStatusBar.__init__(self, parent)
        self.setStyleSheet(STYLE_STATUS_BAR)


class MainWindow(QMainWindow):
    """
    This class implements the main application window.
    """
    def __init__(self):
        QMainWindow.__init__(self)
        # set main window appearance
        self.setWindowTitle(B3_TITLE)
        self.setFixedSize(B3_WIDTH, B3_HEIGHT)
        self.setStatusBar(StatusBar(self))
        # init main window modules
        self.__init_menu()
        self.__init_main_widget()
        # move to center screen
        screen = QDesktopWidget().screenGeometry()
        position_x = (screen.width() - self.geometry().width()) / 2
        position_y = (screen.height() - self.geometry().height()) / 2
        self.move(position_x, position_y)

    def __init_main_widget(self):
        """
        Initialize the central widget.
        """
        self.setCentralWidget(CentralWidget(self))
        self.centralWidget().setFocus()

    def __init_menu(self):
        """
        Initialize the application menu.
        """
        ####  NEW B3 INSTANCE SUBMENU ENTRY
        new_instance = QAction('Add', self)
        new_instance.setShortcut('Ctrl+N')
        new_instance.setStatusTip('Add a new B3')
        new_instance.triggered.connect(self.new_instance)
        ####  QUIT SUBMENU ENTRY
        quit_btn = QAction('Quit', self)
        quit_btn.setShortcut('Ctrl+Q')
        quit_btn.setStatusTip('Quit B3')
        quit_btn.triggered.connect(B3App.Instance().quit)
        quit_btn.setVisible(True)
        ## FILE MENU ENTRY
        file_menu = self.menuBar().addMenu('&File')
        file_menu.addAction(new_instance)
        file_menu.addAction(quit_btn)
        #### ABOUT SUBMENU ENTRY
        about = QAction('About', self)
        about.setStatusTip('Display information about B3')
        about.triggered.connect(self.show_about)
        #### B3 WIKI SUBMENU ENTRY
        wiki = QAction('B3 Wiki', self)
        wiki.setStatusTip('Visit the B3 documentation wiki')
        wiki.triggered.connect(lambda: webbrowser.open(B3_WIKI))
        #### B3 CONFIG GENERATOR SUBMENU ENTRY
        config = QAction('B3 Configuration File Generator', self)
        config.setStatusTip('Open the B3 configuration file generator web tool')
        config.triggered.connect(lambda: webbrowser.open(B3_CONFIG_GENERATOR))
        #### B3 FORUM LINK SUBMENU ENTRY
        forum = QAction('B3 Forum', self)
        forum.setStatusTip('Visit the B3 forums to request support')
        forum.triggered.connect(lambda: webbrowser.open(B3_FORUM))
        #### B3 HOMEPAGE LINK SUBMENU ENTRY
        website = QAction('B3 Website', self)
        website.setStatusTip('Visit the B3 website')
        website.triggered.connect(lambda: webbrowser.open(B3_WEBSITE))
        ## HELP MENU ENTRY
        help_menu = self.menuBar().addMenu('&Help')
        help_menu.addAction(about)

        if PLATFORM != 'darwin':
            help_menu.addSeparator()

        help_menu.addAction(wiki)
        help_menu.addAction(config)
        help_menu.addAction(forum)
        help_menu.addAction(website)

    def new_instance(self):
        """
        Create a new B3 instance entry in the database.
        NOTE: this actually handle also the repainting of the main table but
        since it's not a toolbar button handler it has been implemented here instead.
        """
        ext = 'INI (*.ini);;XML (*.xml);;All Files (*.*)'
        start = b3.getAbsolutePath('@b3/conf')
        filename, _ = QFileDialog.getOpenFileName(self.centralWidget(), B3_NEW_INSTANCE_DIALOG_TITLE, start, ext)

        if filename:

            try:
                path = b3.getAbsolutePath(filename)
                config = MainConfig(load_config(path))
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
                        b3_instance = B3(config=config)
                        b3_instance.insert()
                        main_table = self.centralWidget().main_table
                        main_table.repaint()

    def show_about(self):
        """
        Display the 'about' dialog.
        """
        about = AboutDialog(self.centralWidget())
        about.show()


@Singleton
class B3App(QApplication):
    """
    This class implements the main Qt application.
    The @Singleton decorator ease the QApplication subclass retrieval from within widgets.
    """
    instances = []  # list of B3 instances
    main_window = None  # main application window
    storage = None  # connection with the SQLite database

    def __init__(self, *args, **kwargs):
        """
        Initialize a new application.
        """
        QApplication.__init__(self, *args, **kwargs)

    def init(self):
        """
        Initialize the application.
        """
        self.__init_storage()
        self.__init_instances()
        self.__init_main_window()

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
            cursor = self.storage.cursor()
            cursor.execute("""SELECT * FROM sqlite_master WHERE type='table'""")
            tables = [row[1] for row in cursor.fetchall()]
            cursor.close()

            if not 'b3' in tables:
                msgbox = QMessageBox()
                msgbox.setWindowTitle('ERROR')
                msgbox.setText('The database schema is corrupted and must be rebuilt. Do you want to proceed?')
                msgbox.setInformativeText('NOTE: all the previously saved data will be lost')
                msgbox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                msgbox.setDefaultButton(QMessageBox.No)
                rtn = msgbox.exec_()

                if rtn == QMessageBox.No:
                    raise DatabaseError('Could not start B3: database schema is corrupted!')
                else:
                    try:
                        os.remove(B3_STORAGE)
                    except:
                        raise DatabaseError('Could not remove SQLite database: %s. Make sure B3 has permissions '
                                            'to operate on this file, or remove it manually.' % B3_STORAGE)
                    else:
                        self.__build_schema()

    def __init_instances(self):
        """
        Load available B3 instances from the database.
        """
        self.instances = B3.get_list_from_storage()
        self.instances.sort()

    def __init_main_window(self):
        """
        Initialize the QApplication main window.
        """
        # set the icon here so it's global
        self.setWindowIcon(QIcon(B3_ICON))
        self.main_window = MainWindow()
        self.main_window.show()

    def __build_schema(self):
        """
        Build the database schema.
        Will import the B3 schema SQL script into the database, to create missing tables.
        """
        with open(B3_STORAGE_SQL, 'r') as schema:
            self.storage.executescript(schema.read())


if __name__ == "__main__":

    try:
        main = B3App.Instance(sys.argv)
        with SplashScreen(min_splash_time=0):
            main.init()
    except Exception, e:
        box = QMessageBox()
        box.setIcon(QMessageBox.Critical)
        box.setWindowTitle('CRITICAL')
        box.setText(e.message)
        box.setStandardButtons(QMessageBox.Ok)
        box.exec_()
        sys.exit(127)
    else:
        sys.exit(main.exec_())