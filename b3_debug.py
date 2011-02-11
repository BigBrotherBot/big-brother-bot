#!/usr/bin/env python
#
# BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2010 GrosBedo
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
# CHANGELOG:
# 2010-10-02 - v0.7 - Courgette
#   * separated b3_run.py from b3_debug.py. To use the debug stuff, start B3 
#     using python b3_debug.py instead of python b3_run.py
# 2010-09-17 - v0.6.1 - GrosBedo
#   * fixed import bug
# 2010-09-16 - v0.6 - GrosBedo
#   * fixed function profiler, it now works with threads
# 2010-09-16 - v0.5.5 - GrosBedo
#   * fixed a few more bugs with diagnostic mode
# 2010-09-16 - v0.5.4 - GrosBedo
#   * fixed some bugs with diagnostic mode and removed one list (smaller memory footprint)
# 2010-09-15 - v0.5.3 - GrosBedo
#   * added --diagload to load human readable stats files and merge the results
# 2010-09-15 - v0.5.2 - GrosBedo
#   * fixed a few bugs again in log diagnostic mode
# 2010-09-14 - v0.5.1 - GrosBedo
#   * fixed a few bugs in log diagnostic mode
# 2010-09-13 - v0.5 - GrosBedo
#   * reworked the diagnostic switchs, now can save a raw merged matrix from loaded raw matrix and should be more efficient at memory management
# 2010-09-09 - v0.4.2 - GrosBedo
#   * more memory efficient when loading huge datas matrixes
# 2010-09-09 - v0.4.1 - GrosBedo
#   * fixed some bugs when loading several files at once
# 2010-09-09 - v0.4 - GrosBedo
#    * added diagnostic tool switchs
# 2010-09-08 - v0.3 - GrosBedo
#    * added the debug subparser
#    * does not conflict with standard b3 switchs anymore (--help show the b3 help)
# 2010-09-07 - v0.2 - GrosBedo
#    * added the special debug switchs, like debug, profile save and load.
# 2010-09-06 - v0.1 - GrosBedo
#    * Initial version.

# This section is DoxuGen information. More information on how to comment your code
# is available at http://wiki.bigbrotherbot.net/doku.php/customize:doxygen_rules
## @file
# Run B3 in developer debug mode (for developers)

__author__  = 'GrosBedo'
__version__ = '0.7'

import time, sys, os
import b3.run

pathname = os.path.dirname(sys.argv[0])
sys.path.append(os.path.join(pathname, 'b3','lib')) # we add the b3/lib path for the import to work for some complex libraries (like guppy)
sys.path.append(os.path.join(pathname, 'b3','tools'))

from b3_run import *
import argparse
from functionprofiler import *
from logdiagnostic import *
from memoryprofiler import *
#from datetime import datetime
import pprint, timeit

def parse_cmdline_args():
        # Initializing variables
        #currdateprofile = os.path.join(pathname, '%s.profile' % str(datetime.now().strftime("%Y-%m-%d_%H-%M-%S")))
        cancontinue = True # define if b3 can continue to run normally or not

        # Initializing the arguments parser
        parser = argparse.ArgumentParser(conflict_handler='resolve', add_help=False, usage='%(prog)s [debugoptions]', description='B3 DEBUG MODE: Switch to some special debug functionnalities.', epilog='Note: for the profile to be saved, you need to wait the end of the runtime that the profile ends by itself (do not close b3 !)')
        #parser.add_argument('--help', '-h', dest='help', action='store_true', default=False, help='show this help message and exit')
        parser.add_argument('--debughelp', '-debughelp', '--debug', '-debug', dest='debughelp', action='store_true', default=False, help='show this help message and exit')
        parser.add_argument('--memory', '-m', dest='memory', action='store_true', default=False, help='activate the memory monitor')
        parser.add_argument('--memorysave', '-msave', dest='memorysave', action='store', default=None, type=str, metavar='/dir/memory.profile', help='store the memory profile to the specified file')
        parser.add_argument('--memoryload', '-mload', dest='memoryload', action='store', default=None, type=str, metavar='/dir/memory.profile', help='load a memory profile from the specified file')
        parser.add_argument('--memorydraw', '-mdraw', dest='memorydraw', action='store_true', default=False, help='draw an interactive GUI chart for the loaded memory profile')
        parser.add_argument('--memoryinteractive', '-mi', dest='memoryinteractive', action='store_true', default=False, help='draw an interactive console terminal _while_ the application is running')
        parser.add_argument('--profile', '-p', dest='profile', action='store_true', default=False, help='activate the functions profiler')
        parser.add_argument('--profilesave', '-psave', dest='profilesave', action='store', default=None, type=str, metavar='/dir/some.profile', help='store the generated profile to the specified file')
        parser.add_argument('--profileload', '-pload', dest='profileload', action='store', default=None, type=str, metavar='/dir/some.profile', help='load a profile from the specified file')
        parser.add_argument('--profiledraw', '-pdraw', dest='profiledraw', action='store_true', default=False, help='draw an interactive GUI chart for the loaded profile')
        parser.add_argument('--profiledrawnogui', '-pdraw2', dest='profiledrawnogui', action='store_true', default=False, help='draw an interactive console interface to analyze the loaded profile')
        parser.add_argument('--profilesavestats', '-pstats', dest='profilesavestats', action='store', default=None, type=str, metavar='/dir/somefile.txt', help='parse and save some stats from the loaded profile')
        parser.add_argument('--profileruntime', '-ptime', dest='profileruntime', action='store', default=60, type=float, metavar='seconds', help='time to run the profile test (the program will be stopped after)')
        parser.add_argument('--diagnostic', '-diag', dest='diagnostic', action='store_true', default=False, help='activate the log diagnostic tool')
        parser.add_argument('--diaglog', '-dlog', dest='diaglog', action='store', nargs='+', default=None, type=str, metavar='games_mp.log', help='load and analyze one or several log files, generating stats per second')
        parser.add_argument('--diagzerocount', '-d0', dest='diagzerocount', action='store_true', default=False, help='Zero is significant (count missing lines)')
        parser.add_argument('--diagsave', '-dsave', dest='diagsave', action='store', default=None, type=str, metavar='stats.txt', help='store stats per second to the specified file, in a readable human format (YAML)')
        parser.add_argument('--diagload', '-dload', dest='diagload', action='store', nargs='+', default=None, type=str, metavar='stats.txt', help='load stats in YAML format resulting from a previous diagnostic and weight-merge the stats (much more approximate than rawload !)')
        parser.add_argument('--diagstatssave', '-dssave', dest='diagstatssave', action='store', default=None, type=str, metavar='statsdata.txt', help='(deprecated, see --diagsave) store computer readable stats to the specified file (for later processing)')
        parser.add_argument('--diagstatsload', '-dsload', dest='diagstatsload', action='store', nargs='+', default=None, type=str, metavar='statsdata.txt', help='(deprecated, see --diagload) load stats resulting from a previous diagnostic and weight-merge the stats (much more approximate than rawload !)')
        parser.add_argument('--diagrawsave', '-drsave', dest='diagrawsave', action='store', default=None, type=str, metavar='rawdata.txt', help='store the raw datas matrix from the log(s) for later processing')
        parser.add_argument('--diagrawload', '-drload', dest='diagrawload', action='store', nargs='+', default=None, type=str, metavar='rawdata.txt', help='load the raw datas and merge them')
        parser.add_argument('--diagmergeonly', '-dmerge', dest='diagmergeonly', action='store_true', default=None, help='only save one, merged result from all the gathered stats')
        parser.add_argument('--debugverbose', '-dv', dest='verbose', action='store_true', help='verbose option, output more informations on screen')

        # Parsing (loading) the arguments
        try:
            args, extras = parser.parse_known_args() # We parse only the special commandlines parameter here, for the rest, the normal switchs, we give them up to the rest of B3 functions (namely the main() in b3/run.py). The recognized args are stored in args var, for the rest it's stored in extras var
            extras.insert(0, sys.argv[0]) # add the path to this script file (to normalize the arguments)
            sys.argv = extras # trim out the debug vars we will process here, so that b3 can parse the arguments normally
        except BaseException, e:
            print('Exception: %s' % str(e))
            pass	

        #pprint.pprint(args)

        # Processing the arguments
        if args.debughelp: # debug help message
            parser.print_help()
            return False

        # Profiling functionnalities
        if args.memory:
                print('MEMORY PROFILER MODE\n--------------------\n')
                if args.memorysave:
                        runmemoryprofile(args.memorysave)
                if args.memoryload:
                        if args.memorydraw:
                                memorygui(args.memoryload)
                if args.memoryinteractive:
                        memoryinteractive()
                cancontinue = False

        # Profiling functionnalities
        if args.profile:
            print('FUNCTIONS PROFILER MODE\n--------------------\n')
            if args.profilesave:
                runprofile("""main()""", args.profilesave, args.profileruntime)
            if args.profileload:
                if args.profiledraw:
                    browseprofilegui(args.profileload)
                if args.profilesavestats:
                    parseprofile(args.profileload, args.profilesavestats)
                if args.profiledrawnogui:
                    browseprofile(args.profileload)
                #if cancontinue is not False:
                #    print('Profile loaded but no action specified ! Type --debughelp for more infos')
            cancontinue = False

        # Log Diagnostic functionnalities
        if args.diagnostic:
            print('LOG DIAGNOSTIC MODE\n--------------------\n')
            diag = LogDiagnostic()
            if args.diagzerocount:
                diag.significantzero = True
            else:
                diag.significantzero = False
            supermatrix = []
            superstats = []
            loadmatrix = []
            prestats = []
            # Processing the logs in input
            if args.diaglog:
                print('Analyzing the log(s) %s' % (' - '.join(args.diaglog)))
                supermatrix.extend(diag.lines_per_second(*args.diaglog))
                print('Analyze completed.')
            # Loading some previous results' matrix
            if args.diagrawload:
                print('Loading raw data results from %s. This can take some time, please be patient...' % (' - '.join(args.diagrawload)))
                loadmatrix.extend(diag.load_data(True, *args.diagrawload))
            # Merge the matrix first
            if len(supermatrix) > 1:
                print('Merging the raw data...')
                #mergedmatrix = diag.merge_matrix( *supermatrix)
                for matrix in supermatrix:
                        loadmatrix.extend(matrix[1])
                print('Raw data merge completed.')

            # Save the raw datas matrix(es)
            if args.diagrawsave:
                print('Saving the raw data to %s' % args.diagrawsave)
                if len(loadmatrix) > 0:
                        diag.save_data(args.diagrawsave, *loadmatrix)
                else:
                        diag.save_data(args.diagrawsave, *supermatrix)

            # Stats Generation
            # Input logs stats generation (to show in the final summary digest)
            if args.diaglog:
                print('Generating stats per second from logs...')
                superstats = diag.stats_per_second(*supermatrix)
                del supermatrix
                print('Generation completed.')
            # Raw merged stats generation
            if len(loadmatrix) > 0:
                print('Generating merged stats from raw data...')
                prestats = [diag.stats_per_second( ('raw merged logs', loadmatrix) )[0][1]] # we keep only the stats here, we trim the generated log name because we don't need it for the calculation of the weighted mean
                del loadmatrix
                print('Generation completed.')
            else:
                prestats.extend(superstats)

            # Loading some previous results' stats
            if args.diagstatsload:
                print('Loading previous stats results from %s' % (' - '.join(args.diagstatsload)))
                prestats.extend( (diag.load_data(False, statsfile)[0][0][1] for statsfile in args.diagstatsload ) )
            # Loading some previous results' stats in YAML
            if args.diagload:
                print('Loading previous stats results from %s' % (' - '.join(args.diagload)))
                prestats.extend( diag.load_data_yaml(*args.diagload) )
            # Merge then all the stats (only if there is an additional stats to merge after the matrix merge !)
            if args.diagload or args.diagstatsload:
                print('Merging the stats with a weighted mean algorithm...')
                mergedstats = diag.weighted_mean_merge( *prestats )
                print('Merging of stats completed.')
            else:
                mergedstats = [('raw merged logs', prestats[0])]
            del prestats

            # Save the stats in computer readable format
            if args.diagstatssave:
                if args.diagmergeonly: # Save only the merged result if specified by the user
                    print('Saving the final, merged stats to %s' % args.diagstatssave)
                    diag.save_data(args.diagstatssave, *mergedstats)
                else:
                    print('Saving all the stats + merged to %s' % args.diagstatssave)
                    superstats.extend(mergedstats)
                    diag.save_data(args.diagstatssave, *superstats)
            # Save the stats in human readable format
            if args.diagsave:
                if args.diagmergeonly: # Save only the merged result if specified by the user
                    print('Saving the stats digest to %s' % args.diagsave)
                    diag.save_data_yaml(args.diagsave, *mergedstats)
                else:
                    print('Saving the full stats digest (all the stats + merged) to %s' % args.diagsave)
                    superstats.extend(mergedstats)
                    diag.save_data_yaml(args.diagsave, *superstats)
            # Show the stats results on screen, in the console
            else:
                if args.diagmergeonly: # Save only the merged result if specified by the user
                    diag.show_results(None, *mergedstats)
                else:
                    superstats.extend(mergedstats)
                    diag.show_results(None, *superstats)
            del superstats
            del mergedstats
            
            print('Everything is done. Exiting.')
            cancontinue = False

        return cancontinue




def main():
    b3.run.main()

if __name__ == '__main__':
    result = parse_cmdline_args() # we parse here for special debug switchs, if there are none, the program will continue normally
    if result: # result will be False if we launched the profiler, or any function that should activate a special behaviour that could conflict with the normal main function
        main()
    