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

import b3
import webbrowser

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMenuBar, QAction, QSystemTrayIcon, QMenu
from b3 import B3_PLUGIN_REPOSITORY, B3_DONATE, B3_XLRSTATS,  B3_WIKI, B3_CONFIG_GENERATOR, \
               B3_DOCUMENTATION, B3_FORUM, B3_WEBSITE


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
        new_process.setIcon(QIcon(B3_ICON_SMALL))
        new_process.triggered.connect(self.parent().new_process_dialog)
        new_process.setVisible(True)
        ### INSTALL PLUGIN SUBMENU ENTRY
        install_plugin = QAction('Add Plugin', self.parent())
        install_plugin.setShortcut('Ctrl+P')
        install_plugin.setStatusTip('Install a new B3 plugin')
        install_plugin.setIcon(QIcon(ICON_PLUGINS))
        install_plugin.triggered.connect(self.parent().install_plugin)
        install_plugin.setVisible(True)
        ####  QUIT SUBMENU ENTRY
        quit_btn = QAction('Quit', self.parent())
        quit_btn.setShortcut('Ctrl+Q')
        quit_btn.setStatusTip('Shutdown B3')
        quit_btn.setIcon(QIcon(ICON_QUIT))
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
        update_check = QAction('Check Update', self.parent())
        update_check.setStatusTip('Check if a newer version of B3 is available')
        update_check.setIcon(QIcon(ICON_UPDATE))
        update_check.triggered.connect(self.parent().check_update)
        #### B3 PLUGIN DIRECTORY SUBMENU ENTRY
        plugin_directory = QAction('Plugins Directory', self.parent())
        plugin_directory.setStatusTip('Open the 3rd party plugins directory')
        plugin_directory.setIcon(QIcon(ICON_PLUGINS))
        plugin_directory.triggered.connect(self.parent().open_extplugins_directory)
        #### B3 PLUGIN ARCHIVE SUBMENU ENTRY
        plugin_repository = QAction('Plugins Repository', self.parent())
        plugin_repository.setStatusTip('Browse all the available B3 plugins')
        plugin_repository.setIcon(QIcon(ICON_PLUGINS))
        plugin_repository.triggered.connect(lambda: webbrowser.open(B3_PLUGIN_REPOSITORY))
        #### UPDATE B3 DATABASE ENTRY
        update_database = QAction('Update B3 Database', self.parent())
        update_database.setStatusTip('Update all your B3 databases to the latest version')
        update_database.setIcon(QIcon(ICON_DATABASE))
        update_database.triggered.connect(self.parent().update_database)
        #### PREFERENCES
        preferences = QAction('Preferences...', self.parent())
        preferences.setStatusTip('Open the B3 preferences panel')
        preferences.setIcon(QIcon(ICON_SETTINGS))
        preferences.triggered.connect(self.parent().open_preferences)
        ## TOOLS MENU ENTRY
        tools_menu = self.addMenu('&Tools')
        tools_menu.addAction(preferences)
        if b3.getPlatform() != 'darwin':
            tools_menu.addSeparator()
        tools_menu.addAction(update_check)
        tools_menu.addAction(update_database)
        tools_menu.addSeparator()
        tools_menu.addAction(plugin_directory)
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
        donate.setIcon(QIcon(ICON_PAYPAL))
        donate.triggered.connect(lambda: webbrowser.open(B3_DONATE))
        #### XLRSTATS WEBTOOL
        xlrstats = QAction('XLRstats webtool', self.parent())
        xlrstats.setStatusTip('Visit the XLRstats webtool homepage')
        xlrstats.setIcon(QIcon(ICON_XLRSTATS))
        xlrstats.triggered.connect(lambda: webbrowser.open(B3_XLRSTATS))
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
        help_menu.addAction(xlrstats)
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
        show.triggered.connect(self.parent().make_visible)
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
            self.parent().make_visible()


from b3.gui import B3App
from b3.gui import B3_ICON_SMALL, ICON_DATABASE, ICON_SETTINGS, ICON_UPDATE, ICON_PLUGINS, \
                   ICON_QUIT, ICON_XLRSTATS, ICON_PAYPAL