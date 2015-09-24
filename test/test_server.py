'''
Created on Feb 13, 2014

@author: magus0219
'''
from datetime import datetime
from util.dateutil import DateUtil
import server.server
import unittest

Server = server.server.Server

class ServerTest(unittest.TestCase):
    '''
    Base Test Class for Server
    
    Process fixture of test class
    '''
    engine = None

    def setUp(self):
        self.engine = Server()

    def tearDown(self):
        del self.engine

class ServerInitTestCase(ServerTest):
    '''
    TestCase of Server Initiation
    '''
    
    def testClockTrigger(self):
        '''
        Test normal clock trigger
        
        Test every possible interval value
        '''
        data = [
                [[0, 1], [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]],
                [[1, 2], [1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23]],
                [[2, 3], [2, 5, 8, 11, 14, 17, 20, 23]],
                [[11, 4], [3, 7, 11, 15, 19, 23]],
                [[12, 6], [0, 6, 12, 18]],
                [[13, 8], [5, 13, 21]],
                [[15, 12], [3, 15]],
                [[19, 24], [19]],
                ]
        for param, result in data:
            self.engine._fillclock(*param)
            self.assertEqual(result, self.engine.clocks)
    
    @unittest.expectedFailure
    def testClockTriggerOnInvalidInterval(self):
        '''
        Test normal clock trigger
        
        Test invalid interval
        '''
        try:
            self.engine._fillclock(10, 13)
        except Exception:
            raise
    
    @unittest.expectedFailure
    def testNextScheduleSectionInvalidClock(self):
        '''
        Test get next schedule Section
         
        Test interval clock
        '''
        self.engine._fillclock(11, 4)  # Get clock list [3, 7, 11, 15, 19, 23]
        try:
            self.engine._getNextScheduleSection(DateUtil.datetime('2014-02-14 15:06:34'), 20)
        except Exception:
            raise
    
    @unittest.expectedFailure
    def testNextScheduleSectionOverLongBatch(self):
        '''
        Test get next schedule Section
         
        Test invalid over long interval
        '''
        self.engine._fillclock(11, 4)  # Get clock list [3, 7, 11, 15, 19, 23]
        try:
            self.engine._getNextScheduleSection(DateUtil.datetime('2014-02-14 15:06:34'), 23)
        except Exception:
            raise
            
    def testNextScheduleSection(self):
        '''
        Test get next schedule Section
         
        Test every possible interval value
        '''
        data = [
                ['2014-02-14 15:06:34', 19, '2014-02-14 19:00:00', '2014-02-14 23:00:00'],
                ['2014-02-14 15:06:34', 23, '2014-02-14 23:00:00', '2014-02-15 03:00:00'],
                ['2014-02-14 15:06:34', None, '2014-02-14 15:06:34', '2014-02-14 19:00:00'],
                ['2014-02-14 16:06:34', None, '2014-02-14 16:06:34', '2014-02-14 19:00:00'],
                ['2014-02-14 22:06:34', None, '2014-02-14 22:06:34', '2014-02-14 23:00:00'],
                ['2014-02-14 23:06:34', None, '2014-02-14 23:06:34', '2014-02-15 03:00:00'],
                ['2014-02-15 00:06:34', None, '2014-02-15 00:06:34', '2014-02-15 03:00:00'],
                ]
        for now, starthour, start_time, end_time in data:
            self.engine._fillclock(11, 4)  # Get clock list [3, 7, 11, 15, 19, 23]
            now_time = datetime.strptime(now, "%Y-%m-%d %H:%M:%S")
            rst_start_time, rst_end_time = self.engine._getNextScheduleSection(now_time, starthour)
            self.assertEqual(start_time, rst_start_time.strftime("%Y-%m-%d %H:%M:%S"))
            self.assertEqual(end_time, rst_end_time.strftime("%Y-%m-%d %H:%M:%S"))

if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
