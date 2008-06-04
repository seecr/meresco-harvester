## begin license ##
#
#    "Meresco Harvester" consists of two subsystems, namely an OAI-harvester and
#    a web-control panel.
#    "Meresco Harvester" is originally called "Sahara" and was developed for 
#    SURFnet by:
#        Seek You Too B.V. (CQ2) http://www.cq2.nl
#    Copyright (C) 2006-2007 SURFnet B.V. http://www.surfnet.nl
#    Copyright (C) 2007-2008 Seek You Too (CQ2) http://www.cq2.nl
#    Copyright (C) 2007-2008 SURF Foundation. http://www.surf.nl
#    Copyright (C) 2007-2008 Stichting Kennisnet Ict op school.
#       http://www.kennisnetictopschool.nl
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
from merescoharvester.harvester.harvester import Harvester
from merescoharvester.harvester.harvesterlog import HarvesterLog, printTime, isCurrentDay, getHarvestedUploadedRecords
from harvesterlogtest import LOGDIR, clearTestLog
from merescoharvester.harvester.oairequest import MockOAIRequest, OAIRequest
from cq2utils.wrappers import wrapp, binderytools
from merescoharvester.harvester.mapping import Mapping, DEFAULT_DC_CODE, Upload
import shelve
import os
import sys
import re
from merescoharvester.harvester import harvester
from time import sleep, strftime

class DeletedRecordHeader:
    def isDeleted(self):
        return True
    def identifier(self):
        return 'mockid'


#TODO key == id
class _MockRepository:
    def __init__(self,id,baseurl,set,repositoryGroupId, outer):
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
        m.code = DEFAULT_DC_CODE
        return m

class HarvesterTest(unittest.TestCase):
    def setUp(self):
        clearTestLog()
        self.sendCalled=0
        self.sendReturn=None
        self.sendException = None
        self.upload = None
        self.sendFields=[]
        self.sendId=[]
        self.listRecordsSet = None
        self.listRecordsToken = None
        self.startCalled=0
        self.stopCalled=0
        harvester.p=lambda x:None

    def createLogger(self):
        self.logger=HarvesterLog(LOGDIR,'tud')
        return self.logger

    def createServer(self, url='http://repository.tudelft.nl/oai'):
        return OAIRequest(url)

    def testCreateHarvester(self):
        harvester = self.createHarvesterWithMockUploader('tud')
        self.assertEquals((0,0),(self.startCalled,self.stopCalled))
        harvester.harvest()
        self.assertEquals((1,1),(self.startCalled,self.stopCalled))
        harvester = self.createHarvesterWithMockUploader('eur')
        self.assertEquals((1,1),(self.startCalled,self.stopCalled))
        harvester.harvest()
        self.assertEquals((2,2),(self.startCalled,self.stopCalled))

    def LIVE_test_LIVE_Data(self):
        server = self.createServer('http://arno.uvt.nl/~arno/arno-1.2/oai/wo.uvt.nl.cgi')
        record = server.getRecord(identifier=    'oai:wo.uvt.nl:155002', metadataPrefix='oai_dc')
        print record.header.identifier
        print record.metadata.dc.title

    def testDoUpload(self):
        harvester = self.createHarvesterWithMockUploader('tud')
        harvester.harvest()

        self.assertEqual(3, self.sendCalled)
        self.assertEqual('tud:oai:tudelft.nl:007193', self.sendId[2])
        self.assertEqual(u'quantitative electron microscopy; statistical experimental design; parameter estimation', self.sendFields[2]['meta_dc.subject'])
        self.assertEqual(
            u"http://content.library.tudelft.nl/intradoc-cgi/nph-idc_cgi.exe/as_aert_20030520.pdf?IdcService=GET_FILE&dID=8799&dDocName=007193; ISBN 90-6464-861-1",
            self.sendFields[2]['url'])
        self.assertEqual('tud', self.sendFields[2]['generic1'])
        self.assertEqual('oai:tudelft.nl:007193', self.sendFields[2]['generic2'])
        self.assertEquals('insttud', self.sendFields[2]['generic3'])
        self.assertEqual(u'2003-05-20', self.sendFields[2]['generic4'])
        self.assertEquals('ResumptionToken: TestToken', file(os.path.join(LOGDIR,'tud.stats')).read()[-27:-1])

    def testLogIDsForRemoval(self):
        harvester = self.createHarvesterWithMockUploader('tud')
        harvester.harvest()
        idsfile = open(LOGDIR+'/tud.ids')
        try:
            self.assertEquals('tud:oai:tudelft.nl:007087',idsfile.readline().strip())
            self.assertEquals('tud:oai:tudelft.nl:007192',idsfile.readline().strip())
            self.assertEquals('tud:oai:tudelft.nl:007193',idsfile.readline().strip())
        finally:
            idsfile.close()

    def createHarvesterWithMockUploader(self, name, set=None, mockRequest = None):
        self.logger=HarvesterLog(LOGDIR, name)
        harvester = Harvester(self.MockRepository(name, set), '/some/where', mockLogger=self.logger, mockRequest = mockRequest or MockOAIRequest('mocktud'))
        return harvester

    def testSimpleStat(self):
        harvester = self.createHarvesterWithMockUploader('tud')
        self.sendReturn = '12341234-@tompoes-1234123.134112'
        harvester.harvest()
        self.assert_(os.path.isfile(LOGDIR+'/tud.stats'))
        stats = open(LOGDIR + '/tud.stats').readline().strip().split(',')
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
        stats = open(LOGDIR + '/tud.stats').readline().strip().split(',')
        self.assertEquals(' Error: exceptions.Exception: send failed', stats[2])

    def testResumptionTokenLog(self):
        harvester = self.createHarvesterWithMockUploader('tud')
        self.sendReturn = 'true'
        harvester.harvest()
        stats = open(LOGDIR + '/tud.stats').readline().strip().split(',')
        self.assertEquals(' ResumptionToken: TestToken', stats[3])

    def testOtherMetadataPrefix(self):
        self.logger=HarvesterLog(LOGDIR, 'tud')
        repository = self.MockRepository('tud', None)
        repository.metadataPrefix='lom'
        harvester = Harvester(repository, '/some/where', mockLogger=self.logger, mockRequest = MockOAIRequest('mocktud'))
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
            self.assertEquals('exceptions.Exception', str(sys.exc_type))

    def testIncrementalHarvest(self):
        self.mockRepository = MockOAIRequest('mocktud')
        f = open(LOGDIR + '/tud.stats', 'w')
        f.write(' Started: 1999-12-01 16:37:41, Harvested/Uploaded/Total: 56/23/113, Done: 2004-12-31 16:39:15\n')
        f.close();
        f = open(LOGDIR + '/tud.ids', 'w')
        for i in range(113): f.write('oai:tudfakeid:%05i\n'%i)
        f.close()
        repository = self.MockRepository3('tud' ,'http://repository.tudelft.nl/oai', None, 'tud')
        h = Harvester(repository, '/some/where', mockLogger=self.createLogger(), mockRequest = self)
        self.listRecordsFrom = None
        self.sendReturn = '127.0.0.1-123@localhost-12312-12312424123'
        h.harvest()
        self.assertEquals('1999-12-01', self.listRecordsFrom)
        lines = open(LOGDIR + '/tud.stats').readlines()
        self.assertEquals(2, len(lines))
        self.assertEquals(('3', '3', '0', '116'), getHarvestedUploadedRecords(lines[1]))

    def testNotIncrementalInCaseOfError(self):
        self.mockRepository = MockOAIRequest('mocktud')
        f = open(LOGDIR + '/tud.stats', 'w')
        f.write('Started: 1998-12-01 16:37:41, Harvested/Uploaded/Total: 113/113/113, Done: 2004-12-31 16:39:15\n')
        f.write('Started: 1999-12-01 16:37:41, Harvested/Uploaded/Total: 113/113/113, Error: XXX\n')
        f.close();
        repository = self.MockRepository3('tud' ,'http://repository.tudelft.nl/oai', None, 'tud')
        h = Harvester(repository, '/some/where', mockLogger=self.createLogger(), mockRequest = self)
        self.listRecordsFrom = None
        h.harvest()
        self.assertEquals('1998-12-01', self.listRecordsFrom)

    def testOnlyErrorInLogFile(self):
        self.mockRepository = MockOAIRequest('mocktud')
        f = open(LOGDIR + '/tud.stats', 'w')
        f.write('Started: 1998-12-01 16:37:41, Harvested/Uploaded/Total: 113/113/113, Error:\n')
        f.write('Started: 1999-12-01 16:37:41, Harvested/Uploaded/Total: 113/113/113, Error: XXX\n')
        f.close();
        repository = self.MockRepository3('tud' ,'http://repository.tudelft.nl/oai', None, 'tud')
        h = Harvester(repository, '/some/where', mockLogger=self.createLogger(), mockRequest = self)
        self.listRecordsFrom = None
        h.harvest()
        self.assertEquals('aap', self.listRecordsFrom)

    def testResumptionToken(self):
        self.mockRepository = MockOAIRequest('mocktud')
        f = open(LOGDIR + '/tud.stats', 'w')
        f.write('Started: 1999-12-01 16:37:41, Harvested/Uploaded/Total: 113/113/113, Done: 2004-12-31 16:39:15, ResumptionToken: ga+hier+verder\n')
        f.close();
        repository = self.MockRepository3('tud' ,'http://repository.tudelft.nl/oai', None, 'tud')
        h = Harvester(repository, '/some/where', mockLogger=self.createLogger(), mockRequest = self)
        self.listRecordsToken = None
        h.harvest()
        self.assertEquals('ga+hier+verder', self.listRecordsToken)

    def testHarvestSet(self):
        self.mockRepository = MockOAIRequest('mocktud')
        harvester = self.createHarvesterWithMockUploader('um', set='withfulltext:yes', mockRequest = self)
        harvester.harvest()
        self.assertEquals('withfulltext:yes', self.listRecordsSet)

    def mockHarvest(self, repository, logger, uploader):
        if not hasattr(self, 'mockHarvestArgs'):
            self.mockHarvestArgs=[]
        self.mockHarvestArgs.append({'name':repository.key,'url':repository.url,'set':repository.set,'institutionkey':repository.institutionkey})

    def testNoDateHarvester(self):
        "runs a test with xml containing no dates"
        harvester = self.createHarvesterWithMockUploader('tud')
        self.logger.token='NoDateToken'
        harvester.harvest()

    def testNothingInRepository(self):
        harvester = self.createHarvesterWithMockUploader('tud')
        self.logger.token='EmptyListToken'
        harvester.harvest()
        lines = open(LOGDIR+'/tud.stats').readlines()
        self.assert_('Harvested/Uploaded/Deleted/Total: 0/0/0/0' in lines[0])

    def testNoDcIdentifier(self):
        harvester = self.createHarvesterWithMockUploader('tud')
        self.logger.token='DcIdentifierNo'
        harvester.harvest()
        lines = open(LOGDIR+'/tud.stats').readlines()

    def testUploadRecord(self):
        harvester = self.createHarvesterWithMockUploader('tud')
        header = wrapp(binderytools.bind_string('<header><identifier>mockid</identifier></header>').header)
        metadata = wrapp(binderytools.bind_string('<metadata><dc><title>mocktitle</title></dc></metadata>').metadata)
        about = wrapp(binderytools.bind_string('<about/>').about)
        upload = Upload()
        upload.id = 'tud:mockid'
        harvester._mapper.createUpload = lambda r,h,m,a,logger: upload
        result = harvester.uploadRecord(header, metadata,about)
        self.assertEquals(['tud:mockid'], self.sendId)
        self.assert_(not hasattr(self, 'delete_id'))
        self.assertEquals((1,0), result)

    def testSkippedRecord(self):
        harvester = self.createHarvesterWithMockUploader('tud')
        header = wrapp(binderytools.bind_string('<header><identifier>mockid</identifier></header>').header)
        metadata = wrapp(binderytools.bind_string('<metadata><dc><title>mocktitle</title></dc></metadata>').metadata)
        about = wrapp(binderytools.bind_string('<about/>').about)
        upload = None
        harvester._mapper.createUpload = lambda r,h,m,a,logger: upload
        result = harvester.uploadRecord(header, metadata, about)
        self.assertEquals([], self.sendId)
        self.assert_(not hasattr(self, 'delete_id'))
        self.assertEquals((0,0), result)

    def testDelete(self):
        harvester = self.createHarvesterWithMockUploader('tud')
        header = wrapp(binderytools.bind_string('<header status="deleted"><identifier>mockid</identifier></header>').header)
        metadata = 'true' # don't care
        about = "still don't care"
        result = harvester.uploadRecord(header, metadata, about)
        self.assertEquals([], self.sendId)
        self.assertEquals('tud:mockid', self.delete_id)
        self.assertEquals((0,1), result)

    def testDcIdentifierTake2(self):
        self.sendFulltexturl=None
        harvester = self.createHarvesterWithMockUploader('tud')
        self.logger.token='DcIdentifierHttp2'
        harvester.harvest()
        lines = open(LOGDIR+'/tud.stats').readlines()

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

    #self shunt:
    def send(self, upload):
        self.sendCalled+=1
        self.sendId.append(upload.id)
        self.sendFields.append(upload.fields)
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

    def MockRepository (self, key, set):
            return _MockRepository(key, 'http://mock.server', set, 'inst'+key,self)

    def MockRepository2 (self, nr):
        return _MockRepository('reponame'+nr, 'url'+nr, 'set'+nr, 'instname'+nr,self)

    def MockRepository3(self, key,url,set,institutionkey):
        return _MockRepository(key,url,set,institutionkey,self)

    def mockssetarget(self):
        return self

    def createUploader(self, logger):
        return self

    def identify(self):
        return self.mockRepository.identify()

    def listRecords(self, metadataPrefix = None, from_ = "aap", resumptionToken = 'mies', set = None):
        self.listRecordsFrom = from_
        self.listRecordsToken = resumptionToken
        self.listRecordsSet = set
        if metadataPrefix:
            if set:
                return self.mockRepository.listRecords(metadataPrefix = metadataPrefix, set = set)
            return self.mockRepository.listRecords(metadataPrefix = metadataPrefix)
        return self.mockRepository.listRecords(resumptionToken = resumptionToken)
