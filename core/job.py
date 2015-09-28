# coding:utf-8
'''
Created on Feb 14, 2014

@author: magus0219
'''
from timepattern import TimePattern
from util.mysql_handler import get_conn
import re, datetime

class JobType(object):
    '''
    Job type constants
    
    Simple job means one job contains command and time pattern.
    Complex job is a container including other simple jobs within it.Complex job
    has no command but time pattern and the simple jobs wrapped by it MUST has 
    no time pattern.
    '''
    Simple = 1
    Complex = 2


class Job(object):
    '''
    Job Class
    
    This class holds basic information a job should has.Meanwhile,database operations
    about job are placed here.
    '''

    def __init__(self, jobid, time_pattern_str, sshhost, command, retry, depend, jobtype):
        '''
        @param jobid:int, id of job
        @param time_pattern_str:string, time pattern string @see:TimePattern
        @param sshhost:string, host when command use ssh to execute remote shell
        @param command:stirng, shell command which contains reserved words
        @param retry:int, retry times when fails
        @param depend:dict, a dictionary maintains job dependences.
        @param jobtype:JobType, type of job,simple or complex @see:JobType 
        
        Instance of this class first stores basic but important informations about
        a job.Also it provides features like substitute reserved words and generate
        ssh linker.
        Here are some more details:
        *Substitute Reserve Words:command can contain reserved words,TODAY,YESTERDAY
        e.g.These words are represent use specified format:#{ReservedWord}.When
        extract real command from this job.These reserved words will be replaced.
        *SSH linker:To execute remote shell command,we use the capacity of ssh itself,
        ssh host 'cmd1;cmd2'.Once user assign host,we generate this command.
        *Job Dependence:One job could depend on others.When specified one depend rule.
        user should specified the job depend on,and a structure of delta time:deltaDay,
        deltaHour,deltaMinute.Every unit accepted a negative integer if this unit
        is ignored,or TaskRunner will subtract this value by execute time of a task to tell
        if a depended task has been successfully executed. 
        '''
        self._jobid = jobid
        self._sshhost = sshhost
        self._command = command
        self._retry = retry
        self._depend = depend  # KEY:JOBID_DEPEND,VALUE:LIST[DAY,HOUR,MINUTE]
        self._jobtype = jobtype
        if time_pattern_str:  # a simple job within complex job has no time pattern
            self._time_pattern = TimePattern(time_pattern_str)
        else:
            self._time_pattern = None

    def get_jobid(self):
        return self._jobid

    def get_time_pattern(self):
        return self._time_pattern

    def get_command(self):
        return self._command

    def set_command(self, command):
        self._command = command

    def get_sshhost(self):
        return self._sshhost

    def get_retry(self):
        return self._retry

    def get_depend(self):
        return self._depend

    def get_jobtype(self):
        return self._jobtype

    def _substituteReservedWord(self, params = None):
        '''
        Substitute reserved word 
        
        Support TODAY,YESTERDAY now,more reserved words can be extend here.
        '''
#         cmd = self._command
#         pattern = "#\{([a-zA-Z]+)\}"
#         for word in re.findall(pattern, self._command):
#             if word.upper() == "TODAY":
#                 cmd = cmd.replace("#{TODAY}", datetime.datetime.now().strftime("%Y%m%d"))
#             elif word.upper() == "YESTERDAY":
#                 cmd = cmd.replace("#{YESTERDAY}", (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y%m%d"))
#         return cmd

        return self.substituteReservedWord2(command = self._command, params = params)

    @staticmethod
    def substituteReservedWord2(command, params = None):
        pattern = "#\{([\_a-zA-Z\+\-0-9]+)\}"
        cmd = command
        words = re.findall(pattern, command)
        if params :
            for param in params :
                cmd = cmd.replace(param['param_key'], param['param_value'])
#             for index, word in enumerate(words) :
#                 if len(params) - 1 >= index :
#                     cmd = cmd.replace('#{' + word + '}', params[index])
        else :
            for word in words :
                if word.find('-') != -1 :
                    day = int(word[word.find('-') + 1 : ])
                    date = (datetime.datetime.now() - datetime.timedelta(days = day)).strftime("%Y%m%d")
                elif word.find('+') != -1 :
                    day = int(word[word.find('+') + 1 : ])
                    date = (datetime.datetime.now() + datetime.timedelta(days = day)).strftime("%Y%m%d")
                else :
                    date = datetime.datetime.now().strftime("%Y%m%d")
                cmd = cmd.replace('#{' + word + '}', date)
        return cmd

    @staticmethod
    def substituteReservedWord(command, params = None):
        pattern = "#\{([\_a-zA-Z\+\-0-9]+)\}"
        cmd = command
        words = re.findall(pattern, command)
        if params :
            for index, word in enumerate(words) :
                if len(params) - 1 >= index :
                    cmd = cmd.replace('#{' + word + '}', params[index])
        else :
            for word in words :
                if word.find('-') != -1 :
                    day = int(word[word.find('-') + 1 : ])
                    date = (datetime.datetime.now() - datetime.timedelta(days = day)).strftime("%Y%m%d")
                elif word.find('+') != -1 :
                    day = int(word[word.find('+') + 1 : ])
                    date = (datetime.datetime.now() + datetime.timedelta(days = day)).strftime("%Y%m%d")
                else :
                    date = datetime.datetime.now().strftime("%Y%m%d")
                cmd = cmd.replace('#{' + word + '}', date)
        return cmd

    def getCommandToExcute(self):
        '''
        Extract real command by others 
        
        Logic of ssh linker format here
        '''
        return 'ssh %s "%s"' % (self._sshhost, self._substituteReservedWord()) if self._sshhost else self._substituteReservedWord()

    @staticmethod
    def getAll():
        '''
        Get all jobs
        '''
        conn = get_conn()

        # Job will be load only if it and time pattern and is enable.
        sql = '''select recordid,timepattern,sshhost,command,retry,type from CW_JOB where
                    enableflag = 1 and (timepattern is not null and timepattern<>"")'''
        count, rst = conn.select(sql)
        jobs = []
        if count :
            for recordid, timepattern, sshhost, command, retry, jobtype in rst:
                # Get dependence
                sql2 = '''select jobid_depend,deltaday,deltahour,deltaminute from CW_JOB_DEPENDENCE
                        where jobid=%d''' % recordid
                count2, rst2 = conn.select(sql2)
                depend = {}
                if count2 :
                    for jobid_depend, deltaday, deltahour, deltaminute in rst2:
                        depend[jobid_depend] = [deltaday, deltahour, deltaminute]
                jobs.append(Job(recordid, timepattern, sshhost, command, retry, depend, jobtype))
        return jobs

    @staticmethod
    def getByJobID(jobid):
        '''
        Get one job
        '''
        conn = get_conn()

        sql = '''select recordid,timepattern,sshhost,command,retry,type from CW_JOB where
                    recordid=%d''' % (jobid)
        count, rst = conn.select(sql)
        if count == 1:
            recordid, timepattern, sshhost, command, retry, jobtype = rst[0]
            # JobID_Complex is null , simple dependence
            sql2 = '''select jobid_depend,deltaday,deltahour,deltaminute from CW_JOB_DEPENDENCE
                      where jobid = %d
                      and JobID_Complex is null
                      ''' % recordid
            count2, rst2 = conn.select(sql2)
            depend = {}
            if count2 :
                for jobid_depend, deltaday, deltahour, deltaminute in rst2:
                    depend[jobid_depend] = [deltaday, deltahour, deltaminute]
            return Job(recordid, timepattern, sshhost, command, retry, depend, jobtype)
        else:
            return None

if __name__ == '__main__':
    now = datetime.datetime.now()
    d1 = datetime.timedelta(days = 1)
    d2 = datetime.timedelta(hours = 1)
    d = d1 + d2
    print d, (now - d).strftime("%Y-%m-%d %H:%M:%S")

