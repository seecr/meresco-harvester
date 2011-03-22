## begin license ##
#
#    "Meresco Harvester" consists of two subsystems, namely an OAI-harvester and
#    a web-control panel.
#    "Meresco Harvester" is originally called "Sahara" and was developed for
#    SURFnet by:
#        Seek You Too B.V. (CQ2) http://www.cq2.nl
#    Copyright (C) 2006-2007 SURFnet B.V. http://www.surfnet.nl
#    Copyright (C) 2007-2008 SURF Foundation. http://www.surf.nl
#    Copyright (C) 2007-2009 Seek You Too (CQ2) http://www.cq2.nl
#    Copyright (C) 2007-2009 Stichting Kennisnet Ict op school.
#       http://www.kennisnetictopschool.nl
#    Copyright (C) 2009 Tilburg University http://www.uvt.nl
#
#    This file is part of "Meresco Harvester"
#
#    "Meresco Harvester" is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    "Meresco Harvester" is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with "Meresco Harvester"; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
## end license ##

import unittest
import datetime, tempfile, os, shutil
from meresco.harvester.throughputanalyser import parseToTime, ThroughputAnalyser, ThroughputReport

class ThroughputAnalyserTest(unittest.TestCase):
    
    def setUp(self):
        self.mockAnalyseRepository_arguments = []
        self.testdir = os.path.join(tempfile.gettempdir(), 'throughputanalysertest')
        not os.path.isdir(self.testdir) and os.makedirs(self.testdir)
    
    def tearDown(self):
        shutil.rmtree(self.testdir)
    
    def testParseToTime(self):
        timeString = "1999-12-03 12:34:35.123"
        date = parseToTime(timeString)
        self.assertEquals((1999,12,3,12,34,35,123000), (date.year,date.month,date.day, date.hour, date.minute, date.second, date.microsecond))
        
        date = parseToTime("2006-08-04 10:40:50.644")
        self.assertEquals((2006,8,4,10,40,50,644000), (date.year,date.month,date.day, date.hour, date.minute, date.second, date.microsecond))
        
    def testParseToTimeDiff(self):
        date1 = parseToTime("1999-12-03 12:34:35.123")
        date2 = parseToTime("1999-12-03 12:34:36.423")
        delta = date2 - date1
        self.assertEquals(1.3, delta.seconds + delta.microseconds/1000000.0)
        
        
    def testAnalyse(self):
        t = ThroughputAnalyser(eventpath = self.testdir)
        t._analyseRepository = self.mockAnalyseRepository
        
        report = t.analyse(['repo1','repo2'], '2006-08-31')
        
        self.assertEquals(1000, report.records)
        self.assertEquals(2000.0, report.seconds)
        self.assertEquals(['repo1', 'repo2'], self.mockAnalyseRepository_arguments)
        
    def testAnalyseNothing(self):
        t = ThroughputAnalyser(eventpath = self.testdir)
        t._analyseRepository = self.mockAnalyseRepository
        
        report = t.analyse([], '2006-08-31')
        
        self.assertEquals(0, report.records)
        self.assertEquals(0.0, report.seconds)
        self.assertEquals('-' , report.recordsPerSecond())
        self.assertEquals('-' , report.recordsPerDay())

        
    def testAnalyseRepository(self):
        r = open(os.path.join(self.testdir, 'repo1.events'), 'w')
        try:
            r.write("""
[2006-08-30 00:00:15.500]	ENDHARVEST	[repo1]	
[2006-08-30 01:00:00.000]	STARTHARVEST	[repo1]	Uploader connected ...
[2006-08-30 01:00:10.000]	SUCCES	[repo1]	Harvested/Uploaded/Deleted/Total: 200/200/0/1000, ResumptionToken: r1
[2006-08-30 01:00:15.500]	ENDHARVEST	[repo1]	
[2006-08-31 01:00:00.000]	STARTHARVEST	[repo1]	Uploader connected ...
[2006-08-31 01:00:10.000]	SUCCES	[repo1]	Harvested/Uploaded/Deleted/Total: 200/200/0/1200, ResumptionToken: r1
[2006-08-31 01:00:15.500]	ENDHARVEST	[repo1]	
[2006-08-31 02:00:00.000]	STARTHARVEST	[repo1]	Uploader connected ...
[2006-08-31 02:00:10.000]	SUCCES	[repo1]	Harvested/Uploaded/Deleted/Total: 200/200/0/1400, ResumptionToken: r2
[2006-08-31 02:00:25.500]	ENDHARVEST	[repo1]	
[2006-08-31 03:00:00.000]	STARTHARVEST	[repo1]	Uploader connected ...
[2006-08-31 03:00:10.000]	SUCCES	[repo1]	Harvested/Uploaded/Deleted/Total: 200/200/0/1600, ResumptionToken: r3
[2006-08-31 03:00:35.500]	ENDHARVEST	[repo1]	
""")
        finally:
            r.close()
        t = ThroughputAnalyser(eventpath = self.testdir)
        records, seconds = t._analyseRepository('repo1', '2006-08-31')
        self.assertEquals(600, records)
        self.assertEquals(76.5, seconds)
        
    def testAnalyseNonExistingRepository(self):
        t = ThroughputAnalyser(eventpath = self.testdir)
        records, seconds = t._analyseRepository('repository', '2006-08-31')
        self.assertEquals(0, records)
        self.assertEquals(0.0, seconds)
            
    def testReportOnEmptyEventsFile(self):
        t = ThroughputAnalyser(eventpath = self.testdir)
        records, seconds = t._analyseRepository('repo1', '2006-08-31')
        self.assertEquals(0, records)
        self.assertEquals(0, seconds)

    def testReport(self):
        report = ThroughputReport()
        report.add(100000,10000.0)
        self.assertEquals('10.00', report.recordsPerSecond())
        self.assertEquals('864000', report.recordsPerDay())
        self.assertEquals("02:46:40", report.hmsString())
        
    #Mock    self shunt
    def mockAnalyseRepository(self, repositoryName, dateSince):
        self.mockAnalyseRepository_arguments.append(repositoryName)
        return 500, 1000.0
