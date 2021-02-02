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
# Copyright (C) 2010-2012, 2015, 2020-2021 Stichting Kennisnet https://www.kennisnet.nl
# Copyright (C) 2012-2015, 2020-2021 Seecr (Seek You Too B.V.) https://seecr.nl
# Copyright (C) 2020-2021 Data Archiving and Network Services https://dans.knaw.nl
# Copyright (C) 2020-2021 SURF https://www.surf.nl
# Copyright (C) 2020-2021 The Netherlands Institute for Sound and Vision https://beeldengeluid.nl
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

import os
import sys
import re
import unittest
from time import sleep, strftime
from shutil import rmtree
from tempfile import mkdtemp
from io import StringIO
from lxml.etree import parse

from seecr.test import CallTrace

from meresco.components.json import JsonDict
from meresco.harvester.harvester import Harvester
from meresco.harvester.harvesterlog import HarvesterLog
from meresco.harvester.oairequest import OaiRequest
from meresco.harvester.virtualuploader import InvalidDataException, TooMuchInvalidDataException
from meresco.harvester.mapping import Mapping, DEFAULT_CODE, Upload
from meresco.harvester import namespaces

from mockoairequest import MockOaiRequest
from oairequesttest import oaiResponse


class DeletedRecordHeader(object):
    def isDeleted(self):
        return True
    def identifier(self):
        return 'mockid'

class _MockRepository(object):
    def __init__(self, id, baseurl, set, repositoryGroupId, outer, continuous=False):
        self.repositoryGroupId=repositoryGroupId
        self.id = id
        self.baseurl = baseurl
        self.set = set
        self.metadataPrefix = 'oai_dc'
        self.targetId= outer.mockssetarget
        self.createUploader = outer.createUploader
        self.continuous = continuous

    def mapping(self):
        m = Mapping('id')
        m.name = self.repositoryGroupId
        m.code = DEFAULT_CODE
        return m

class HarvesterTest(unittest.TestCase):
    def setUp(self):
        self.sendCalled=0
        self.sendException = None
        self.upload = None
        self.sendParts=[]
        self.sendId=[]
        self.listRecordsSet = None
        self.listRecordsToken = None
        self.startCalled=0
        self.stopCalled=0
        self.logDir = self.stateDir = mkdtemp()
        self.logger = None

    def tearDown(self):
        if not self.logger is None:
            self.logger.close()
        rmtree(self.logDir)

    def createLogger(self):
        self.logger=HarvesterLog(stateDir=self.stateDir, logDir=self.logDir, name='tud')
        return self.logger

    def createServer(self, url='http://repository.tudelft.nl/oai'):
        return OaiRequest(url)

    def testCreateHarvester(self):
        harvester = self.createHarvesterWithMockUploader('tud')
        self.assertEqual((0,0),(self.startCalled,self.stopCalled))
        harvester.harvest()
        self.assertEqual((1,1),(self.startCalled,self.stopCalled))
        harvester = self.createHarvesterWithMockUploader('eur')
        self.assertEqual((1,1),(self.startCalled,self.stopCalled))
        harvester.harvest()
        self.assertEqual((2,2),(self.startCalled,self.stopCalled))

    def testDoUpload(self):
        harvester = self.createHarvesterWithMockUploader('tud')
        harvester.harvest()

        self.assertEqual(3, self.sendCalled)
        self.assertEqual('tud:oai:tudelft.nl:007193', self.sendId[2])
        record = parse(StringIO(self.sendParts[2]['record']))
        subjects = record.xpath('/oai:record/oai:metadata/oai_dc:dc/dc:subject/text()', namespaces=namespaces)
        self.assertEqual(['quantitative electron microscopy', 'statistical experimental design', 'parameter estimation'], subjects)
        with open(os.path.join(self.stateDir, 'tud.stats')) as f:
            self.assertEqual('ResumptionToken: TestToken', f.read()[-27:-1])

    def testLogIDsForRemoval(self):
        harvester = self.createHarvesterWithMockUploader('tud')
        harvester.harvest()
        with open(self.stateDir+'/tud.ids') as idsfile:
            self.assertEqual('tud:oai:tudelft.nl:007087',idsfile.readline().strip())
            self.assertEqual('tud:oai:tudelft.nl:007192',idsfile.readline().strip())
            self.assertEqual('tud:oai:tudelft.nl:007193',idsfile.readline().strip())

    def createHarvesterWithMockUploader(self, name, set=None, mockRequest=None):
        self.logger = HarvesterLog(stateDir=self.stateDir, logDir=self.logDir, name=name)
        repository = self.MockRepository(name, set)
        uploader = repository.createUploader(self.logger.eventLogger())
        self.mapper = repository.mapping()
        harvester = Harvester(repository)
        harvester.addObserver(mockRequest or MockOaiRequest('mocktud'))
        harvester.addObserver(self.logger)
        harvester.addObserver(uploader)
        harvester.addObserver(self.mapper)
        return harvester

    def testSimpleStat(self):
        harvester = self.createHarvesterWithMockUploader('tud')
        harvester.harvest()
        self.assertTrue(os.path.isfile(self.stateDir+'/tud.stats'))
        with open(self.stateDir + '/tud.stats') as fp:
            stats = fp.readline().strip().split(',')
        year = strftime('%Y')
        self.assertEqual('Started: %s-'%year, stats[0][:14])
        self.assertEqual(' Harvested/Uploaded/Deleted/Total: 3/3/0/3', stats[1])
        self.assertEqual(' Done: %s-'%year, stats[2][:12])

    def testErrorStat(self):
        harvester = self.createHarvesterWithMockUploader('tud')
        self.sendException = Exception('send failed')
        try:
            harvester.harvest()
        except:
            pass
        with open(self.stateDir + '/tud.stats') as fp:
            stats = fp.readline().strip().split(',')
        self.assertTrue(stats[2].startswith(' Error: '), stats[2])
        self.assertTrue(stats[2].endswith('send failed'), stats[2])

    def testResumptionTokenLog(self):
        harvester = self.createHarvesterWithMockUploader('tud')
        harvester.harvest()
        with open(self.stateDir + '/tud.stats') as fp:
            stats = fp.readline().strip().split(',')
        self.assertEqual(' ResumptionToken: TestToken', stats[3])

    def testOtherMetadataPrefix(self):
        self.logger=HarvesterLog(stateDir=self.stateDir, logDir=self.logDir, name='tud')
        repository = self.MockRepository('tud', None)
        repository.metadataPrefix='lom'
        harvester = Harvester(repository)
        harvester.addObserver(MockOaiRequest('mocktud'))
        harvester.addObserver(self.logger)
        harvester.addObserver(repository.createUploader(self.logger.eventLogger))
        harvester.addObserver(repository.mapping())
        harvester.harvest()
        self.assertEqual(['tud:oai:lorenet:147'],self.sendId)

    def testWriteAndSeek(self):
        with open('test','w') as f:
            f.write('enige info: ')
            pos = f.tell()
            f.write('20000')
            f.seek(pos)
            f.write('12345')
        with open("test", "r") as f:
            self.assertEqual('enige info: 12345', f.readline().strip())
        os.remove('test')

    def testException(self):
        try:
            raise Exception('aap')
            self.fail()
        except:
            self.assertEqual('aap', str(sys.exc_info()[1]))
            self.assertEqual("<class 'Exception'>", str(sys.exc_info()[0]))

    def testIncrementalHarvest(self):
        self.mockRepository = MockOaiRequest('mocktud')
        with open(self.stateDir + '/tud.stats', 'w') as f:
            f.write(' Started: 1999-12-01 16:37:41, Harvested/Uploaded/Total: 56/23/113, Done: 2004-12-31 16:39:15\n')
        with open(self.stateDir + '/tud.next', 'w') as fp:
            JsonDict({'resumptionToken': None, 'from': "1999-12-01T16:37:41Z"}).dump(fp)

        with open(self.stateDir + '/tud.ids', 'w') as f:
            for i in range(113): 
                f.write('oai:tudfakeid:%05i\n'%i)
        repository = self.MockRepository3('tud' ,'http://repository.tudelft.nl/oai', None, 'tud')
        logger = self.createLogger()
        h = Harvester(repository)
        h.addObserver(self)
        h.addObserver(logger)
        h.addObserver(repository.createUploader(logger.eventLogger))
        h.addObserver(repository.mapping())
        self.listRecordsFrom = None
        h.harvest()
        self.assertEqual('1999-12-01', self.listRecordsFrom)
        with open(self.stateDir + '/tud.stats') as f:
            lines = f.readlines()
        self.assertEqual(2, len(lines))
        self.assertEqual(('3', '3', '0', '116'), getHarvestedUploadedRecords(lines[1]))

    def testNotIncrementalInCaseOfError(self):
        self.mockRepository = MockOaiRequest('mocktud')
        with open(self.stateDir + '/tud.stats', 'w') as f:
            f.write('Started: 1998-12-01 16:37:41, Harvested/Uploaded/Total: 113/113/113, Done: 2004-12-31 16:39:15\n')
            f.write('Started: 1999-12-01 16:37:41, Harvested/Uploaded/Total: 113/113/113, Error: XXX\n')
        repository = self.MockRepository3('tud' ,'http://repository.tudelft.nl/oai', None, 'tud')
        logger = self.createLogger()
        h = Harvester(repository)
        h.addObserver(self)
        h.addObserver(logger)
        h.addObserver(repository.createUploader(logger.eventLogger))
        h.addObserver(repository.mapping())
        self.listRecordsFrom = None
        h.harvest()
        self.assertEqual('1998-12-01', self.listRecordsFrom)

    def testOnlyErrorInLogFile(self):
        self.mockRepository = MockOaiRequest('mocktud')
        with open(self.stateDir + '/tud.stats', 'w') as f:
            f.write('Started: 1998-12-01 16:37:41, Harvested/Uploaded/Total: 113/113/113, Error:\n')
            f.write('Started: 1999-12-01 16:37:41, Harvested/Uploaded/Total: 113/113/113, Error: XXX\n')
        repository = self.MockRepository3('tud' ,'http://repository.tudelft.nl/oai', None, 'tud')
        logger = self.createLogger()
        h = Harvester(repository)
        h.addObserver(self)
        h.addObserver(logger)
        h.addObserver(repository.createUploader(logger.eventLogger))
        h.addObserver(repository.mapping())
        self.listRecordsFrom = None
        h.harvest()
        self.assertEqual('aap', self.listRecordsFrom)

    def testResumptionToken(self):
        self.mockRepository = MockOaiRequest('mocktud')
        f = open(self.stateDir + '/tud.stats', 'w')
        f.write('Started: 1999-12-01 16:37:41, Harvested/Uploaded/Total: 113/113/113, Done: 2004-12-31 16:39:15, ResumptionToken: ga+hier+verder\n')
        f.close();
        repository = self.MockRepository3('tud' ,'http://repository.tudelft.nl/oai', None, 'tud')
        logger = self.createLogger()
        h = Harvester(repository)
        h.addObserver(self)
        h.addObserver(logger)
        h.addObserver(repository.createUploader(logger.eventLogger))
        h.addObserver(repository.mapping())
        self.listRecordsToken = None
        h.harvest()
        self.assertEqual('ga+hier+verder', self.listRecordsToken)

    def testContinuousHarvesting(self):
        self.mockRepository = MockOaiRequest('mocktud')
        with open(self.stateDir + '/tud.stats', 'w') as f:
            f.write(' Started: 1999-12-01 16:37:41, Harvested/Uploaded/Total: 56/23/113, Done: 2004-12-31 16:39:15\n')
        
        with open(self.stateDir + '/tud.next', 'w') as f:
            JsonDict({'resumptionToken': None, 'from': "2015-01-01T00:12:13Z"}).dump(f)
        repository = self.MockRepository3('tud' ,'http://repository.tudelft.nl/oai', None, 'tud', continuous=True)
        logger = self.createLogger()
        h = Harvester(repository)
        h.addObserver(self)
        h.addObserver(logger)
        h.addObserver(repository.createUploader(logger.eventLogger))
        h.addObserver(repository.mapping())
        self.listRecordsFrom = None
        h.harvest()
        self.assertEqual('2015-01-01T00:12:13Z', self.listRecordsFrom)

    def testHarvestSet(self):
        self.mockRepository = MockOaiRequest('mocktud')
        harvester = self.createHarvesterWithMockUploader('um', set='withfulltext:yes', mockRequest = self)
        harvester.harvest()
        self.assertEqual('withfulltext:yes', self.listRecordsSet)

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
        with open(self.stateDir+'/tud.stats') as fp:
            lines = fp.readlines()
        self.assertTrue('Harvested/Uploaded/Deleted/Total: 0/0/0/0' in lines[0])

    def testUploadRecord(self):
        harvester = self.createHarvesterWithMockUploader('tud')
        harvester.upload(oaiResponse(identifier='mockid'))
        self.assertEqual(['tud:mockid'], self.sendId)
        self.assertFalse(hasattr(self, 'delete_id'))

    def testSkippedRecord(self):
        harvester = self.createHarvesterWithMockUploader('tud')
        def createUpload(repository, oaiResponse):
            upload = Upload(repository=repository, oaiResponse=oaiResponse)
            upload.id = "tud:mockid"
            upload.skip = True
            return upload
        self.mapper.createUpload = createUpload
        harvester.upload(oaiResponse(identifier='mockid'))
        self.assertEqual([], self.sendId)
        self.assertFalse(hasattr(self, 'delete_id'))

    def testDelete(self):
        harvester = self.createHarvesterWithMockUploader('tud')
        harvester.upload(oaiResponse(identifier='mockid', deleted=True))
        self.assertEqual([], self.sendId)
        self.assertEqual('tud:mockid', self.delete_id)

    def testDcIdentifierTake2(self):
        self.sendFulltexturl=None
        harvester = self.createHarvesterWithMockUploader('tud')
        self.logger.token='DcIdentifierHttp2'
        harvester.harvest()
        with open(self.stateDir+'/tud.stats') as f:
            f.readlines()

    def testHarvesterStopsIgnoringAfter100records(self):
        observer = CallTrace('observer')
        upload = Upload(repository=None, oaiResponse=oaiResponse(identifier='mockid'))
        upload.id = 'mockid'
        observer.returnValues['createUpload'] = upload
        observer.returnValues['totalInvalidIds'] = 101
        observer.exceptions['send'] =  InvalidDataException(upload.id, "message")
        repository=CallTrace("repository", returnValues={'maxIgnore': 100})
        harvester = Harvester(repository)
        harvester.addObserver(observer)
        self.assertRaises(TooMuchInvalidDataException, lambda: harvester.upload(oaiResponse(identifier='mockid')))
        self.assertEqual(['createUpload', "notifyHarvestedRecord", "send", "logInvalidData", "totalInvalidIds"], [m.name for m in observer.calledMethods])

    def testHarvesterIgnoringInvalidDataErrors(self):
        observer = CallTrace('observer')
        upload = Upload(repository=None, oaiResponse=oaiResponse(identifier='mockid'))
        upload.id = 'mockid'
        observer.returnValues['createUpload'] = upload
        observer.returnValues['totalInvalidIds'] = 0
        observer.exceptions['send'] =  InvalidDataException(upload.id, "message")
        repository=CallTrace("repository", returnValues={'maxIgnore': 100})
        harvester = Harvester(repository)
        harvester.addObserver(observer)
        harvester.upload(oaiResponse())
        self.assertEqual(['createUpload', "notifyHarvestedRecord", "send", 'logInvalidData', "totalInvalidIds", 'logIgnoredIdentifierWarning'], [m.name for m in observer.calledMethods])

    #self shunt:
    def send(self, upload):
        self.sendCalled+=1
        self.sendId.append(upload.id)
        self.sendParts.append(upload.parts)
        self.upload = upload
        if self.sendException:
            raise self.sendException

    def delete(self, anUpload):
        self.delete_id = anUpload.id

    def uploaderInfo(self):
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

    def MockRepository3(self, id, baseurl, set, repositoryGroupId, continuous=False):
        return _MockRepository(id, baseurl, set, repositoryGroupId, self, continuous=continuous)

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


def getHarvestedUploadedRecords(logline):
    matches=re.search('Harvested/Uploaded/(?:Deleted/)?Total: \s*(\d*)/\s*(\d*)(?:/\s*(\d*))?/\s*(\d*)', logline)
    return matches.groups('0')

