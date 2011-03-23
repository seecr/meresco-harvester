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
        open(join(repoId1LogDir, "ignoredId1"), 'w').write("ERROR1")
        open(join(repoId1LogDir, "ignoredId2"), 'w').write("ERROR2")
        open(join(repoId2LogDir, "ignoredId3"), 'w').write("ERROR3")
        open(join(stateDir, self.domainId, "repoId1_ignored.ids"), 'w').write("ignoredId1\nignoredId2")
        open(join(stateDir, self.domainId, "repoId2_ignored.ids"), 'w').write("ignoredId3")
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
        self.assertEquals(["ignoredId1", "ignoredId2"], self.status.ignoredRecords(self.domainId, "repoId1"))
        self.assertEquals(["ignoredId3"], self.status.ignoredRecords(self.domainId, "repoId2"))

    def testGetIgnoredRecord(self):
        self.assertEquals("ERROR1", self.status.getIgnoredRecord(self.domainId, "repoId1", "ignoredId1")) 
        self.assertEquals("ERROR2", self.status.getIgnoredRecord(self.domainId, "repoId1", "ignoredId2")) 
        self.assertEquals("ERROR3", self.status.getIgnoredRecord(self.domainId, "repoId2", "ignoredId3")) 
