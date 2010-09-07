#
# BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2010 GrosBedo
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
# TODO:
# to optimize the runtime, we could go for numpy, but this would add a dependancy.
# Here is a quick comparison of runtimes :
# length | numpy | pure python
#   1            11.7      0.698
#   10          11.7      2.94
#   100        12.1      24.4
#   1000      15         224
#   10000    41         2170
#   100000  301       22200
# found at http://www.gossamer-threads.com/lists/python/dev/704781
#
# CHANGELOG:
# 2010-09-07 - 0.4 - GrosBedo
#    * added a facility to save and load stats and matrix
# 2010-09-07 - 0.3 - GrosBedo
#    * added weighted_mean and merge_matrix to merge the stats of several logs at once
# 2010-09-06 - 0.2 - GrosBedo
#     Initial release.
#
 
__version__ = '0.3'
__author__ = 'GrosBedo'
 
import os.path
import time
import re
import sys
import math
import pprint
import mstats
import itertools
import pickle

#--------------------------------------------------------------------------------------------------
class DiagPlugin():

    _lineFormat = r'^\s*(?P<minutes>[0-9]+):(?P<seconds>[0-9]+)\s*.*'
    
    maxlines = 0
    significantzero = True
    debug = False
    faster = True # space more some outputs like the percentage of completion in lines_per_second, this speeds up the process a lot
    morefaster = False # disable any feedback output, this is the fastest, but you won't see the process progression at all

    def lines_per_second(self, *args):
        self.supermatrix = []
        for game_log in args:
            matrix = [] # we will store the count of each lines in this matrix
            previoustime = None # this var will permit us to know what to do and fill the gaps in the matrix
            f = re.compile(self._lineFormat, re.IGNORECASE)
            previouscursor = 0 # keeps track of the current positionning in the file (useless technically, only used for user's feedback)
            try:
                # Opening the game file
                self.file = open(game_log, 'r')
                self.file.seek(0, os.SEEK_SET)

                i = 0
                for line in self.file:
                    i += 1
                    m = re.match(f, line)
                    if m:
                        gametime = int(m.group('seconds')) + (int(m.group('minutes')) * 60) # game time at the time this line was outputted
                        if self.debug: print('%i- gametime %s %s:%s' % (i, str(gametime), str(m.group('minutes')), str(m.group('seconds'))))
                        if previoustime is None:
                            matrix.append(1)
                        elif gametime == previoustime:
                            matrix[-1] += 1 # adding 1 count to the last item in the array
                        else:
                            if gametime > previoustime + 1: # if the gametime is more than one second ahead, then we see if we either add the missing zero values (for missing lines), or if we just skip them and only count existing lines
                                if self.significantzero: # if we think that zero values _are_ significant (time for which the server have outputted no line), then we fill in the array the missing values
                                    matrix.extend( [0 for j in range(previoustime, gametime - 1)] )
                                matrix.append(1) # we then append a count for the current line
                            else: # else, if the gametime is just one second ahead OR if the gametime is lower than the previoustime (at the end of a match, the server gametime may come back to 0), we just append a new value of 1
                                matrix.append(1)
                        #elif gametime < self.previoustime: # at the end of a match, the game server time may come back to 0, we just continue as our math algo don't care as long as these were generated after
                        #    matrix.append(1)

                        previoustime = gametime
                    if i >= self.maxlines and self.maxlines > 0: # to avoid infinite loops, you can specify a max number of lines to process
                        print('Reached maxlines, breaking...')
                        break
                    # Feedback the current status of the process
                    filestats = os.fstat(self.file.fileno())
                    currpos = self.file.tell() # we store the current cursor position and filesize to avoid accessing several times the same file at once
                    filesize = filestats.st_size
                    if previouscursor != currpos:
                        if self.faster:
                            if (i % 1000) == 0: print('Processing %s%% (byte %s of %s)...' % (str(currpos*100/filesize), str(currpos), str(filesize)))
                        elif not self.morefaster:
                            print('Processing %s%% (byte %s of %s)...' % (str(currpos*100/filesize), str(currpos), str(filesize)))
                        previouscursor = currpos
                    # Sleep cycle to avoid freezing the system
                    time.sleep(0.0001)

                self.file.close()
                if self.debug: pprint.pprint(matrix)
                self.supermatrix.append( (game_log, matrix) )
            except Exception, e:
                print('Exception when reading the logs per second: '+str(e))

        return self.supermatrix
    
    def load_stats(self, *args):
        print('hihi')
    def save_stats(self, savelocation):
        print('hihi')
        
    def stats_per_second(self, *args):
        superstats = []
        for game_log, matrix in args:
            stats = {}
            mode = self.mode(matrix)
            stats['mode'] = mode[0][0]
            stats['modenext'] = mode[1][0]
            stats['mean'] = mstats.mean(matrix)
            stats['median'] = mstats.median(matrix)
            #stats['harmonicmean'] = mstats.harmonicmean(matrix)
            stats['variance'] = mstats.var(matrix)
            stats['stddeviation'] = math.sqrt(stats['variance'])
            stats['3sigma'] = 3*stats['stddeviation']
            stats['cumfreq'] = mstats.cumfreq(matrix)
            stats['min'] = min(matrix)
            stats['max'] = max(matrix)
            stats['samplespace'] = stats['max'] - stats['min']
            stats['count'] = len(matrix)
            stats['kurtosis'] = mstats.kurtosis(matrix)
            stats['skew'] = mstats.skew(matrix) # if positive, there are more smaller than higher values from the mean. If negative, there are more higher than smaller values from the mean.
            if stats['skew'] > 0:
                stats['skewmeaning'] = 'There exist more smaller values from the mean than higher'
            else:
                stats['skewmeaning'] = 'There exist more higher values from the mean than smaller'
            superstats.append( (game_log, stats) )
        return superstats

    def show_results(self, *args):
        try:
            for game_log, stats in args:
                print('\n-------------------------')
                print('\nStats per second of the log file %s:\n' % game_log)
                print('Zero is significant (count missing lines): %s' % str(self.significantzero))
                pprint.pprint(stats)
        except:
            pprint.pprint(args)
    
    def save_stats(self, filename, *args):
        try:
            file = open(filename, 'w')
            pickle.dump([object for object in args], file)
            file.close
            return True
        except Exception, e:
            print('Exception when trying to save the stats: %s' % str(e))
            return False

    def load_stats(self, filename):
        try:
            file = open(filename, 'r')
            superstats = pickle.load(file)
            file.close
            return superstats
        except Exception, e:
            print('Exception when trying to load the stats: %s' % str(e))
            return False
    
    def merge_matrix(self, *args):
        # this way to merge several logs is the most precise : it will take all the values and do the stats calculation directly against this huge amount of data
        # the drawback of this method is that it is very ressources consuming, so you may prefer the weighted_mean_merge approach for very huge logs
        merged_matrix = self.flatten([somelist[1] for somelist in args])
        return ('merged gamelogs', merged_matrix)
    
    def weighted_mean_merge(self, *args):
        # The weighted mean sum the stats and ponderate (multiply then divide) them with their number of lines that were counted in the calculation
        # this produces a final weighted stat that should provide a good merge between all the stats based on their weight (number of lines)
        newstat = {}
        superstats = {}
        # first, we multiply each stats values to the count of lines, then we do the sum of these stats
        for game_log, stats in args:
            count = stats['count']
            for key, value in stats.iteritems():
                if key is not 'count' and key is not 'skewmeaning' and key is not 'cumfreq':
                    newstat[key] = value * count # multiply by the count of lines
                    try: # doing the sum of all the stats (one stat at a time)
                        superstats[key] += newstat[key]
                    except Exception, e:
                        superstats[key] = newstat[key]
        divisor = sum([stat[1]['count'] for stat in args]) # calculating the common divisor, being the sum of all the counts of lines of all the stats
        weighted_stats = dict( (map(lambda (key, value): (key,float(value) / divisor), superstats.iteritems())) ) # dividing each of the superstats by the common divisor, this gives us the final weighted_stats
        # adding a few useful fields
        weighted_stats['count'] = divisor
        if weighted_stats['skew'] > 0:
            weighted_stats['skewmeaning'] = 'There exist more smaller values from the mean than higher'
        else:
            weighted_stats['skewmeaning'] = 'There exist more higher values from the mean than smaller'
        # return weighted stats (and print it if debug mode)
        if self.debug: pprint.pprint(weighted_stats)
        return ('weighted-mean merged log', weighted_stats)

    def flatten(self, *args):
        # flatten a list of sublists into one level of list
        return [item for sublist in args[0] for item in sublist]
        #for elem in lst:
        #    if type(elem) in (tuple, list):
        #        for i in self.flatten(elem):
        #            yield i
        #    else:
        #        yield elem

    def flatten2(self, sequence):
        # flatten any level of nested lists or dict to one level of list
        def rflat(seq2):
            seq = []
            for entry in seq2:
                if '__contains__' in dir(entry) and \
                             type(entry) != str and \
                             type(entry)!=dict:
                    seq.extend([i for i in entry])
                else:
                    seq.append(entry)
            return seq

        def seqin(sequence):
            for i in sequence:
                if '__contains__' in dir(i) and \
                             type(i) != str and \
                             type(i) != dict:
                    return True
            return False

        seq = sequence[:]
        while seqin(seq):
            seq = rflat(seq)
        return seq

    def mode(self, matrix):
        results = {}
        for item in matrix:
            results.setdefault(item, 0)
            results[item] += 1
        results = sorted(results.iteritems(), key=lambda (k,v):(v,k), reverse=True) # Sort by value (count), then if 2 keys have the same count, it will sort them by their keys
        return results
    
    
if __name__ == '__main__':
    # Instanciating the class
    p = DiagPlugin()
    # Configuring the general parameters
    p.significantzero = False # fill in the missing lines and count them as zero (ie: take into account the times when no lines were outputted by the game server)
    p.debug = False # show some more debug stuffs
    p.maxlines = 0 # limit the logs processing to a maximum of lines. Set to 0 for unlimited.
    
    # Parsing the logs
    supermatrix = p.lines_per_second(r'C:\Users\lrq3000\Desktop\test\1\insta.log', r'C:\Users\lrq3000\Desktop\test\1\insta.log')
    # Generating the stats
    superstats = p.stats_per_second(*supermatrix)
    # Merging the stats of all logs into one, weighted-mean method (approximative but less ressource consuming)
    weighted_merged_stats = p.weighted_mean_merge( *superstats )
    # Merging the stats of all logs into one, matrix merge method (exact but more ressource consuming)
    merged_matrix = p.merge_matrix( *supermatrix )    
    merged_stats = p.stats_per_second( merged_matrix )
    
    # Showing the results
    p.show_results(*superstats)
    p.show_results(weighted_merged_stats)
    p.show_results(*merged_stats)
    
    # Testing some quick save and load, you can try with matrix too instead of stats
    p.save_stats(r'C:\Users\lrq3000\Desktop\test\1\labriquette.txt', *superstats)
    somestats = p.load_stats(r'C:\Users\lrq3000\Desktop\test\1\labriquette.txt')
    p.show_results(*somestats)

    # some sample stats if you want to try
    testsuperstats = [('C:\\Users\\lrq3000\\Desktop\\test\\1\\insta.log',
  {'3sigma': 6.945390758841171,
   'count': 11,
   'cumfreq': ([20171,
                25702,
                25808,
                25850,
                25862,
                25879,
                25891,
                25898,
                25908,
                25909],
               -1.86000005,
               5.7200001,
               0),
   'kurtosis': 114.34922587149542,
   'max': 53,
   'mean': 2.651009301787024,
   'median': 2.0230774326176335,
   'min': 1,
   'mode': 2,
   'modenext': 1,
   'samplespace': 52,
   'skew': 7.7869815045235207,
   'skewmeaning': 'There exist more smaller values from the mean than higher',
   'stddeviation': 2.315130252947057,
   'variance': 5.3598280881107039}),
 ('C:\\Users\\lrq3000\\Desktop\\test\\1\\insta.log',
  {'3sigma': 6.945390758841171,
   'count': 11,
   'cumfreq': ([20171,
                25702,
                25808,
                25850,
                25862,
                25879,
                25891,
                25898,
                25908,
                25909],
               -1.86000005,
               5.7200001,
               0),
   'kurtosis': 114.34922587149542,
   'max': 53,
   'mean': 2.651009301787024,
   'median': 2.0230774326176335,
   'min': 6,
   'mode': 2,
   'modenext': 1,
   'samplespace': 52,
   'skew': 7.7869815045235207,
   'skewmeaning': 'There exist more smaller values from the mean than higher',
   'stddeviation': 2.315130252947057,
   'variance': 5.3598280881107039})]
    