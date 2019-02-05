# -*- coding: utf-8 -*-

# ################################################################### #
#                                                                     #
#  BigBrotherBot (B3) (www.bigbrotherbot.net)                         #
#  Copyright (C) 2018 Daniele Pantaleone <danielepantaleone@me.com>   #
#                                                                     #
#  This program is free software; you can redistribute it and/or      #
#  modify it under the terms of the GNU General Public License        #
#  as published by the Free Software Foundation; either version 2     #
#  of the License, or (at your option) any later version.             #
#                                                                     #
#  This program is distributed in the hope that it will be useful,    #
#  but WITHOUT ANY WARRANTY; without even the implied warranty of     #
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the       #
#  GNU General Public License for more details.                       #
#                                                                     #
#  You should have received a copy of the GNU General Public License  #
#  along with this program; if not, write to the Free Software        #
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA      #
#  02110-1301, USA.                                                   #
#                                                                     #
# ################################################################### #


import sys
import logging

from logging import handlers
from logging import CRITICAL, ERROR, WARNING, INFO, DEBUG


VERBOSE = 9


logging.addLevelName(CRITICAL, 'CRITICAL')
logging.addLevelName(ERROR,    'ERROR   ')
logging.addLevelName(INFO,     'INFO    ')
logging.addLevelName(WARNING,  'WARNING ')
logging.addLevelName(DEBUG,    'DEBUG   ')
logging.addLevelName(VERBOSE,  'VERBOSE ')


class OutputHandler(logging.Logger):
    """Custom logging output handler class"""

    def verbose(self, msg:str, *args, **kwargs):
        """Log 'msg % args' with severity VERBOSE"""
        self.log(VERBOSE, msg, *args, **kwargs)


class STDOutLogger(object):
    """A class to redirect STDOut messages to the logger"""

    def __init__(self, logger):
        self.logger = logger

    def write(self, msg:str):
        """Write a message in the logger with severity INFO"""
        self.logger.info('STDOUT %r' % msg)


class STDErrLogger(object):
    """A class to redirect STDErr messages to the logger"""

    def __init__(self, logger):
        self.logger = logger

    def write(self, msg:str):
        """Write a message in the logger with severity ERROR"""
        self.logger.error('STDERR %r' % msg)


logging.setLoggerClass(OutputHandler)


__output = None


def getLogger(name:str='b3.log', level:int=WARNING, size:int=10485760, console=False):
    """Returns an instance of the logger"""
    global __output

    if __output is None:

        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s', '%Y/%m/%d %H:%M:%S')

        # FILE HANDLER
        handler = logging.handlers.RotatingFileHandler(name, maxBytes=size, backupCount=10, encoding="UTF-8")
        handler.doRollover()
        handler.setFormatter(formatter)
        logger = logging.getLogger('output')
        logger.addHandler(handler)
        logger.setLevel(level)

        # CONSOLE HANDLER
        if console:
            stdout = logging.StreamHandler(sys.stdout)
            stdout.setFormatter(formatter)
            stderr = logging.StreamHandler(sys.stderr)
            stderr.setFormatter(formatter)
            stderr.setLevel(logging.ERROR)
            logger.addHandler(stdout)
            logger.addHandler(stderr)

        __output = logger

    return __output


class LoggerMixin(object):
    """Mixin implementation to feature logging capabilities"""

    def __init__(self, *args, **kwargs):
        self.logger = getLogger()

    def critical(self, msg, *args, **kwargs):
        """Log a CRITICAL message and exit"""
        self.logger.critical(msg, *args, **kwargs)
        raise SystemExit(220)

    def debug(self, msg:str, *args, **kwargs):
        """Log a DEBUG message"""
        self.logger.debug(msg, *args, **kwargs)

    def error(self, msg:str, *args, **kwargs):
        """Log a ERROR message"""
        self.logger.error(msg, *args, **kwargs)

    def exception(self, msg:str, *args, exc_info=True, **kwargs):
        """Log a ERROR message"""
        self.logger.exception(msg, *args, exc_info, **kwargs)

    def info(self, msg:str, *args, **kwargs):
        """Log a INFO message"""
        self.logger.info(msg, *args, **kwargs)

    def verbose(self, msg:str, *args, **kwargs):
        """Log a VERBOSE message"""
        self.logger.verbose(msg, *args, **kwargs)

    def warning(self, msg:str, *args, **kwargs):
        """Log a WARNING message"""
        self.logger.warning(msg, *args, **kwargs)