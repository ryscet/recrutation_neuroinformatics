#!/usr/bin/env python
# encoding: utf-8

import os    
import numpy as np                                           
import time
from ConfigParser import RawConfigParser, NoSectionError
import matplotlib.ticker
import matplotlib.dates as mpd

class ExperimentConfigFile(RawConfigParser, matplotlib.ticker.Formatter):
    def __init__(self, path, fname=None):    
        RawConfigParser.__init__(self)
        self.path = path               
        if fname is None:
            if os.path.isfile(os.path.join(path, 'config.txt')):
                self.fname = 'config.txt'
            else:
                self.fname = filter(lambda x: x.startswith('config') 
                        and x.endswith('.txt'), os.listdir(path))[0]
        else:                  
            self.fname = fname
        self.read(os.path.join(path, self.fname)) 
        
    def gettime(self, sec): 
        """Convert start and end time and date read from section sec
        (might be a list)
        of the config file 
        to a tuple of times from epoch."""
        if type(sec) == list:
            starts = []
            ends = []
            for ss in sec:
                st, et = self.gettime(ss)
                starts.append(st)
                ends.append(et)
            return min(starts), max(ends)
        else:
            tstr1 = self.get(sec, 'startdate') + self.get(sec, 'starttime')
            tstr2 = self.get(sec, 'enddate') + self.get(sec, 'endtime')
            if len(tstr1) == 15:
                t1 = time.strptime(tstr1, '%d.%m.%Y%H:%M')
            elif len(tstr1) == 18:                        
                t1 = time.strptime(tstr1, '%d.%m.%Y%H:%M:%S')
            else: 
                raise Exception('Wrong date format in %s' %self.fname)

            if len(tstr2) == 15:
                t2 = time.strptime(tstr2, '%d.%m.%Y%H:%M')
            elif len(tstr2) == 18:                        
                t2 = time.strptime(tstr2, '%d.%m.%Y%H:%M:%S')
            else: 
                raise Exception('Wrong date format in %s' %self.fname)

            return time.mktime(t1), time.mktime(t2)

    def __call__(self, x, pos=0):
        x = mpd.num2epoch(x)
        for sec in self.sections():
            t1, t2 = self.gettime(sec)
            if t1 <= x and x < t2:
                return sec
        return 'Unknown'    