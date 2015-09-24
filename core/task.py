# coding:utf-8
'''
Created on Feb 16, 2014

@author: magus0219
'''
from util.mysql_handler import get_conn
from job import Job

class Status(object):
    '''
    Task status constants
    
    Status machine has no circle
    
    ---------------------------
    |WAITING ----> Running ---+->SUCCESS/FAIL
    |                | |      |
    |                | |      |    
    |              Blocking   |
    ---------------------------   
                        |
                    Cancel
    '''
    WAITING = 10
    RUNNING = 20
    BLOCKING = 25
    SUCCESS = 30
    FAIL = 40
    CANCEL = 50
    
class Task(object):
    '''
    Task Class

    Task inherit all important informations of job, but replace time pattern with
    real execute time and status.
    Task will used as key in inner structure of ServerStatus
    '''
    def __init__(self, jobid, taskid, exc_time, command, retry, job=None, depend=None, taskid_complex=None, status=Status.WAITING):
        self._jobid = jobid
        self._taskid = taskid
        self._exc_time = exc_time
        self._command = command
        self._retry = retry
        self._depend = depend
        self._status = status
        self._taskid_complex = taskid_complex
        self._endtime = None

        if job:        
            self._job = job
        else:
            j = Job.getByJobID(jobid)
            self._job = j
            self._depend = j.get_depend()
            
    def get_taskid_complex(self):
        return self._taskid_complex
            
    def get_jobid(self):
        return self._jobid
    
    def get_taskid(self):
        return self._taskid
        
    def get_exc_time(self):
        return self._exc_time
    
    def get_command(self):
        return self._command
    
    def get_retry(self):
        return self._retry
    
    def get_status(self):
        return self._status
    
    def get_depend(self):
        return self._depend
    
    def get_jobtype(self):
        return self._job.get_jobtype()
    
    def set_status(self, status):
        self._status = status
        
    def set_endtime(self, endtime):
        self._endtime = endtime
        
    def __hash__(self):
        return hash(self._taskid)
    
    def __eq__(self, other):
        return self._taskid == other._taskid
    
    def save(self):
        '''
        Save this task to database
        '''
        conn = get_conn()
        
        sql = '''insert into CW_TASK
                    (taskid,taskid_cmplx,jobid,executetime,endtime,retry,command,status,description)
                values
                    ('%s',%s,%d,'%s',%s,%d,'%s',%d,'Spawned by BI_ClockWork Publisher')
                on duplicate key update status=%d,endtime=%s
                ''' % (
                     self._taskid,
                     "'" + self._taskid_complex + "'" if self._taskid_complex else 'NULL',
                     self._jobid,
                     self._exc_time.strftime('%Y-%m-%d %H:%M:%S'),
                     "'" + self._endtime.strftime('%Y-%m-%d %H:%M:%S') + "'" if self._endtime else 'NULL',
                     self._retry,
                     self._command,
                     self._status,
                     self._status,
                     "'" + self._endtime.strftime('%Y-%m-%d %H:%M:%S') + "'" if self._endtime else 'NULL')
        print sql
#         print id(conn), self._taskid, self._status, 'save'
        conn.insert(sql)
        
    def delete(self):
        '''
        Save this task to database
        '''
        conn = get_conn()
        
        sql = '''delete from CW_TASK where taskid='%s' and status=%d
                ''' % (self._taskid, Status.WAITING)
#         print id(conn), self._taskid, 'save'
        conn.delete(sql)
        
    @staticmethod
    def getByTaskID(taskid):
        '''
        Get one job
        '''
        conn = get_conn()
        
        sql = '''select jobid,taskid,executetime,command,retry,status from CW_TASK where
                    taskid="%s"''' % (taskid)
        count, rst = conn.select(sql)
        if count == 1:
            jobid, taskid, exe_time, command, retry, status = rst[0]
            return Task(jobid, taskid, exe_time, command, retry, None, None, None, status)
        else:
            return None
        
        
    
    
    
