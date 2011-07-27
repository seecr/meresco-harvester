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
from os import makedirs
from os.path import join

from cq2utils import CQ2TestCase, CallTrace

from meresco.harvester.repositorystatus import RepositoryStatus
from weightless.core import compose
from lxml.etree import tostring, parse
from StringIO import StringIO

class RepositoryStatusTest(CQ2TestCase):

    def setUp(self):
        CQ2TestCase.setUp(self)
        self.stateDir = join(self.tempdir, "state")
        self.logDir = join(self.tempdir, "log")
        self.domainId = "adomain"
        makedirs(join(self.stateDir, self.domainId))
        repoId1LogDir = join(self.logDir, self.domainId, "ignored", "repoId1")
        repoId2LogDir = join(self.logDir, self.domainId, "ignored", "repoId2")
        makedirs(repoId1LogDir)
        makedirs(repoId2LogDir)
        open(join(repoId1LogDir, "ignoredId1"), 'w').write("<diagnostic>ERROR1</diagnostic>")
        open(join(repoId1LogDir, "ignoredId2"), 'w').write("<diagnostic>ERROR2</diagnostic>")
        open(join(repoId2LogDir, "ignoredId3"), 'w').write("<diagnostic>ERROR3</diagnostic>")
        open(join(self.stateDir, self.domainId, "repoId1_ignored.ids"), 'w').write("ignoredId1\nignoredId2")
        open(join(self.stateDir, self.domainId, "repoId2_ignored.ids"), 'w').write("ignoredId3")
        open(join(self.stateDir, self.domainId, "repoId3_ignored.ids"), 'w').write("")
        self.status = RepositoryStatus(self.logDir, self.stateDir)
        observer = CallTrace("HarvesterData")
        observer.returnValues["getRepositoryGroupIds"] = ["repoGroupId1", "repoGroupId2"]
        def getRepositoryIds(domainId, repositoryGroupId):
            if repositoryGroupId == "repoGroupId1":
                return ["repoId1", "repoId2"]
            return ["repoId3", "anotherRepoId"]
        observer.methods["getRepositoryIds"] = getRepositoryIds
        def getRepositoryGroupId(domainId, repositoryId):
            return 'repoGroupId1' if repositoryId in ['repoId1', 'repoId2'] else 'repoGroupId2'
        observer.methods["getRepositoryGroupId"] = getRepositoryGroupId
        self.status.addObserver(observer)

    def testGetStatusForRepoIdAndDomainId(self):
        self.assertEqualsWS("""<GetStatus>
            <status repositoryId="repoId1" repositoryGroupId="repoGroupId1">
                <lastHarvestDate></lastHarvestDate>
                <harvested></harvested>
                <uploaded></uploaded>
                <deleted></deleted>
                <total></total>
                <totalerrors>0</totalerrors>
                <recenterrors></recenterrors>
                <ignored>2</ignored>
                <recentignores>
                    <ignoredId>ignoredId2</ignoredId>
                    <ignoredId>ignoredId1</ignoredId>
                </recentignores>
                <lastHarvestAttempt></lastHarvestAttempt>
            </status>
        </GetStatus>""", ''.join(compose(self.status.getStatus(domainId=self.domainId, repositoryId="repoId1"))))
        self.assertEqualsWS("""<GetStatus>
            <status repositoryId="anotherRepoId" repositoryGroupId="repoGroupId2">
                <lastHarvestDate></lastHarvestDate>
                <harvested></harvested>
                <uploaded></uploaded>
                <deleted></deleted>
                <total></total>
                <totalerrors>0</totalerrors>
                <recenterrors></recenterrors>
                <ignored>0</ignored>
                <recentignores></recentignores>
                <lastHarvestAttempt></lastHarvestAttempt>
            </status>
        </GetStatus>""", ''.join(compose(self.status.getStatus(domainId=self.domainId, repositoryId="anotherRepoId"))))

    def testGetStatusForDomainIdAndRepositoryGroupId(self):
        self.assertEqualsWS("""<GetStatus>
            <status repositoryId="repoId1" repositoryGroupId="repoGroupId1">
                <lastHarvestDate></lastHarvestDate>
                <harvested></harvested>
                <uploaded></uploaded>
                <deleted></deleted>
                <total></total>
                <totalerrors>0</totalerrors>
                <recenterrors></recenterrors>
                <ignored>2</ignored>
                <recentignores>
                    <ignoredId>ignoredId2</ignoredId>
                    <ignoredId>ignoredId1</ignoredId>
                </recentignores>
                <lastHarvestAttempt></lastHarvestAttempt>
            </status>
            <status repositoryId="repoId2" repositoryGroupId="repoGroupId1">
                <lastHarvestDate></lastHarvestDate>
                <harvested></harvested>
                <uploaded></uploaded>
                <deleted></deleted>
                <total></total>
                <totalerrors>0</totalerrors>
                <recenterrors></recenterrors>
                <ignored>1</ignored>
                <recentignores>
                    <ignoredId>ignoredId3</ignoredId>
                </recentignores>
                <lastHarvestAttempt></lastHarvestAttempt>
            </status>
            </GetStatus>""", ''.join(compose(self.status.getStatus(domainId=self.domainId, repositoryGroupId="repoGroupId1"))))

    def testGetStatusForDomainId(self):
        self.assertEqualsWS("""<GetStatus>
            <status repositoryId="repoId1" repositoryGroupId="repoGroupId1">
                <lastHarvestDate></lastHarvestDate>
                <harvested></harvested>
                <uploaded></uploaded>
                <deleted></deleted>
                <total></total>
                <totalerrors>0</totalerrors>
                <recenterrors></recenterrors>
                <ignored>2</ignored>
                <recentignores>
                    <ignoredId>ignoredId2</ignoredId>
                    <ignoredId>ignoredId1</ignoredId>
                </recentignores>
                <lastHarvestAttempt></lastHarvestAttempt>
            </status>
            <status repositoryId="repoId2" repositoryGroupId="repoGroupId1">
                <lastHarvestDate></lastHarvestDate>
                <harvested></harvested>
                <uploaded></uploaded>
                <deleted></deleted>
                <total></total>
                <totalerrors>0</totalerrors>
                <recenterrors></recenterrors>
                <ignored>1</ignored>
                <recentignores>
                    <ignoredId>ignoredId3</ignoredId>
                </recentignores>
                <lastHarvestAttempt></lastHarvestAttempt>
            </status>
            <status repositoryId="repoId3" repositoryGroupId="repoGroupId2">
                <lastHarvestDate></lastHarvestDate>
                <harvested></harvested>
                <uploaded></uploaded>
                <deleted></deleted>
                <total></total>
                <totalerrors>0</totalerrors>
                <recenterrors></recenterrors>
                <ignored>0</ignored>
                <recentignores></recentignores>
                <lastHarvestAttempt></lastHarvestAttempt>
            </status>
            <status repositoryId="anotherRepoId" repositoryGroupId="repoGroupId2">
                <lastHarvestDate></lastHarvestDate>
                <harvested></harvested>
                <uploaded></uploaded>
                <deleted></deleted>
                <total></total>
                <totalerrors>0</totalerrors>
                <recenterrors></recenterrors>
                <ignored>0</ignored>
                <recentignores></recentignores>
                <lastHarvestAttempt></lastHarvestAttempt>
            </status>
        </GetStatus>""", ''.join(compose(self.status.getStatus(self.domainId))))

    def testGetAllIgnoredRecords(self):
        def ignoredRecords(repoId):
            return list(self.status.ignoredRecords(self.domainId, repoId))
        self.assertEquals(["ignoredId2", "ignoredId1"], ignoredRecords("repoId1"))
        self.assertEquals(["ignoredId3"], ignoredRecords("repoId2"))
        self.assertEquals([], ignoredRecords("repoId3"))
        self.assertEquals([], ignoredRecords("repoId4"))

    def testGetIgnoredRecord(self):
        def getIgnoredRecord(repoId, recordId):
            return tostring(self.status.getIgnoredRecord(self.domainId, repoId, recordId)) 
        self.assertEquals("<diagnostic>ERROR1</diagnostic>", getIgnoredRecord("repoId1", "ignoredId1")) 
        self.assertEquals("<diagnostic>ERROR2</diagnostic>", getIgnoredRecord("repoId1", "ignoredId2")) 
        self.assertEquals("<diagnostic>ERROR3</diagnostic>", getIgnoredRecord("repoId2", "ignoredId3")) 

    def testLotOfIgnoresGivesOnly10(self):
        with open(join(self.stateDir, self.domainId, "repoId1_ignored.ids"), 'w') as f:
            for i in range(20):
                f.write("ignoredId%d\n" % i)
        lxmlResult = parse(StringIO(''.join(compose(self.status.getStatus(domainId=self.domainId, repositoryId="repoId1")))))
        self.assertEquals("20", lxmlResult.xpath("/GetStatus/status/ignored/text()")[0])
        self.assertEquals(10, len(lxmlResult.xpath("/GetStatus/status/recentignores/ignoredId")))

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
        self.assertEqualsWS("""<GetStatus>
<status repositoryId="repoId1" repositoryGroupId="repoGroupId1">
  <lastHarvestDate>2005-08-24T00:00:00Z</lastHarvestDate>
  <harvested>8</harvested>
  <uploaded>4</uploaded>
  <deleted>3</deleted>
  <total>20</total>
  <totalerrors>1</totalerrors>
  <recenterrors>
    <error date="2005-08-24T20:00:00Z">Error With Scary Characters &lt; &amp; &gt; " '</error>
  </recenterrors>
  <ignored>2</ignored>
  <recentignores>
    <ignoredId>ignoredId2</ignoredId>
    <ignoredId>ignoredId1</ignoredId>
  </recentignores>
  <lastHarvestAttempt>2005-08-24T20:00:00Z</lastHarvestAttempt>
</status>
</GetStatus>""", ''.join(compose(self.status.getStatus(domainId=self.domainId, repositoryId='repoId1'))))
