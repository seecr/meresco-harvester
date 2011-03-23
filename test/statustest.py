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

    def testGetStatusForRepoIdAndDomainId(self):
        stateDir = join(self.tempdir, "state")
        domainId = "domainId"
        repositoryId = "repoId"
        makedirs(join(stateDir, domainId))
        open(join(stateDir, domainId, "%s_ignored.ids" % repositoryId), 'w').write("ignoredId1\nignoredId2")
        s = Status(join(self.tempdir, "log"), stateDir)
        self.assertEqualsWS("""<GetStatus>
            <status repositoryId="repoId">
                <ignored>2</ignored>
            </status>
        </GetStatus>""", ''.join(s.getStatus(domainId, repositoryId)))
        self.assertEqualsWS("""<GetStatus>
            <status repositoryId="anotherRepoId">
                <ignored>0</ignored>
            </status>
        </GetStatus>""", ''.join(s.getStatus(domainId, "anotherRepoId")))

    def testGetStatusForDomainId(self):
        stateDir = join(self.tempdir, "state")
        logDir = join(self.tempdir, "log")
        domainId = "domainId"
        makedirs(join(stateDir, domainId))
        makedirs(join(logDir, domainId, "ignored", "repoId1"))
        makedirs(join(logDir, domainId, "ignored", "repoId2"))
        open(join(stateDir, domainId, "repoId1_ignored.ids"), 'w').write("ignoredId1\nignoredId2")
        open(join(stateDir, domainId, "repoId2_ignored.ids"), 'w').write("ignoredId3")
        s = Status(logDir, stateDir)
        self.assertEqualsWS("""<GetStatus>
            <status repositoryId="repoId1">
                <ignored>2</ignored>
            </status>
            <status repositoryId="repoId2">
                <ignored>1</ignored>
            </status>
        </GetStatus>""", ''.join(s.getStatus(domainId, None)))

    def testGetAllIgnoredRecords(self):
        stateDir = join(self.tempdir, "state")
        logDir = join(self.tempdir, "log")
        domainId = "domainId"
        makedirs(join(stateDir, domainId))
        makedirs(join(logDir, domainId, "ignored", "repoId1"))
        makedirs(join(logDir, domainId, "ignored", "repoId2"))
        open(join(stateDir, domainId, "repoId1_ignored.ids"), 'w').write("ignoredId1\nignoredId2")
        open(join(stateDir, domainId, "repoId2_ignored.ids"), 'w').write("ignoredId3")
        s = Status(logDir, stateDir)
        self.assertEquals(["ignoredId1", "ignoredId2"], s.ignoredRecords("domainId", "repoId1"))
