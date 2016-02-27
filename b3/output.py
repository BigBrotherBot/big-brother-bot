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
# 17/11/2009 - 1.4.0 - Courgette - add an option to create an instance of the logger that will write to stderr instead
# 22/10/2010 - 1.5.0 - xlr8or    - add an option to write to both logfile and stderr
# 08/04/2011 - 1.6.0 - Courgette - make the console logger write to stdout and repeat errors on stderr
# 20/04/2011 - 1.6.1 - Courgette - should get rid of UnicodeDecodeError
# 20/04/2011 - 1.6.2 - Courgette - again getting rid of UnicodeDecodeError
# 21/07/2014 - 1.7   - Fenix     - syntax cleanup
# 04/02/2015 - 1.7.1 - Fenix     - getInstance() now accepts an optional 'logsize' parameter (amount of bytes of the log file)
# 04/07/2015 - 1.7.2 - Fenix     - changed log formatter to keep the same width for log levels

__author__  = 'ThorN'
__version__ = '1.7.2'

import sys
import logging

from logging import handlers
from logging import CRITICAL, ERROR, INFO, WARNING, DEBUG

CONSOLE = 22
BOT = 21
VERBOSE = 9
VERBOSE2 = 8

logging.addLevelName(CRITICAL, 'CRITICAL')
logging.addLevelName(ERROR,    'ERROR   ')
logging.addLevelName(INFO,     'INFO    ')
logging.addLevelName(WARNING,  'WARNING ')
logging.addLevelName(DEBUG,    'DEBUG   ')
logging.addLevelName(CONSOLE,  'CONSOLE ')
logging.addLevelName(BOT,      'BOT     ')
logging.addLevelName(VERBOSE,  'VERBOSE ')
logging.addLevelName(VERBOSE2, 'VERBOS2 ')

# this has to be done to prevent callstack checking in the logging
# has been causing problems with threaded applications logging
logging._srcfile = None

# logger object instance
__output = None


class OutputHandler(logging.Logger):

    def __init__(self, name, level=logging.NOTSET):
        """
        Object constructor.
        :param name: The logger name
        :param level: The default logging level
        """
        logging.Logger.__init__(self, name, level)

    def critical(self, msg, *args, **kwargs):
        """
        Log 'msg % args' with severity 'CRITICAL' and exit.
        """
        kwargs['exc_info'] = True
        logging.Logger.critical(self, msg, *args, **kwargs)
        sys.exit(220)

    def console(self, msg, *args, **kwargs):
        """
        Log 'msg % args' with severity 'CONSOLE'.
        """
        self.log(CONSOLE, msg, *args, **kwargs) 

    def bot(self, msg, *args, **kwargs):
        """
        Log 'msg % args' with severity 'BOT'.
        """
        self.log(BOT, msg, *args, **kwargs) 

    def verbose(self, msg, *args, **kwargs):
        """
        Log 'msg % args' with severity 'VERBOSE'.
        """
        self.log(VERBOSE, msg, *args, **kwargs) 

    def verbose2(self, msg, *args, **kwargs):
        """
        Log 'msg % args' with severity 'VERBOSE2'.
        """
        self.log(VERBOSE2, msg, *args, **kwargs) 

    def raiseError(self, raiseError, msg, *args, **kwargs):
        """
        Log 'msg % args' with severity 'ERROR'.
        And raises the exception.
        """
        self.log(logging.ERROR, msg, *args, **kwargs) 
        raise raiseError, msg % args


class STDOutLogger:
    """
    A class to redirect STDOut messages to the logger.
    """
    def __init__(self, logger):
        """
        Object constructor.
        :param logger: The logger object instance
        """
        self.logger = logger

    def write(self, msg):
        """
        Write a message in the logger with severity 'INFO'
        :param msg: The message to write
        """
        self.logger.info('STDOUT %r' % msg)


class STDErrLogger:
    """
    A class to redirect STDErr messages to the logger.
    """
    def __init__(self, logger):
        """
        Object constructor.
        :param logger: The logger object instance
        """
        self.logger = logger

    def write(self, msg):
        """
        Write a message in the logger with severity 'ERROR'
        :param msg: The message to write
        """
        self.logger.error('STDERR %r' % msg)


logging.setLoggerClass(OutputHandler)


def getInstance(logfile='b3.log', loglevel=21, logsize=10485760, log2console=False):
    """
    Return a Logger instance.
    :param logfile: The logfile name.
    :param loglevel: The logging level.
    :param logsize: The size of the log file (in bytes)
    :param log2console: Whether or not to extend logging to the console.
    """
    global __output

    if __output is None:

        __output = logging.getLogger('output')

        # FILE HANDLER
        file_formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)r', '%y%m%d %H:%M:%S')
        handler = handlers.RotatingFileHandler(logfile, maxBytes=logsize, backupCount=5, encoding="UTF-8")
        handler.doRollover()
        handler.setFormatter(file_formatter)

        __output.addHandler(handler)

        if log2console:
            # CONSOLE HANDLER
            console_formatter = logging.Formatter('%(asctime)s\t%(levelname)s\t%(message)r', '%M:%S')
            handler2 = logging.StreamHandler(sys.stdout)
            handler2.setFormatter(console_formatter)

            __output.addHandler(handler2)

            handler_error = logging.StreamHandler(sys.stderr)
            handler_error.setFormatter(console_formatter)
            handler_error.setLevel(logging.ERROR)

            __output.addHandler(handler_error)

        __output.setLevel(loglevel)

    return __output