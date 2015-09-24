# coding:utf-8
'''
Created on Feb 17, 2014

@author: magus0219
'''

import re

_PATTERN = ['^\*$', '^\*/\d+$', '^\d+$']

class TimeMatcher(object):
    '''
    Tool class for match time pattern
    '''
    
    @staticmethod
    def matchOneUnit(unit_pattern, value):
        '''
        Determine if value matches the pattern
        
        Possible values we supported:
        1.* means everything
        2.*/2 means every 2 units
        3.Positive integer means specific value
        
        @param unit_pattern: String pattern on one unit position
        @param value:int one unit value of datetime
        '''
        #=======================================================================
        # Validate parameters
        #=======================================================================
        if type(value) != int or value < 0:
            raise ValueError("Invalid value %s" % (str(value)))
        
        pattern_matched = None
        for p in _PATTERN:
            if re.match(p, unit_pattern):
                pattern_matched = p
                break
        if pattern_matched is None:
            raise ValueError("Invalid pattern %s" % (unit_pattern))
        
        #=======================================================================
        # Match values
        #=======================================================================
        if pattern_matched == '^\*$':
            return True
        elif pattern_matched == '^\*/\d+$':
            return eval(unit_pattern.replace("*/", str(value) + "%") + "==0")  # value % sth ==0
        elif pattern_matched == '^\d+$':
            return int(unit_pattern) == value
        
        return False
    
    @staticmethod
    def matchTimePattern(time_pattern, time):
        '''
        Determine if time matches one job's time pattern
        
        Time match the time pattern only if every portion of time meet relevant
        time unit pattern.
        
        @param time_pattern: TimePattern
        @param time: datetime 
        '''
        for unit_pattern,value in zip(time_pattern.toList(),
                                      [time.minute,
                                       time.hour,
                                       time.day,
                                       time.month,
                                       time.isoweekday()]):
            if not TimeMatcher.matchOneUnit(unit_pattern, value):
                return False
        return True
        
