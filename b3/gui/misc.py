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


from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QCursor, QPixmap
from PyQt5.QtWidgets import QPushButton, QProgressBar, QSplashScreen, QTextEdit, QStatusBar

from time import sleep, time


class Button(QPushButton):
    """
    This class implements a custom button.
    """
    def __init__(self, parent=None, text='', shortcut=''):
        """
        Initialize a Button object.
        :param parent: the widget this QPushButton is connected to :type QObject:
        :param text: the text to be displayed in the button :type str:
        :param shortcut: the keyboard sequence to be used as button shortcut :type str:
        """
        QPushButton.__init__(self, text, parent)
        self.setContentsMargins(0, 0, 0, 0)
        self.setFixedSize(70, 40)
        self.setShortcut(shortcut)
        self.setStyleSheet("""
        QPushButton {
            background: #B7B7B7;
            border: 0;
            color: #484848;
            min-width: 70px;
            min-height: 40px;
            outline: none;
        }
        QPushButton:hover {
            background: #C2C2C2;
        }
        """)

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
        self.setFixedSize(32, 32)
        self.setIconSize(QSize(32, 32))
        self.setIcon(icon)
        self.setStyleSheet("""
        QPushButton {
            border: 0;
        }
        """)

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
        self.setFixedSize(300, 20)

    def start(self):
        """
        Start the progress bar animation.
        """
        self.setRange(0, 0)
        self.setValue(-1)

    def stop(self):
        """
        Stop the progress bar.
        """
        self.setRange(0, 100)
        self.setValue(100)
        self.setTextVisible(False)


class ProgressBar(QProgressBar):
    """
    This class implements a progress bar.
    """
    def __init__(self, parent=None):
        """
        Initialize the progress bar.
        :param parent: the parent widget
        """
        QProgressBar.__init__(self, parent)
        self.setFixedSize(300, 20)
        self.setTextVisible(False)


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
        self.setReadOnly(True)
        self.setStyleSheet("""
        QTextEdit {
            background: #000000;
            border: 0;
            color: #F2F2F2;
            font-family: Courier, sans-serif;
        }
        """)


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
        self.setSizeGripEnabled(False)
        self.setStyleSheet("""
        QStatusBar {
            background: #B7B7B7;
            border: 0;
            color: #484848;
        }
        """)


class SplashScreen(QSplashScreen):
    """
    This class implements the splash screen.
    It can be used with the context manager, i.e:

    >>> import sys
    >>> from PyQt5.QtWidgets import QApplication
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


from b3.gui import B3App, B3_SPLASH
