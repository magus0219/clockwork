'''
Created on Feb 17, 2014

@author: magus0219
'''
import unittest,datetime
from util.dateutil import DateUtil
from core.timematcher import TimeMatcher
from core.timepattern import TimePattern

class TimeMatcherTest(unittest.TestCase):

    @unittest.expectedFailure
    def testUnvaidValueNotInt(self):
        TimeMatcher.matchOneUnit("*", "dsf")
        
    @unittest.expectedFailure
    def testUnvaidValueNegitiveInt(self):
        TimeMatcher.matchOneUnit("*", -2)
        
    @unittest.expectedFailure
    def testUnvaidValuePattern1(self):
        TimeMatcher.matchOneUnit("fjf/2", 1)
        
    @unittest.expectedFailure
    def testUnvaidValuePattern2(self):
        TimeMatcher.matchOneUnit("sdf", 1)
        
    @unittest.expectedFailure
    def testUnvaidValuePattern3(self):
        TimeMatcher.matchOneUnit("*/sd", 1)
        
    def testMatchOnePattern(self):
        self.assertEqual(True, TimeMatcher.matchOneUnit("*", 1))
        self.assertEqual(True, TimeMatcher.matchOneUnit("*", 24))
        
        self.assertEqual(True, TimeMatcher.matchOneUnit("*/2", 22))
        self.assertEqual(False, TimeMatcher.matchOneUnit("*/2", 13))
        
        self.assertEqual(True, TimeMatcher.matchOneUnit("*/5", 15))
        self.assertEqual(False, TimeMatcher.matchOneUnit("*/5", 13))
        
        self.assertEqual(True, TimeMatcher.matchOneUnit("23", 23))
        self.assertEqual(False, TimeMatcher.matchOneUnit("23", 13))
        
    def testMatchTimePattern(self):
        self.assertEqual(True, TimeMatcher.matchTimePattern(TimePattern("* * * * *"), 
                                                            DateUtil.datetime("2014-02-17 20:28:35")))
        self.assertEqual(True, TimeMatcher.matchTimePattern(TimePattern("28 * * * *"), 
                                                            DateUtil.datetime("2014-02-17 20:28:35")))
        self.assertEqual(True, TimeMatcher.matchTimePattern(TimePattern("* 20 * * *"), 
                                                            DateUtil.datetime("2014-02-17 20:28:35")))
        self.assertEqual(True, TimeMatcher.matchTimePattern(TimePattern("* * 17 * *"), 
                                                            DateUtil.datetime("2014-02-17 20:28:35")))
        self.assertEqual(True, TimeMatcher.matchTimePattern(TimePattern("* * * 2 *"), 
                                                            DateUtil.datetime("2014-02-17 20:28:35")))
        self.assertEqual(True, TimeMatcher.matchTimePattern(TimePattern("* * * * 1"), 
                                                            DateUtil.datetime("2014-02-17 20:28:35")))
        self.assertEqual(True, TimeMatcher.matchTimePattern(TimePattern("28 20 17 2 1"), 
                                                            DateUtil.datetime("2014-02-17 20:28:35")))
        self.assertEqual(True, TimeMatcher.matchTimePattern(TimePattern("*/2 * * * *"), 
                                                            DateUtil.datetime("2014-02-17 20:28:35")))
        
        self.assertEqual(False, TimeMatcher.matchTimePattern(TimePattern("*/3 * * * *"), 
                                                            DateUtil.datetime("2014-02-17 20:28:35")))

if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testUnvaidValue']
    unittest.main()
