# coding:utf-8
'''
Created on Feb 17, 2014

@author: magus0219
'''
import re

_TIMERUNIT = ['MINITE', 'HOUR', 'DAY', 'MONTH', 'WEEKDAY']


class TimePattern(object):
    '''
    Base class of TimePattern
    
    Validation is needed here, we confirm pattern string has the following 
    format:
    * * * * *:minute hour day month weekday
    '''
    unit = "(\*|\*/\d+|\d+)"
    blank = "\s+"
    validator = re.compile("^" + unit + blank +  # minute
                                unit + blank +  # hour
                                unit + blank +  # day
                                unit + blank +  # month
                                unit + "$")  # weekday
    
    def __init__(self, pattern_str):
        m = TimePattern.validator.match(pattern_str)
        if not m:
            raise ValueError("Invalid pattern string: %s" % (pattern_str))
        
        for attr,value in zip(_TIMERUNIT,m.groups()):
            setattr(self,attr,value)
            
    def toList(self):
        return [getattr(self,unit) for unit in _TIMERUNIT]
            
    def __str__(self):
        return " ".join([getattr(self,unit) for unit in _TIMERUNIT])
            
