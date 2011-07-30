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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
# CHANGELOG:
# 17/11/2009 - 1.4.0 - Courgette
#    * add an option to create an instance of the logger that will write to 
#      stderr instead
# 22/10/2010 - 1.5.0 - xlr8or
#    * add an option to write to both logfile and stderr 
# 08/04/2011 - 1.6.0 - Courgette
#    * make the console logger write to stdout and repeat errors on 
#      stderr
# 20/04/2011 - 1.6.1 - Courgette
#    * should get rid of UnicodeDecodeError
# 20/04/2011 - 1.6.2 - Courgette
#    * again getting rid of UnicodeDecodeError
#
__author__  = 'ThorN'
__version__ = '1.6.2'

import sys
import logging
from logging import handlers

CONSOLE = 22
BOT = 21
VERBOSE = 9
VERBOSE2 = 8

logging.addLevelName(CONSOLE, 'CONSOLE')
logging.addLevelName(BOT, 'BOT    ')
logging.addLevelName(VERBOSE, 'VERBOSE')
logging.addLevelName(VERBOSE2, 'VERBOS2')

# this has to be done to prevent callstack checking in the logging
# has been causing problems with threaded applications logging
logging._srcfile = None

#--------------------------------------------------------------------------------------------------
class OutputHandler(logging.Logger):
    def __init__(self, name, level=logging.NOTSET):
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
        Log 'msg % args' with severity 'ERROR'. And raises
        the exception.
        """
        self.log(logging.ERROR, msg, *args, **kwargs) 
        raise raiseError, msg % args

class stdoutLogger:
    def __init__(self, logger):
        self.logger = logger

    def write(self, msg):
        self.logger.info('STDOUT %r' % msg)
        
class stderrLogger:
    def __init__(self, logger):
        self.logger = logger

    def write(self, msg):
        self.logger.error('STDERR %r' % msg)

#--------------------------------------------------------------------------------------------------
logging.setLoggerClass(OutputHandler)



#handler = logging.StreamHandler(sys.stdout)

#handler = handlers.RotatingFileHandler(__main__.cp.config.get('b3', 'logfile'), 'a', 10485760, 5)
#handler.setFormatter(logging.Formatter('%(asctime)s\t%(levelname)s\t%(message)s', '%y%m%d %H:%I:%S'))
#output.addHandler(handler)
#output.setLevel(__main__.cp.config.get('b3', 'log_level'))

__output = None

def getInstance(logfile='b3.log', loglevel=21, log2console=False):
    """NOTE: log2console is mostly useful for developers. This will make the bot
    log everything to stderr additionally of into the usual logfile.
    """
    global __output

    if __output == None:
        __output = logging.getLogger('output')

        handler = handlers.RotatingFileHandler(logfile, 'a', 10485760, 5, encoding="UTF-8")
        handler.doRollover()
        handler.setFormatter(logging.Formatter('%(asctime)s\t%(levelname)s\t%(message)r', '%y%m%d %H:%M:%S'))
        __output.addHandler(handler)
        
        if log2console:
            consoleFormatter = logging.Formatter('%(asctime)s\t%(levelname)s\t%(message)r', '%M:%S')
            handler2 = logging.StreamHandler(sys.stdout)
            handler2.setFormatter(consoleFormatter)
            __output.addHandler(handler2)
            handlerError = logging.StreamHandler(sys.stderr)
            handlerError.setFormatter(consoleFormatter)
            handlerError.setLevel(logging.ERROR)
            __output.addHandler(handlerError)
           
        __output.setLevel(loglevel)
    return __output

if __name__ == '__main__':
    # test output handler
    log = getInstance('test.log', 1, True)
    log.error('Test error')
    log.debug('Test debug')
    log.console('Test console')
    log.bot('Test bot')
    log.verbose('Test verbose')
    log.verbose2('Test verbose')
    log.warning('Test warning')
    log.info('Test info')

    try:
        raise Exception('error test')
    except:
        log.exception('Test exception')
        log.error('Test error with exc_info',  exc_info=True)
        
    try:
        log.raiseError(Exception, 'Test raiseError')
    except Exception, e:
        # expected behavior
        log.debug('Got expected Exception %s', e)
    else:
        # unexpected behavior
        raise Exception('raiseError should have raised an exception')

    # critical will exit
    log.critical('Test info')
    raise Exception('log.critical should have exited')
    