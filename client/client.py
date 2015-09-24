# coding:utf-8
'''
Created on Feb 20, 2014

@author: magus0219
'''
import socket, pickle, sys
from core.command import Command

def recv_until(socket, suffix):
    message = ''
    while not message.endswith(suffix):
        data = socket.recv(4096)
        if not data:
            raise EOFError('Socket closed before we see suffix.')
        message += data
    return message

class UsingType(object):
    Module = 1
    CommandLine = 2

class SocketClient(object):
    '''
    Client communicate with server to trigger specified operations
    '''

    def __init__(self, host, port, using = UsingType.Module):
        '''
        Constructor
        '''
        self.host = host
        self.port = port
        self.using = using
        self.socket = None

    #===========================================================================
    # API for modules which import client to use
    #===========================================================================

    def addJob(self, jobid):
        command = Command(Command.JOB_ADD, "", jobid)
        return self._sendCommand(command)

    def deletaJob(self, jobid):
        command = Command(Command.JOB_REMOVE, "", jobid)
        return self._sendCommand(command)

    def queryStatus(self, jobid):
        command = Command(Command.STATUS, "", jobid)
        return self._sendCommand(command)

    def reloadJob(self, jobid):
        command = Command(Command.JOB_RELOAD, "", jobid)
        return self._sendCommand(command)

    def runTask(self, jobid, params):
        '''
        params : [{'param_key' : '#{today-1}', 'param_value' : '20140526'}]
        '''
        command = Command(Command.TASK_RUN_IMMEDIATELY, "", [jobid, params])
        return self._sendCommand(command)

    def cancelTask(self, taskid):
        command = Command(Command.TASK_CANCEL, "", taskid)
        return self._sendCommand(command)

    #===========================================================================
    # Input handlers
    #===========================================================================
    def _input_jobid(self):
        jobid = None
        try:
            jobid = int(raw_input("Input JobID:"))
        except:
            print 'Unvalid Input'
        return jobid

    def _input_shellcmd(self):
        shellcmd = raw_input("Input ShellCmd:")
        return shellcmd

    def _input_taskid(self):
        taskid = raw_input("Input TaskID:")
        return taskid

    #===========================================================================
    # Core methods
    #===========================================================================

    def _sendCommand(self, command):
        '''
        Send command and recieve result which is a instance of Commmand
        
        @param command:Command,command to send
        Information sent and received are both wrapped as Command 
        '''
        # send command
        self.socket.sendall(pickle.dumps(command))
        cmd = pickle.loads(recv_until(self.socket, '.'))
        return cmd

    def _handler(self, cmd):
        '''
        Command dispather
        
        @param cmd:string,input by terminal user
        '''
        if cmd in ('help', 'h'):
            Command.printCommandList()
        elif cmd in ('add', 'a'):
            jobid = self._input_jobid()
            if jobid:
                command = Command(Command.JOB_ADD, "", jobid)
                print self._sendCommand(command).msg
        elif cmd in ('delete', 'd'):
            jobid = self._input_jobid()
            if jobid:
                command = Command(Command.JOB_REMOVE, "", jobid)
                print self._sendCommand(command).msg
        elif cmd in ('reload', 'r'):
            jobid = self._input_jobid()
            if jobid:
                command = Command(Command.JOB_RELOAD, "", jobid)
                print self._sendCommand(command).msg
        elif cmd in ('runtask', 'rt'):
            jobid = self._input_jobid()
            if jobid:
                shellcmd = self._input_shellcmd()
                # TODO : added params UsingType.CommandLine is not modify, is here
                command = Command(Command.TASK_RUN_IMMEDIATELY, "", [jobid, shellcmd])
                print self._sendCommand(command).msg
        elif cmd in ('canceltask', 'ct'):
            taskid = self._input_taskid()
            command = Command(Command.TASK_CANCEL, "", taskid)
            print self._sendCommand(command).msg
        elif cmd in ('status', 's'):
            command = Command(Command.STATUS, "", None)
            print self._sendCommand(command).msg
        else:
            print 'Unvalid Command %s,input again.' % cmd


    def start(self):
        '''
        Entry of client
        
        Using means use type of this client.
        CommandLine: start by command line and loop in command input
        Module: imported by other modules
        '''
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.host, self.port))

        print 'Client has been assigned socket name', self.socket.getsockname()

        if self.using == UsingType.CommandLine:
            cmd = raw_input("Client>").lower()
            while cmd not in ('exit', 'e'):
                self._handler(cmd)
                cmd = raw_input("Client>").lower()
            self.socket.sendall(pickle.dumps(Command(Command.EXIT, None)))

if __name__ == '__main__':
    host = sys.argv[1]
    port = sys.argv[2]
    client = SocketClient(host, int(port), UsingType.CommandLine)
    client.start()


