# coding:utf-8
'''
Created on Feb 17, 2014

@author: magus0219
'''

import socket, logging, threading, pickle
from core.command import Command

def recv_until(socket, suffix):
    '''
    Receive message suffixed with specified char
    
    @param socket:socket
    @param suffix:suffix  
    '''
    message = ''
    while not message.endswith(suffix):
        data = socket.recv(4096)
        if not data:
            raise EOFError('Socket closed before we see suffix.')
        message += data
    return message

class SocketServer(object):
    '''
    Socket Server
    
    This socket server is started by clockwork server and only used to invoke methods
    of JobManager
    '''
    def __init__(self, host, port, jobmanager):
        '''
        Constructor
        '''
        self.host = host
        self.port = port
        self.jobmanager = jobmanager
        self.logger = logging.getLogger("Server.SocketThread")
        
    def handleCommand(self, command):
        '''
        Handle one request command of client and return server's answer
        
        @param command:Command to handle
        This function return a Command object which contains result type and detail
        information.
        '''
        cmd = command.cmd
        try:
            if cmd == Command.JOB_ADD:
                jobid = int(command.data)
                self.jobmanager.addJob(jobid)
                return Command(Command.RESULT_SUCCESS, "Successful!")
            elif cmd == Command.JOB_REMOVE:
                jobid = int(command.data)
                self.jobmanager.removeJob(jobid)
                return Command(Command.RESULT_SUCCESS, "Successful!")
            elif cmd == Command.JOB_RELOAD:
                jobid = int(command.data)
                self.jobmanager.reloadJob(jobid)
                return Command(Command.RESULT_SUCCESS, "Successful!")
            elif cmd == Command.TASK_RUN_IMMEDIATELY:
                jobid, params = command.data
                jobid = int(jobid)
                task = self.jobmanager.spawnImmediateTask(jobid=jobid, params=params)
                return Command(Command.RESULT_SUCCESS, "Successful!", task.get_taskid())
            elif cmd == Command.TASK_CANCEL:
                taskid = command.data
                self.jobmanager.cancelTask(taskid)
                return Command(Command.RESULT_SUCCESS, "Successful!")
            elif cmd == Command.STATUS:
                return Command(Command.RESULT_SUCCESS, self.jobmanager.getServerStatus())
        except ValueError, e:
            self.logger.exception(e)
            return Command(Command.RESULT_FAIL, str(e))
        
    def process(self, conn, address):
        '''
        Thread entry where new socket created
        
        '''
        self.logger.info("Accepted a connection from %s" % str(address))
        self.logger.info("Socket connects %s and %s" % (conn.getsockname(), conn.getpeername()))
        
        cmd = pickle.loads(recv_until(conn, '.'))
        self.logger.info("Recieve Command:[%s]" % str(cmd))
        while cmd.cmd != Command.EXIT:
            conn.sendall(pickle.dumps(self.handleCommand(cmd)))
            
            cmd = pickle.loads(recv_until(conn, '.'))
            self.logger.info("Recieve Command:[%s]" % str(cmd))
        self.logger.info("Socket is Over")
        
    def start(self):
        '''
        Start the socket server and enter the main loop
        '''
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((self.host, self.port))
        s.listen(10)
        self.logger.info("SocketThread is Listening at %s:%s" % (self.host, str(self.port)))
        
        while True:
            conn, address = s.accept()
            thread = threading.Thread(target=self.process, args=(conn, address))
            thread.daemon = True
            thread.start()

if __name__ == '__main__':
    server = SocketServer("0.0.0.0", 3993)
    server.start()
            
