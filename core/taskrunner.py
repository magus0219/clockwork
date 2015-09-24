# coding:utf-8
'''
Created on Feb 16, 2014

@author: magus0219
'''

import logging, subprocess, os, threading, time
from datetime import datetime, timedelta
from threading import Event

from conf.server import ENVION as _eviron
from conf.server import SERVER_CONFIG as _server_conf

from job import Job, JobType
from task import Status
from util.mysql_handler import get_conn
from util.email_util import EmailUtil

class TaskRunner(threading.Thread):
    '''
    Task Runner as thread entry
    
    This class has features of Threading.Timer,adding stoppable capability.
    Here cancel means stop timer where this task is still in the waiting queue and
    stop means stop task which is running.
    
    There are several stages after task is running:
    *Check Dependence:Check if all jobs depend on is finished.(RUNNING->BLOCKING->RUNNING)
    Then two choices:
    *Run simple task:call popen to run shell command.(RUNNING->SUCCESS/FAIL)
    *Run complex task:spawn all child simple tasks and entry a loop to check status of 
    them.If any of child tasks goes to fail or cancel,the complex task returned fail.
    If complex task is canceled,it is its duty to cancel all running child tasks.
    (RUNNING->SUCCESS/FAIL)
    
    By the way,all task can be canceled by each stage.
    '''
    def __init__(self, interval, task, server_status, jobmanager, params=None):
        threading.Thread.__init__(self)
        self.task = task
        self.server_status = server_status
        self.jobmanager = jobmanager
        self.process = None
        self.stopped = False
        self.params = params
        self.interval = interval
        self.finished = Event()
        self.logger = logging.getLogger("TaskThread." + task.get_taskid())
        self.start_time = None
        
    def cancel(self):
        """Stop the timer if it hasn't finished yet"""
        self.finished.set()
        
    def checkDependence(self):
        '''
        Check dependence of task
        
        This function use a inner structure of delta to determine if this task 
        should run.If not,thread will sleep until next wake up.
        '''
        start_time = self.start_time
        task = self.task
        
        dependence = True
        depend = task.get_depend()
        taskid_complex = self.task.get_taskid_complex()
        
        jobid_checked = [ ]
        if taskid_complex:
            '''
            1. Check in the same complex dependence , save dependence info
            2. By the CW_INCLUSION , check EnableSimpleDependence == 0(not use) or 1(use)
            3. If use, check simple dependence
               If not use, check done
            '''
            
            conn = get_conn()
            select_sql = '''
                SELECT JobID FROM CW_TASK WHERE TaskID = '{taskid_complex}'
            '''.format(taskid_complex=taskid_complex)
            jobid_complex = int(conn.select_unique(select_sql))
            jobid = int(self.task.get_jobid())
            
            check_sql = '''
                SELECT depend.JobID_Depend FROM CW_JOB_DEPENDENCE depend
                WHERE depend.JobID_Complex = {jobid_complex}
                AND depend.JobID = {jobid}
            '''.format(jobid_complex=jobid_complex, jobid=jobid)
            count, rst = conn.select(check_sql)
            
            if count :
                for row in rst:
                    check_sql = '''
                        SELECT ExecuteTime FROM CW_TASK task
                        WHERE jobid = {jobid}
                        AND Status = {status}
                        AND TaskID_Cmplx = '{taskid_complex}'
                    '''.format(jobid=int(row[0]), status=Status.SUCCESS, taskid_complex=taskid_complex)
                    print check_sql
                    count = conn.select_count(check_sql)
                    if not count:
                        dependence = False
                        break
                    jobid_checked.append(int(row[0]))
            
            if dependence :
                check_sql = '''
                    SELECT inclusion.EnableSimpleDependence FROM CW_JOB_INCLUSION inclusion
                    WHERE JobID = {jobid_complex}
                    AND JobID_Inclusion = {jobid}
                '''.format(jobid_complex=jobid_complex, jobid=jobid)
                enable_simple_dependence = int(conn.select_unique(check_sql))
                if enable_simple_dependence == 0 :
                    return dependence
                else :
                    # goto if not taskid_complex
                    pass
            else :
                return dependence
                
#             for jobid_depend, delta in depend.iteritems():
#                 sql = "select executetime from CW_TASK where jobid=%d and status=%d and taskid_cmplx='%s'" % (
#                                                                     jobid_depend, Status.SUCCESS, taskid_complex)
#                 conn = get_conn()
#                 count, rst = conn.select(sql)
#                 if not count:
#                     dependence = False
#                     break
        if not taskid_complex :
            for jobid_depend, delta in depend.iteritems():
                if jobid_depend in jobid_checked:
                    continue
                d = timedelta(days=0)
                day, hour, minute = delta
                if day >= 0:
                    d += timedelta(days=day)
                if hour >= 0:
                    d += timedelta(hours=hour)
                if minute >= 0:
                    d += timedelta(minutes=minute)
                determine_time = start_time - d
                conn = get_conn()
                
                sql = "select executetime from CW_TASK where jobid=%d and status=%d order by executetime desc limit 1" % (
                                                                    jobid_depend, Status.SUCCESS)
                count, rst = conn.select(sql)
                if not count:
                    dependence = False
                    break
                else:
                    last_execute_time = rst[0][0]
                    if day >= 0:
                        if last_execute_time.day != determine_time.day:
                            dependence = False
                            break
                    if hour >= 0:
                        if last_execute_time.hour != determine_time.hour:
                            dependence = False
                            break
                    if minute >= 0:
                        if last_execute_time.minute != determine_time.minute:
                            dependence = False
                            break
        
        return dependence

    def runChildTask(self):
        '''
        Run child tasks of complex job
        
        '''
        jobid = self.task.get_jobid()
        conn = get_conn()
        sql = "select jobid_inclusion from CW_JOB_INCLUSION where jobid=%d" % (jobid)
        sql2 = "select status from CW_TASK where taskid='%s'"
        count, rst = conn.select(sql)
        if count:
            child_task = {}  # KEY:TASK VALUE:TASKSTATUS
            for jobid_inclusion, in rst:
                job = Job.getByJobID(jobid_inclusion)
                if job:
                    task = self.jobmanager.spawnImmediateTask(jobid=jobid_inclusion, taskid_complex=self.task.get_taskid(), params=self.params)
                    child_task[task] = Status.RUNNING
                    
        while True:
            done = True
            normal = True
            for task, task_status in child_task.iteritems():
                if task_status != Status.SUCCESS:
                    conn = get_conn()
                    count2, rst2 = conn.select(sql2 % (task.get_taskid()))
                    if count2 == 1:  # Task is not written to database
                        t_status = rst2[0][0]
                        self.logger.debug ("check db " + task.get_taskid() + " " + str(t_status))
                        child_task[task] = t_status
                        
                        if t_status != Status.SUCCESS:
                            done = False
                        
                        if t_status == Status.FAIL or t_status == Status.CANCEL:
                            child_task[task] = t_status
                            normal = False
                    else:
                        done = False
                        
            if done == True:  # All children success
                return Status.SUCCESS
            elif not normal:  # Some Task fails or cancels,then we cancel all other running
                for task, task_status in child_task.iteritems():
                    self.logger.debug ("check dict " + task.get_taskid() + " " + str(task_status))
                    if task_status in (Status.RUNNING, Status.BLOCKING):
                        self.server_status.cancelTask(task)
                        self.logger.debug ("task %s is canceled by complex task." % task.get_taskid())
                        
                
                if self.stopped:
                    return Status.CANCEL
                else :
                    return Status.FAIL
            else:
                if self.stopped:
                    return Status.CANCEL
                else :
                    return Status.FAIL
                time.sleep(_server_conf[_eviron]['COMPLEX_JOB_CHECKER_SECONDS'])
        

    def run(self):
        '''
        Run Task.
        
        This is the entry of timer thread which call system call popen to execute 
        task's shell command.
        Here we also should code all necessary work around task running including:
        1.logging
        2.time cost counter
        3.redirect stdout/stderr 
        4.maintain task status in database
        5.maintain Server's running_task list
        6.retry when falls
        7.check dependence 
        8.send error email
        and so on.
        '''
        self.finished.wait(self.interval)
        task = self.task
        if not self.finished.is_set():
            server_status = self.server_status
            logger = self.logger
            
            server_status.add_running_task(task, threading.current_thread())
            task.set_status(Status.RUNNING)
            task.save()
            
            self.start_time = start_time = datetime.now()
            logger.info("Start at %s" % start_time.strftime("%Y-%m-%d %H:%M:%S"))
            
            #===================================================================
            # Check dependence
            #===================================================================
            while not self.checkDependence() and not self.stopped:
                task.set_status(Status.BLOCKING)
                task.save()
                time.sleep(_server_conf[_eviron]['BLOCK_SECONDS'])
                
            if self.stopped:
                end_time = datetime.now()
                status = Status.CANCEL
                task.set_status(status)
                task.set_endtime(end_time)
                task.save()
                logger.info("Canceled at %s,cost %s" % (end_time.strftime("%Y-%m-%d %H:%M:%S"), end_time - start_time))
                server_status.remove_running_task(task)
                return
                
            task.set_status(Status.RUNNING)
            task.save()
            
            #=======================================================================
            # Get log file name
            #=======================================================================
            date_str = datetime.now().strftime("%Y%m%d")
            path = _server_conf[_eviron]['DIR'] + os.sep + "task" + os.sep + date_str
            if not os.path.exists(path):
                os.mkdir(path)
            task_log_filename = path + os.sep + task.get_taskid() + ".log"
            
            #=======================================================================
            # Run Simple Task
            #=======================================================================
            jobtype = task.get_jobtype()
            
            if jobtype == JobType.Simple:
                return_code = -1
                retry_total = 0
                retry = task.get_retry()
                while return_code != 0 and retry > retry_total:
                    f = open(task_log_filename, "a")
                    f.write("\n%s\n%sTry %d%s\n%s\n" % ("*"*100, "*"*48, retry_total + 1, "*"*48, "*"*100))
                    f.close()
                    
                    if retry_total > 0:
                        logger.info("Retry %d at %s" % (retry_total, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                    self.process = p = subprocess.Popen("%s 1>>%s 2>>%s" % (task.get_command(), task_log_filename, task_log_filename), shell=True)
                    p.wait()
                    
                    if self.stopped:
                        end_time = datetime.now()
                        status = Status.CANCEL
                        task.set_status(status)
                        task.set_endtime(end_time)
                        task.save()
                        logger.info("Canceled at %s,cost %s" % (end_time.strftime("%Y-%m-%d %H:%M:%S"), end_time - start_time))
                        server_status.remove_running_task(task)
                        return
                    else:
                        return_code = p.returncode
                        retry_total += 1
                
                end_time = datetime.now()
                if return_code != 0:
                    logger.info("Failed at %s,cost %s" % (end_time.strftime("%Y-%m-%d %H:%M:%S"), end_time - start_time))
                    status = Status.FAIL
                else:
                    logger.info("Succeed at %s,cost %s" % (end_time.strftime("%Y-%m-%d %H:%M:%S"), end_time - start_time))
                    status = Status.SUCCESS
                
            #===================================================================
            # Run Complex Task
            #===================================================================
            elif jobtype == JobType.Complex:
                retry_total = 0
                retry = task.get_retry()
                status = Status.RUNNING
                while status not in (Status.SUCCESS, Status.CANCEL) and retry > retry_total:
                    if retry_total > 0:
                        logger.info("Retry %d at %s" % (retry_total, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                    status = self.runChildTask()
                    retry_total += 1
                    
                end_time = datetime.now()
                if status == Status.FAIL:
                    logger.info("Failed at %s,cost %s" % (end_time.strftime("%Y-%m-%d %H:%M:%S"), end_time - start_time))
                elif status == Status.SUCCESS:
                    logger.info("Succeed at %s,cost %s" % (end_time.strftime("%Y-%m-%d %H:%M:%S"), end_time - start_time))
                elif status == Status.CANCEL:
                    task.set_status(status)
                    task.set_endtime(end_time)
                    task.save()
                    logger.info("Canceled at %s,cost %s" % (end_time.strftime("%Y-%m-%d %H:%M:%S"), end_time - start_time))
                    #===================================================================
                    # Add logic to remove child task if this task is complex
                    #===================================================================
                    if task.get_jobtype == JobType.Complex:
                        check_sql = '''
                                SELECT TaskID,Status FROM CW_TASK task
                                WHERE TaskID_Cmplx = '{taskid_complex}'
                            '''.format(taskid_complex=task.get_taskid())
                        conn = get_conn()
                        count, rst = conn.select(check_sql)
                        if count:
                            for taskid, _status in rst:
                                if _status not in (Status.FAIL, Status.SUCCESS, Status.CANCEL):
                                    self.jobmanager.cancelTask(taskid, from_system=True)
                    
                    server_status.remove_running_task(task)
                    return
            
            #=======================================================================
            # Update task status
            #=======================================================================
            task.set_status(status)
            task.set_endtime(end_time)
            task.save()
            
            server_status.remove_running_task(task)
            
            self.finished.set()
        
        #=======================================================================
        # Cancel the task timer
        #=======================================================================
        else:
            end_time = datetime.now()
            status = Status.CANCEL
            task.set_status(status)
            task.set_endtime(end_time)
            task.save()

        #=======================================================================
        # send error email
        # if simple job and not in complex ...
        # if complex job send to error of child job
        # if simple job and in complex ...pass...
        #=======================================================================
        if task.get_status() == Status.FAIL :
            conn = get_conn()
            select_sql = '''
                SELECT cts.Description, cj.Name, cj.Email FROM CW_TASK ct
                INNER JOIN CW_JOB cj ON cj.RecordID = ct.JobID
                INNER JOIN CW_TASK_STATUS cts ON cts.StatusID = ct.Status
                WHERE ct.TaskID = '{taskid}'
            '''.format(taskid=task.get_taskid())
            count , rst = conn.select(select_sql)
            email = None
            content = ''
            if count :
                email = rst[0][2]
                if email :
                    email_list = email.split(';')
                    content += 'TaskID : %s <br/>' % (str(task.get_taskid()))
                    content += 'TaskStatus : %s <br/>' % (str(rst[0][0]))
                    content += 'JobID : %s <br/>' % (str(task.get_jobid()))
                    content += 'JobName : %s <br/>' % (str(rst[0][1]))
                    type_name = '简单任务'
                    if task.get_jobtype() == JobType.Complex :
                        type_name = '复杂任务'
                    content += 'JobType : %s <br/>' % (type_name)
            if task.get_jobtype() == JobType.Simple and not task.get_taskid_complex() :
                if email :
                    EmailUtil.send(email_list, 'JOB ERROR!~', content)
            elif task.get_jobtype() == JobType.Complex :
                if email :
                    select_sql = '''
                        SELECT ct.TaskID, cts.Description, cj.RecordID, cj.Name, cj.Type FROM CW_TASK ct
                        INNER JOIN CW_JOB cj ON cj.RecordID = ct.JobID
                        INNER JOIN CW_TASK_STATUS cts ON cts.StatusID = ct.Status
                        WHERE ct.TaskID_Cmplx = '{taskid}'
                    '''.format(taskid=task.get_taskid())
                    count2 , rst2 = conn.select(select_sql)
                    if count2 :
                        content += '<table width="100%">'
                        content += '<tbody>'
                        content += '<tr>'
                        content += '<td>TaskID</td>'
                        content += '<td>TaskStatus</td>'
                        content += '<td>JobID</td>'
                        content += '<td>JobName</td>'
                        content += '<td>JobType</td>'
                        content += '</tr>'
                        for row in rst2 :
                            content += '<tr>'
                            content += '<td>%s</td>' % str(row[0])
                            content += '<td>%s</td>' % str(row[1])
                            content += '<td>%s</td>' % str(row[2])
                            content += '<td>%s</td>' % str(row[3])
                            type_name = '简单任务'
                            if int(row[4]) == JobType.Complex :
                                type_name = '复杂任务'
                            content += '<td>%s</td>' % type_name
                            content += '</tr>'
                        content += '</tbody>'
                        content += '</table>'
                    EmailUtil.send(email_list, 'JOB ERROR!~', content)
            else :
                pass

    def stop(self):
        '''
        Stop this task from running
        
        '''
        logger = self.logger
        if not self.stopped and not self.finished.is_set():
            self.stopped = True
            logger.info("Trying to stop at %s" % datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        if self.process is not None:
            try:
                self.process.terminate()
            except OSError, e:
                logger.warn("%s" % str(e))
            self.process = None
