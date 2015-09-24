# coding:utf-8
'''
Created on Feb 13, 2014

@author: magus0219
'''
import os

ENVION = "test"

SERVER_CONFIG = {
    "test":{
            # Clock calculation
            'START_HOUR':11,
            'INTERVAL':1,
            # Schedule Thread
            'AHEAD_MINUTES':100,
            # TaskRunner
            'BLOCK_SECONDS':35,
            'COMPLEX_JOB_CHECKER_SECONDS':15,
            # Communication socket
            'HOST':'0.0.0.0',
            'PORT':3993,
            # Log dir
            'DIR':'./logs'  # relative path
            
            
            }   
                 }

MYSQL_DATABASES = {
    'test': {
        'DBNAME': 'clockwork',
        'USER': 'root',
        'PASSWORD': '',
        'HOST': '127.0.0.1',
        'PORT': 3306,
        'MINCACHED': 3,
        'MAXCACHED': 5,
    },
    'self': {
        'DBNAME': 'DW_SupportData',
        'USER': 'root',
        'PASSWORD': 'root',
        'HOST': '172.17.13.38',
        'PORT': 3306,
        'MINCACHED': 3,
        'MAXCACHED': 5,
    },
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'verbose': {
            'format': '[%(levelname)s][%(module)s-%(lineno)d][PID:%(process)d,TID:%(thread)d]%(asctime)s %(name)s:%(message)s'
                    },
        'simple': {
            'format': '%(levelname)s %(message)s' 
                    },
                },
    'handlers': {
        'console':{
            'level':'DEBUG',
            'class':'logging.StreamHandler',
            'formatter': 'verbose'
        },
        'file':{
            'level':'DEBUG',
            'class':'logging.handlers.TimedRotatingFileHandler',
            'formatter': 'verbose',
            'filename': SERVER_CONFIG[ENVION]['DIR'] + os.sep + "server.log",
            'when':'midnight'
        },
                },
    'loggers': {
        'Server': {
            'handlers':['console','file'],
            'propagate': True,
            'level':'DEBUG',
            },
        'TaskThread': {
            'handlers':['console','file'],
            'propagate': True,
            'level':'DEBUG',
            },
                },
           }
