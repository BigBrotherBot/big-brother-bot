'''
kthread.py: A killable thread implementation.

Copyright (C) 2004 Connelly Barnes (connellybarnes@yahoo.com)

This module allows you to kill threads. The class KThread is a drop-in 
replacement for threading.Thread. It adds the kill() method, which should stop 
most threads in their tracks.

This library is free software; you can redistribute it and/or modify it under 
the terms of the GNU Lesser General Public License as published by the Free 
Software Foundation; either version 2.1 of the License, or (at your option) 
any later version.

This library is distributed in the hope that it will be useful, but WITHOUT 
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS 
FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more 
details.

You should have received a copy of the GNU Lesser General Public License along 
with this library; if not, write to the Free Software Foundation, Inc., 59 
Temple Place, Suite 330, Boston, MA 02111-1307 USA 
'''

__first__ = '2004.9.9'
__last__ = '2004.10.29'

import sys
import trace
import threading
import time

class KThreadError(Exception):
    '''Encapsulates KThread exceptions.'''
    pass

class KThread(threading.Thread):
  """A subclass of threading.Thread, with a kill() method."""
  def __init__(self, *args, **keywords):
    threading.Thread.__init__(self, *args, **keywords)
    self.killed = False

  def start(self):
    """Start the thread."""
    self.__run_backup = self.run
    self.run = self.__run      # Force the Thread to install our trace.
    threading.Thread.start(self)

  def __run(self):
    """Hacked run function, which installs the trace."""
    sys.settrace(self.globaltrace)
    self.__run_backup()
    self.run = self.__run_backup

  def globaltrace(self, frame, why, arg):
    if why == 'call':
      return self.localtrace
    else:
      return None

  def localtrace(self, frame, why, arg):
    if self.killed:
      if why == 'line':
        raise SystemExit()
    return self.localtrace

  def kill(self):
    self.killed = True

if __name__ == '__main__':
    
    def func():
        print('Function started')
        for i in xrange(1000000):
            pass
        print('Function finished')

    A = KThread(target=func)
    A.start()
    for i in xrange(1000):
      pass
    A.kill()

    print('End of main program')
