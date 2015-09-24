# coding:utf-8
'''
Created on Feb 23, 2014

@author: magus0219
'''
from core.job import JobType
import threading
import time

class ServerStatus(object):
    '''
    Server status
    
    This class holds main counters of server status,
    Meanwhile methods maintain these statistic data structures are also placed
    here.
    '''


    def __init__(self):
        '''
        Constructor
        '''
        self.waiting_tasks = {}  # key:task value:thread
        self.waiting_jobs = {}  # key:jobid value task list
        self.running_tasks = {}  # key:task value:thread
        self.running_jobs = {}  # key:jobid value task list
        self.lock = threading.Lock()
        
    def add_waiting_task(self, task, thread):
        '''
        Add one task and thread into waiting queue
        
        Invoked only by task runner
        '''
        self.lock.acquire()
        try:
            self.waiting_tasks.update({task:thread})
            
            jobid = task.get_jobid()
            if jobid not in self.waiting_jobs:
                self.waiting_jobs[jobid] = []
            self.waiting_jobs[jobid].append(task)
            self.lock.release()
        except Exception, e:
            self.lock.release()
            raise e;
        
    def remove_waiting_task(self, task):
        '''
        Remove one task and thread into waiting queue
        
        Invoked only by task runner
        '''
        self.lock.acquire()
        try:
            self.waiting_tasks.pop(task)
            
            jobid = task.get_jobid()
            jobs = self.waiting_jobs[jobid]
            jobs.remove(task)
            
            if len(jobs) == 0:
                self.waiting_jobs.pop(jobid)
            self.lock.release()
        except Exception, e:
            self.lock.release()
            raise e;
            
    def add_running_task(self, task, thread):
        '''
        Add one task and thread into running queue
        
        Invoked only by task runner
        '''
        self.lock.acquire()
        try:
            self.running_tasks.update({task:thread})
            
            jobid = task.get_jobid()
            if jobid not in self.running_jobs:
                self.running_jobs[jobid] = []
            self.running_jobs[jobid].append(task)
            
            self.waiting_tasks.pop(task)
        
            # remove from waiting
            jobs = self.waiting_jobs[jobid]
            jobs.remove(task)
            
            if len(jobs) == 0:
                self.waiting_jobs.pop(jobid)
            
            self.lock.release()
        
        except Exception, e:
            self.lock.release()
            raise e;
        
    def remove_running_task(self, task):
        '''
        Remove one task and thread into running queue
        
        Invoked only by task runner
        '''
        self.lock.acquire()
        try:
            self.running_tasks.pop(task)
            
            jobid = task.get_jobid()
            jobs = self.running_jobs[jobid]
            jobs.remove(task)
            
            if len(jobs) == 0:
                self.running_jobs.pop(jobid)
            
            self.lock.release()
        except Exception, e:
            self.lock.release()
            raise e;
        
    def stop(self):
        '''
        Clean up all tasks
        
        '''
        self.lock.acquire()
        try:
            for task in self.waiting_tasks.keys():
                t = self.waiting_tasks.pop(task)
                t.cancel()
                t.stop()
                task.delete()
            for t in self.running_tasks.itervalues():
                t.stop()
            # Wait until all clean up done
            self.lock.release()
        except Exception, e:
            self.lock.release()
            raise e;
        while len(self.waiting_tasks) != 0 or len(self.running_tasks) != 0:
#             print "waiting_tasks:%d;running_tasks:%d"%(len(self.waiting_tasks),len(self.running_tasks))
            time.sleep(5);
        
    def remove_job(self, job):
        '''
        Remove one job and all related tasks
        
        '''
        self.lock.acquire()
        try:
            jobid = job.get_jobid()
            if jobid in self.waiting_jobs:
                for task in self.waiting_jobs[jobid]:
                    t = self.waiting_tasks.pop(task)
                    t.cancel()
                    task.delete()
                self.waiting_jobs.pop(jobid)
            self.lock.release()
        except Exception, e:
            self.lock.release()
            raise e;
        
    def cancelTask(self, task, from_system):
        '''
        Cancel one running task
        '''
        self.lock.acquire()
        try:
            if task in self.running_tasks:  # Maybe this task has terminated normally by itself
                t = self.running_tasks[task]
                t.stop()
            if from_system:
                if task in self.waiting_tasks:  # Maybe this task has terminated normally by itself
                    t = self.running_tasks[task]
                    t.stop()
            self.lock.release()
        except Exception, e:
            self.lock.release()
            raise e;
        
    def get_status(self):
        '''
        Get status string
        '''
        self.lock.acquire()
        try:
            rst = "%d task(s) spawned by %d job(s) are running and %d task(s) spawned by %d job(s) are waiting." % (
                            len(self.running_tasks.keys()), len(self.running_jobs.keys()), len(self.waiting_tasks.keys()), len(self.waiting_jobs.keys()))
            
            self.lock.release()
        except Exception, e:
            self.lock.release()
            raise e;
        return rst
        
        
