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
import b3.config
import glob
import imp
import json
import logging
import os
import shutil
import tempfile
import urllib2

from PyQt5.QtCore import Qt, QThread, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QTextCursor
from PyQt5.QtWidgets import QDialog, QHBoxLayout, QLabel, QVBoxLayout, QGroupBox, QCheckBox, QRadioButton

from b3 import B3_COPYRIGHT, B3_LICENSE, B3_TITLE, B3_TITLE_SHORT, B3_WEBSITE
from b3.parser import StubParser
from b3.functions import unzip, splitDSN, main_is_frozen
from b3.storage import getStorage
from b3.update import getDefaultChannel, B3version
from b3.update import URL_B3_LATEST_VERSION, UPDATE_CHANNEL_DEV, UPDATE_CHANNEL_BETA, UPDATE_CHANNEL_STABLE
from time import sleep

LOG = logging.getLogger('B3')


GEOMETRY = {
    'nt': {
        'ABOUT_DIALOG_WIDTH': 400,
        'ABOUT_DIALOG_HEIGHT': 520,
        'LICENSE_DIALOG_WIDTH': 400,
        'LICENSE_DIALOG_HEIGHT': 300,
    },
    'darwin': {
        'ABOUT_DIALOG_WIDTH': 400,
        'ABOUT_DIALOG_HEIGHT': 520,
        'LICENSE_DIALOG_WIDTH': 400,
        'LICENSE_DIALOG_HEIGHT': 300,
    },
    'linux': {
        'ABOUT_DIALOG_WIDTH': 400,
        'ABOUT_DIALOG_HEIGHT': 540,
        'LICENSE_DIALOG_WIDTH': 420,
        'LICENSE_DIALOG_HEIGHT': 380,
    }
}


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
        self.setFixedSize(GEOMETRY[b3.getPlatform()]['ABOUT_DIALOG_WIDTH'],
                          GEOMETRY[b3.getPlatform()]['ABOUT_DIALOG_HEIGHT'])
        self.setStyleSheet("""
        QDialog {
            background: #F2F2F2;
        }
        """)

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
            btn_license.clicked.connect(parent.show_license)
            btn_license.setVisible(True)
            btn_close = Button(parent=parent, text='Close')
            btn_close.clicked.connect(parent.close)
            btn_close.setVisible(True)
            layout = QHBoxLayout()
            layout.addWidget(btn_license)
            layout.addWidget(btn_close)
            layout.setAlignment(Qt.AlignHCenter|Qt.AlignTop)
            layout.setContentsMargins(0, 30, 0, 0)
            layout.setSpacing(20 if b3.getPlatform() == 'darwin' else 10)
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
        Initialize the 'License' dialog window.
        :param parent: the parent widget
        """
        QDialog.__init__(self, parent)
        self.initUI()

    def initUI(self):
        """
        Initialize the Dialog layout.
        """
        self.setWindowTitle(B3_LICENSE)
        self.setFixedSize(GEOMETRY[b3.getPlatform()]['LICENSE_DIALOG_WIDTH'],
                          GEOMETRY[b3.getPlatform()]['LICENSE_DIALOG_HEIGHT'])
        self.setStyleSheet("""
        QDialog {
            background: #F2F2F2;
        }
        """)

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
            layout.setAlignment(Qt.AlignHCenter|Qt.AlignTop)
            layout.setContentsMargins(0, 20, 0, 0)
            return layout

        main_layout = QVBoxLayout()
        main_layout.addLayout(__get_top_layout(self))
        main_layout.addLayout(__get_bottom_layout(self))
        self.setLayout(main_layout)
        self.setModal(True)


class UpdateCheckDialog(QDialog):
    """
    This class is used to display the 'update check' dialog.
    """
    channel = None
    layout = None
    message = None
    progress = None
    qthread = None

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
        self.setWindowTitle('Checking update')
        self.setFixedSize(400, 120)
        self.setStyleSheet("""
        QDialog {
            background: #F2F2F2;
        }
        """)
        ## INIT PROGRESS BAR
        self.progress = BusyProgressBar(self)
        self.progress.setAlignment(Qt.AlignHCenter)
        self.progress.start()
        ## INITIALIZE UPDATE CHANNEL
        self.channel = B3App.Instance().settings.value('update_channel')
        if self.channel not in (UPDATE_CHANNEL_STABLE, UPDATE_CHANNEL_BETA, UPDATE_CHANNEL_DEV):
            self.channel = getDefaultChannel(b3.__version__)
        ## INITIALIZE DEFAULT MESSAGE
        self.message = QLabel('connecting to update channel: %s' % self.channel, self)
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
        UI update is then handled through signals.
        """
        class UpdateCheck(QThread):

            msignal = pyqtSignal(str) # update message

            def run(self):
                """
                Threaded code.
                """
                sleep(2)
                LOG.info('retrieving update data from remote server: %s', URL_B3_LATEST_VERSION)

                try:
                    jsondata = urllib2.urlopen(URL_B3_LATEST_VERSION, timeout=4).read()
                    versioninfo = json.loads(jsondata)
                except urllib2.URLError, err:
                    self.msignal.emit('ERROR: could not connect to the update server: %s' % err.reason)
                    LOG.error('could not connect to the update server: %s', err.reason)
                except IOError, err:
                    self.msignal.emit('ERROR: could not read data: %s' % err)
                    LOG.error('could not read data: %s', err)
                except Exception, err:
                    self.msignal.emit('ERROR: unknown error: %s' % err)
                    LOG.error('ERROR: unknown error: %s', err)
                else:
                    self.msignal.emit('parsing data')
                    sleep(1.5)

                    channels = versioninfo['B3']['channels']
                    if self.parent().channel not in channels:
                        self.msignal.emit('ERROR: unknown channel \'%s\': expecting (%s)' % (self.parent().channel, ', '.join(channels.keys())))
                        LOG.error('unknown channel \'%s\': expecting (%s)', self.parent().channel, ', '.join(channels.keys()))
                    else:
                        try:
                            latestversion = channels[self.parent().channel]['latest-version']
                        except KeyError:
                            self.msignal.emit('ERROR: could not get latest B3 version for channel: %s' % self.parent().channel)
                            LOG.error('could not get latest B3 version for channel: %s', self.parent().channel)
                        else:
                            if B3version(b3.__version__) < B3version(latestversion):

                                try:
                                    url = versioninfo['B3']['channels'][self.parent().channel]['url']
                                except KeyError:
                                    url = B3_WEBSITE

                                self.msignal.emit('update available: <a href="%s">%s</a>' % (url, latestversion))
                                LOG.info('update available: %s - %s', url, latestversion)
                            else:
                                self.msignal.emit('no update available')
                                LOG.info('no update available')

        self.qthread = UpdateCheck(self)
        self.qthread.msignal.connect(self.update_message)
        self.qthread.finished.connect(self.finished)
        self.qthread.start()

    @pyqtSlot(str)
    def update_message(self, message):
        """
        Update the status message.
        """
        self.message.setText(message)

    def finished(self):
        """
        Execute when the QThread emits the finished signal.
        """
        self.progress.stop()


class UpdateDatabaseDialog(QDialog):
    """
    This class is used to display the 'update check' dialog.
    """
    btn_close = None
    btn_update = None
    layout1 = None
    layout2 = None
    main_layout = None
    message = None
    progress = None
    qthread = None

    def __init__(self, parent=None):
        """
        Initialize the 'update check' dialog window
        :param parent: the parent widget
        """
        QDialog.__init__(self, parent)
        self.initUI()

    def initUI(self):
        """
        Initialize the Dialog layout.
        """
        self.setWindowTitle('B3 database update')
        self.setFixedSize(420, 160)
        self.setStyleSheet("""
        QDialog {
            background: #F2F2F2;
        }
        """)

        ## INIT CLOSE BUTTON
        self.btn_close = Button(parent=self, text='Close')
        self.btn_close.clicked.connect(self.close)
        self.btn_close.hide()
        ## INIT UPDATE BUTTON
        self.btn_update = Button(parent=self, text='Update')
        self.btn_update.clicked.connect(self.do_update)
        self.btn_update.show()
        ## CREATE THE PROGRESS BAR
        self.progress = ProgressBar(self)
        self.progress.setAlignment(Qt.AlignHCenter)
        self.progress.hide()
        self.progress.setRange(0, 0)
        self.progress.setValue(-1)
        ## INIT DISPLAY MESSAGE
        self.message = QLabel("This tool will update all your B3 databases to version %s.\n"
                              "The update process should take less than 2 minutes and\n"
                              "cannot be interrupted." % b3.__version__, self)

        def __get_top_layout(parent):
            parent.layout1 = QVBoxLayout()
            parent.layout1.addWidget(parent.progress)
            parent.layout1.addWidget(parent.message)
            parent.layout1.setAlignment(Qt.AlignTop|Qt.AlignHCenter)
            parent.layout1.setContentsMargins(0, 0, 0, 0)
            return parent.layout1

        def __get_bottom_layout(parent):
            parent.layout2 = QHBoxLayout()
            parent.layout2.addWidget(parent.btn_close)
            parent.layout2.addWidget(parent.btn_update)
            parent.layout2.setAlignment(Qt.AlignHCenter)
            parent.layout2.setSpacing(20 if b3.getPlatform() != 'win32' else 10)
            parent.layout2.setContentsMargins(0, 10, 0, 0)
            return parent.layout2

        self.setModal(True)
        self.main_layout = QVBoxLayout()
        self.main_layout.addLayout(__get_top_layout(self))
        self.main_layout.addLayout(__get_bottom_layout(self))
        self.main_layout.setAlignment(Qt.AlignCenter)
        self.setLayout(self.main_layout)

    def keyPressEvent(self, event):
        """
        Prevent the user from closing the dialog using the ESC key.
        """
        if event.key() == Qt.Key_Escape:
            event.ignore()
        else:
            QDialog.keyPressEvent(self, event)

    def do_update(self):
        """
        Update B3 databases.
        """
        ## CREATE THE PROGRESS BAR
        self.progress.show()
        self.progress.setAlignment(Qt.AlignHCenter)
        ## CHANGE CURRENT MESSAGE WITH A PLACEHOLDER
        self.message.setText('starting update')
        self.message.setAlignment(Qt.AlignHCenter)
        ## HIDE CONTROL BUTTONS
        self.btn_close.hide()
        self.btn_update.hide()

        class DatabaseUpdate(QThread):

            msignal = pyqtSignal(str)
            psignal = pyqtSignal(int, int, int)

            def run(self):
                """
                Threaded code.
                """
                sleep(1.5)
                LOG.debug('requested B3 database update')

                def _update_database(process, storage, version):
                    """
                    Update a B3 database.
                    :param process: the B3 process we are updating
                    :param storage: the initialized storage module
                    :param version: the update version
                    """
                    if B3version(b3.__version__) >= version:
                        sql = b3.getAbsolutePath('@b3/sql/%s/b3-update-%s.sql' % (storage.protocol, version))
                        if os.path.isfile(sql):

                            try:
                                LOG.debug('updating %s database to version %s', process.name, version)
                                storage.queryFromFile(sql)
                            except Exception, err:
                                LOG.warning('could not update %s database properly: %s', process.name, err)

                collection = [x for x in B3App.Instance().processes if x.isFlag(CONFIG_VALID)]
                collection_len = len(collection)
                self.psignal.emit(0, collection_len, 0)
                sleep(.5)

                # LOOP AND UPDATE
                for proc in collection:

                    index = collection.index(proc) + 1
                    self.msignal.emit('(%s/%s) updating database: %s' % (index, collection_len, proc.name))
                    self.psignal.emit(0, collection_len, index)

                    sleep(1)

                    try:
                        dsn = proc.config.get('b3', 'database')
                        dsndict = splitDSN(dsn)
                        database = getStorage(dsn, dsndict, StubParser())
                        # START UPDATING THE PROCESS DATABASE
                        _update_database(proc, database, '1.3.0')
                        _update_database(proc, database, '1.6.0')
                        _update_database(proc, database, '1.7.0')
                        _update_database(proc, database, '1.8.1')
                        _update_database(proc, database, '1.9.0')
                        _update_database(proc, database, '1.10.0')
                    except Exception, e:
                        LOG.error('unhandled exception raised while updating %s database: %s', proc.name, e)
                        self.msignal.emit('ERROR: could not update %s database' % proc.name)
                        sleep(2)

        self.qthread = DatabaseUpdate(self)
        self.qthread.msignal.connect(self.update_message)
        self.qthread.psignal.connect(self.update_progress)
        self.qthread.finished.connect(self.finished)
        self.qthread.start()

    @pyqtSlot(str)
    def update_message(self, message):
        """
        Update the status message
        """
        self.message.setText(message)

    @pyqtSlot(int, int, int)
    def update_progress(self, range_1, range_2, value):
        """
        Update the progress bar.
        """
        self.progress.setRange(range_1, range_2)
        self.progress.setValue(value)

    def finished(self):
        """
        Execute when the QThread emits the finished signal.
        """
        if self.progress.maximum() > 0:
            # normally set the maximum value
            self.progress.setValue(self.progress.maximum())
        else:
            # probably no update needed to be performed hence no max value is set (fake it)
            self.progress.setRange(0, 100)
            self.progress.setValue(100)

        self.message.setText('database update completed')
        self.btn_close.show()


class PluginInstallDialog(QDialog):
    """
    This class can be used to initialize the 'install plugin' dialog window.
    """
    archive = None
    layout = None
    message = None
    progress = None
    qthread = None

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
        self.setWindowTitle('Installing plugin')
        self.setFixedSize(500, 140)
        self.setStyleSheet("""
        QDialog {
            background: #F2F2F2;
        }
        """)
        self.progress = BusyProgressBar(self)
        self.progress.start()
        self.message = QLabel('initializing setup', self)
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
        UI update is then handled through signals.
        """
        class PluginInstall(QThread):

            msignal = pyqtSignal(str)

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
                extplugins_dir = b3.getAbsolutePath('@b3/extplugins', True)
                tmp_dir = tempfile.mkdtemp()

                if not os.path.isdir(extplugins_dir):

                    try:
                        LOG.warning('missing %s directory: attempt to create it' % extplugins_dir)
                        os.mkdir(extplugins_dir)
                        with open(os.path.join(extplugins_dir, '__init.__py'), 'w') as f:
                            f.write('#')
                    except Exception, err:
                        LOG.error('could create default extplugins directory: %s', err)
                        self.msignal.emit('ERROR: could not create extplugins directory!')
                        return
                    else:
                        LOG.debug('created directory %s: resuming plugin installation' % extplugins_dir)

                self.msignal.emit('uncompressing plugin archive')
                LOG.debug('uncompressing plugin archive: %s', self.archive)
                sleep(.5)

                try:
                    unzip(self.archive, tmp_dir)
                except Exception, err:
                    LOG.error('could not uncompress plugin archive: %s', err)
                    self.msignal.emit('ERROR: plugin installation failed!')
                    shutil.rmtree(tmp_dir, True)
                else:
                    self.msignal.emit('searching plugin')
                    LOG.debug('searching plugin')
                    sleep(.5)

                    try:
                        name, path, mod, clz = plugin_import(tmp_dir)
                    except ImportError:
                        self.msignal.emit('ERROR: no valid plugin module found!')
                        LOG.warning('no valid plugin module found')
                        shutil.rmtree(tmp_dir, True)
                    else:
                        self.msignal.emit('plugin found: %s...' % name)

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
                                self.msignal.emit('NOTICE: plugin %s is already installed!' % name)
                                LOG.info('plugin %s is already installed' % name)
                                shutil.rmtree(tmp_dir, True)
                                return
                            finally:
                                if x:
                                    x.close()

                        else:

                            self.msignal.emit('NOTICE: %s is built-in plugin!' % name)
                            LOG.info('%s is built-in plugin' % name)
                            shutil.rmtree(tmp_dir, True)
                            return

                        finally:
                            if x:
                                x.close()

                        if clz.requiresConfigFile:
                            self.msignal.emit('searching plugin %s configuration file' % name)
                            LOG.debug('searching plugin %s configuration file', name)
                            sleep(.5)

                            collection = glob.glob('%s%s*%s*' % (os.path.join(path, 'conf'), os.path.sep, name))
                            if len(collection) == 0:
                                self.msignal.emit('ERROR: no configuration file found for plugin %s' % name)
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
                                self.msignal.emit('ERROR: no valid configuration file found for plugin %s' % name)
                                LOG.warning('no valid configuration file found for plugin %s', name)
                                shutil.rmtree(tmp_dir, True)
                                return

                        # move into extplugins folder and remove temp directory
                        shutil.move(path, extplugins_dir)
                        shutil.rmtree(tmp_dir, True)

                        self.msignal.emit('plugin %s installed' % name)
                        LOG.info('plugin %s installed successfully', name)

        self.qthread = PluginInstall(self, self.archive)
        self.qthread.msignal.connect(self.update_message)
        self.qthread.finished.connect(self.finished)
        self.qthread.start()

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


class STDOutDialog(QDialog):
    """
    This class is used to display the 'B3 console output' dialog.
    """
    stdout = None
    lstrip = ['\x0c', 'TERM environment variable not set.\n']

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
        self.setMinimumSize(800, 300)
        self.setStyleSheet("""
        QDialog {
            background: #F2F2F2;
        }
        """)
        self.stdout = STDOutText(self)
        layout = QVBoxLayout(self)
        layout.addWidget(self.stdout)
        layout.setAlignment(Qt.AlignCenter)
        self.setLayout(layout)
        self.setModal(False)
        self.hide()

    @pyqtSlot()
    def read_stdout(self):
        """
        Read STDout and append it to the QTextEdit.
        """
        self.stdout.moveCursor(QTextCursor.End)
        output = str(self.process.readAllStandardOutput())
        for v in self.lstrip:
            if output.startswith(v):
                output = output.lstrip(v)
        self.stdout.insertPlainText(output)


class PreferencesDialog(QDialog):
    """
    This class is used to display the 'Preferences' dialog.
    """
    autoRestartCheckBox = None
    showNewsCheckBox = None
    updateChannel = {UPDATE_CHANNEL_STABLE: None, UPDATE_CHANNEL_BETA: None, UPDATE_CHANNEL_DEV: None}

    def __init__(self, parent=None):
        """
        Initialize the 'License' dialog window.
        :param parent: the parent widget
        """
        QDialog.__init__(self, parent)
        self.initUI()

    def initUI(self):
        """
        Initialize the Dialog layout.
        """
        self.setWindowTitle('Preferences')
        self.setFixedSize(400, 300)
        self.setStyleSheet("""
            QDialog {
                background: #F2F2F2;
            }
            QGroupBox, QCheckBox, QRadioButton {
                background: transparent;
                outline: none;
            }
            QGroupBox::title {
                background-color: transparent;
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 2 4px;
                outline: none;
            }
            QGroupBox {
                margin-top: 20px;
                spacing: 26px;
            }
            QCheckBox::indicator::unchecked, QRadioButton::indicator::unchecked {
                border: 1px solid darkgray;
                border-radius: 0px;
                background-color: #F2F2F2;
                width: 10px;
                height: 10px;
                margin-right: 2px;
            }
            QCheckBox::indicator::checked, QRadioButton::indicator::checked {
                border: 1px solid #777777;
                border-radius: 0px;
                background-color: #777777;
                width: 10px;
                height: 10px;
                margin-right: 2px;
            }
        """)

        def __get_top_layout(parent):
            ## AUTORESTART
            parent.autoRestartCheckBox = QCheckBox('Automatically restart B3 on crash')
            if not main_is_frozen():
                parent.autoRestartCheckBox.setWhatsThis('If enabled, every B3 process will be automatically restarted upon crash.')
                parent.autoRestartCheckBox.setChecked(B3App.Instance().settings.value('auto_restart_on_crash', type=bool))
            else:
                parent.autoRestartCheckBox.setWhatsThis('You need to run B3 from sources if you want this feature enabled.')
                parent.autoRestartCheckBox.setChecked(False)
                parent.autoRestartCheckBox.setEnabled(False)

            ## SHOW NEWS
            parent.showNewsCheckBox = QCheckBox('Show latest news')
            parent.showNewsCheckBox.setWhatsThis('If enabled, will display B3 RSS feed news in the main window.')
            parent.showNewsCheckBox.setChecked(B3App.Instance().settings.value('show_rss_news', type=bool))

            ## UPDATE CHANNEL OPTIONS
            for key in (UPDATE_CHANNEL_STABLE, UPDATE_CHANNEL_BETA, UPDATE_CHANNEL_DEV):
                parent.updateChannel[key] = QRadioButton(key.title())
                parent.updateChannel[key].setWhatsThis('Set the update channel to: %s' % key)
                parent.updateChannel[key].setChecked(B3App.Instance().settings.value('update_channel', type=str) == key)

            ## GENERAL LAYOUT
            generalLayout = QVBoxLayout()
            generalLayout.addWidget(parent.autoRestartCheckBox)
            generalLayout.addWidget(parent.showNewsCheckBox)
            ## GENERAL FIELDSET
            generalGroup = QGroupBox("General", parent)
            generalGroup.setLayout(generalLayout)
            ## UPDATE LAYOUT
            updateLayout = QVBoxLayout()
            updateLayout.addWidget(parent.updateChannel['stable'])
            updateLayout.addWidget(parent.updateChannel['beta'])
            updateLayout.addWidget(parent.updateChannel['dev'])
            ## UPDATE FIELDSET
            updateGroup = QGroupBox("Update channel", parent)
            updateGroup.setLayout(updateLayout)
            ## TOP MAIN LAYOUT
            layout = QVBoxLayout()
            layout.addWidget(generalGroup)
            layout.addWidget(updateGroup)
            return layout

        def __get_bottom_layout(parent):
            btn_close = Button(parent=parent, text='Close')
            btn_close.clicked.connect(parent.close)
            btn_close.setVisible(True)
            btn_save = Button(parent=parent, text='Save')
            btn_save.clicked.connect(parent.save)
            btn_save.setVisible(True)
            layout = QHBoxLayout()
            layout.addWidget(btn_close)
            layout.addWidget(btn_save)
            layout.setAlignment(Qt.AlignRight|Qt.AlignBottom)
            layout.setContentsMargins(0, 30, 0, 0)
            layout.setSpacing(20 if b3.getPlatform() == 'darwin' else 10)
            return layout

        mainLayout = QVBoxLayout()
        mainLayout.addLayout(__get_top_layout(self))
        mainLayout.addLayout(__get_bottom_layout(self))
        self.setLayout(mainLayout)
        self.setModal(True)

    def save(self):
        """
        Save the configuration file.
        """
        B3App.Instance().settings.setValue('auto_restart_on_crash', self.autoRestartCheckBox.isChecked())
        B3App.Instance().settings.setValue('show_rss_news', self.showNewsCheckBox.isChecked())
        for key in self.updateChannel.keys():
            if self.updateChannel[key].isChecked():
                B3App.Instance().settings.setValue('update_channel', key)
                break

        ## FORCE WRITE
        B3App.Instance().settings.sync()

        ## SHOW/HIDE NEWS WIDGET
        self.parent().news.setVisible(B3App.Instance().settings.value('show_rss_news', type=bool))

        self.close()


from b3.gui import B3App, B3_ICON, CONFIG_VALID
from b3.gui.misc import Button, BusyProgressBar, ProgressBar, STDOutText
from b3.gui.widgets import ImageWidget
