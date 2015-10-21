## begin license ##
#
# "Meresco Harvester" consists of two subsystems, namely an OAI-harvester and
# a web-control panel.
# "Meresco Harvester" is originally called "Sahara" and was developed for
# SURFnet by:
# Seek You Too B.V. (CQ2) http://www.cq2.nl
#
# Copyright (C) 2011-2012, 2015 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2012 Stichting Kennisnet http://www.kennisnet.nl
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

from os.path import join
from seecr.test import SeecrTestCase
from weightless.core import compose

from meresco.harvester.harvesterdata import HarvesterData

class HarvesterDataTest(SeecrTestCase):
    def setUp(self):
        SeecrTestCase.setUp(self)
        open(join(self.tempdir, 'adomain.domain'), 'w').write("""{
    "identifier": "adomain",
    "mappingIds": ["ignored MAPPING"],
    "repositoryGroupIds": ["Group1", "Group2"]
}""")
        open(join(self.tempdir, 'adomain.Group1.repositoryGroup'), 'w').write("""{
    "identifier": "Group1",
    "name": {"nl": "Groep1", "en": "Group1"},
    "repositoryIds": ["repository1", "repository2"]
}""")
        open(join(self.tempdir, 'adomain.Group2.repositoryGroup'), 'w').write("""{
    "identifier": "Group2",
    "name": {"nl": "Groep2", "en": "Group2"},
    "repositoryIds": ["repository2_1", "repository2_2"]
} """)
        open(join(self.tempdir, 'adomain.repository1.repository'), 'w').write("""{
    "identifier": "repository1",
    "repositoryGroupId": "Group1"
}""")
        open(join(self.tempdir, 'adomain.repository2.repository'), 'w').write("""{
    "identifier": "repository2",
    "repositoryGroupId": "Group1"
}""")
        open(join(self.tempdir, 'adomain.repository2_1.repository'), 'w').write("""{
    "identifier": "repository2_1",
    "repositoryGroupId": "Group2"
}""")
        open(join(self.tempdir, 'adomain.repository2_2.repository'), 'w').write("""{
    "identifier": "repository2_2",
    "repositoryGroupId": "Group2"
}""")
        open(join(self.tempdir, 'adomain.remi.repository'), 'w').write("""{
    "identifier": "remi",
    "repositoryGroupId": "NoGroup"
}""")
        self.hd = HarvesterData(self.tempdir)

    def testGetRepositoryGroupIds(self):
        self.assertEquals(["Group1", "Group2"], self.hd.getRepositoryGroupIds(domainId="adomain"))

    def testGetRepositoryIds(self):
        self.assertEquals(["repository1", "repository2"], self.hd.getRepositoryIds(domainId="adomain", repositoryGroupId="Group1"))
        self.assertEquals(["repository1", "repository2", "repository2_1", "repository2_2"], self.hd.getRepositoryIds(domainId="adomain"))

    def testGetRepositoryGroupId(self):
        self.assertEquals("Group1", self.hd.getRepositoryGroupId(domainId="adomain", repositoryId="repository1"))

    def testGetRepositories(self):
        result = self.hd.getRepositories(domainId='adomain')
        self.assertEqualsWS("""[
{
    "identifier": "repository1",
    "repositoryGroupId": "Group1"
},
{
    "identifier": "repository2",
    "repositoryGroupId": "Group1"
},
{
    "identifier": "repository2_1",
    "repositoryGroupId": "Group2"
},
{
    "identifier": "repository2_2",
    "repositoryGroupId": "Group2"
}
]""", result.dumps())

    def testGetRepositoriesWithError(self):
        result = ''.join(compose(self.hd.getRepositories(domainId='adomain', repositoryGroupId='doesnotexist')))
        self.assertEqualsWS("""<error code="idDoesNotExist">The value of an argument (id or key) is unknown or illegal.</error>""", result)
        result = ''.join(compose(self.hd.getRepositories(domainId='baddomain')))
        self.assertEqualsWS("""<error code="idDoesNotExist">The value of an argument (id or key) is unknown or illegal.</error>""", result)

    def testGetRepository(self):
        result = self.hd.getRepository(domainId='adomain', repositoryId='repository1')
        self.assertEqualsWS("""{
    "identifier": "repository1",
    "repositoryGroupId": "Group1"
}""", result)

    def testGetRepositoryWithErrors(self):
        result = ''.join(compose(self.hd.getRepository(domainId='adomain', repositoryId='repository12')))
        self.assertEqualsWS("""<error code="idDoesNotExist">The value of an argument (id or key) is unknown or illegal.</error>""", result)

    def testAddDomain(self):
        self.assertEqual([
                {'mappingIds': ['ignored MAPPING'], 'identifier': 'adomain', 'repositoryGroupIds': ['Group1', 'Group2']}
            ], self.hd.getDomains())
        self.hd.addDomain(domainId="newdomain")
        self.assertEqual([
                {'mappingIds': ['ignored MAPPING'], 'identifier': 'adomain', 'repositoryGroupIds': ['Group1', 'Group2']},
                {'id': 'newdomain'}
            ], self.hd.getDomains())
        try:
            self.hd.addDomain(domainId="newdomain")
            self.fail()
        except ValueError, e:
            self.assertEqual('The domain already exists.', str(e))
        try:
            self.hd.addDomain(domainId="domain#with#invalid%characters")
            self.fail()
        except ValueError, e:
            self.assertEqual('Name is not valid. Only use alphanumeric characters.', str(e))
        try:
            self.hd.addDomain(domainId="")
            self.fail()
        except ValueError, e:
            self.assertEqual('No name given.', str(e))
