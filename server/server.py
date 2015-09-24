# coding:utf-8
'''
Created on Feb 13, 2014

@author: magus0219
'''
#===============================================================================
# Import items in conf
#===============================================================================
from conf.server import ENVION as _eviron
from conf.server import SERVER_CONFIG as _server_conf
from conf.server import LOGGING as _logging_conf
import logging.config
#===============================================================================
# Import system libs
#===============================================================================
from datetime import datetime, timedelta, time
import os
import threading

from core.jobmanager import JobManager
from core.socketserver import SocketServer

logging.config.dictConfig(_logging_conf)
logger = logging.getLogger("Server")

class Server(object):
    '''
    Daemon serves as schedule engine
    '''
    clocks = []

    def __init__(self):
        self.interval = _server_conf[_eviron]['INTERVAL']
        self.starthour = _server_conf[_eviron]['START_HOUR']
        self.host = _server_conf[_eviron]['HOST']
        self.port = _server_conf[_eviron]['PORT']
        self.jobmanager = JobManager(self)
        
        self.lock_spawn = threading.Lock()
        self.next_batch_start_time = None
        
        self.socketserver = SocketServer(self.host, self.port, self.jobmanager)
    
    def _fillClock(self, starthour, interval):
        '''
        Fill clock triggers
        
        Server use clocks as triggers to schedule next batch of tasks.
        This clock values should be stable every day ,so interval causes variable
        clocks is not accepted.
        @param starthour:Integer as start hour
        @param interval:Integer as interval hours to generate clock triggers  
        '''
        self.clocks = []
        if (24 % interval != 0):
            raise ValueError("Invalid Interval %d" % (interval))
        else:
            for i in range(0, 24, interval):
                self.clocks.append((i + starthour) % 24)
        self.clocks.sort() 
        
    def _spawnScheduleThread(self, next_batch_start_time):
        '''
        Spawn schedule thread after one batch of task threads have been spawned

        Execute Time of the schedule thread is subtraction of next_batch_start_time
        and AHEAD_MINUTES of configuration.If execute time is gone,the thread will
        be started at once.
        @param next_batch_start_time: datetime,start time of next batch 
        '''
        next_schedule_time = next_batch_start_time - timedelta(minutes=_server_conf[_eviron]['AHEAD_MINUTES'])
        delay = 0 if next_schedule_time <= datetime.now() else (next_schedule_time - datetime.now()).seconds + 1
        next_batch_end_time = next_batch_start_time + timedelta(hours=self.interval)
        schedule_thread = threading.Timer(delay,
                        self._spawnTaskThreads,
                        args=[next_batch_start_time, next_batch_end_time ],
                        kwargs={})
        schedule_thread.daemon = True
        schedule_thread.start()
        logger.info("Schedule Thread for %s to %s has been created." % (next_batch_start_time.strftime("%Y-%m-%d %H:%M:%S"),
                                                                   next_batch_end_time.strftime("%Y-%m-%d %H:%M:%S")))
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           
    def spawnTaskThread(self, jobid):
        '''
        Spawn task threads of one job
        
        @param jobid:int job id to spawn 
        '''
        self.lock_spawn.acquire()
        try:
            now = datetime.now()
            self.jobmanager.spawnTask(jobid, now, self.next_batch_start_time)
            
            self.lock_spawn.release()
        except Exception, e:
            self.lock_spawn.release()
            raise e;
        logger.info("TaskThreads of Job(id:%d) have been spawned from %s to %s." % (jobid,
                                                                                    now.strftime("%Y-%m-%d %H:%M:%S"),
                                                                                    self.next_batch_start_time.strftime("%Y-%m-%d %H:%M:%S")))
    
    def _spawnTaskThreads(self, batch_start_time, batch_end_time):
        '''
        Spawn task Threads then spawn next schedule thread
        
        @param batch_start_time: datetime of start
        @param batch_end_time: datetime of end
        '''
        logger.info("Schedule Thread for %s to %s started." % (batch_start_time.strftime("%Y-%m-%d %H:%M:%S"),
                                                                   batch_end_time.strftime("%Y-%m-%d %H:%M:%S")))
        self.lock_spawn.acquire()
        try:
            self.jobmanager.spawnTasks(batch_start_time, batch_end_time)
            
            self._spawnScheduleThread(batch_end_time)
        
            self.next_batch_start_time = batch_end_time
            self.lock_spawn.release()
        except Exception, e:
            self.lock_spawn.release()
            raise e;
    
    def _getNextScheduleSection(self, now_time, starthour=None):
        '''
        Get Next Schedule Section consist of start time and end time
        
        If starthour is specified, here calculates starttime and endtime of one 
        normal batch of schedule.
        Or this calculates the first batch of schedule which starttime is now
        and endtime is next hour in clock list.
        @param now_time:time now. 
        @param starthour:Start hour which is the starttime of next batch.This 
                         value must in the clock list if specified.
        '''
        #=======================================================================
        #  Get next clock considering over night
        #=======================================================================
        next_clock = None
        next_clock_overnight = False
        for clock in self.clocks:
            if now_time.hour < clock:
                next_clock = clock
                break
        if not next_clock:
            next_clock_overnight = True
            next_clock = self.clocks[0]
        #=======================================================================
        #  calculate start and end time
        #=======================================================================
        if starthour:
            # normal batch
            if starthour not in self.clocks:
                raise ValueError("Start hour value:%d not in the clock list" % (starthour))
            if next_clock_overnight:
                next_clock_modified = next_clock + 24
            else:
                next_clock_modified = next_clock
            if next_clock_modified - now_time.hour > self.interval:
                raise ValueError("We can not schedule normal batch for interval over long")
            
            if starthour < now_time.hour:  # change date if over night
                batch_start_time = now_time + timedelta(days=1)
            else:
                batch_start_time = now_time + timedelta(days=0)
            batch_start_time = datetime.combine(batch_start_time.date(), time(hour=starthour))
            batch_end_time = batch_start_time + timedelta(hours=self.interval) 
        else:
            # first batch after server start up
            batch_start_time = now_time
            batch_end_time = None
            if not next_clock_overnight:
                batch_end_time = datetime.combine(now_time.date(), time(hour=next_clock))
            else:
                batch_end_time = now_time + timedelta(days=1)
                batch_end_time = datetime.combine(batch_end_time.date(), time(hour=next_clock))
        return batch_start_time, batch_end_time
               
    def start(self):
        '''
        Start the engine
        '''
        #=======================================================================
        # Initialize the Server
        #=======================================================================
        logger.info("Start...")
        self._fillClock(self.starthour, self.interval)
        logger.info("Generate Clocks:%s" % (str(self.clocks)))
        self.jobmanager.loadJobs()
        logger.info("Load %d jobs" % self.jobmanager.count)
        
        # create task log dir if not exists
        path = _server_conf[_eviron]['DIR']
        if not os.path.exists(path):
            os.mkdir(path)
        path = _server_conf[_eviron]['DIR'] + os.sep + "task"
        if not os.path.exists(path):
            os.mkdir(path)
        date_str = datetime.now().strftime("%Y%m%d")
        path = _server_conf[_eviron]['DIR'] + os.sep + "task" + os.sep + date_str
        if not os.path.exists(path):
            os.mkdir(path)
            
        #=======================================================================
        # Spawn one batch of Timer threads to run tasks
        #=======================================================================
        batch_start_time, batch_end_time = self._getNextScheduleSection(datetime.now())
        self._spawnTaskThreads(batch_start_time, batch_end_time)
        
        #=======================================================================
        # Start socket for client
        #=======================================================================
        self.socketserver.start()
        
    def stop(self):
        self.jobmanager.stop()

if __name__ == '__main__':
    server = Server()
    try:
        server.start()
    except KeyboardInterrupt:
        logger.info("has been Interrupted...")
    except Exception, e:
        logger.exception(e)
    finally:
        # clean up running and waiting tasks
        server.stop()
        logger.info("Terminated.")
        
