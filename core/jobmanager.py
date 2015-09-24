# coding:utf-8
'''
Created on Feb 14, 2014

@author: magus0219
'''
import threading, logging, uuid
from datetime import datetime, timedelta, time
from job import Job
from task import Task, Status
from taskrunner import TaskRunner
from timematcher import TimeMatcher
from core.serverstatus import ServerStatus

class JobManager(object):
    '''
    Main class to manager each operation of job and task
    
    Socket server should only invoke methods of this class.
    '''
    

    def __init__(self, server):
        '''
        Constructor
        '''
        self._server = server
        self._status = ServerStatus()
        self._depository = {}  # key:jobid value:job
        self._lock = threading.Lock()
        self._logger = logging.getLogger("Server.JobManager")
        self.count = 0
        self.hour_index = {}  # key:hour value: job list
        
    def indexJobs(self):
        '''
        Create hour index for every job loaded.
        
        To increment efficiency, we select hour(total 24 keys) as a key to index
        jobs
        '''
        for clock in range(24):
            for job in self._depository.itervalues():
                if TimeMatcher.matchOneUnit(job.get_time_pattern().HOUR, clock):
                    if clock not in self.hour_index:
                        self.hour_index[clock] = []
                    self.hour_index[clock].append(job)
    
    def indexJob(self, job):
        '''
        Index job by hour recording to its time pattern
        
        @param job:Job 
        '''
        for clock in range(24):
            if TimeMatcher.matchOneUnit(job.get_time_pattern().HOUR, clock):
                if clock not in self.hour_index:
                    self.hour_index[clock] = []
                self.hour_index[clock].append(job)
            
    def addJob(self, jobid):
        '''
        Add one job to Server and then server start to schedule it.
        
        @param jobid:int 
        '''
        jobid = int(jobid)
        if jobid in self._depository:
            raise ValueError("Job(id:%d) has been loaded." % (jobid))
        else:
            self._lock.acquire()
            try:
                job = Job.getByJobID(jobid)
                if not job:
                    raise ValueError("Job(id:%d) is not exsited or not enabled." % (jobid))
                self.loadJob(job)
                self.indexJob(job)
                self._lock.release()
            except Exception, e:
                self._lock.release()
                raise e;
            self._logger.info("Job(id:%d) is added." % (jobid))
            self._server.spawnTaskThread(jobid)
            
    def loadJobs(self):
        '''
        Load jobs from database and index them use hour
        '''
        self._lock.acquire()
        try:
            for job in Job.getAll():
                self.loadJob(job)
            self.indexJobs()
            self._lock.release()
        except Exception, e:
            self._lock.release()
            raise e;
    
    def loadJob(self, job):
        '''
        Load one job to depository,checking if it has been loaded.
        
        @param job:Job
        '''
        jobid = job.get_jobid()
        if jobid in self._depository:
            self._logger.warn("Job(jobid:%d) has been loaded ,overwrite it now." % jobid)
            self.count = self.count - 1
        
        self._depository[jobid] = job
        self.count = self.count + 1
        
    def reloadJob(self, jobid):
        '''
        Reload one job
        
        @param jobid:int 
        '''
        self.removeJob(jobid)
        self.addJob(jobid)
    
    def removeJob(self, jobid):
        '''
        Remove one job from server
        
        @param jobid: int jobid
        We remove task from waiting queue but do not care of the running tasks  
        '''
        self._lock.acquire()
        try:
            job = Job.getByJobID(jobid)
            if not job:
                raise ValueError("Job(id:%d) is not exsited or not enabled." % (jobid))
            
            self._status.remove_job(job)
            
            if jobid in self._depository:
                self._depository.pop(jobid)
            
            for job_list in self.hour_index.itervalues():
                for job in job_list:
                    if job.get_jobid() == jobid:
                        job_list.remove(job)
    
        
            self.count -= 1
            
            self._lock.release()
        except Exception, e:
            self._lock.release()
            raise e;
        self._logger.info("Job(id:%d) is removed." % (jobid))
        
    def cancelTask(self, taskid, from_system=False):
        '''
        Cancel one task which is running
        
        @param taskid:str
        '''
        task = Task.getByTaskID(taskid)
        if not task:
            raise ValueError("Task(id:%s) is not exsited." % (taskid))
        if not from_system:
            if task.get_status() != Status.RUNNING:
                raise ValueError("Task(id:%s) is not running." % (taskid))
        
        self._status.cancelTask(task)
    
    def spawnImmediateTask(self, jobid, taskid_complex=None, params=None):
        '''
        Run task immediately using basic configuration of job
        
        @param jobid:int
        @param taskid_complex: string 
        @param params: string
        '''
        job = Job.getByJobID(jobid)
        if not job:
            raise ValueError("Job(id:%d) is not existed or not enabled." % (jobid))
        if params :
            job.set_command(job._substituteReservedWord(params))

        if taskid_complex:
            task = Task(job.get_jobid(), uuid.uuid1().hex, datetime.now(),
                            job.getCommandToExcute(), job.get_retry(), job, job.get_depend(), taskid_complex)
        else:
            task = Task(job.get_jobid(), uuid.uuid1().hex, datetime.now(),
                            job.getCommandToExcute(), job.get_retry(), job, job.get_depend())
        t = TaskRunner(0, task, self._status, self, params)
        t.daemon = True
        task.save()
        self._status.add_waiting_task(task, t)
        t.start()
        
        return task
    
    def spawnTask(self, jobid, start_time, end_time):
        '''
        Spawn thread based on one Job's timer
        
        @param jobid:int
        @param start_time:datetime ,start time of time section
        @param end_time:datetime ,end time of time section
        '''
        tasks = []
        self._lock.acquire()
        try:
            job = Job.getByJobID(jobid)
            if not job:
                raise ValueError("Job(id:%d) is not exsited or not enabled." % (jobid))
            
            # Clear second and be care of start minute
            determine_time = start_time
            if start_time.second != 0:
                determine_time = start_time + timedelta(minutes=1)
            determine_time = datetime.combine(determine_time.date(), time(hour=determine_time.hour, minute=determine_time.minute))
            
            while determine_time < end_time:
                if TimeMatcher.matchTimePattern(job.get_time_pattern(), determine_time):
                    task = Task(job.get_jobid(), uuid.uuid1().hex, determine_time,
                                job.getCommandToExcute(), job.get_retry(), job, job.get_depend())
                    t = TaskRunner((determine_time - datetime.now()).seconds + 1,
                                                                       task, self._status, self)
                    t.daemon = True
                    t.start()
                    task.save()
                    tasks.append(task)
                    self._status.add_waiting_task(task, t)
                determine_time = determine_time + timedelta(minutes=1)
                                                                                                                                                                                                                                                                                                                                                                                               
            self._lock.release()
        except Exception, e:
            self._lock.release()
            raise e;
        self._logger.info("Schedule %d Tasks from %s to %s" % (len(tasks),
                                                           start_time.strftime("%Y-%m-%d %H:%M:%S"),
                                                           end_time.strftime("%Y-%m-%d %H:%M:%S")))
        return tasks
        
    def spawnTasks(self, start_time, end_time):
        '''
        Spawn thread based on Job's timer.
        
        According to start_time and end_time,Job satisfied the job will be 
        wrapped as Task which launched by Timer thread.For Timer accept delay as
        its first parameter,we convert job's timer to delay seconds here.
        These Timer tasks will be started in main thread.
        
        '''
        tasks = []
        jobs = []
        self._lock.acquire()
        try:
            for hour in range(start_time.hour, end_time.hour):
                if hour in self.hour_index:
                    jobs.extend(self.hour_index[hour])
            jobs = set(jobs)
            
            # Clear second and be care of start minute
            determine_time = start_time
            if start_time.second != 0:
                determine_time = start_time + timedelta(minutes=1)
            determine_time = datetime.combine(determine_time.date(), time(hour=determine_time.hour, minute=determine_time.minute))
            
            while determine_time < end_time:
                for job in jobs:
                    if TimeMatcher.matchTimePattern(job.get_time_pattern(), determine_time):
                        task = Task(job.get_jobid(), uuid.uuid1().hex, determine_time,
                                    job.getCommandToExcute(), job.get_retry(), job, job.get_depend())
                        t = TaskRunner((determine_time - datetime.now()).seconds + 1,
                                                       task, self._status, self)
                        t.daemon = True
                        t.start()
                        task.save()
                        tasks.append(task)
                        self._status.add_waiting_task(task, t)
                determine_time = determine_time + timedelta(minutes=1)
                                                                                                                                                                                                                                                                                                                                                                                               
            self._lock.release()
        except Exception, e:
            self._lock.release()
            raise e;
        
        self._logger.info("Schedule %d Tasks from %s to %s" % (len(tasks),
                                                           start_time.strftime("%Y-%m-%d %H:%M:%S"),
                                                           end_time.strftime("%Y-%m-%d %H:%M:%S")))
        return tasks
    
    def getServerStatus(self):
        return self._status.get_status()
    
    def stop(self):
        self._status.stop()
