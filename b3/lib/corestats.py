#!/usr/bin/env python

#  corestats.py (COREy STATS) 
#  Copyright (c) 2006-2007, Corey Goldberg (corey@goldb.org)
#  updated on 2010-09 by GrosBedo
#
#    statistical calculation class
#    for processing numeric sequences
#
#  license: GNU LGPL
#
#  This library is free software; you can redistribute it and/or
#  modify it under the terms of the GNU Lesser General Public
#  License as published by the Free Software Foundation; either
#  version 2.1 of the License, or (at your option) any later version.
#
# CHANGELOG:
# 2010-09-14 - GrosBedo:
# * enhanced variance(), no more memory leak
# 2010-09-13 - GrosBedo:
# * added variance()
# * added mode()
# * added unique()
# * fixed median() algo
# 2010-09-09 - GrosBedo:
# * added percentileforvalue() (inverse of valueforpercentile() )
# * CRITICAL: removed the init function and the self.sequence float conversion (which was a BIG memory hog !)



import sys, math


class Stats:
    
    def sum(self, sequence):
        if len(sequence) < 1: 
            return None
        else:
            return sum(sequence)
    
    
    def count(self, sequence):
        return len(sequence)

    
    def min(self, sequence):
        if len(sequence) < 1: 
            return None
        else:
            return min(sequence)
    
    
    def max(self, sequence):
        if len(sequence) < 1: 
            return None
        else:
            return max(sequence)
    

    def mean(self, sequence):
        if len(sequence) < 1: 
            return None
        else: 
            return float(sum(sequence)) / len(sequence)    
    
    
    def median(self, sequence):
        if len(sequence) < 1: 
            return None
        else:
            sequence.sort()
            element_idx = float(len(sequence)) / 2
            if (element_idx != int(element_idx)):
                median1 = sequence[int(math.floor(element_idx))]
                median2 = sequence[int(math.ceil(element_idx))]
                return float(median1 + median2) / 2
            else:
                return sequence[int(element_idx)]
            

    def modeold(self, sequence):
        results = {}
        for item in sequence:
            results.setdefault(item, 0) # if index does not already exists, create it and set a value of 0
            results[item] += 1
        results = sorted(results.iteritems(), key=lambda (k,v):(v,k), reverse=True) # Sort by value (count), then if 2 keys have the same count, it will sort them by their keys
        return results

    def mode(self, sequence):
        """
        Enhanced version of mode(), inspired by statlib/stats.py
        The advantage is that this function (as well as mode) can return several modes at once (so you can see the next most frequent values)
        """
        scores = self.unique(sequence)
        scores.sort()
        freq = {}
        for item in scores:
            freq.setdefault(item, 0) # if index does not already exists, create it and set a value of 0
            freq[item] = sequence.count(item)
        results = sorted(freq.iteritems(), key=lambda (k,v):(v,k), reverse=True) # Sort by value (count), then if 2 keys have the same count, it will sort them by their keys
        return results

    def variance(self, sequence):
        if len(sequence) < 1: 
            return None
        else:
            avg = self.mean(sequence)
            sdsq = 0
            for i in sequence:
                sdsq += (i - avg) ** 2
            #sdsq = sum([(i - avg) ** 2 for i in sequence]) # this one-liner hogs a lot of memory, avoid
            variance = (float(sdsq) / (len(sequence) - 1))
            return variance
    
    def stdev(self, sequence):
        if len(sequence) < 1: 
            return None
        else:
            variance = self.variance(sequence)
            stdev = float(variance) ** 0.5
            return stdev

    def valueforpercentile(self, sequence, percentile):
        if len(sequence) < 1: 
            value = None
        elif (percentile > 100):
            sys.stderr.write('ERROR: percentile must be <= 100.  you supplied: %s\n'% percentile)
            value = None
        elif (percentile == 100):
            value = max(sequence)
        else:
            element_idx = int(len(sequence) * (float(percentile) / 100.0))
            sequence.sort()
            value = sequence[element_idx]
        return value

    def percentileforvalue(self, sequence, value):
        maxnb = max(sequence)
        minnb = min(sequence)
        if len(sequence) < 1: 
            percentile = None
        elif (value > maxnb or value < minnb ):
            #sys.stderr.write('ERROR: value must be between %s < value < %s.  you supplied: %s\n'% (minnb, maxnb, value))
            #percentile = None
            if (value > maxnb):
                percentile = 100
            else:
                percentile = 0
        else:
            sequence.sort()
            sequence.reverse()
            element_idx = sequence.index(value) # list.index() returns the first occurence, but we want to enclose all equal values, so we must reverse the sequence and do some calculations in order to get the right value
            element_idx = (len(sequence) - element_idx)
            percentile = float(element_idx) * 100.0 / len(sequence)
        return percentile

    def unique(self, sequence):
        return list(set(sequence))





# Sample script using this class:
# -------------------------------------------    
#    #!/usr/bin/env python
#    import corestats
#    
#    sequence = [1, 2.5, 7, 13.4, 8.0]
#    stats = corestats.Stats()
#    print stats.mean(sequence)
#    print stats.valueforpercentile(sequence, 90)
# -------------------------------------------