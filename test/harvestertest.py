## begin license ##
#
#    "Meresco Harvester" consists of two subsystems, namely an OAI-harvester and
#    a web-control panel.
#    "Meresco Harvester" is originally called "Sahara" and was developed for
#    SURFnet by:
#        Seek You Too B.V. (CQ2) http://www.cq2.nl
#    Copyright (C) 2006-2007 SURFnet B.V. http://www.surfnet.nl
#    Copyright (C) 2007-2008 SURF Foundation. http://www.surf.nl
#    Copyright (C) 2007-2011 Seek You Too (CQ2) http://www.cq2.nl
#    Copyright (C) 2007-2009 Stichting Kennisnet Ict op school.
#       http://www.kennisnetictopschool.nl
#    Copyright (C) 2009 Tilburg University http://www.uvt.nl
#    Copyright (C) 2010-2011 Stichting Kennisnet http://www.kennisnet.nl
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

import shelve
import os
import sys
import re
import unittest
from time import sleep, strftime
from shutil import rmtree
from tempfile import mkdtemp
from StringIO import StringIO
from lxml.etree import parse

from cq2utils import CallTrace
from slowfoot.wrappers import wrapp, binderytools

from meresco.harvester.harvester import Harvester
from meresco.harvester.harvesterlog import HarvesterLog
from meresco.harvester.state import getHarvestedUploadedRecords
from meresco.harvester.oairequest import OaiRequest
from meresco.harvester.virtualuploader import InvalidDataException, TooMuchInvalidDataException
from meresco.harvester.mapping import Mapping, DEFAULT_CODE, Upload, parse_xml
from meresco.harvester import namespaces

from mockoairequest import MockOaiRequest


class DeletedRecordHeader(object):
    def isDeleted(self):
        return True
    def identifier(self):
        return 'mockid'

class _MockRepository(object):
    def __init__(self, id, baseurl, set, repositoryGroupId, outer):
        self.repositoryGroupId=repositoryGroupId
        self.id = id
        self.baseurl = baseurl
        self.set = set
        self.metadataPrefix = 'oai_dc'
        self.targetId= outer.mockssetarget
        self.createUploader = outer.createUploader

    def mapping(self):
        m = Mapping('id')
        m.name = self.repositoryGroupId
        m.code = DEFAULT_CODE
        return m

class HarvesterTest(unittest.TestCase):
    def setUp(self):
        self.sendCalled=0
        self.sendReturn=None
        self.sendException = None
        self.upload = None
        self.sendParts=[]
        self.sendId=[]
        self.listRecordsSet = None
        self.listRecordsToken = None
        self.startCalled=0
        self.stopCalled=0
        self.logDir = self.stateDir = mkdtemp()

    def tearDown(self):
        rmtree(self.logDir)

    def createLogger(self):
        self.logger=HarvesterLog(stateDir=self.stateDir, logDir=self.logDir, name='tud')
        return self.logger

    def createServer(self, url='http://repository.tudelft.nl/oai'):
        return OaiRequest(url)

    def testCreateHarvester(self):
        harvester = self.createHarvesterWithMockUploader('tud')
        self.assertEquals((0,0),(self.startCalled,self.stopCalled))
        harvester.harvest()
        self.assertEquals((1,1),(self.startCalled,self.stopCalled))
        harvester = self.createHarvesterWithMockUploader('eur')
        self.assertEquals((1,1),(self.startCalled,self.stopCalled))
        harvester.harvest()
        self.assertEquals((2,2),(self.startCalled,self.stopCalled))

    def testDoUpload(self):
        harvester = self.createHarvesterWithMockUploader('tud')
        harvester.harvest()

        self.assertEqual(3, self.sendCalled)
        self.assertEqual('tud:oai:tudelft.nl:007193', self.sendId[2])
        record = parse(StringIO(self.sendParts[2]['record']))
        subjects = record.xpath('/oai:record/oai:metadata/oai_dc:dc/dc:subject/text()', namespaces=namespaces)
        self.assertEqual(['quantitative electron microscopy', 'statistical experimental design', 'parameter estimation'], subjects)
        self.assertEquals('ResumptionToken: TestToken', file(os.path.join(self.stateDir, 'tud.stats')).read()[-27:-1])

    def testLogIDsForRemoval(self):
        harvester = self.createHarvesterWithMockUploader('tud')
        harvester.harvest()
        idsfile = open(self.stateDir+'/tud.ids')
        try:
            self.assertEquals('tud:oai:tudelft.nl:007087',idsfile.readline().strip())
            self.assertEquals('tud:oai:tudelft.nl:007192',idsfile.readline().strip())
            self.assertEquals('tud:oai:tudelft.nl:007193',idsfile.readline().strip())
        finally:
            idsfile.close()

    def createHarvesterWithMockUploader(self, name, set=None, mockRequest = None):
        self.logger=HarvesterLog(stateDir=self.stateDir, logDir=self.logDir, name=name)
        harvester = Harvester(self.MockRepository(name, set), stateDir=self.stateDir, logDir=self.logDir, eventLogger=self.logger.eventLogger())
        harvester.addObserver(mockRequest or MockOaiRequest('mocktud'))
        harvester.addObserver(self.logger)
        return harvester

    def testSimpleStat(self):
        harvester = self.createHarvesterWithMockUploader('tud')
        self.sendReturn = '12341234-@tompoes-1234123.134112'
        harvester.harvest()
        self.assert_(os.path.isfile(self.stateDir+'/tud.stats'))
        stats = open(self.stateDir + '/tud.stats').readline().strip().split(',')
        year = strftime('%Y')
        self.assertEquals('Started: %s-'%year, stats[0][:14])
        self.assertEquals(' Harvested/Uploaded/Deleted/Total: 3/3/0/3', stats[1])
        self.assertEquals(' Done: %s-'%year, stats[2][:12])

    def testErrorStat(self):
        harvester = self.createHarvesterWithMockUploader('tud')
        self.sendException = Exception('send failed')
        try:
            harvester.harvest()
        except:
            pass
        stats = open(self.stateDir + '/tud.stats').readline().strip().split(',')
        self.assertTrue(stats[2].startswith(' Error: '), stats[2])
        self.assertTrue(stats[2].endswith('send failed'), stats[2])

    def testResumptionTokenLog(self):
        harvester = self.createHarvesterWithMockUploader('tud')
        self.sendReturn = 'true'
        harvester.harvest()
        stats = open(self.stateDir + '/tud.stats').readline().strip().split(',')
        self.assertEquals(' ResumptionToken: TestToken', stats[3])

    def testOtherMetadataPrefix(self):
        self.logger=HarvesterLog(stateDir=self.stateDir, logDir=self.logDir, name='tud')
        repository = self.MockRepository('tud', None)
        repository.metadataPrefix='lom'
        harvester = Harvester(repository, stateDir=self.stateDir, logDir=self.logDir, eventLogger=self.logger.eventLogger())
        harvester.addObserver(MockOaiRequest('mocktud'))
        harvester.addObserver(self.logger)
        harvester.harvest()
        self.assertEquals(['tud:oai:lorenet:147'],self.sendId)

    def testWriteAndSeek(self):
        f = open('test','w')
        f.write('enige info: ')
        pos = f.tell()
        f.write('20000')
        f.seek(pos)
        f.write('12345')
        f.close()
        self.assertEquals('enige info: 12345', open('test','r').readline().strip())
        os.remove('test')

    def testException(self):
        try:
            raise Exception('aap')
            self.fail()
        except:
            self.assertEquals('aap', str(sys.exc_value))
            self.assertTrue('exceptions.Exception' in str(sys.exc_type), str(sys.exc_type))

    def testIncrementalHarvest(self):
        self.mockRepository = MockOaiRequest('mocktud')
        f = open(self.stateDir + '/tud.stats', 'w')
        f.write(' Started: 1999-12-01 16:37:41, Harvested/Uploaded/Total: 56/23/113, Done: 2004-12-31 16:39:15\n')
        f.close();
        f = open(self.stateDir + '/tud.ids', 'w')
        for i in range(113): f.write('oai:tudfakeid:%05i\n'%i)
        f.close()
        repository = self.MockRepository3('tud' ,'http://repository.tudelft.nl/oai', None, 'tud')
        logger = self.createLogger()
        h = Harvester(repository, stateDir=self.stateDir, logDir=self.logDir, eventLogger=logger.eventLogger())
        h.addObserver(self)
        h.addObserver(logger)
        self.listRecordsFrom = None
        self.sendReturn = '127.0.0.1-123@localhost-12312-12312424123'
        h.harvest()
        self.assertEquals('1999-12-01', self.listRecordsFrom)
        lines = open(self.stateDir + '/tud.stats').readlines()
        self.assertEquals(2, len(lines))
        self.assertEquals(('3', '3', '0', '116'), getHarvestedUploadedRecords(lines[1]))

    def testNotIncrementalInCaseOfError(self):
        self.mockRepository = MockOaiRequest('mocktud')
        f = open(self.stateDir + '/tud.stats', 'w')
        f.write('Started: 1998-12-01 16:37:41, Harvested/Uploaded/Total: 113/113/113, Done: 2004-12-31 16:39:15\n')
        f.write('Started: 1999-12-01 16:37:41, Harvested/Uploaded/Total: 113/113/113, Error: XXX\n')
        f.close();
        repository = self.MockRepository3('tud' ,'http://repository.tudelft.nl/oai', None, 'tud')
        logger = self.createLogger()
        h = Harvester(repository, stateDir=self.stateDir, logDir=self.logDir, eventLogger=logger.eventLogger())
        h.addObserver(self)
        h.addObserver(logger)
        self.listRecordsFrom = None
        h.harvest()
        self.assertEquals('1998-12-01', self.listRecordsFrom)

    def testOnlyErrorInLogFile(self):
        self.mockRepository = MockOaiRequest('mocktud')
        f = open(self.stateDir + '/tud.stats', 'w')
        f.write('Started: 1998-12-01 16:37:41, Harvested/Uploaded/Total: 113/113/113, Error:\n')
        f.write('Started: 1999-12-01 16:37:41, Harvested/Uploaded/Total: 113/113/113, Error: XXX\n')
        f.close();
        repository = self.MockRepository3('tud' ,'http://repository.tudelft.nl/oai', None, 'tud')
        logger = self.createLogger()
        h = Harvester(repository, stateDir=self.stateDir, logDir=self.logDir, eventLogger=logger.eventLogger())
        h.addObserver(self)
        h.addObserver(logger)
        self.listRecordsFrom = None
        h.harvest()
        self.assertEquals('aap', self.listRecordsFrom)

    def testResumptionToken(self):
        self.mockRepository = MockOaiRequest('mocktud')
        f = open(self.stateDir + '/tud.stats', 'w')
        f.write('Started: 1999-12-01 16:37:41, Harvested/Uploaded/Total: 113/113/113, Done: 2004-12-31 16:39:15, ResumptionToken: ga+hier+verder\n')
        f.close();
        repository = self.MockRepository3('tud' ,'http://repository.tudelft.nl/oai', None, 'tud')
        logger = self.createLogger()
        h = Harvester(repository, stateDir=self.stateDir, logDir=self.logDir, eventLogger=logger.eventLogger())
        h.addObserver(self)
        h.addObserver(logger)
        self.listRecordsToken = None
        h.harvest()
        self.assertEquals('ga+hier+verder', self.listRecordsToken)

    def testHarvestSet(self):
        self.mockRepository = MockOaiRequest('mocktud')
        harvester = self.createHarvesterWithMockUploader('um', set='withfulltext:yes', mockRequest = self)
        harvester.harvest()
        self.assertEquals('withfulltext:yes', self.listRecordsSet)

    def mockHarvest(self, repository, logger, uploader):
        if not hasattr(self, 'mockHarvestArgs'):
            self.mockHarvestArgs=[]
        self.mockHarvestArgs.append({'name':repository.id,'baseurl':repository.baseurl,'set':repository.set,'repositoryGroupId':repository.repositoryGroupId})

    def testNoDateHarvester(self):
        "runs a test with xml containing no dates"
        harvester = self.createHarvesterWithMockUploader('tud')
        self.logger._state.token='NoDateToken'
        harvester.harvest()

    def testNothingInRepository(self):
        harvester = self.createHarvesterWithMockUploader('tud')
        self.logger._state.token='EmptyListToken'
        harvester.harvest()
        lines = open(self.stateDir+'/tud.stats').readlines()
        self.assert_('Harvested/Uploaded/Deleted/Total: 0/0/0/0' in lines[0])

    def testNoDcIdentifier(self):
        harvester = self.createHarvesterWithMockUploader('tud')
        self.logger.token='DcIdentifierNo'
        harvester.harvest()
        lines = open(self.stateDir+'/tud.stats').readlines()

    def testUploadRecord(self):
        harvester = self.createHarvesterWithMockUploader('tud')
        record = parse_xml("""<record><header><identifier>mockid</identifier></header><metadata><dc><title>mocktitle</title></dc></metadata><about/></record>""").record
        upload = Upload(record=record)
        upload.id = 'tud:mockid'
        harvester._mapper.createUpload = lambda repository,record,logger: upload
        harvester.uploadRecord(record)
        self.assertEquals(['tud:mockid'], self.sendId)
        self.assertFalse(hasattr(self, 'delete_id'))

    def testSkippedRecord(self):
        harvester = self.createHarvesterWithMockUploader('tud')
        record = parse_xml("""<record><header><identifier>mockid</identifier></header><metadata><dc><title>mocktitle</title></dc></metadata><about/></record>""").record
        upload = Upload(record=record)
        upload.id = "tud:mockid"
        upload.skip = True
        harvester._mapper.createUpload = lambda repository,record,logger: upload
        harvester.uploadRecord(record)
        self.assertEquals([], self.sendId)
        self.assertFalse(hasattr(self, 'delete_id'))

    def testDelete(self):
        harvester = self.createHarvesterWithMockUploader('tud')
        record = parse_xml("""<record><header status="deleted"><identifier>mockid</identifier></header></record>""").record
        harvester.uploadRecord(record)
        self.assertEquals([], self.sendId)
        self.assertEquals('tud:mockid', self.delete_id)

    def testDcIdentifierTake2(self):
        self.sendFulltexturl=None
        harvester = self.createHarvesterWithMockUploader('tud')
        self.logger.token='DcIdentifierHttp2'
        harvester.harvest()
        lines = open(self.stateDir+'/tud.stats').readlines()

    def testMapping(self):
        harvester = self.createHarvesterWithMockUploader('tud')
        self.assertEquals('insttud',harvester._mapper.name)
        harvester = self.createHarvesterWithMockUploader('other')
        self.assertEquals('instother',harvester._mapper.name)

    def xtestHarvestNottoolong(self):
        harvester = self.createHarvesterWithMockUploader('tud')
        harvester._MAXTIME=5
        harvester.listRecords = self.listRecordsButWaitLong
        harvester.harvest()

    def testHarvesterIgnoringInvalidDataErrors(self):
        record = parse_xml("""<record><header><identifier>mockid</identifier></header><metadata><dc><title>mocktitle</title></dc></metadata><about/></record>""").record
        upload = Upload(record=record)
        upload.id = 'mockid'
        uploader=CallTrace("uploader")
        uploader.exceptions['send'] =  InvalidDataException(upload.id, "message")
        mapper=CallTrace("mapper", returnValues={'createUpload': upload})
        repository=CallTrace("repository", returnValues={'createUploader': uploader, 'mapping': mapper, 'maxIgnore': 0})
        observer=CallTrace("observer", returnValues={'totalIgnoredIds': 42})
        harvester = Harvester(repository, stateDir=self.stateDir, logDir=self.logDir, eventLogger=None)
        harvester.addObserver(observer)
        self.assertRaises(TooMuchInvalidDataException, lambda: harvester.uploadRecord(record))
        self.assertEquals(["notifyHarvestedRecord", "totalIgnoredIds"], [m.name for m in observer.calledMethods])
        observer.calledMethods = []
        repository.returnValues['maxIgnore'] = 43
        harvester.uploadRecord(record)
        self.assertEquals(["notifyHarvestedRecord", "totalIgnoredIds", "ignoreIdentifier"], [m.name for m in observer.calledMethods])

    def testHarvesterStopsIgnoringAfter100records(self):
        record = parse_xml("""<record><header><identifier>mockid</identifier></header><metadata><dc><title>mocktitle</title></dc></metadata><about/></record>""").record
        upload = Upload(record=record)
        upload.id = 'mockid'
        uploader=CallTrace("uploader")
        uploader.exceptions['send'] =  InvalidDataException(upload.id, "message")
        mapper=CallTrace("mapper", returnValues={'createUpload': upload})
        repository=CallTrace("repository", returnValues={'createUploader': uploader, 'mapping': mapper, 'maxIgnore': 100})
        observer=CallTrace("observer", returnValues={'totalIgnoredIds': 100})
        harvester = Harvester(repository, stateDir=self.stateDir, logDir=self.logDir, eventLogger=None)
        harvester.addObserver(observer)
        self.assertRaises(TooMuchInvalidDataException, lambda: harvester.uploadRecord(record))
        self.assertEquals(["notifyHarvestedRecord", "totalIgnoredIds"], [m.name for m in observer.calledMethods])

    #self shunt:
    def send(self, upload):
        self.sendCalled+=1
        self.sendId.append(upload.id)
        self.sendParts.append(upload.parts)
        self.upload = upload
        if self.sendException:
            raise self.sendException
        return self.sendReturn

    def delete(self, anUpload):
        self.delete_id = anUpload.id

    def info(self):
        return 'The uploader is connected to /dev/null'

    def start(self):
        self.startCalled += 1

    def stop(self):
        self.stopCalled += 1

    def listRecordsButWaitLong(self, a, b, c, d):
        sleep(20)

    def MockRepository (self, id, set):
        return _MockRepository(id, 'http://mock.server', set, 'inst'+id,self)

    def MockRepository2 (self, nr):
        return _MockRepository('reponame'+nr, 'url'+nr, 'set'+nr, 'instname'+nr,self)

    def MockRepository3(self, id, baseurl, set, repositoryGroupId):
        return _MockRepository(id, baseurl, set, repositoryGroupId, self)

    def mockssetarget(self):
        return self

    def createUploader(self, logger):
        return self

    def listRecords(self, metadataPrefix = None, from_ = "aap", resumptionToken = 'mies', set = None):
        self.listRecordsFrom = from_
        self.listRecordsToken = resumptionToken
        self.listRecordsSet = set
        if metadataPrefix:
            if set:
                return self.mockRepository.listRecords(metadataPrefix = metadataPrefix, set = set)
            return self.mockRepository.listRecords(metadataPrefix = metadataPrefix)
        return self.mockRepository.listRecords(resumptionToken = resumptionToken)
