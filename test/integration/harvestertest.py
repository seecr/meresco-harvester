# -*- coding: utf-8 -*-
## begin license ##
#
# "Meresco Harvester" consists of two subsystems, namely an OAI-harvester and
# a web-control panel.
# "Meresco Harvester" is originally called "Sahara" and was developed for
# SURFnet by:
# Seek You Too B.V. (CQ2) http://www.cq2.nl
#
# Copyright (C) 2011 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2011-2012, 2015 Stichting Kennisnet http://www.kennisnet.nl
# Copyright (C) 2012-2013, 2015 Seecr (Seek You Too B.V.) http://seecr.nl
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

from os import system, listdir
from os.path import join
from time import sleep
from threading import Thread
from lxml.etree import parse

from seecr.test import IntegrationTestCase
from seecr.test.utils import getRequest, sleepWheel

from meresco.components.json import JsonDict
from meresco.harvester.harvesterdata import HarvesterData
from meresco.harvester.state import getResumptionToken
from meresco.harvester.harvesterlog import HarvesterLog
from meresco.harvester.namespaces import xpath
from meresco.xml import xpathFirst

BATCHSIZE=10
DOMAIN='adomain'
REPOSITORY='harvestertestrepository'
REPOSITORYGROUP='harvesterTestGroup'

class HarvesterTest(IntegrationTestCase):
    def setUp(self):
        IntegrationTestCase.setUp(self)
        system("rm -rf %s" % self.harvesterLogDir)
        system("rm -rf %s" % self.harvesterStateDir)
        self.filesystemDir = join(self.integrationTempdir, 'filesystem')
        system("rm -rf %s" % self.filesystemDir)
        self.emptyDumpDir()
        system("mkdir -p %s" % join(self.harvesterStateDir, DOMAIN))
        self.harvesterData = HarvesterData(join(self.integrationTempdir, 'data'))
        try:
            self.harvesterData.addRepositoryGroup(identifier=REPOSITORYGROUP, domainId=DOMAIN)
        except ValueError:
            pass
        self.saveRepository(DOMAIN, REPOSITORY, REPOSITORYGROUP)

    def tearDown(self):
        self.removeRepository(DOMAIN, REPOSITORY, REPOSITORYGROUP)
        IntegrationTestCase.tearDown(self)

    def saveRepository(self, domain, repositoryId, repositoryGroupId, metadataPrefix="oai_dc", action=None, mappingId='MAPPING', targetId='SRUUPDATE', maximumIgnore=5, complete=False):
        try:
            self.harvesterData.addRepository(identifier=repositoryId, domainId=domain, repositoryGroupId=repositoryGroupId)
        except ValueError:
            pass
        self.harvesterData.updateRepository(
                identifier=repositoryId,
                domainId=domain,
                baseurl='http://localhost:%s/oai' % self.helperServerPortNumber,
                set=None,
                metadataPrefix=metadataPrefix,
                mappingId=mappingId,
                targetId=targetId,
                collection=None,
                maximumIgnore=maximumIgnore,
                use=True,
                complete=complete,
                action=action,
                shopclosed=[]
            )

    def removeRepository(self, domain, repositoryId, repositoryGroupId):
        self.harvesterData.deleteRepository(identifier=repositoryId, domainId=domain, repositoryGroupId=repositoryGroupId)

    def testHarvestReturnsErrorWillNotSaveState(self):
        logs = self.getLogs()
        self.saveRepository(DOMAIN, "repo_invalid_metadataPrefix", REPOSITORYGROUP, metadataPrefix="not_existing")
        try:
            self.startHarvester(repository="repo_invalid_metadataPrefix")
            self.startHarvester(repository="repo_invalid_metadataPrefix")
            logs = self.getLogs()[len(logs):]
            self.assertEquals(2, len(logs))
            self.assertEquals('/oai', logs[-2]['path'])
            self.assertEquals({'verb':['ListRecords'], 'metadataPrefix':['not_existing']}, logs[0]['arguments'])
            self.assertEquals('/oai', logs[-1]['path'])
            self.assertEquals({'verb':['ListRecords'], 'metadataPrefix':['not_existing']}, logs[1]['arguments'])
        finally:
            self.removeRepository(DOMAIN, 'repo_invalid_metadataPrefix', REPOSITORYGROUP)


    def testHarvestToSruUpdate(self):
        # initial harvest
        oldlogs = self.getLogs()
        self.startHarvester(repository=REPOSITORY)
        self.assertEquals(BATCHSIZE, self.sizeDumpDir())
        self.assertEquals(2, len([f for f in listdir(self.dumpDir) if "info:srw/action/1/delete" in open(join(self.dumpDir, f)).read()]))
        ids = open(join(self.harvesterStateDir, DOMAIN, "%s.ids" % REPOSITORY)).readlines()
        self.assertEquals(8, len(ids))
        invalidIds = open(join(self.harvesterStateDir, DOMAIN, "%s_invalid.ids" % REPOSITORY)).readlines()
        self.assertEquals(0, len(invalidIds))
        logs = self.getLogs()[len(oldlogs):]
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
        logs = self.getLogs()[len(oldlogs):]
        self.assertEquals(2, len(logs))
        self.assertEquals('/oai', logs[-1]['path'])
        self.assertEquals({'verb':['ListRecords'], 'resumptionToken':[token]}, logs[-1]['arguments'])

        # Nothing
        self.startHarvester(repository=REPOSITORY)
        logs = self.getLogs()[len(oldlogs):]
        self.assertEquals(2, len(logs))
        self.assertEquals(None, getResumptionToken(open(statsFile).readlines()[-1]))

    def testIncrementalHarvesting(self):
        oldlogs = self.getLogs()
        statsFile = join(self.harvesterStateDir, DOMAIN, '%s.stats' % REPOSITORY)
        with open(statsFile, 'w') as f:
            f.write('Started: 2011-03-31 13:11:44, Harvested/Uploaded/Deleted/Total: 300/300/0/300, Done: 2011-03-31 13:12:36, ResumptionToken: xyz\n')
            f.write('Started: 2011-04-01 14:11:44, Harvested/Uploaded/Deleted/Total: 300/300/0/300, Done: 2011-04-01 14:12:36, ResumptionToken:\n')
        self.startHarvester(repository=REPOSITORY)
        self.assertEquals(BATCHSIZE, self.sizeDumpDir())
        logs = self.getLogs()[len(oldlogs):]
        self.assertEquals(1, len(logs))
        self.assertEquals('/oai', logs[-1]['path'])
        self.assertEquals({'verb':['ListRecords'], 'metadataPrefix':['oai_dc'], 'from':['2011-03-31']}, logs[-1]['arguments'])

    def testClear(self):
        self.startHarvester(repository=REPOSITORY)
        self.assertEquals(BATCHSIZE, self.sizeDumpDir())

        header, result = getRequest(self.harvesterInternalServerPortNumber, '/get', {'verb': 'GetStatus', 'domainId': DOMAIN, 'repositoryId': REPOSITORY}, parse=False)
        data = JsonDict.loads(result)
        self.assertEquals(8, data['response']['GetStatus'][0]['total'])

        self.saveRepository(DOMAIN, REPOSITORY, REPOSITORYGROUP, action='clear')

        self.startHarvester(repository=REPOSITORY)
        self.assertEquals(18, self.sizeDumpDir())
        for filename in sorted(listdir(self.dumpDir))[-8:]:
            self.assertTrue('_delete.updateRequest' in filename, filename)

        header, result = getRequest(self.harvesterInternalServerPortNumber, '/get', {'verb': 'GetStatus', 'domainId': DOMAIN, 'repositoryId': REPOSITORY}, parse=False)
        self.assertEqual(0, JsonDict.loads(result)['response']['GetStatus'][0]['total'])

    def testRefresh(self):
        oldlogs = self.getLogs()
        log = HarvesterLog(stateDir=join(self.harvesterStateDir, DOMAIN), logDir=join(self.harvesterLogDir, DOMAIN), name=REPOSITORY)
        log.startRepository()
        for uploadId in ['%s:oai:record:%02d' % (REPOSITORY, i) for i in [1,7,120,121]]:
            log.notifyHarvestedRecord(uploadId)
            log.uploadIdentifier(uploadId)
        for uploadId in ['%s:oai:record:%02d' % (REPOSITORY, i) for i in [4,5,122,123]]:
            log.notifyHarvestedRecord(uploadId)
            log.deleteIdentifier(uploadId)
        log.endRepository('token', '2012-01-01T09:00:00Z')
        log.close()

        self.saveRepository(DOMAIN, REPOSITORY, REPOSITORYGROUP, action='refresh')

        self.startHarvester(repository=REPOSITORY)
        logs = self.getLogs()[len(oldlogs):]
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
        self.assertEquals(17, self.sizeDumpDir())
        deleteFiles = [join(self.dumpDir, f) for f in listdir(self.dumpDir) if '_delete' in f]
        deletedIds = set([xpathFirst(parse(open(x)), '//ucp:recordIdentifier/text()') for x in deleteFiles])
        self.assertEquals(set(['%s:oai:record:03' % REPOSITORY, '%s:oai:record:06' % REPOSITORY, '%s:oai:record:120' % REPOSITORY, '%s:oai:record:121' % REPOSITORY]), deletedIds)

        logs = self.getLogs()[len(oldlogs):]
        self.startHarvester(repository=REPOSITORY)
        self.assertEquals(len(logs), len(self.getLogs()[len(oldlogs):]), 'Action is over, expect nothing more.')

    def testInvalidIgnoredUptoMaxIgnore(self):
        maxIgnore = 5
        self.controlHelper(action='allInvalid')
        nrOfDeleted = 2
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
        self.saveRepository(DOMAIN, REPOSITORY, REPOSITORYGROUP, targetId='FILESYSTEM')
        self.startHarvester(repository=REPOSITORY)

        self.assertEquals(8, len(listdir(join(self.filesystemDir, REPOSITORYGROUP, REPOSITORY))))
        self.assertEquals(['%s:oai:record:%02d' % (REPOSITORY, i) for i in [3,6]],
                [id.strip() for id in open(join(self.filesystemDir, 'deleted_records'))])

    def testClearOnFilesystemTarget(self):
        self.saveRepository(DOMAIN, REPOSITORY, REPOSITORYGROUP, targetId='FILESYSTEM')
        self.startHarvester(repository=REPOSITORY)

        self.saveRepository(DOMAIN, REPOSITORY, REPOSITORYGROUP, targetId='FILESYSTEM', action='clear')
        self.startHarvester(repository=REPOSITORY)
        self.assertEquals(0, len(listdir(join(self.filesystemDir, REPOSITORYGROUP, REPOSITORY))))
        self.assertEquals(set([
                'harvestertestrepository:oai:record:10', 'harvestertestrepository:oai:record:09', 'harvestertestrepository:oai:record:08',
                'harvestertestrepository:oai:record:07', 'harvestertestrepository:oai:record:06', 'harvestertestrepository:oai:record:05',
                'harvestertestrepository:oai:record:04', 'harvestertestrepository:oai:record:03', 'harvestertestrepository:oai:record:02%2F&gkn',
                'harvestertestrepository:oai:record:01'
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

        self.saveRepository(DOMAIN, REPOSITORY, REPOSITORYGROUP, action='clear')
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
                uploadId = '%s:oai:record:02/&gkn' % (REPOSITORY)
            log.notifyHarvestedRecord(uploadId)
            log.uploadIdentifier(uploadId)
        for uploadId in ['%s:oai:record:%02d' % (REPOSITORY, i) for i in [4,5,122,123,124]]:
            log.notifyHarvestedRecord(uploadId)
            log.deleteIdentifier(uploadId)
        for uploadId in ['%s:oai:record:%02d' % (REPOSITORY, i) for i in [7,8,125,126,127,128]]:
            log.notifyHarvestedRecord(uploadId)
            log.logInvalidData(uploadId, 'ignored message')
            log.logIgnoredIdentifierWarning(uploadId)
        log.endRepository('token', '2012-01-01T09:00:00Z')
        log.close()
        totalRecords = 15
        oldUploads = 2
        oldDeletes = 3
        oldIgnoreds = 4

        self.saveRepository(DOMAIN, REPOSITORY, REPOSITORYGROUP, action='refresh')

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
        log.endRepository('token', '2012-01-01T09:00:00Z')
        log.close()
        oldUploads = 4
        oldDeletes = 5
        oldInvalids = 6

        self.saveRepository(DOMAIN, REPOSITORY, REPOSITORYGROUP, action='clear')

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
        self.assertEquals(set(['repository2', 'integrationtest', 'harvestertestrepository']), repositoryIdsSet)

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

    def testConcurrentHarvestToSruUpdateBUG(self):
        self.saveRepository(DOMAIN, REPOSITORY, REPOSITORYGROUP, complete=True)

        self.startHarvester(concurrency=1)

        requestsLogged = sorted(listdir(self.dumpDir))
        repositoryIds = []
        for f in requestsLogged:
            lxml = parse(open(join(self.dumpDir, f)))
            repositoryIds.append(xpath(lxml, '//ucp:recordIdentifier/text()')[0].split(':', 1)[0])
        self.assertEquals(15, repositoryIds.count(REPOSITORY))
        self.assertEquals(10, repositoryIds.count('repository2'))
        self.assertEquals(10, repositoryIds.count('integrationtest'))

    def testStartHarvestingAddedRepository(self):
        t = Thread(target=lambda: self.startHarvester(concurrency=1, runOnce=False))
        t.start()

        while not listdir(self.dumpDir):
            sleep(0.1)

        self.saveRepository(DOMAIN, 'xyz', REPOSITORYGROUP)
        stdoutfile = join(self.integrationTempdir, "stdouterr-meresco-harvester-harvester.log")
        sleepWheel(9)
        log = open(stdoutfile).read()
        try:
            self.assertTrue('xyz' in log, log)
        finally:
            self.removeRepository(DOMAIN, 'xyz', REPOSITORYGROUP)
            t.join()

    def testDontHarvestDeletedRepository(self):
        stdoutfile = join(self.integrationTempdir, "stdouterr-meresco-harvester-harvester.log")
        self.saveRepository(DOMAIN, 'xyz', REPOSITORYGROUP)
        t = Thread(target=lambda: self.startHarvester(concurrency=1, runOnce=False))
        t.start()

        while not listdir(self.dumpDir):
            sleep(0.1)
        sleepWheel(1)
        log = open(stdoutfile).read()
        xyzOccurrences = log.count('[xyz]')

        self.removeRepository(DOMAIN, 'xyz', REPOSITORYGROUP)
        sleepWheel(8)
        log = open(stdoutfile).read()
        try:
            self.assertFalse('Traceback' in log, log)
            newXyzOccurrences = log.count('[xyz]')
            self.assertEquals(xyzOccurrences, newXyzOccurrences, "%s!=%s\n%s" % (xyzOccurrences, newXyzOccurrences, log))
        finally:
            t.join()

    def testConcurrencyAtLeastOne(self):
        stdouterrlog = self.startHarvester(concurrency=0, expectedReturnCode=2)
        self.assertTrue("Concurrency must be at least 1" in stdouterrlog, stdouterrlog)

        stdouterrlog = self.startHarvester(concurrency=-1, expectedReturnCode=2)
        self.assertTrue("Concurrency must be at least 1" in stdouterrlog, stdouterrlog)

    def testCompleteInOnAttempt(self):
        self.saveRepository(DOMAIN, REPOSITORY, REPOSITORYGROUP, complete=True)
        stdouterrlog = self.startHarvester(repository=REPOSITORY, runOnce=True, timeoutInSeconds=5)
        self.assertEquals(15, self.sizeDumpDir())
        self.assertTrue("Repository will be completed in one attempt" in stdouterrlog, stdouterrlog)

    def testHarvestingContinues4Ever(self):
        try:
            self.startHarvester(repository=REPOSITORY, runOnce=False, timeoutInSeconds=5)
        except SystemExit, e:
            self.assertTrue('took more than 5 seconds' in str(e), str(e))
        self.assertEquals(15, self.sizeDumpDir())

    def emptyDumpDir(self):
        if listdir(self.dumpDir):
            system('rm %s/*' % self.dumpDir)

    def sizeDumpDir(self):
        return len(listdir(self.dumpDir))
