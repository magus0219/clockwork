'''
Created on Feb 13, 2014

@author: magus0219
'''
from core.job import Job
from core.jobmanager import JobManager
from util.dateutil import DateUtil
import unittest


class JobManagerTest(unittest.TestCase):
    '''
    TestCase of Job Manager
    '''
    
    def setUp(self):
        self.jobmanager = JobManager()

    def tearDown(self):
        del self.jobmanager
        
class IndexJobTest(JobManagerTest):
    
    def testIndeJobs(self):
        '''
        Test indexJobs
        
        '''
        self.jobmanager.loadJob(Job(1, "* 1 * * *", "sdfs", 5))
        self.jobmanager.loadJob(Job(2, "* 1 * * *", "sdfs", 5))
        self.jobmanager.loadJob(Job(3, "* 2 * * *", "sdfs", 5))
        self.jobmanager.loadJob(Job(4, "* */2 * * *", "sdfs", 5))
        self.jobmanager.loadJob(Job(5, "* * * * *", "sdfs", 5))
        self.jobmanager.indexJobs()
        
        self.assertEqual(3, len(self.jobmanager.hour_index[2]))
        self.assertEqual(3, len(self.jobmanager.hour_index[1]))
    
class SpawnThreadsTest(JobManagerTest):
    
    def testSpawnThreads(self):
        self.jobmanager.loadJob(Job(1, "*/2 * * * *", "echo haha", 5))
        self.jobmanager.indexJobs()
        
        self.assertEqual(1, len(self.jobmanager.hour_index[15]))
        
        threads = self.jobmanager.spwanTasks(DateUtil.datetime("2014-02-18 15:30:00"), DateUtil.datetime("2014-02-18 16:00:00"))
        self.assertEqual(15, len(threads))
        
        threads = self.jobmanager.spwanTasks(DateUtil.datetime("2014-02-18 15:30:23"), DateUtil.datetime("2014-02-18 16:00:00"))
        self.assertEqual(14, len(threads))
        
    def testSpawnThreads2(self):
        self.jobmanager.loadJob(Job(1, "* * * * *", "echo haha", 5))
        self.jobmanager.indexJobs()
        
        threads = self.jobmanager.spwanTasks(DateUtil.datetime("2014-02-19 15:00:00"), DateUtil.datetime("2014-02-19 16:00:00"))
        self.assertEqual(60, len(threads))
        print threads[0].args[0].get_exc_time()
        
if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
