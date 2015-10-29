## begin license ##
#
# "Meresco Harvester" consists of two subsystems, namely an OAI-harvester and
# a web-control panel.
# "Meresco Harvester" is originally called "Sahara" and was developed for
# SURFnet by:
# Seek You Too B.V. (CQ2) http://www.cq2.nl
#
# Copyright (C) 2011-2012, 2015 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2011 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2011-2012, 2015 Stichting Kennisnet http://www.kennisnet.nl
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

from os import makedirs
from os.path import join

from lxml.etree import tostring
from simplejson import dump as jsonDump

from seecr.test import SeecrTestCase, CallTrace

from escaping import escapeFilename
from meresco.harvester.repositorystatus import RepositoryStatus


class RepositoryStatusTest(SeecrTestCase):
    def setUp(self):
        SeecrTestCase.setUp(self)
        self.stateDir = join(self.tempdir, "state")
        self.logDir = join(self.tempdir, "log")
        self.domainId = "adomain"
        makedirs(join(self.stateDir, self.domainId))
        repoId1LogDir = join(self.logDir, self.domainId, "invalid", "repoId1")
        repoId2LogDir = join(self.logDir, self.domainId, "invalid", escapeFilename("repoId/2"))
        makedirs(repoId1LogDir)
        makedirs(repoId2LogDir)
        open(join(repoId1LogDir, "invalidId1"), 'w').write("<diagnostic>ERROR1</diagnostic>")
        open(join(repoId1LogDir, "invalidId&2"), 'w').write("<diagnostic>ERROR2</diagnostic>")
        open(join(repoId2LogDir, escapeFilename("invalidId/3")), 'w').write("<diagnostic>ERROR3</diagnostic>")
        open(join(self.stateDir, self.domainId, "repoId1_invalid.ids"), 'w').write("invalidId1\ninvalidId&2")
        open(join(self.stateDir, self.domainId, escapeFilename("repoId/2_invalid.ids")), 'w').write("invalidId/3")
        open(join(self.stateDir, self.domainId, "repoId3_invalid.ids"), 'w').write("")
        self.status = RepositoryStatus(self.logDir, self.stateDir)
        observer = CallTrace("HarvesterData")
        observer.returnValues["getRepositoryGroupIds"] = ["repoGroupId1", "repoGroupId2"]
        def getRepositoryIds(domainId, repositoryGroupId):
            if repositoryGroupId == "repoGroupId1":
                return ["repoId1", "repoId/2"]
            return ["repoId3", "anotherRepoId"]
        observer.methods["getRepositoryIds"] = getRepositoryIds
        def getRepositoryGroupId(domainId, repositoryId):
            return 'repoGroupId1' if repositoryId in ['repoId1', 'repoId/2'] else 'repoGroupId2'
        observer.methods["getRepositoryGroupId"] = getRepositoryGroupId
        self.status.addObserver(observer)

    def testGetRunningStatesForDomain(self):
        jsonDump(
                {'changedate': "2012-08-14 12:00:00",'status': "Ok", 'message': ""},
                open(join(self.stateDir, self.domainId, "repoId1.running"), 'w')
        )
        jsonDump(
                {'changedate': "2012-08-13 12:00:00",'status': "Error", 'message': "an error message"},
                open(join(self.stateDir, self.domainId, "repoId3.running"), 'w')
        )
        jsonDump(
                {'changedate': "2012-08-16 12:00:00",'status': "Ok", 'message': ""},
                open(join(self.stateDir, self.domainId, "anotherRepoId.running"), 'w')
        )

        expected = [
            {'repositoryId': 'anotherRepoId', 'changedate': "2012-08-16 12:00:00",'status': "Ok", 'message': ""},
            {'repositoryId': 'repoId1', 'changedate': "2012-08-14 12:00:00",'status': "Ok", 'message': ""},
            {'repositoryId': 'repoId3', 'changedate': "2012-08-13 12:00:00",'status': "Error", 'message': "an error message"},
        ]
        self.assertEquals(expected, self.status.getRunningStatesForDomain(self.domainId))


    def testGetStatusForRepoIdAndDomainId(self):
        self.assertEquals([{
                        "repositoryId": "repoId1",
                        "repositoryGroupId": "repoGroupId1",
                        "lastHarvestDate": None,
                        "harvested": 0,
                        "uploaded": 0,
                        "deleted": 0,
                        "total": 0,
                        "totalerrors": 0,
                        "recenterrors": [],
                        "invalid": 2,
                        "recentinvalids": [
                            "invalidId&2",
                            "invalidId1"
                        ],
                        "lastHarvestAttempt": None
                    }], self.status.getStatus(domainId=self.domainId, repositoryId="repoId1"))
        self.assertEquals([{
                        "repositoryId": "anotherRepoId",
                        "repositoryGroupId": "repoGroupId2",
                        "lastHarvestDate": None,
                        "harvested": 0,
                        "uploaded": 0,
                        "deleted": 0,
                        "total": 0,
                        "totalerrors": 0,
                        "recenterrors": [],
                        "invalid": 0,
                        "recentinvalids": [],
                        "lastHarvestAttempt": None
                    }], self.status.getStatus(domainId=self.domainId, repositoryId="anotherRepoId"))

    def testGetStatusForDomainIdAndRepositoryGroupId(self):
        self.assertEquals([{
                        "repositoryId": "repoId1",
                        "repositoryGroupId": "repoGroupId1",
                        "lastHarvestDate": None,
                        "harvested": 0,
                        "uploaded": 0,
                        "deleted": 0,
                        "total": 0,
                        "totalerrors": 0,
                        "recenterrors": [],
                        "invalid": 2,
                        "recentinvalids": [
                            "invalidId&2",
                            "invalidId1"
                        ],
                        "lastHarvestAttempt": None
                    }, {
                        "repositoryId": "repoId/2",
                        "repositoryGroupId": "repoGroupId1",
                        "lastHarvestDate": None,
                        "harvested": 0,
                        "uploaded": 0,
                        "deleted": 0,
                        "total": 0,
                        "totalerrors": 0,
                        "recenterrors": [],
                        "invalid": 1,
                        "recentinvalids": ['invalidId/3'],
                        "lastHarvestAttempt": None
                    }], self.status.getStatus(domainId=self.domainId, repositoryGroupId='repoGroupId1'))

    def testGetStatusForDomainId(self):
        self.assertEquals([{
                        "repositoryId": "repoId1",
                        "repositoryGroupId": "repoGroupId1",
                        "lastHarvestDate": None,
                        "harvested": 0,
                        "uploaded": 0,
                        "deleted": 0,
                        "total": 0,
                        "totalerrors": 0,
                        "recenterrors": [],
                        "invalid": 2,
                        "recentinvalids": [
                            "invalidId&2",
                            "invalidId1"
                        ],
                        "lastHarvestAttempt": None
                    }, {
                        "repositoryId": "repoId/2",
                        "repositoryGroupId": "repoGroupId1",
                        "lastHarvestDate": None,
                        "harvested": 0,
                        "uploaded": 0,
                        "deleted": 0,
                        "total": 0,
                        "totalerrors": 0,
                        "recenterrors": [],
                        "invalid": 1,
                        "recentinvalids": ['invalidId/3'],
                        "lastHarvestAttempt": None
                    }, {
                        "repositoryId": "repoId3",
                        "repositoryGroupId": "repoGroupId2",
                        "lastHarvestDate": None,
                        "harvested": 0,
                        "uploaded": 0,
                        "deleted": 0,
                        "total": 0,
                        "totalerrors": 0,
                        "recenterrors": [],
                        "invalid": 0,
                        "recentinvalids": [],
                        "lastHarvestAttempt": None
                    }, {
                        "repositoryId": "anotherRepoId",
                        "repositoryGroupId": "repoGroupId2",
                        "lastHarvestDate": None,
                        "harvested": 0,
                        "uploaded": 0,
                        "deleted": 0,
                        "total": 0,
                        "totalerrors": 0,
                        "recenterrors": [],
                        "invalid": 0,
                        "recentinvalids": [],
                        "lastHarvestAttempt": None
                    }], self.status.getStatus(domainId=self.domainId))

    def testGetAllInvalidRecords(self):
        def invalidRecords(repoId):
            return list(self.status.invalidRecords(self.domainId, repoId))
        self.assertEquals(["invalidId&2", "invalidId1"], invalidRecords("repoId1"))
        self.assertEquals(["invalidId/3"], invalidRecords("repoId/2"))
        self.assertEquals([], invalidRecords("repoId3"))
        self.assertEquals([], invalidRecords("repoId4"))

    def testGetInvalidRecord(self):
        def getInvalidRecord(repoId, recordId):
            return tostring(self.status.getInvalidRecord(self.domainId, repoId, recordId))
        self.assertEquals("<diagnostic>ERROR1</diagnostic>", getInvalidRecord("repoId1", "invalidId1"))
        self.assertEquals("<diagnostic>ERROR2</diagnostic>", getInvalidRecord("repoId1", "invalidId&2"))
        self.assertEquals("<diagnostic>ERROR3</diagnostic>", getInvalidRecord("repoId/2", "invalidId/3"))

    def testRecentInvalidsOnlyGives10InCaseOfManyMoreInvalids(self):
        with open(join(self.stateDir, self.domainId, "repoId1_invalid.ids"), 'w') as f:
            for i in range(20):
                f.write("invalidId%d\n" % i)
        status = self.status.getStatus(domainId=self.domainId, repositoryId="repoId1")
        self.assertEquals(20, status[0]['invalid'])
        self.assertEquals(10, len(status[0]['recentinvalids']))

    def testSucces(self):
        logLine = '\t'.join(['[2006-03-13 12:13:14]', 'SUCCES', 'repoId1', 'Harvested/Uploaded/Deleted/Total: 200/199/1/1542, ResumptionToken: None'])
        open(join(self.logDir, self.domainId, 'repoId1.events'), 'w').write(logLine)
        state = self.status._parseEventsFile(domainId=self.domainId, repositoryId='repoId1')
        self.assertEquals('2006-03-13T12:13:14Z', state["lastHarvestDate"])
        self.assertEquals('200', state["harvested"])
        self.assertEquals('199', state["uploaded"])
        self.assertEquals('1', state["deleted"])
        self.assertEquals('1542', state["total"])
        self.assertEquals(0, state["totalerrors"])
        self.assertEquals([], state["recenterrors"])

    def testOnlyErrors(self):
        logLine = '\t'.join(['[2006-03-11 12:13:14]', 'ERROR', 'repoId1', 'Sorry, but the VM has crashed.'])
        open(join(self.logDir, self.domainId, 'repoId1.events'), 'w').write(logLine)
        state = self.status._parseEventsFile(domainId=self.domainId, repositoryId='repoId1')
        self.assertTrue("lastHarvestDate" not in state, state.keys())
        self.assertTrue("harvested" not in state, state.keys())
        self.assertTrue("uploaded" not in state, state.keys())
        self.assertTrue("deleted" not in state, state.keys())
        self.assertTrue("total" not in state, state.keys())
        self.assertEquals(1, state["totalerrors"])
        self.assertEquals("2006-03-11T12:13:14Z", state["lastHarvestAttempt"])
        self.assertEquals([('2006-03-11T12:13:14Z','Sorry, but the VM has crashed.')], state["recenterrors"])

    def testTwoErrors(self):
        logLine1 = '\t'.join(['[2006-03-11 12:13:14]', 'ERROR', 'repoId1', 'Sorry, but the VM has crashed.'])
        logLine2 = '\t'.join(['[2006-03-11 12:14:14]', 'ERROR', 'repoId1', 'java.lang.NullPointerException.'])
        open(join(self.logDir, self.domainId, 'repoId1.events'), 'w').write(logLine1 + "\n" + logLine2)
        state = self.status._parseEventsFile(domainId=self.domainId, repositoryId='repoId1')
        self.assertEquals(2, state["totalerrors"])
        self.assertEquals("2006-03-11T12:14:14Z", state["lastHarvestAttempt"])
        self.assertEquals([('2006-03-11T12:14:14Z', 'java.lang.NullPointerException.'), ('2006-03-11T12:13:14Z','Sorry, but the VM has crashed.')], state["recenterrors"])

    def testErrorAfterSucces(self):
        logLine1 = '\t'.join(['[2006-03-11 12:13:14]', 'SUCCES', 'repoId1', 'Harvested/Uploaded/Deleted/Total: 200/199/1/1542, ResumptionToken: abcdef'])
        logLine2 = '\t'.join(['[2006-03-11 12:14:14]', 'ERROR', 'repoId1', 'java.lang.NullPointerException.'])
        open(join(self.logDir, self.domainId, 'repoId1.events'), 'w').write(logLine1 + "\n" + logLine2)
        state = self.status._parseEventsFile(domainId=self.domainId, repositoryId='repoId1')
        self.assertEquals("2006-03-11T12:13:14Z", state["lastHarvestDate"])
        self.assertEquals("200", state["harvested"])
        self.assertEquals("199", state["uploaded"])
        self.assertEquals("1", state["deleted"])
        self.assertEquals("1542", state["total"])
        self.assertEquals(1, state["totalerrors"])
        self.assertEquals("2006-03-11T12:14:14Z", state["lastHarvestAttempt"])
        self.assertEquals([('2006-03-11T12:14:14Z', 'java.lang.NullPointerException.')], state["recenterrors"])

    def testErrorBeforeSucces(self):
        logLine1 = '\t'.join(['[2006-03-11 12:13:14]', 'ERROR', 'repoId1', 'java.lang.NullPointerException.'])
        logLine2 = '\t'.join(['[2006-03-11 12:14:14]', 'SUCCES', 'repoId1', 'Harvested/Uploaded/Deleted/Total: 200/199/1/1542, ResumptionToken: abcdef'])
        open(join(self.logDir, self.domainId, 'repoId1.events'), 'w').write(logLine1 + "\n" + logLine2)
        state = self.status._parseEventsFile(domainId=self.domainId, repositoryId='repoId1')
        self.assertEquals("2006-03-11T12:14:14Z", state["lastHarvestDate"])
        self.assertEquals("200", state["harvested"])
        self.assertEquals("199", state["uploaded"])
        self.assertEquals("1", state["deleted"])
        self.assertEquals("1542", state["total"])
        self.assertEquals(0, state["totalerrors"])
        self.assertEquals([], state["recenterrors"])
        self.assertEquals("2006-03-11T12:14:14Z", state["lastHarvestAttempt"])

    def testLotOfErrors(self):
        with open(join(self.logDir, self.domainId, 'repoId1.events'), 'w') as f:
            for i in range(20):
                logLine = '\t'.join(['[2006-03-11 12:%.2d:14]' % i, 'ERROR', 'repoId1', 'Error %d, Crash' % i])
                f.write(logLine + "\n")
        state = self.status._parseEventsFile(domainId=self.domainId, repositoryId='repoId1')
        self.assertEquals(20, state["totalerrors"])
        self.assertEquals(10, len(state["recenterrors"]))
        self.assertEquals([('2006-03-11T12:19:14Z', 'Error 19, Crash'), ('2006-03-11T12:18:14Z', 'Error 18, Crash'), ('2006-03-11T12:17:14Z', 'Error 17, Crash'), ('2006-03-11T12:16:14Z', 'Error 16, Crash'), ('2006-03-11T12:15:14Z', 'Error 15, Crash'), ('2006-03-11T12:14:14Z', 'Error 14, Crash'), ('2006-03-11T12:13:14Z', 'Error 13, Crash'), ('2006-03-11T12:12:14Z', 'Error 12, Crash'), ('2006-03-11T12:11:14Z', 'Error 11, Crash'), ('2006-03-11T12:10:14Z', 'Error 10, Crash')], state["recenterrors"])

    def testIntegration(self):
        open(join(self.logDir, self.domainId, 'repoId1.events'), 'w').write("""[2005-08-20 20:00:00.456]\tERROR\t[repositoryId]\tError 1
[2005-08-21 20:00:00.456]\tSUCCES\t[repositoryId]\tHarvested/Uploaded/Deleted/Total: 4/3/2/10
[2005-08-22 00:00:00.456]\tSUCCES\t[repositoryId]\tHarvested/Uploaded/Deleted/Total: 8/4/3/16
[2005-08-22 20:00:00.456]\tERROR\t[repositoryId]\tError 2
[2005-08-23 20:00:00.456]\tERROR\t[repositoryId]\tError 3
[2005-08-23 20:00:01.456]\tERROR\t[repositoryId]\tError 4
[2005-08-23 20:00:02.456]\tERROR\t[repositoryId]\tError 5
[2005-08-24 00:00:00.456]\tSUCCES\t[repositoryId]\tHarvested/Uploaded/Deleted/Total: 8/4/3/20
[2005-08-24 20:00:00.456]\tERROR\t[repositoryId]\tError With Scary Characters < & > " '
""")
        self.assertEquals([{
                "repositoryId": "repoId1",
                "repositoryGroupId": "repoGroupId1",
                "lastHarvestDate": "2005-08-24T00:00:00Z",
                "harvested": 8,
                "uploaded": 4,
                "deleted": 3,
                "total": 20,
                "totalerrors": 1,
                "recenterrors": [dict(date="2005-08-24T20:00:00Z", error='Error With Scary Characters < & > " \'')],
                "invalid": 2,
                "recentinvalids": ['invalidId&2', 'invalidId1'],
                "lastHarvestAttempt": "2005-08-24T20:00:00Z"
            }], self.status.getStatus(domainId=self.domainId, repositoryId='repoId1'))
