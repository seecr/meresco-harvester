## begin license ##
#
# "Meresco Harvester" consists of two subsystems, namely an OAI-harvester and
# a web-control panel.
# "Meresco Harvester" is originally called "Sahara" and was developed for
# SURFnet by:
# Seek You Too B.V. (CQ2) http://www.cq2.nl
#
# Copyright (C) 2006-2007 SURFnet B.V. http://www.surfnet.nl
# Copyright (C) 2007-2008 SURF Foundation. http://www.surf.nl
# Copyright (C) 2007-2011 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2007-2009 Stichting Kennisnet Ict op school. http://www.kennisnetictopschool.nl
# Copyright (C) 2009 Tilburg University http://www.uvt.nl
# Copyright (C) 2010-2012, 2015, 2020 Stichting Kennisnet https://www.kennisnet.nl
# Copyright (C) 2011-2012, 2015, 2017, 2020 Seecr (Seek You Too B.V.) https://seecr.nl
#
# This file is part of "Meresco Harvester"
#
# "Meresco Harvester" is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# "Meresco Harvester" is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with "Meresco Harvester"; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
## end license ##

from sys import exc_info
from time import strftime, gmtime, time
from os import makedirs
from os.path import isfile, join

from meresco.harvester.harvesterlog import HarvesterLog
from meresco.harvester.eventlogger import LOGLINE_RE
from seecr.zulutime import ZuluTime
from seecr.test import SeecrTestCase

class HarvesterLogTest(SeecrTestCase):
    def setUp(self):
        SeecrTestCase.setUp(self)
        self.stateDir = join(self.tempdir, 'state')
        makedirs(self.stateDir)
        self.logDir = join(self.tempdir, 'log')
        makedirs(self.logDir)

    def testSameDate(self):
        logger = HarvesterLog(stateDir=self.stateDir, logDir=self.logDir, name='someuni')
        date=logger._state.getTime()[:10]
        self.assertTrue(logger.isCurrentDay(date))
        self.assertFalse(logger.isCurrentDay('2005-01-02'))

    def testHasWork(self):
        logger = HarvesterLog(stateDir=self.stateDir, logDir=self.logDir, name='someuni')
        self.assertEqual(None, logger._state.from_)
        self.assertEqual(None, logger._state.token)
        self.assertTrue(logger.hasWork())
        logger._state.from_=strftime('%Y-%m-%d', gmtime())
        self.assertTrue(not logger.hasWork())
        logger._state.token='SomeToken'
        self.assertTrue(logger.hasWork())
        logger._state.from_='2005-01-02'
        self.assertTrue(logger.hasWork())
        logger._state.token=None
        self.assertTrue(logger.hasWork())

    def testHasWorkBeforeAndAfterDoingWork(self):
        logger = HarvesterLog(stateDir=self.stateDir, logDir=self.logDir, name= 'name')
        self.assertTrue(logger.hasWork())
        logger.startRepository()
        logger.endRepository(None, logger._state.getZTime().zulu())
        logger.close()
        logger = HarvesterLog(stateDir=self.stateDir, logDir=self.logDir, name= 'name')
        self.assertFalse(logger.hasWork())

    def testHasWorkBeforeAndAfterDoingWorkContinuous(self):
        logger = HarvesterLog(stateDir=self.stateDir, logDir=self.logDir, name= 'name')
        self.assertTrue(logger.hasWork(continuousInterval=60))
        logger.startRepository()
        logger.endRepository(None, logger._state.getZTime().zulu())
        logger.close()
        logger = HarvesterLog(stateDir=self.stateDir, logDir=self.logDir, name= 'name')
        # mock current Time
        logger._state.getZTime = lambda: ZuluTime().add(seconds=-61)
        self.assertFalse(logger.hasWork(continuousInterval=60))
        logger.startRepository()
        logger.endRepository(None, "2000-01-02T03:04:05Z") # ignore what repository says as responseDate
        logger.close()
        logger = HarvesterLog(stateDir=self.stateDir, logDir=self.logDir, name= 'name')
        self.assertFalse(logger.hasWork(continuousInterval=65))
        self.assertTrue(logger.hasWork(continuousInterval=60))

    def testHasWorkWithResumptionTokenContinuous(self):
        logger = HarvesterLog(stateDir=self.stateDir, logDir=self.logDir, name= 'name')
        self.assertTrue(logger.hasWork(continuousInterval=60))
        logger.startRepository()
        logger.endRepository('resumptionToken', logger._state.getZTime().zulu())
        logger.close()
        logger = HarvesterLog(stateDir=self.stateDir, logDir=self.logDir, name= 'name')
        self.assertTrue(logger.hasWork(continuousInterval=60))
        logger.startRepository()
        logger.endRepository('resumptionToken2', logger._state.getZTime().add(seconds=-61).zulu())
        logger.close()

    def testLoggingAlwaysStartsNewline(self):
        "Tests an old situation that when a log was interrupted, it continued on the same line"
        f = open(self.stateDir+'/name.stats','w')
        f.write('Started: 2005-01-02 16:12:56, Harvested/Uploaded/Total: 199/200/1650, Don"crack"')
        f.close()
        logger = HarvesterLog(stateDir=self.stateDir, logDir=self.logDir, name= 'name')
        logger.startRepository()
        logger.close()
        lines = open(self.stateDir+'/name.stats').readlines()
        self.assertEqual(2,len(lines))

    def testLogLine(self):
        logger = HarvesterLog(stateDir=self.stateDir, logDir=self.logDir, name= 'name')
        logger.startRepository()
        logger.notifyHarvestedRecord("name:uploadId1")
        logger.uploadIdentifier("name:uploadId1")
        logger.notifyHarvestedRecord("name:uploadId1")
        logger.deleteIdentifier("name:uploadId1")
        logger.notifyHarvestedRecord("name:uploadId2")
        logger.logInvalidData("name:uploadId2", "Test Exception")
        logger.logIgnoredIdentifierWarning("name:uploadId2")
        logger.endRepository(None, '2012-01-01T09:00:00Z')
        logger.close()
        lines = open(self.stateDir + '/name.stats').readlines()
        eventline = open(self.logDir + '/name.events').readlines()[1].strip()
        invalidUploadId2 = open(self.logDir + '/invalid/name/uploadId2').read()
        #Total is now counted based upon the id's
        self.assertTrue('3/1/1/0, Done:' in lines[0], lines[0])
        date, event, id, comments = LOGLINE_RE.match(eventline).groups()
        self.assertEqual('SUCCES', event.strip())
        self.assertEqual('name', id)
        self.assertEqual('Harvested/Uploaded/Deleted/Total: 3/1/1/0, ResumptionToken: None', comments)
        self.assertEqual('Test Exception', invalidUploadId2)

    def testLogLineError(self):
        logger = HarvesterLog(stateDir=self.stateDir, logDir=self.logDir, name='name')
        logger.startRepository()
        try:
            logger.notifyHarvestedRecord("name:uploadId1")
            logger.uploadIdentifier("name:uploadId1")
            logger.notifyHarvestedRecord("name:uploadId2")
            raise Exception('FATAL')
        except:
            exType, exValue, exTb = exc_info()
            logger.endWithException(exType, exValue, exTb)
        logger.close()
        lines = open(self.stateDir+'/name.stats').readlines()
        eventline = open(self.logDir+'/name.events').readlines()[0].strip()
        #Total is now counted based upon the id's
        self.assertTrue('2/1/0/1, Error: ' in lines[0], lines[0])
        date,event,id,comments = LOGLINE_RE.match(eventline).groups()
        self.assertEqual('ERROR', event.strip())
        self.assertEqual('name', id)
        self.assertTrue(comments.startswith('Traceback (most recent call last):|File "'))
        self.assertTrue('harvesterlogtest.py", line ' in comments)
        self.assertTrue(comments.endswith(', in testLogLineError raise Exception(\'FATAL\')|Exception: FATAL'))

    def testLogWithoutDoubleIDs(self):
        f = open(self.stateDir+'/name.ids','w')
        f.writelines(['id:1\n','id:2\n','id:1\n'])
        f.close()
        logger = HarvesterLog(stateDir=self.stateDir, logDir=self.logDir, name= 'name')
        logger.startRepository()
        self.assertEqual(2,logger.totalIds())
        logger.uploadIdentifier('id:3')
        self.assertEqual(3,logger.totalIds())
        logger.uploadIdentifier('id:3')
        logger.uploadIdentifier('id:2')
        self.assertEqual(3,logger.totalIds())

    def testLogIgnoredIdentifierWarning(self):
        logger = HarvesterLog(stateDir=self.stateDir, logDir=self.logDir, name='name')
        logger.startRepository()
        logger.notifyHarvestedRecord('repoid:oai:bla/bla')
        logger.logInvalidData('repoid:oai:bla/bla', 'bla/bla')
        self.assertEqual('', open(self.logDir + '/name.events').read())
        logger.logIgnoredIdentifierWarning('repoid:oai:bla/bla')
        self.assertTrue(open(self.logDir + '/name.events').read().endswith("\tWARNING\t[repoid:oai:bla/bla]\tIGNORED\n"))
        self.assertEqual(1, logger.totalInvalidIds())

        logger.notifyHarvestedRecord('repoid:oai:bla/bla')
        self.assertEqual(0, logger.totalInvalidIds())
        logger.uploadIdentifier('repoid:oai:bla/bla')
        self.assertEqual(1, logger.totalIds())

    def testLogInvalidData(self):
        logger = HarvesterLog(stateDir=self.stateDir, logDir=self.logDir, name='name')
        logger.startRepository()
        logger.notifyHarvestedRecord('repo/id:oai:bla/bla')
        logger.logInvalidData('repo/id:oai:bla/bla', "Error")
        self.assertEqual(1, logger.totalInvalidIds())
        expectedFile = self.logDir + '/invalid/repo%2Fid/oai:bla%2Fbla'
        self.assertEqual("Error", open(expectedFile).read())
        logger.notifyHarvestedRecord('repo/id:oai:bla/bla')
        self.assertEqual(0, logger.totalInvalidIds())
        self.assertFalse(isfile(expectedFile))

    def testInvalidIDs(self):
        logger = HarvesterLog(stateDir=self.stateDir, logDir=self.logDir, name='name')
        logger.startRepository()
        logger.notifyHarvestedRecord('id:1')
        logger.logInvalidData('id:1', 'exception message')
        logger.notifyHarvestedRecord('id:2')
        logger.logInvalidData('id:2', 'exception message')
        self.assertEqual(['id:1', 'id:2'], logger.invalidIds())

    def testClearInvalidData(self):
        logger = HarvesterLog(stateDir=self.stateDir, logDir=self.logDir, name='name')
        logger.startRepository()
        logger.notifyHarvestedRecord('repoid:oai:bla/bla')
        logger.logInvalidData('repoid:oai:bla/bla', "Error")
        self.assertTrue(isfile(self.logDir + '/invalid/repoid/oai:bla%2Fbla'))
        logger.notifyHarvestedRecord('repoid:recordid')
        logger.logInvalidData('repoid:recordid', "Error")
        self.assertTrue(isfile(self.logDir + '/invalid/repoid/recordid'))
        logger.notifyHarvestedRecord('repo2:1')
        logger.logInvalidData('repo2:1', "Error")
        self.assertTrue(isfile(self.logDir + '/invalid/repo2/1'))
        self.assertEqual(['repoid:oai:bla/bla', 'repoid:recordid', 'repo2:1'], logger.invalidIds())
        logger.clearInvalidData('repoid')
        self.assertEqual(['repo2:1'], logger.invalidIds())
        self.assertFalse(isfile(self.logDir + '/invalid/repoid/oai:bla%2Fbla'))
        self.assertFalse(isfile(self.logDir + '/invalid/repoid/recordid'))
        self.assertTrue(isfile(self.logDir + '/invalid/repo2/1'))

    def testMarkDeleted(self):
        f = open(self.stateDir+'/name.stats','w')
        f.write('Started: 2005-01-02 16:12:56, Harvested/Uploaded/Total: 199/200/1650, Done: 2005-04-22 11:48:30, ResumptionToken: resumption')
        f.close()
        logger = HarvesterLog(stateDir=self.stateDir, logDir=self.logDir, name='name')
        self.assertEqual('resumption', logger._state.token)
        logger.markDeleted()
        logger.close()
        logger = HarvesterLog(stateDir=self.stateDir, logDir=self.logDir, name='name')
        self.assertEqual(None, logger._state.token)
        self.assertEqual(None, logger._state.from_)
        self.assertEqual(0, logger.totalIds())

