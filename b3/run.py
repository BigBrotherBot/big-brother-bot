#
# BigBrotherBot(B3) (www.bigbrotherbot.com)
# Copyright (C) 2005 Michael "ThorN" Thornton
# 
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
# $Id: b3_run.py 6 2005-11-18 05:36:17Z thorn $

__author__  = 'ThorN'
__version__ = '1.1.1'

import b3, sys, os, time
from optparse import OptionParser
import pkg_handler
modulePath = pkg_handler.resource_directory(__name__)

def run_autorestart(args=None):
	script = os.path.join(modulePath, 'run.py')
	if os.path.isfile(script + 'c'):
		script += 'c'

	if args:
		script = '%s %s %s' % (sys.executable, script, ' '.join(args))
	else:
		script = '%s %s' % (sys.executable, script)

	while True:
		try:
			print 'Running in auto-restart mode...'

			status = os.system(script)

			print 'Exited with status %s' % status

			if status == 221:
				# restart
				print 'Restart requested...'
			elif status == 222:
				# stop
				print 'Shutdown requested.'
				break
			elif status == 220:
				# stop
				print 'B3 Error, check log file.'
				break
			elif status == 223:
				# stop
				print 'B3 Error Restart, check log file.'
				break
			elif status == 224:
				# stop
				print 'B3 Error, check console.'
				break
			elif status == 256:
				# stop
				print 'Python error, stopping, check log file.'
				break
			elif status == 0:
				# stop
				print 'Normal shutdown, stopping.'
				break
			elif status == 1:
				# stop
				print 'Error, stopping, check console.'
				break
			else:
				print 'Unknown shutdown status (%s), restarting...' % status
		
			time.sleep(5)
		except KeyboardInterrupt:
			print 'Quit'
			break

def run(config=None):
	if config:
		config = b3.getAbsolutePath(config)
	else:
		# search for the config file
		config = None
		for p in ('b3.xml', 'conf/b3.xml', 'b3/conf/b3.xml', '~/b3.xml', '~/conf/b3.xml', '~/b3/conf/b3.xml', '@b3/conf/b3.xml'):
			path = b3.getAbsolutePath(p)
			print 'Searching for config file: %s' % path
			if os.path.isfile(path):
				config = path
				break

	if not config:
		raise SystemExit('Could not find config file.')

	b3.start(config)

def main():
	parser = OptionParser(version=b3.sversion)
	parser.add_option('-c', '--config', dest='config', default=None,
					  help='B3 config file. Example: -c b3.xml')
	parser.add_option('-r', '--restart',
					  action='store_true', dest='restart', default=False,
					  help='Auto-restart B3 on crash')

	(options, args) = parser.parse_args()

	if not options.config and len(args) == 1:
		options.config = args[0]

	if options.restart:
		if options.config:
			run_autorestart(['--config', options.config] + args)
		else:
			run_autorestart([])
	else:
		run(config=options.config)
	
if __name__ == '__main__':
	main()