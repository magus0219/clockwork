# coding:utf-8
class Command(object):
    '''
    Class holding command and binding data
    
    This class holds all command constants
    '''
    RESULT_SUCCESS = -1
    RESULT_FAIL = -2
    EXIT = 0
    JOB_ADD = 1
    JOB_REMOVE = 2
    JOB_RELOAD = 3
    TASK_RUN_IMMEDIATELY = 4
    TASK_CANCEL = 5
    STATUS = 6
    
    @staticmethod
    def printCommandList():
        print 'Command            Description\n' + \
              'add  or a          Add one job for server to schedule\n' + \
              'delete  or d       Delete one job and waiting tasks spawned by this job from server\n' + \
              'reload  or r       Reload one job and schedule it\n' + \
              'runtask or rt      Run task immediately\n' + \
              'canceltask or ct   Cancel task which is running\n' + \
              'status or s        Show status of server\n' + \
              'help or h          Show command list\n' + \
              'exit or e          Exit\n'
    
    def __init__(self, cmd, msg, data=None):
        self.cmd = cmd
        self.msg = msg
        self.data = data
        
        
    def __str__(self):
        return 'Cmd:%s,MSG:%s,Data:%s' % (self.cmd, self.msg, str(self.data))
