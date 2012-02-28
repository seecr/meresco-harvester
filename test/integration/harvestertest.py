#!/usr/bin/env python2.5
# -*- coding: utf-8 -*-
## begin license ##
#
#    "Meresco Harvester" consists of two subsystems, namely an OAI-harvester and
#    a web-control panel.
#    "Meresco Harvester" is originally called "Sahara" and was developed for
#    SURFnet by:
#        Seek You Too B.V. (CQ2) http://www.cq2.nl
#    Copyright (C) 2011 Seek You Too (CQ2) http://www.cq2.nl
#    Copyright (C) 2011 Stichting Kennisnet http://www.kennisnet.nl
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
from __future__ import with_statement

from os import system, waitpid, listdir, remove
from os.path import join, dirname, abspath
from urllib import urlopen
from time import time, sleep
from subprocess import Popen
from shutil import copytree
from lxml.etree import parse, tostring

from cq2utils import CQ2TestCase
from utils import getRequest

from integrationtestcase import IntegrationTestCase

from meresco.harvester.state import getResumptionToken
from meresco.harvester.harvesterlog import HarvesterLog
from meresco.harvester.controlpanel import RepositoryData
from meresco.harvester.namespaces import xpath

BATCHSIZE=10
DOMAIN='adomain'
REPOSITORY='harvestertest'
REPOSITORYGROUP='harvesterTestGroup'

class HarvesterTest(IntegrationTestCase):
    def setUp(self):
        IntegrationTestCase.setUp(self)
        system("rm -rf %s" % self.harvesterLogDir)
        system("rm -rf %s" % self.harvesterStateDir)
        self.filesystemDir = join(self.integrationTempdir, 'filesystem')
        system("rm -rf %s" % self.filesystemDir)
        system("mkdir -p %s" % join(self.harvesterStateDir, DOMAIN))
        self.repofilepath = join(self.integrationTempdir, 'data', "%s.%s.repository" % (DOMAIN, REPOSITORY))
        repo = RepositoryData(REPOSITORY)
        repo.use = 'true'
        repo.baseurl = 'http://localhost:%s/oai' % self.helperServerPortNumber
        repo.targetId = 'SRUUPDATE'
        repo.repositoryGroupId = REPOSITORYGROUP
        repo.mappingId = 'MAPPING'
        repo.metadataPrefix = 'oai_dc'
        repo.maximumIgnore = '5'
        repo.save(self.repofilepath)

    def tearDown(self):
        remove(self.repofilepath)

    def testHarvestToSruUpdate(self):
        # initial harvest
        self.startHarvester(repository=REPOSITORY)
        self.assertEquals(BATCHSIZE, self.sizeDumpDir())
        self.assertEquals(2, len([f for f in listdir(self.dumpDir) if "info:srw/action/1/delete" in open(join(self.dumpDir, f)).read()]))
        ids = open(join(self.harvesterStateDir, DOMAIN, "%s.ids" % REPOSITORY)).readlines()
        self.assertEquals(8, len(ids))
        invalidIds = open(join(self.harvesterStateDir, DOMAIN, "%s_invalid.ids" % REPOSITORY)).readlines()
        self.assertEquals(0, len(invalidIds))
        logs = self.getLogs()
        self.assertEquals(1, len(logs))
        self.assertEquals('/oai', logs[-1]['path'])
        self.assertEquals({'verb':['ListRecords'], 'metadataPrefix':['oai_dc']}, logs[-1]['arguments'])
        statsFile = join(self.harvesterStateDir, DOMAIN, '%s.stats' % REPOSITORY)
        token = getResumptionToken(open(statsFile).readlines()[-1])

        # resumptionToken
        self.startHarvester(repository=REPOSITORY)
        self.assertEquals(15, self.sizeDumpDir())
        ids = open(join(self.harvesterStateDir, DOMAIN, "%s.ids" % REPOSITORY)).readlines()
        self.assertEquals(13, len(ids))
        logs = self.getLogs()
        self.assertEquals(2, len(logs))
        self.assertEquals('/oai', logs[-1]['path'])
        self.assertEquals({'verb':['ListRecords'], 'resumptionToken':[token]}, logs[-1]['arguments'])

        # Nothing
        self.startHarvester(repository=REPOSITORY)
        self.assertEquals(2, len(self.getLogs()))
        self.assertEquals(None, getResumptionToken(open(statsFile).readlines()[-1]))

    def testIncrementalHarvesting(self):
        statsFile = join(self.harvesterStateDir, DOMAIN, '%s.stats' % REPOSITORY)
        with open(statsFile, 'w') as f:
            f.write('Started: 2011-04-01 14:11:44, Harvested/Uploaded/Deleted/Total: 300/300/0/300, Done: 2011-04-01 14:12:36, ResumptionToken:\n')
        self.startHarvester(repository=REPOSITORY)
        self.assertEquals(BATCHSIZE, self.sizeDumpDir())
        logs = self.getLogs()
        self.assertEquals(1, len(logs))
        self.assertEquals('/oai', logs[-1]['path'])
        self.assertEquals({'verb':['ListRecords'], 'metadataPrefix':['oai_dc'], 'from':['2011-04-01']}, logs[-1]['arguments'])

    def testClear(self):
        self.startHarvester(repository=REPOSITORY)
        logLen = len(self.getLogs())
        self.assertEquals(BATCHSIZE, self.sizeDumpDir())

        header, result = getRequest(self.harvesterInternalServerPortNumber, '/getStatus', {'domainId': DOMAIN, 'repositoryId': REPOSITORY}, parse='lxml')
        self.assertEquals(['8'], xpath(result, "/status:saharaget/status:GetStatus/status:status/status:total/text()"))

        r = RepositoryData.read(self.repofilepath)
        r.action='clear'
        r.save(self.repofilepath)

        self.startHarvester(repository=REPOSITORY)
        logs = self.getLogs()
        self.assertEquals(logLen+1, len(logs))
        self.assertEquals('/setactiondone', logs[-1]["path"])
        self.assertEquals({'domainId': [DOMAIN], 'repositoryId': [REPOSITORY]}, logs[-1]["arguments"])
        r = RepositoryData.read(self.repofilepath) #really set action done
        r.action=''
        r.save(self.repofilepath)
        self.assertEquals(18, self.sizeDumpDir())
        for filename in sorted(listdir(self.dumpDir))[-8:]:
            self.assertTrue('_delete.updateRequest' in filename, filename)

        header, result = getRequest(self.harvesterInternalServerPortNumber, '/getStatus', {'domainId': DOMAIN, 'repositoryId': REPOSITORY}, parse='lxml')
        self.assertEquals(['0'], xpath(result, "/status:saharaget/status:GetStatus/status:status/status:total/text()"))

    def testRefresh(self):
        log = HarvesterLog(stateDir=join(self.harvesterStateDir, DOMAIN), logDir=join(self.harvesterLogDir, DOMAIN), name=REPOSITORY)
        log.startRepository()
        for uploadId in ['%s:oai:record:%02d' % (REPOSITORY, i) for i in [1,7,120,121]]:
            log.notifyHarvestedRecord(uploadId)
            log.uploadIdentifier(uploadId)
        for uploadId in ['%s:oai:record:%02d' % (REPOSITORY, i) for i in [4,5,122,123]]:
            log.notifyHarvestedRecord(uploadId)
            log.deleteIdentifier(uploadId)
        log.endRepository('token')
        log.close()

        r = RepositoryData.read(self.repofilepath)
        r.action='refresh'
        r.save(self.repofilepath)

        self.startHarvester(repository=REPOSITORY)
        logs = self.getLogs()
        self.assertEquals(0, len(logs))
        self.startHarvester(repository=REPOSITORY)
        logs = self.getLogs()
        self.assertEquals('/oai', logs[-1]["path"])
        self.assertEquals({'verb': ['ListRecords'], 'metadataPrefix': ['oai_dc']}, logs[-1]["arguments"])
        statsFile = join(self.harvesterStateDir, DOMAIN, '%s.stats' % REPOSITORY)
        token = getResumptionToken(open(statsFile).readlines()[-1])

        self.startHarvester(repository=REPOSITORY)
        logs = self.getLogs()
        self.assertEquals('/oai', logs[-1]["path"])
        self.assertEquals({'verb': ['ListRecords'], 'resumptionToken': [token]}, logs[-1]["arguments"])
        self.assertEquals(15, self.sizeDumpDir())

        self.startHarvester(repository=REPOSITORY)
        logs = self.getLogs()
        self.assertEquals('/setactiondone', logs[-1]["path"])
        self.assertEquals({'domainId': [DOMAIN], 'repositoryId': [REPOSITORY]}, logs[-1]["arguments"])
        r = RepositoryData.read(self.repofilepath) #really set action done
        r.action=''
        r.save(self.repofilepath)
        self.assertEquals(17, self.sizeDumpDir())
        deletedIds = set([
            xpath(parse(open(join(self.dumpDir, '00016_delete.updateRequest'))), '//ucp:recordIdentifier/text()')[0],
            xpath(parse(open(join(self.dumpDir, '00017_delete.updateRequest'))), '//ucp:recordIdentifier/text()')[0]
        ])
        self.assertEquals(set(['%s:oai:record:120' % REPOSITORY, '%s:oai:record:121' % REPOSITORY]), deletedIds)


        logLen = len(self.getLogs())
        self.startHarvester(repository=REPOSITORY)
        self.assertEquals(logLen, len(self.getLogs()), 'Action is over, expect nothing more.')

    def testInvalidIgnoredUptoMaxIgnore(self):
        maxIgnore = 5
        self.controlHelper(action='allInvalid')
        nrOfDeleted = 2
        r = RepositoryData.read(self.repofilepath)
        r.maximumIgnore = "%s" % maxIgnore
        r.save(self.repofilepath)
        self.startHarvester(repository=REPOSITORY)
        self.assertEquals(nrOfDeleted, self.sizeDumpDir())
        ids = open(join(self.harvesterStateDir, DOMAIN, "%s.ids" % REPOSITORY)).readlines()
        self.assertEquals(0, len(ids))
        invalidIds = open(join(self.harvesterStateDir, DOMAIN, "%s_invalid.ids" % REPOSITORY)).readlines()
        self.assertEquals(maxIgnore + 1, len(invalidIds), invalidIds)
        invalidDataMessagesDir = join(self.harvesterLogDir, DOMAIN, "invalid", REPOSITORY)
        self.assertEquals(maxIgnore + 1, len(listdir(invalidDataMessagesDir)))
        invalidDataMessage01 = open(join(invalidDataMessagesDir, "oai:record:01")).read()
        self.assertTrue('uploadId: "integrationtest:oai:record:01"', invalidDataMessage01)
        self.controlHelper(action='noneInvalid')
        self.startHarvester(repository=REPOSITORY)
        self.assertEquals(nrOfDeleted + BATCHSIZE, self.sizeDumpDir()) 
        ids = open(join(self.harvesterStateDir, DOMAIN, "%s.ids" % REPOSITORY)).readlines()
        self.assertEquals(BATCHSIZE - nrOfDeleted, len(ids))
        invalidIds = open(join(self.harvesterStateDir, DOMAIN, "%s_invalid.ids" % REPOSITORY)).readlines()
        self.assertEquals(0, len(invalidIds), invalidIds)
        self.assertEquals(0, len(listdir(invalidDataMessagesDir)))

    def testHarvestToFilesystemTarget(self):
        r = RepositoryData.read(self.repofilepath)
        r.targetId = 'FILESYSTEM'
        r.save(self.repofilepath)

        self.startHarvester(repository=REPOSITORY)

        self.assertEquals(8, len(listdir(join(self.filesystemDir, REPOSITORYGROUP, REPOSITORY))))
        self.assertEquals(['%s:oai:record:%02d' % (REPOSITORY, i) for i in [3,6]],
                [id.strip() for id in open(join(self.filesystemDir, 'deleted_records'))])

    def testClearOnFilesystemTarget(self):
        r = RepositoryData.read(self.repofilepath)
        r.targetId = 'FILESYSTEM'
        r.save(self.repofilepath)
        self.startHarvester(repository=REPOSITORY)

        r = RepositoryData.read(self.repofilepath)
        r.action = 'clear'
        r.save(self.repofilepath)

        self.startHarvester(repository=REPOSITORY)
        self.assertEquals(0, len(listdir(join(self.filesystemDir, REPOSITORYGROUP, REPOSITORY))))
        self.assertEquals(set([
                'harvestertest:oai:record:10', 'harvestertest:oai:record:09', 'harvestertest:oai:record:08', 
                'harvestertest:oai:record:07', 'harvestertest:oai:record:06', 'harvestertest:oai:record:05', 
                'harvestertest:oai:record:04', 'harvestertest:oai:record:03', 'harvestertest:%0A oai:record:02%2F&gkn', 
                'harvestertest:oai:record:01'
            ]), 
            set([id.strip() for id in open(join(self.filesystemDir, 'deleted_records'))])
        )

    def testHarvestWithError(self):
        self.startHarvester(repository=REPOSITORY)
        self.emptyDumpDir()

        self.controlHelper(action='raiseExceptionOnIds', id=['%s:oai:record:12' % REPOSITORY]) 
        self.startHarvester(repository=REPOSITORY)
        successFullRecords=['oai:record:11']
        self.assertEquals(len(successFullRecords), self.sizeDumpDir())
        self.emptyDumpDir()

        self.controlHelper(action='raiseExceptionOnIds', id=[]) 
        self.startHarvester(repository=REPOSITORY)
        secondBatchSize = 5
        self.assertEquals(secondBatchSize, self.sizeDumpDir())

    def testClearWithError(self):
        self.startHarvester(repository=REPOSITORY)

        r = RepositoryData.read(self.repofilepath)
        r.action = 'clear'
        r.save(self.repofilepath)
        self.controlHelper(action='raiseExceptionOnIds', id=['%s:oai:record:05' % REPOSITORY]) 
        self.emptyDumpDir()

        self.startHarvester(repository=REPOSITORY)
        successFullDeletes = [1,2,4]
        deletesTodo = [5,7,8,9,10]
        self.assertEquals(len(successFullDeletes), self.sizeDumpDir())

        self.controlHelper(action='raiseExceptionOnIds', id=[]) 
        self.emptyDumpDir()
        self.startHarvester(repository=REPOSITORY)
        self.assertEquals(len(deletesTodo), self.sizeDumpDir())

    def testRefreshWithIgnoredRecords(self):
        log = HarvesterLog(stateDir=join(self.harvesterStateDir, DOMAIN), logDir=join(self.harvesterLogDir, DOMAIN), name=REPOSITORY)
        log.startRepository()
        for uploadId in ['%s:oai:record:%02d' % (REPOSITORY, i) for i in [1,2,120,121]]:
            if uploadId == '%s:oai:record:02' % (REPOSITORY):
                uploadId = '%s:\n oai:record:02/&gkn' % (REPOSITORY)
            log.notifyHarvestedRecord(uploadId)
            log.uploadIdentifier(uploadId)
        for uploadId in ['%s:oai:record:%02d' % (REPOSITORY, i) for i in [4,5,122,123,124]]:
            log.notifyHarvestedRecord(uploadId)
            log.deleteIdentifier(uploadId)
        for uploadId in ['%s:oai:record:%02d' % (REPOSITORY, i) for i in [7,8,125,126,127,128]]:
            log.notifyHarvestedRecord(uploadId)
            log.logInvalidData(uploadId, 'ignored message')
            log.logIgnoredIdentifierWarning(uploadId)
        log.endRepository('token')
        log.close()
        totalRecords = 15
        oldUploads = 2
        oldDeletes = 3
        oldIgnoreds = 4

        r = RepositoryData.read(self.repofilepath)
        r.action='refresh'
        r.save(self.repofilepath)

        self.startHarvester(repository=REPOSITORY) # Smoot init
        self.assertEquals(0, self.sizeDumpDir())
        self.startHarvester(repository=REPOSITORY) # Smooth harvest
        self.startHarvester(repository=REPOSITORY) # Smooth harvest
        self.assertEquals(totalRecords, self.sizeDumpDir())
        self.startHarvester(repository=REPOSITORY) # Smooth finish
        self.assertEquals(totalRecords + oldUploads + oldIgnoreds, self.sizeDumpDir())
        invalidIds = open(join(self.harvesterStateDir, DOMAIN, "%s_invalid.ids" % REPOSITORY)).readlines()
        self.assertEquals(0, len(invalidIds), invalidIds)
        ids = open(join(self.harvesterStateDir, DOMAIN, "%s.ids" % REPOSITORY)).readlines()
        self.assertEquals(13, len(ids), ids)

    def testClearWithInvalidRecords(self):
        log = HarvesterLog(stateDir=join(self.harvesterStateDir, DOMAIN), logDir=join(self.harvesterLogDir, DOMAIN), name=REPOSITORY)
        log.startRepository()
        for uploadId in ['%s:oai:record:%02d' % (REPOSITORY, i) for i in [1,2,120,121]]:
            log.notifyHarvestedRecord(uploadId)
            log.uploadIdentifier(uploadId)
        for uploadId in ['%s:oai:record:%02d' % (REPOSITORY, i) for i in [4,5,122,123,124]]:
            log.notifyHarvestedRecord(uploadId)
            log.deleteIdentifier(uploadId)
        for uploadId in ['%s:oai:record:%02d' % (REPOSITORY, i) for i in [7,8,125,126,127,128]]:
            log.notifyHarvestedRecord(uploadId)
            log.logInvalidData(uploadId, 'ignored message')
            log.logIgnoredIdentifierWarning(uploadId)
        log.endRepository('token')
        log.close()
        oldUploads = 4
        oldDeletes = 5
        oldInvalids = 6

        r = RepositoryData.read(self.repofilepath)
        r.action='clear'
        r.save(self.repofilepath)
        
        self.startHarvester(repository=REPOSITORY)
        self.assertEquals(oldUploads+oldInvalids, self.sizeDumpDir())
        invalidIds = open(join(self.harvesterStateDir, DOMAIN, "%s_invalid.ids" % REPOSITORY)).readlines()
        self.assertEquals(0, len(invalidIds), invalidIds)
        ids = open(join(self.harvesterStateDir, DOMAIN, "%s.ids" % REPOSITORY)).readlines()
        self.assertEquals(0, len(ids), ids)

    def testConcurrentHarvestToSruUpdate(self):
        self.startHarvester(concurrency=3)

        requestsLogged = sorted(listdir(self.dumpDir))

        repositoryIds = []
        for f in requestsLogged:
            lxml = parse(open(join(self.dumpDir, f)))
            repositoryIds.append(xpath(lxml, '//ucp:recordIdentifier/text()')[0].split(':', 1)[0])

        repositoryIdsSet = set(repositoryIds)
        self.assertEquals(set(['repository2', 'integrationtest', 'harvestertest']), repositoryIdsSet)

        lastSeenRepoId = None
        try:
            for repo in repositoryIds:
                if repo != lastSeenRepoId:
                    repositoryIdsSet.remove(repo)
                    lastSeenRepoId = repo
                    continue
        except KeyError:
            pass
        else:
            self.fail('Records should have been inserted out-of-order.')

    def testConcurrencyAtLeastOne(self):
        stdouterrlog = self.startHarvester(concurrency=0)
        self.assertTrue("Concurrency must be at least 1" in stdouterrlog, stdouterrlog)

        stdouterrlog = self.startHarvester(concurrency=-1)
        self.assertTrue("Concurrency must be at least 1" in stdouterrlog, stdouterrlog)

    def emptyDumpDir(self):
        system('rm %s/*' % self.dumpDir)

    def sizeDumpDir(self):
        return len(listdir(self.dumpDir))

