## begin license ##
#
# "Meresco Harvester" consists of two subsystems, namely an OAI-harvester and
# a web-control panel.
# "Meresco Harvester" is originally called "Sahara" and was developed for
# SURFnet by:
# Seek You Too B.V. (CQ2) http://www.cq2.nl
#
# Copyright (C) 2011-2012, 2015-2016 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2012, 2015 Stichting Kennisnet http://www.kennisnet.nl
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

from meresco.harvester.harvesterdata import HarvesterData

class HarvesterDataTest(SeecrTestCase):
    def setUp(self):
        SeecrTestCase.setUp(self)
        open(join(self.tempdir, 'adomain.domain'), 'w').write("""{
    "identifier": "adomain",
    "mappingIds": ["ignored MAPPING"],
    "targetIds": ["ignored TARGET"],
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

    def testGetRepositoryGroup(self):
        self.assertEqual({
                'identifier': 'Group1',
                'name': {'en': 'Group1', 'nl': 'Groep1'},
                'repositoryIds': ['repository1', 'repository2']
            }, self.hd.getRepositoryGroup(identifier='Group1', domainId='adomain'))

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
        try:
            self.hd.getRepositories(domainId='adomain', repositoryGroupId='doesnotexist')
            self.fail()
        except ValueError, e:
            self.assertEqual('idDoesNotExist', str(e))

        try:
            self.hd.getRepositories(domainId='baddomain')
            self.fail()
        except ValueError, e:
            self.assertEqual('idDoesNotExist', str(e))

    def testGetRepository(self):
        result = self.hd.getRepository(domainId='adomain', identifier='repository1')
        self.assertEquals({
    "identifier": "repository1",
    "repositoryGroupId": "Group1"
}, result)

    def testGetRepositoryWithErrors(self):
        try:
            self.hd.getRepository(domainId='adomain', identifier='repository12')
            self.fail()
        except ValueError, e:
            self.assertEqual('idDoesNotExist', str(e))

    def testAddDomain(self):
        self.assertEqual(['adomain'], self.hd.getDomainIds())
        self.hd.addDomain(identifier="newdomain")
        self.assertEqual(['adomain', 'newdomain'], self.hd.getDomainIds())
        try:
            self.hd.addDomain(identifier="newdomain")
            self.fail()
        except ValueError, e:
            self.assertEqual('The domain already exists.', str(e))
        try:
            self.hd.addDomain(identifier="domain#with#invalid%characters")
            self.fail()
        except ValueError, e:
            self.assertEqual('Name is not valid. Only use alphanumeric characters.', str(e))
        try:
            self.hd.addDomain(identifier="")
            self.fail()
        except ValueError, e:
            self.assertEqual('No name given.', str(e))

    def testUpdateDomain(self):
        self.assertEqual('', self.hd.getDomain('adomain').get('description', ''))
        self.hd.updateDomain('adomain', description='Beschrijving')
        self.assertEqual('Beschrijving', self.hd.getDomain('adomain').get('description', ''))

    def testAddRepositoryGroup(self):
        self.assertEqual(['Group1', 'Group2'], self.hd.getRepositoryGroupIds(domainId='adomain'))
        self.hd.addRepositoryGroup(identifier="newgroup", domainId='adomain')
        self.assertEqual(['Group1', 'Group2', 'newgroup'], self.hd.getRepositoryGroupIds(domainId='adomain'))
        try:
            self.hd.addRepositoryGroup(identifier="Group1", domainId='adomain')
            self.fail()
        except ValueError, e:
            self.assertEqual('The repositoryGroup already exists.', str(e))
        try:
            self.hd.addRepositoryGroup(identifier="GROUP1", domainId='adomain')
            self.fail()
        except ValueError, e:
            self.assertEqual('The repositoryGroup already exists.', str(e))
        try:
            self.hd.addRepositoryGroup(identifier="group#with#invalid%characters", domainId='adomain')
            self.fail()
        except ValueError, e:
            self.assertEqual('Name is not valid. Only use alphanumeric characters.', str(e))
        try:
            self.hd.addRepositoryGroup(identifier="", domainId='adomain')
            self.fail()
        except ValueError, e:
            self.assertEqual('No name given.', str(e))

    def testUpdateRepositoryGroup(self):
        self.assertEqual('Groep1', self.hd.getRepositoryGroup('Group1', 'adomain').get('name', {}).get('nl', ''))
        self.hd.updateRepositoryGroup('Group1', domainId='adomain', name={"nl":"naam"})
        self.assertEqual('naam', self.hd.getRepositoryGroup('Group1', 'adomain')['name']['nl'])
        self.assertEqual('Group1', self.hd.getRepositoryGroup('Group1', 'adomain')['name']['en'])

    def testDeleteRepositoryGroup(self):
        self.assertEqual(['Group1', 'Group2'], self.hd.getRepositoryGroupIds(domainId='adomain'))
        self.hd.deleteRepositoryGroup('Group2', domainId='adomain')
        self.assertEqual(['Group1'], self.hd.getRepositoryGroupIds(domainId='adomain'))

    def testAddRepository(self):
        self.assertEqual(['repository1', 'repository2'], self.hd.getRepositoryIds(domainId='adomain', repositoryGroupId='Group1'))
        self.hd.addRepository(identifier="newrepo", domainId='adomain', repositoryGroupId='Group1')
        self.assertEqual(['repository1', 'repository2', 'newrepo'], self.hd.getRepositoryIds(domainId='adomain', repositoryGroupId='Group1'))
        self.assertEquals('Group1', self.hd.getRepository(identifier='newrepo', domainId='adomain')['repositoryGroupId'])
        try:
            self.hd.addRepository(identifier="repository1", domainId='adomain', repositoryGroupId='Group1')
            self.fail()
        except ValueError, e:
            self.assertEqual('The repository already exists.', str(e))
        try:
            self.hd.addRepository(identifier="Repository1", domainId='adomain', repositoryGroupId='Group1')
            self.fail()
        except ValueError, e:
            self.assertEqual('The repository already exists.', str(e))
        try:
            self.hd.addRepository(identifier="repository#with#invalid%characters", domainId='adomain', repositoryGroupId='Group1')
            self.fail()
        except ValueError, e:
            self.assertEqual('Name is not valid. Only use alphanumeric characters.', str(e))
        try:
            self.hd.addRepository(identifier="", domainId='adomain', repositoryGroupId='Group1')
            self.fail()
        except ValueError, e:
            self.assertEqual('No name given.', str(e))

    def testDeleteRepository(self):
        self.assertEqual(['repository1', 'repository2'], self.hd.getRepositoryIds(domainId='adomain', repositoryGroupId='Group1'))
        self.hd.deleteRepository(identifier="repository2", domainId='adomain', repositoryGroupId='Group1')
        self.assertEqual(['repository1'], self.hd.getRepositoryIds(domainId='adomain', repositoryGroupId='Group1'))

    def testUpdateRepository(self):
        self.hd.updateRepository('repository1',
                domainId='adomain',
                baseurl='baseurl',
                set='set',
                metadataPrefix='metadataPrefix',
                mappingId='mappingId',
                targetId='targetId',
                collection='collection',
                maximumIgnore=0,
                use=False,
                complete=True,
                continuous=True,
                action='action',
                shopclosed=['40:1:09:55-40:1:10:00'],
            )
        repository = self.hd.getRepository('repository1', 'adomain')
        self.assertEquals('baseurl', repository['baseurl'])
        self.assertEquals('set', repository['set'])
        self.assertEquals('metadataPrefix', repository['metadataPrefix'])
        self.assertEquals('mappingId', repository['mappingId'])
        self.assertEquals('targetId', repository['targetId'])
        self.assertEquals('collection', repository['collection'])
        self.assertEquals(0, repository['maximumIgnore'])
        self.assertEquals(False, repository['use'])
        self.assertEquals(True, repository['complete'])
        self.assertEquals(True, repository['continuous'])
        self.assertEquals('action', repository['action'])
        self.assertEquals(['40:1:09:55-40:1:10:00'], repository['shopclosed'])

    def testRepositoryDone(self):
        self.hd.updateRepository('repository1',
                domainId='adomain',
                baseurl='baseurl',
                set='set',
                metadataPrefix='metadataPrefix',
                mappingId='mappingId',
                targetId='targetId',
                collection='collection',
                maximumIgnore=0,
                use=False,
                complete=True,
                continuous=True,
                action='action',
                shopclosed=['40:1:09:55-40:1:10:00'],
            )
        self.hd.repositoryDone(identifier='repository1', domainId='adomain')
        repository = self.hd.getRepository('repository1', 'adomain')
        self.assertEqual(None, repository['action'])

    def testAddMapping(self):
        domain = self.hd.getDomain('adomain')
        self.assertEqual(['ignored MAPPING'], domain['mappingIds'])
        mappingId = self.hd.addMapping(name='newMapping', domainId='adomain')
        mappingIds = self.hd.getDomain('adomain')['mappingIds']
        self.assertEquals(2, len(mappingIds))
        mapping = self.hd.getMapping(mappingId)
        self.assertEquals(mappingId, mappingIds[-1])
        self.assertEqual('newMapping', mapping['name'])
        self.assertEqual('This mapping is what has become the default mapping for most Meresco based projects.\n', mapping['description'])
        self.assertTrue(len(mapping['code']) > 100)
        self.assertEqual(mappingIds[1], mapping['identifier'])
        try:
            self.hd.addMapping(name="", domainId='adomain')
            self.fail()
        except ValueError, e:
            self.assertEqual('No name given.', str(e))

    def testUpdateMapping(self):
        mappingId = self.hd.addMapping(name='newMapping', domainId='adomain')
        self.assertEqual(mappingId, self.hd.getMapping(mappingId)["identifier"])
        self.assertRaises(ValueError, lambda: self.hd.updateMapping(mappingId, name='newName', description="a description", code="new code"))
        self.assertEqual('newName', self.hd.getMapping(mappingId)['name'])
        self.assertEqual('a description', self.hd.getMapping(mappingId)['description'])
        self.assertEqual('new code', self.hd.getMapping(mappingId)['code'])

    def testDeleteMapping(self):
        mappingId = self.hd.addMapping(name='newMapping', domainId='adomain')
        self.assertEqual(['ignored MAPPING', mappingId], self.hd.getDomain('adomain')['mappingIds'])
        self.hd.deleteMapping(identifier=mappingId, domainId='adomain')
        self.assertEqual(['ignored MAPPING'], self.hd.getDomain('adomain')['mappingIds'])

    def testAddTarget(self):
        self.assertEquals(['ignored TARGET'], self.hd.getDomain('adomain')['targetIds'])
        targetId = self.hd.addTarget(name='new target', domainId='adomain', targetType='sruUpdate')
        targetIds = self.hd.getDomain('adomain')['targetIds']
        self.assertEquals(2, len(targetIds))
        target = self.hd.getTarget(targetId)
        self.assertEquals(targetId, targetIds[-1])
        self.assertEqual('new target', target['name'])
        self.assertEqual(targetId, target['identifier'])
        try:
            self.hd.addTarget(name="", domainId='adomain', targetType='sruUpdate')
            self.fail()
        except ValueError, e:
            self.assertEqual('No name given.', str(e))

    def testUpdateTarget(self):
        targetId = self.hd.addTarget(name='new target', domainId='adomain', targetType='sruUpdate')
        self.hd.updateTarget(identifier=targetId,
                name='updated target',
                username='username',
                port=1234,
                targetType='composite',
                delegateIds=['id1', 'id2'],
                path='path',
                baseurl='baseurl',
                oaiEnvelope=False,
            )
        target = self.hd.getTarget(targetId)
        self.assertEquals('updated target', target['name'])
        self.assertEquals('username', target['username'])
        self.assertEquals(1234, target['port'])
        self.assertEquals('composite', target['targetType'])
        self.assertEquals(['id1', 'id2'], target['delegateIds'])
        self.assertEquals('path', target['path'])
        self.assertEquals('baseurl', target['baseurl'])
        self.assertEquals(False, target['oaiEnvelope'])

    def testDeleteTarget(self):
        targetId = self.hd.addTarget(name='new target', domainId='adomain', targetType='sruUpdate')
        self.assertEquals(['ignored TARGET', targetId], self.hd.getDomain('adomain')['targetIds'])
        self.hd.deleteTarget(targetId, domainId='adomain')
        self.assertEquals(['ignored TARGET'], self.hd.getDomain('adomain')['targetIds'])


