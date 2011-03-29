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

from os import makedirs
from os.path import join

from cq2utils import CQ2TestCase

from meresco.harvester.status import Status
from lxml.etree import tostring

class StatusTest(CQ2TestCase):

    def setUp(self):
        CQ2TestCase.setUp(self)
        stateDir = join(self.tempdir, "state")
        logDir = join(self.tempdir, "log")
        self.domainId = "adomain"
        makedirs(join(stateDir, self.domainId))
        repoId1LogDir = join(logDir, self.domainId, "ignored", "repoId1")
        repoId2LogDir = join(logDir, self.domainId, "ignored", "repoId2")
        makedirs(repoId1LogDir)
        makedirs(repoId2LogDir)
        open(join(repoId1LogDir, "ignoredId1"), 'w').write("<diagnostic>ERROR1</diagnostic>")
        open(join(repoId1LogDir, "ignoredId2"), 'w').write("<diagnostic>ERROR2</diagnostic>")
        open(join(repoId2LogDir, "ignoredId3"), 'w').write("<diagnostic>ERROR3</diagnostic>")
        open(join(stateDir, self.domainId, "repoId1_ignored.ids"), 'w').write("ignoredId1\nignoredId2")
        open(join(stateDir, self.domainId, "repoId2_ignored.ids"), 'w').write("ignoredId3")
        open(join(stateDir, self.domainId, "repoId3_ignored.ids"), 'w').write("")
        self.status = Status(logDir, stateDir)

    def testGetStatusForRepoIdAndDomainId(self):
        self.assertEqualsWS("""<GetStatus>
            <status repositoryId="repoId1">
                <ignored>2</ignored>
            </status>
        </GetStatus>""", ''.join(self.status.getStatus(self.domainId, "repoId1")))
        self.assertEqualsWS("""<GetStatus>
            <status repositoryId="anotherRepoId">
                <ignored>0</ignored>
            </status>
        </GetStatus>""", ''.join(self.status.getStatus(self.domainId, "anotherRepoId")))

    def testGetStatusForDomainId(self):
        self.assertEqualsWS("""<GetStatus>
            <status repositoryId="repoId1">
                <ignored>2</ignored>
            </status>
            <status repositoryId="repoId2">
                <ignored>1</ignored>
            </status>
        </GetStatus>""", ''.join(self.status.getStatus(self.domainId, None)))

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
