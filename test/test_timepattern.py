'''
Created on Feb 17, 2014

@author: magus0219
'''
import unittest
from core.timepattern import TimePattern

class TimePatternTest(unittest.TestCase):

    def testValidPattern(self):
        TimePattern("* * * * \t*")
        TimePattern("* * * * \t*")
        TimePattern("* *    23 * \t*")
        TimePattern("*/2 13    23 * \t*")
        
    @unittest.expectedFailure  
    def testUnvalidPattern(self):
        TimePattern("* sdf * * \t*")
        
    @unittest.expectedFailure  
    def testUnvalidPattern2(self):
        TimePattern("* */dsf * * \t*")
        
    @unittest.expectedFailure  
    def testUnvalidPattern3(self):
        TimePattern("* 3/* * * \t*")
        
    @unittest.expectedFailure  
    def testUnvalidPattern4(self):
        TimePattern("* * * * \t* *")
        
    def testTimePatternInit(self):
        time_pattern = TimePattern("* */2 323 \t * 72")
        self.assertEqual('*', time_pattern.MINITE)
        self.assertEqual('*/2', time_pattern.HOUR)
        self.assertEqual('323', time_pattern.DAY)
        self.assertEqual('*', time_pattern.MONTH)
        self.assertEqual('72', time_pattern.WEEKDAY)
        
    def testTimePatternStr(self):
        time_pattern = TimePattern("* */2 323 \t * 72")
        self.assertEqual("* */2 323 * 72", str(time_pattern))

if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testUnvaidValue']
    unittest.main()
