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
import feedparser
import logging
import os
import re

from PyQt5.QtCore import QProcess, Qt, QEvent, QTimer, QThread, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QPixmap, QIcon, QCursor, QPainter, QFont
from PyQt5.QtWidgets import QLabel, QVBoxLayout, QTableWidget, QAbstractItemView, QHeaderView, QSpacerItem, QSizePolicy
from PyQt5.QtWidgets import QHBoxLayout, QWidget, QMessageBox, QMainWindow, QDesktopWidget, QSystemTrayIcon, QFileDialog
from b3 import B3_TITLE, B3_RSS
from b3.config import MainConfig, XmlConfigParser, load as load_config
from b3.exceptions import ConfigFileNotFound
from b3.exceptions import ConfigFileNotValid
from datetime import datetime, date, timedelta
from functools import partial

LOG = logging.getLogger('B3')

GEOMETRY = {
    'nt': {
        'MAIN_TABLE_HEIGHT': 260,
        'MAIN_TABLE_COLUMN_NAME_WIDTH': 200,
        'MAIN_TABLE_COLUMN_NAME_WIDTH_SCROLLBAR': 188,
        'MAIN_TABLE_COLUMN_STATUS_WIDTH': 158,
        'MAIN_TABLE_COLUMN_STATUS_WIDTH_SCROLLBAR': 148,
        'CENTRAL_WIDGET_BOTTOM_LAYOUT_MARGIN_BOTTOM': 52,
        'MARQUEE_LABEL_FONT_SIZE': 9,
    },
    'darwin': {
        'MAIN_TABLE_HEIGHT': 280,
        'MAIN_TABLE_COLUMN_NAME_WIDTH': 198,
        'MAIN_TABLE_COLUMN_NAME_WIDTH_SCROLLBAR': 188,
        'MAIN_TABLE_COLUMN_STATUS_WIDTH': 160,
        'MAIN_TABLE_COLUMN_STATUS_WIDTH_SCROLLBAR': 154,
        'CENTRAL_WIDGET_BOTTOM_LAYOUT_MARGIN_BOTTOM': 32,
        'MARQUEE_LABEL_FONT_SIZE': 12,
    },
    'linux': {
        'MAIN_TABLE_HEIGHT': 260,
        'MAIN_TABLE_COLUMN_NAME_WIDTH': 200,
        'MAIN_TABLE_COLUMN_NAME_WIDTH_SCROLLBAR': 188,
        'MAIN_TABLE_COLUMN_STATUS_WIDTH': 158,
        'MAIN_TABLE_COLUMN_STATUS_WIDTH_SCROLLBAR': 148,
        'CENTRAL_WIDGET_BOTTOM_LAYOUT_MARGIN_BOTTOM': 56,
        'MARQUEE_LABEL_FONT_SIZE': 9,
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


class IconWidget(QLabel):
    """
    This class can be used to render game icons.
    """
    def __init__(self, parent=None, image=None):
        """
        :param parent: the parent widget
        :param image: the image to display
        """
        QLabel.__init__(self, parent)
        pixmap = QPixmap(image)
        self.setPixmap(pixmap.scaled(32, 32))
        self.setGeometry(0, 0, 32, 32)
        self.setProperty('class', 'icon')


class MarqueeLabel(QLabel):
    """
    This class can be used to display news in the Main Window.
    """
    px = 0
    py = 0
    font = None
    paused = False
    qthread = None
    refresh_msec = 30
    textWidth = 0
    timer = None

    def __init__(self, parent=None):
        """
        :param parent: the parent widget
        """
        QLabel.__init__(self, parent)
        self.initUI()

    def initUI(self):
        """
        Initialize the MarqueeLabel layout.
        """
        self.setFixedSize(433, 40)
        self.font = QFont("Arial", GEOMETRY[b3.getPlatform()]['MARQUEE_LABEL_FONT_SIZE'])
        self.font.setItalic(True)
        self.setFont(self.font)
        self.setStyleSheet("""
        QLabel {
            background: transparent;
            color: #484848;
        }
        """)

        self.setVisible(B3App.Instance().settings.value('show_rss_news', type=bool))

    def parseFeed(self):
        """
        Parse the news feed and start the news scrolling.
        """
        class FeedParser(QThread):

            msignal = pyqtSignal(str)

            def run(self):
                """
                Threaded code.
                """
                try:
                    LOG.debug('parsing RSS feeds from: %s', B3_RSS)
                    feed = feedparser.parse(B3_RSS)
                except Exception, e:
                    LOG.warning('could not parse RSS feed from %s: %s', B3_RSS, e)
                else:
                    feedlist = []
                    for item in feed['entries']:
                        feeddate = ' '.join(item['published'].split(' ')[1:4])
                        feedlist.append('[%(DATE)s] %(TEXT)s' % dict(DATE=feeddate, TEXT=item['title']))

                    self.msignal.emit(' - '.join(feedlist))

        self.qthread = FeedParser(self)
        self.qthread.msignal.connect(self.setMarqueeText)
        self.qthread.finished.connect(self.start)
        self.qthread.start()

    @pyqtSlot(str)
    def setMarqueeText(self, text):
        """
        Set the scrolling text.
        """
        self.setText(text)
        self.textWidth = self.fontMetrics().boundingRect(self.text()).width()
        self.px = self.width()
        self.py = self.height() - self.fontMetrics().boundingRect(self.text()).height() + 10

    def start(self):
        """
        Start the news scroller.
        """
        if self.text():
            self.timer = QTimer(self)
            self.timer.timeout.connect(self.scrollText)
            self.timer.start(self.refresh_msec)

    ################################################## EVENTS ##########################################################

    def event(self, event):
        """
        Handle intercepted events.
        """
        if event.type() == QEvent.Enter:
            self.paused = True
        elif event.type() == QEvent.Leave:
            self.paused = False
        return QLabel.event(self, event)

    def paintEvent(self, QPaintEvent):
        """
        Executed whenever the QLabel is painted.
        """
        if self.text():
            p = QPainter(self)
            p.setFont(self.font)
            p.drawText(self.px, self.py, self.text())
            p.translate(self.px, self.py)

    ############################################## EVENT HANDLERS ######################################################

    def scrollText(self):
        """
        Scroll the QLabel text from right to left.
        """
        if not self.paused:
            if -self.px > self.textWidth:
                self.px = self.width()
            else:
                self.px -= 1
        self.repaint()


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
        self.setFixedSize(594, GEOMETRY[b3.getPlatform()]['MAIN_TABLE_HEIGHT'])
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
        QTableWidget QLabel.name {
            margin-left: 1px;
        }
        QTableWidget QLabel.icon {
            margin-left: 1px;
        }
        QTableWidget QLabel.idle {
            font-style: italic;
            background: yellow;
            color: #484848;
            margin: 1px;
        }
        QTableWidget QLabel.running {
            font-style: italic;
            background: green;
            color: white;
            margin: 1px;
        }
        QTableWidget QLabel.errored {
            font-style: italic;
            background: red;
            color: white;
            margin: 1px;
        }
        """)
        self.setShowGrid(False)
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setSelectionMode(QAbstractItemView.NoSelection)
        self.setFocusPolicy(Qt.NoFocus)
        self.horizontalHeader().setVisible(False)
        self.verticalHeader().setVisible(False)
        self.verticalHeader().sectionResizeMode(QHeaderView.Fixed)
        self.verticalHeader().setDefaultSectionSize(34)
        self.verticalScrollBar().setStyleSheet("""
        QScrollBar:vertical {
            background: #B7B7B7;
            border: 0;
        }
        """)

    def paint(self):
        """
        Paint table contents.
        """
        rowcount = len(B3App.Instance().processes)
        self.setRowCount(rowcount)
        self.setColumnCount(4)
        self.setColumnWidth(0, 34)

        ## MAKE SPACE FOR SCROLLBAR
        if len(B3App.Instance().processes) > 8:
            self.setColumnWidth(1, GEOMETRY[b3.getPlatform()]['MAIN_TABLE_COLUMN_NAME_WIDTH_SCROLLBAR'])
            self.setColumnWidth(2, GEOMETRY[b3.getPlatform()]['MAIN_TABLE_COLUMN_STATUS_WIDTH_SCROLLBAR'])
        else:
            self.setColumnWidth(1, GEOMETRY[b3.getPlatform()]['MAIN_TABLE_COLUMN_NAME_WIDTH'])
            self.setColumnWidth(2, GEOMETRY[b3.getPlatform()]['MAIN_TABLE_COLUMN_STATUS_WIDTH'])

        self.setColumnWidth(3, 200)
        for i in range(len(B3App.Instance().processes)):
            self.paint_row(i)

        ## SHOW THE HELP LABEL IF NEEDED
        if self.parent().help_label:
            self.parent().help_label.setVisible(rowcount == 0)

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

        def __paint_column_icon(parent, numrow, proc):
            """
            Paint the B3 instance icon in the 1st column.
            """
            path = ICON_GAME % proc.game
            if not os.path.isfile(path):
                path = ICON_GAME % 'default'
            parent.setCellWidget(numrow, 0, IconWidget(self, path))

        def __paint_column_name(parent, numrow, proc):
            """
            Paint the B3 instance name in the 2nd column.
            """
            def __get_formatted_lastrun(lastrun_time):
                """
                Return a formatted string representing the process last run.
                """
                formatted_time = 'never'
                if lastrun_time:
                    lastrun_date = date.fromtimestamp(lastrun_time)
                    if lastrun_date == date.today():
                        formatted_time = 'today @ %s' % datetime.fromtimestamp(lastrun_time).strftime('%H:%M')
                    elif lastrun_date == date.today() - timedelta(days=1):
                        formatted_time = 'yesterday @ %s' % datetime.fromtimestamp(lastrun_time).strftime('%H:%M')
                    else:
                        formatted_time = datetime.fromtimestamp(lastrun_time).strftime('%Y/%m/%d %H:%M')
                return formatted_time

            text = """
            <b>%(NAME)s</b><br/>
            <i style="font-size: 11px; color: #777777;">Last run: %(LASTRUN)s</i>
            """ % dict(NAME=re.sub(RE_COLOR, '', proc.name).strip(), LASTRUN=__get_formatted_lastrun(proc.lastrun))

            label = QLabel(text, parent)
            label.setProperty('class', 'name')
            label.setWordWrap(True)
            label.setAlignment(Qt.AlignLeft|Qt.AlignVCenter)
            parent.setCellWidget(numrow, 1, label)

        def __paint_column_status(parent, numrow, proc):
            """
            Paint the B3 instance status in the 3rd column.
            """
            if proc.state() == QProcess.Running:
                clazz = 'running'
                text = 'RUNNING'
            else:
                if proc.isFlag(CONFIG_READY):
                    clazz = 'idle'
                    text = 'IDLE'
                else:
                    clazz = 'errored'
                    text = 'INVALID CONFIG' if proc.isFlag(CONFIG_FOUND) else 'MISSING CONFIG'

            label = QLabel(text, parent)
            label.setProperty('class', clazz)
            label.setWordWrap(True)
            label.setAlignment(Qt.AlignCenter)
            parent.setCellWidget(numrow, 2, label)

        def __paint_column_toolbar(parent, numrow, proc):
            """
            Paint the B3 instance toolbar in the 4th column.
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
            btn_refresh.clicked.connect(partial(parent.process_refresh, row=numrow, process=proc))
            ## LOGFILE BUTTON
            btn_log = IconButton(parent=parent, icon=QIcon(ICON_LOG))
            btn_log.setStatusTip('Show %s log' % proc.name)
            btn_log.setVisible(True)
            btn_log.clicked.connect(partial(parent.process_log, process=proc))
            ## CONSOLE BUTTON
            btn_console = IconButton(parent=parent, icon=QIcon(ICON_CONSOLE))
            btn_console.setStatusTip('Show %s console output' % proc.name)
            btn_console.setVisible(True)
            btn_console.clicked.connect(partial(parent.process_console, process=proc))

            ## CONFIG BUTTON
            ICON_CONFIG = ICON_INI
            if proc.isFlag(CONFIG_FOUND) and isinstance(proc.config._config_parser, XmlConfigParser):
                ICON_CONFIG = ICON_XML

            btn_config = IconButton(parent=parent, icon=QIcon(ICON_CONFIG))
            btn_config.setStatusTip('Show %s configuration file' % proc.name)
            btn_config.setVisible(True)
            btn_config.clicked.connect(partial(parent.process_config, process=proc))

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
            layout.addWidget(btn_config)
            layout.addWidget(btn_ctrl)
            layout.setAlignment(Qt.AlignCenter)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(1)
            widget = QWidget(parent)
            widget.setLayout(layout)
            widget.setStyleSheet("""
            QDialog {
                background: #FFFFFF;
                border: 0;
            }
            """)

            parent.setCellWidget(numrow, 3, widget)

        __paint_column_icon(self, row, process)
        __paint_column_name(self, row, process)
        __paint_column_status(self, row, process)
        __paint_column_toolbar(self, row, process)

    ############################################# EVENT HANDLERS #######################################################

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
                path = url.path()
                if b3.getPlatform() == 'nt':
                    # on win32 the absolute path returned for each url has a leading slash: this obviously
                    # is not correct on win32 platform when absolute url have the form C:\\Programs\\... (Qt bug?)
                    path = path.lstrip('/').lstrip('\\')
                if os.path.isfile(path):
                    self.parent().parent().make_new_process(path)
            event.accept()
        else:
            event.ignore()

    ############################################ TOOLBAR HANDLERS ######################################################

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
            self.paint_row(row)
            if process.isFlag(CONFIG_READY):
                process.stateChanged.connect(partial(self.paint_row, row=row))
                process.start()
            else:
                if warn:
                    suffix = 'not found' if process.isFlag(CONFIG_FOUND) else 'not valid'
                    reason = 'configuration file %s: %s' % (suffix, process.config_path)
                    msgbox = QMessageBox()
                    msgbox.setIcon(QMessageBox.Warning)
                    msgbox.setWindowTitle('WARNING')
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
        msgbox = QMessageBox()
        msgbox.setIcon(QMessageBox.Question)
        msgbox.setWindowTitle('CONFIRM')
        msgbox.setText('Are you sure?')
        msgbox.setInformativeText('Do you want to remove %s?' % process.name)
        msgbox.setStandardButtons(QMessageBox.No|QMessageBox.Yes)
        msgbox.setDefaultButton(QMessageBox.No)
        msgbox.layout().addItem(QSpacerItem(300, 0, QSizePolicy.Minimum, QSizePolicy.Expanding),
                                msgbox.layout().rowCount(), 0, 1, msgbox.layout().columnCount())
        msgbox.exec_()

        if msgbox.result() == QMessageBox.Yes:
            if process.state() != QProcess.NotRunning:
                self.process_shutdown(process)
            process.delete()
            self.repaint()

    def process_refresh(self, row, process):
        """
        Refresh a process configuration file
        """
        if process.state() == QProcess.Running:
            msgbox = QMessageBox()
            msgbox.setIcon(QMessageBox.Information)
            msgbox.setWindowTitle('NOTICE')
            msgbox.setText('%s is currently running: you need to stop it to refresh the configuration file.' % process.name)
            msgbox.setStandardButtons(QMessageBox.Ok)
            msgbox.exec_()
        else:
            process.config = process.config_path
            self.paint_row(row)

    def process_console(self, process):
        """
        Display the STDOut console of a process.
        """
        if not process.stdout:
            msgbox = QMessageBox()
            msgbox.setIcon(QMessageBox.Warning)
            msgbox.setWindowTitle('WARNING')
            msgbox.setText('%s console initialization failed!' % process.name)
            msgbox.setStandardButtons(QMessageBox.Ok)
            msgbox.exec_()
        else:
            process.stdout.show()

    def process_config(self, process):
        """
        Open the B3 instance configuration file.
        """
        if not process.isFlag(CONFIG_FOUND):
            msgbox = QMessageBox()
            msgbox.setIcon(QMessageBox.Warning)
            msgbox.setWindowTitle('WARNING')
            msgbox.setText('Missing %s configuration file' % process.name)
            msgbox.setStandardButtons(QMessageBox.Ok)
            msgbox.exec_()
        else:
            B3App.Instance().openpath(process.config.fileName)

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

            path = b3.getAbsolutePath(process.config.get('b3', 'logfile'), decode=True, conf=process.config)
            if not os.path.isfile(path):
                message = '- missing: %s' % path
                path = os.path.join(b3.HOMEDIR, os.path.basename(path))
                if not os.path.isfile(path):
                    raise Exception(message + '\n- missing: %s' % path)

        except Exception, err:
            msgbox = QMessageBox()
            msgbox.setIcon(QMessageBox.Warning)
            msgbox.setWindowTitle('WARNING')
            msgbox.setText('%s log file no found' % process.name)
            msgbox.setDetailedText(err.message)
            msgbox.setStandardButtons(QMessageBox.Ok)
            msgbox.layout().addItem(QSpacerItem(400, 0, QSizePolicy.Minimum, QSizePolicy.Expanding),
                                    msgbox.layout().rowCount(), 0, 1, msgbox.layout().columnCount())
            msgbox.exec_()
        else:
            B3App.Instance().openpath(path)


class HelpLabel(QLabel):
    """
    This class implements the text which is overlaying the Main Table when there are no B3 processes.
    """
    def __init__(self, parent=None):
        """
        :param parent: the parent widget
        """
        QLabel.__init__(self, parent)
        self.initUI()

    def initUI(self):
        """
        Initialize the Help label user interface.
        """
        self.setText('drop your configuration(s) file here')
        self.setFixedSize(594, GEOMETRY[b3.getPlatform()]['MAIN_TABLE_HEIGHT'])
        self.setAlignment(Qt.AlignCenter)
        self.setVisible(len(B3App.Instance().processes) == 0)
        self.setAcceptDrops(True)
        self.setStyleSheet("""
        QLabel {
            background: transparent;
            font-size: 20px;
            font-style: italic;
            color: #CCCCCC;
        }
        """)

    ############################################# EVENT HANDLERS #######################################################

    def dragEnterEvent(self, event):
        """
        Handle 'Drag Enter' event.
        """
        self.parent().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        """
        Handle 'Drag Move' event.
        """
        self.parent().dragMoveEvent(event)

    def dragLeaveEvent(self, event):
        """
        Handle 'Drag Leave' event.
        """
        self.parent().dragLeaveEvent(event)

    def dropEvent(self, event):
        """
        Handle 'Drop' event.
        """
        self.parent().dropEvent(event)


class CentralWidget(QWidget):
    """
    This class implements the central widget.
    """
    main_table = None
    help_label = None
    news = None

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
            parent.help_label = HelpLabel(parent.main_table)
            layout = QVBoxLayout()
            layout.addWidget(parent.main_table)
            #layout.addWidget(parent.help_label)
            layout.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
            layout.setContentsMargins(0, 2, 0, 0)
            return layout

        def __get_bottom_layout(parent):
            parent.news = MarqueeLabel(parent)
            parent.news.parseFeed()
            btn_new = Button(parent=parent, text='Add', shortcut='Ctrl+N')
            btn_new.clicked.connect(self.parent().new_process_dialog)
            btn_new.setStatusTip('Add a new B3')
            btn_new.setVisible(True)
            btn_quit = Button(parent=parent, text='Quit', shortcut='Ctrl+Q')
            btn_quit.clicked.connect(B3App.Instance().shutdown)
            btn_quit.setStatusTip('Shutdown B3')
            btn_quit.setVisible(True)
            layout = QHBoxLayout()
            layout.addWidget(parent.news)
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
        self.setFixedSize(614, 512)
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
    system_tray_minimized = False
    system_tray_balloon = {
        'win32': "B3 is still running! "
                 "If you want to quit B3, right click this icon and select 'Quit'.",
        'darwin': "B3 is still running! "
                  "If you want to quit B3, close the application using the Dock launcher.",
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
        self.setFixedSize(614, 512)
        ## INIT SUBCOMPONENTS
        self.setStatusBar(StatusBar(self))
        self.setMenuBar(MainMenuBar(self))
        self.setCentralWidget(CentralWidget(self))

        ## INIT SYSTEM TRAY ICON
        if b3.getPlatform() != 'linux':
            self.system_tray = SystemTrayIcon(self)
            self.system_tray.show()

        ## MOVE TO CENTER SCREEN
        screen = QDesktopWidget().screenGeometry()
        position_x = (screen.width() - self.geometry().width()) / 2
        position_y = (screen.height() - self.geometry().height()) / 2
        self.move(position_x, position_y)

    ############################################# EVENTS HANDLERS ######################################################

    def closeEvent(self, event):
        """
        Executed when the main window is closed.
        """
        if b3.getPlatform() != 'darwin':
            # close the application on win32 and linux
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
        if b3.getPlatform() == 'nt':
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
        if b3.getPlatform() != 'linux':
            # do not use system tray on linux since it looks bad on Ubuntu
            # which is the mainly used Linux client distribution (they can live without it)
            self.hide()
            if not self.system_tray_minimized:
                self.system_tray_minimized = True
                self.system_tray.showMessage("B3 is still running!",
                                             self.system_tray_balloon[b3.getPlatform()],
                                             QSystemTrayIcon.Information, 20000)

    ############################################# ACTION HANDLERS ######################################################

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
                msgbox.setWindowTitle('WARNING')
                msgbox.setText('You selected an invalid configuration file')
                msgbox.setStandardButtons(QMessageBox.Ok)
                msgbox.exec_()
            else:
                analysis = config.analyze()
                if analysis:
                    msgbox = QMessageBox()
                    msgbox.setIcon(QMessageBox.Critical)
                    msgbox.setWindowTitle('ERROR')
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
        self.make_visible()
        init = b3.getAbsolutePath('@b3/conf')
        extensions = ['INI (*.ini)', 'XML (*.xml)', 'All Files (*.*)']
        path, _ = QFileDialog.getOpenFileName(self.centralWidget(), 'Select configuration file', init, ';;'.join(extensions))
        self.make_new_process(path)

    def install_plugin(self):
        """
        Handle the install of a new B3 plugin.
        """
        self.make_visible()
        init = b3.getAbsolutePath('~')
        path, _ = QFileDialog.getOpenFileName(self.centralWidget(), 'Select plugin package', init, 'ZIP (*.zip)')
        if path:
            install = PluginInstallDialog(self.centralWidget(), path)
            install.show()

    def show_about(self):
        """
        Display the 'about' dialog.
        """
        self.make_visible()
        about = AboutDialog(self.centralWidget())
        about.show()

    def check_update(self):
        """
        Display the 'update check' dialog.
        """
        self.make_visible()
        update = UpdateCheckDialog(self.centralWidget())
        update.show()

    def open_preferences(self):
        """
        Open the 'Preferences' dialog.
        """
        self.make_visible()
        preferences = PreferencesDialog(self.centralWidget())
        preferences.show()

    def open_extplugins_directory(self):
        """
        Open the default extplugins directory.
        """
        self.make_visible()
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
                msgbox.setWindowTitle('WARNING')
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
            msgbox.setWindowTitle('NOTICE')
            msgbox.setText('Some B3 processes are still running: you need to terminate them to update B3 database.')
            msgbox.setStandardButtons(QMessageBox.Ok)
            msgbox.exec_()
        else:
            update = UpdateDatabaseDialog(self.centralWidget())
            update.show()

from b3.gui import B3App, RE_COLOR, CONFIG_READY, CONFIG_FOUND, ICON_DEL, ICON_REFRESH, ICON_CONSOLE, ICON_LOG, ICON_GAME
from b3.gui import ICON_STOP, ICON_START, ICON_INI, ICON_XML, CONFIG_VALID, B3_BANNER, B3
from b3.gui.dialogs import AboutDialog, PluginInstallDialog, UpdateCheckDialog, UpdateDatabaseDialog, PreferencesDialog
from b3.gui.misc import Button, IconButton, StatusBar
from b3.gui.system import MainMenuBar, SystemTrayIcon