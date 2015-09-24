# coding:utf-8
'''
Created on Feb 18, 2014

@author: magus0219
'''
import datetime

class DateUtil(object):
    
    _format = "%Y-%m-%d %H:%M:%S"
    
    @staticmethod
    def datetime(datetime_str):
        return datetime.datetime.strptime(datetime_str,DateUtil._format)