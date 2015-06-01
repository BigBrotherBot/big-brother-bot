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
import logging
import os
import re

from PyQt5.QtCore import QProcess, Qt, QEvent
from PyQt5.QtGui import QPixmap, QIcon, QCursor
from PyQt5.QtWidgets import QLabel, QVBoxLayout, QTableWidget, QAbstractItemView, QHeaderView, QTableWidgetItem
from PyQt5.QtWidgets import QHBoxLayout, QWidget, QMessageBox, QMainWindow, QDesktopWidget, QSystemTrayIcon, QFileDialog
from b3 import B3_TITLE
from b3.config import MainConfig, load as load_config
from b3.exceptions import ConfigFileNotFound
from b3.exceptions import ConfigFileNotValid
from functools import partial

LOG = logging.getLogger('B3')

GEOMETRY = {
    'win32': {
        'MAIN_TABLE_HEIGHT': 260,
        'CENTRAL_WIDGET_BOTTOM_LAYOUT_MARGIN_BOTTOM': 52,
    },
    'darwin': {
        'MAIN_TABLE_HEIGHT': 280,
        'CENTRAL_WIDGET_BOTTOM_LAYOUT_MARGIN_BOTTOM': 40,
    },
    'linux': {
        'MAIN_TABLE_HEIGHT': 280,
        'CENTRAL_WIDGET_BOTTOM_LAYOUT_MARGIN_BOTTOM': 32,
    }
}


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
        self.setFixedSize(500, GEOMETRY[b3.getPlatform()]['MAIN_TABLE_HEIGHT'])
        self.setStyleSheet("""
        QWidget {
            background: #FFFFFF;
            border: 0;
        }
        QTableWidget {
            background: #FFFFFF;
            border: 1px solid #B7B7B7;
            color: #484848;
        }
        """)
        self.setShowGrid(False)
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setSelectionMode(QAbstractItemView.NoSelection)
        self.horizontalHeader().setVisible(False)
        self.verticalHeader().setVisible(False)
        self.verticalHeader().sectionResizeMode(QHeaderView.Fixed)
        self.verticalHeader().setDefaultSectionSize(24)

    def paint(self):
        """
        Paint table contents.
        """
        self.setRowCount(len(B3App.Instance().processes))
        self.setColumnCount(3)
        self.setColumnWidth(0, 200)
        self.setColumnWidth(1, 180)
        self.setColumnWidth(2, 118)
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
            widget.setStyleSheet("""
            QDialog {
                background: #FFFFFF;
                border: 0;
            }
            """)

            parent.setCellWidget(numrow, 2, widget)

        __paint_column_name(self, row, process)
        __paint_column_status(self, row, process)
        __paint_column_toolbar(self, row, process)

    ############################################# EVENT HANDLERS  ######################################################

    def dragEnterEvent(self, event):
        """
        Handle 'Drag Enter' event.
        """
        if event.mimeData().hasUrls():
            B3App.Instance().setOverrideCursor(QCursor(Qt.DragCopyCursor))
            event.setDropAction(Qt.CopyAction)
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        """
        Handle 'Drag Move' event.
        """
        event.accept()

    def dragLeaveEvent(self, event):
        """
        Handle 'Drag Leave' event.
        """
        B3App.Instance().setOverrideCursor(QCursor(Qt.ArrowCursor))

    def dropEvent(self, event):
        """
        Handle 'Drop' event.
        """
        if event.mimeData().hasUrls():
            B3App.Instance().setOverrideCursor(QCursor(Qt.ArrowCursor))
            event.setDropAction(Qt.CopyAction)
            # multi-drag support
            for url in event.mimeData().urls():
                path = url.path().lstrip('/').lstrip('\\')
                if os.path.isfile(path):
                    self.parent().parent().make_new_process(path)
            event.accept()
        else:
            event.ignore()

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

            path = os.path.abspath(process.config.getpath('b3', 'logfile'))
            if not os.path.isfile(path):
                message = '- missing: %s' % path
                path = os.path.join(b3.HOMEDIR, os.path.basename(path))
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
            B3App.Instance().openpath(path)


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
            btn_new.clicked.connect(self.parent().new_process_dialog)
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
            layout.setSpacing(10)
            layout.setContentsMargins(0, 0, 11, GEOMETRY[b3.getPlatform()]['CENTRAL_WIDGET_BOTTOM_LAYOUT_MARGIN_BOTTOM'])
            return layout

        main_layout = QVBoxLayout()
        main_layout.addLayout(__get_top_layout(self))
        main_layout.addLayout(__get_middle_layout(self))
        main_layout.addLayout(__get_bottom_layout(self))
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(main_layout)
        self.setFixedSize(520, 512)
        self.setStyleSheet("""
        QWidget, QDialog, QMessageBox {
            background: #F2F2F2;
        }
        """)
        self.setFocus()


class MainWindow(QMainWindow):
    """
    This class implements the main application window.
    """
    system_tray = None
    system_tray_minimized = False # this will be set to True after the first minimization
    system_tray_balloon = {
        'win32': "B3 will continue to run so that all your B3 processes will stay alive. "
                 "If you want to quit B3, right click this icon and select 'Quit'.",
        'darwin': "B3 will continue to run so that all your B3 processes will stay alive. "
                  "If you want to quit B3, close the application using the Dock launcher.",
        'linux': "B3 will continue to run so that all your B3 processes will stay alive. "
                 "If you want to quit B3, click the 'Quit' button in the main window.",
    }

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
        self.setFixedSize(520, 512)
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
                    self.minimize_in_system_tray()

    def make_visible(self):
        """
        Make sure that the main window is visible
        """
        self.setWindowState((self.windowState() & ~Qt.WindowMinimized) | Qt.WindowActive)
        self.activateWindow()
        self.raise_()
        self.show()

    def minimize_in_system_tray(self):
        """
        Minimize B3 in system tray icon
        """
        self.hide()
        if not self.system_tray_minimized:
            self.system_tray_minimized = True
            self.system_tray.showMessage("B3 is still running!",
                                         self.system_tray_balloon[b3.getPlatform()],
                                         QSystemTrayIcon.Information, 20000)

    ############################################# ACTION HANDLERS  #####################################################

    def make_new_process(self, path):
        """
        Create a new B3 process using the provided configuration file path.
        NOTE: this actually handle also the repainting of the main table but
        since it's not a toolbar button handler it has been implemented here instead.
        :param path: the configuration file path
        """
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

    def new_process_dialog(self):
        """
        Open the File dialog used to select a B3 configuration file.
        """
        self.show()
        init = b3.getAbsolutePath('@b3/conf')
        extensions = ['INI (*.ini)', 'XML (*.xml)', 'All Files (*.*)']
        path, _ = QFileDialog.getOpenFileName(self.centralWidget(), 'Select configuration file', init, ';;'.join(extensions))
        self.make_new_process(path)

    def install_plugin(self):
        """
        Handle the install of a new B3 plugin.
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
        Display the 'update check' dialog.
        """
        self.show()
        update = UpdateCheckDialog(self.centralWidget())
        update.show()

    def open_extplugins_directory(self):
        """
        Open the default extplugins directory.
        """
        extplugins_dir = b3.getAbsolutePath('@b3/extplugins', True)
        if not os.path.isdir(extplugins_dir):

            try:
                LOG.warning('missing %s directory: attempt to create it' % extplugins_dir)
                os.mkdir(extplugins_dir)
                with open(os.path.join(extplugins_dir, '__init.__py'), 'w') as f:
                    f.write('#')
            except Exception, err:
                LOG.error('could create default extplugins directory: %s', err)
                msgbox = QMessageBox()
                msgbox.setIcon(QMessageBox.Warning)
                msgbox.setText('Missing 3rd party plugins directory!')
                msgbox.setDetailedText('B3 could not create missing 3rd party plugins directory (%s). '
                                       'Please make sure B3 has writing permissions on "%s"' % (extplugins_dir,
                                                                                                b3.getAbsolutePath('@b3//', True)))
                msgbox.setStandardButtons(QMessageBox.Ok)
                msgbox.exec_()
                return
            else:
                LOG.debug('created directory %s: resuming directory prompt' % extplugins_dir)

        B3App.Instance().openpath(extplugins_dir)


    def update_database(self):
        """
        Display the 'database update' dialog.
        """
        self.show()

        is_something_running = False
        for x in B3App.Instance().processes:
            if x.state() == QProcess.Running:
                is_something_running = True
                break

        if is_something_running:
            msgbox = QMessageBox()
            msgbox.setIcon(QMessageBox.Information)
            msgbox.setText('Some B3 processes are still running: you need to terminate them to update B3 database.')
            msgbox.setStandardButtons(QMessageBox.Ok)
            msgbox.exec_()
        else:
            update = UpdateDatabaseDialog(self.centralWidget())
            update.show()

from b3.gui import B3App, RE_COLOR, CONFIG_READY, CONFIG_FOUND, ICON_DEL, ICON_REFRESH, ICON_CONSOLE, ICON_LOG
from b3.gui import ICON_STOP, ICON_START, CONFIG_VALID, B3_BANNER, B3
from b3.gui.dialogs import AboutDialog, PluginInstallDialog, UpdateCheckDialog, UpdateDatabaseDialog
from b3.gui.misc import Button, IconButton, StatusBar
from b3.gui.system import MainMenuBar, SystemTrayIcon