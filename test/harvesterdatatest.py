## begin license ##
# 
# "Meresco Harvester" consists of two subsystems, namely an OAI-harvester and
# a web-control panel.
# "Meresco Harvester" is originally called "Sahara" and was developed for 
# SURFnet by:
# Seek You Too B.V. (CQ2) http://www.cq2.nl 
# 
# Copyright (C) 2011-2012 Seecr (Seek You Too B.V.) http://seecr.nl
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
        open(join(self.tempdir, 'adomain.domain'), 'w').write("""<?xml version="1.0" encoding="UTF-8"?>
<domain>
    <id>adomain</id>
    <mappingId>ignored MAPPING</mappingId>
    <repositoryGroupId>Group1</repositoryGroupId>
    <repositoryGroupId>Group2</repositoryGroupId>
</domain>""")
        open(join(self.tempdir, 'adomain.Group1.repositoryGroup'), 'w').write("""<?xml version="1.0" encoding="UTF-8"?>
<repositoryGroup>
  <id>Group1</id>
  <name xml:lang="nl">Groep1</name>
  <name xml:lang="en">Group1</name>
  <repositoryId>repository1</repositoryId>
  <repositoryId>repository2</repositoryId>
</repositoryGroup>""")
        open(join(self.tempdir, 'adomain.Group2.repositoryGroup'), 'w').write("""<?xml version="1.0" encoding="UTF-8"?>
<repositoryGroup>
  <id>Group2</id>
  <name xml:lang="nl">Groep2</name>
  <name xml:lang="en">Group2</name>
  <repositoryId>repository2_1</repositoryId>
  <repositoryId>repository2_2</repositoryId>
</repositoryGroup>""")
        open(join(self.tempdir, 'adomain.repository1.repository'), 'w').write("""<?xml version="1.0" encoding="UTF-8"?>
<repository>
  <id>repository1</id>
  <repositoryGroupId>Group1</repositoryGroupId>
</repository>""")
        open(join(self.tempdir, 'adomain.repository2.repository'), 'w').write("""<repository>
  <id>repository2</id>
  <repositoryGroupId>Group1</repositoryGroupId>
</repository>""")
        open(join(self.tempdir, 'adomain.repository2_1.repository'), 'w').write("""<?xml version="1.0" encoding="UTF-8"?>
<repository>
  <id>repository2_1</id>
  <repositoryGroupId>Group2</repositoryGroupId>
</repository>""")
        open(join(self.tempdir, 'adomain.repository2_2.repository'), 'w').write("""<?xml version="1.0" encoding="UTF-8"?>
<repository>
  <id>repository2_2</id>
  <repositoryGroupId>Group2</repositoryGroupId>
</repository>""")
        open(join(self.tempdir, 'adomain.remi.repository'), 'w').write("""<?xml version="1.0" encoding="UTF-8"?>
<repository>
  <id>remi</id>
  <repositoryGroupId>NoGroup</repositoryGroupId>
</repository>""")
        self.hd = HarvesterData(self.tempdir)

    def testGetRepositoryGroupIds(self):
        self.assertEquals(["Group1", "Group2"], self.hd.getRepositoryGroupIds(domainId="adomain"))
 
    def testGetRepositoryIds(self):
        self.assertEquals(["repository1", "repository2"], self.hd.getRepositoryIds(domainId="adomain", repositoryGroupId="Group1"))
        self.assertEquals(["repository1", "repository2", "repository2_1", "repository2_2"], self.hd.getRepositoryIds(domainId="adomain"))

    def testGetRepositoryGroupId(self):
        self.assertEquals("Group1", self.hd.getRepositoryGroupId(domainId="adomain", repositoryId="repository1"))

    def testGetRepositoryAsXml(self):
        expected = """<repository>
  <id>repository1</id>
  <repositoryGroupId>Group1</repositoryGroupId>
</repository>"""
        self.assertEquals(expected, self.hd.getRepositoryAsXml(domainId='adomain', repositoryId='repository1'))

    def testGetRepositoryAsXmlWithoutXMLHeader(self):
        expected = """<repository>
  <id>repository2</id>
  <repositoryGroupId>Group1</repositoryGroupId>
</repository>"""
        self.assertEquals(expected, self.hd.getRepositoryAsXml(domainId='adomain', repositoryId='repository2'))

    def testGetRepositories(self):
        result = ''.join(compose(self.hd.getRepositories(domainId='adomain')))
        self.assertEqualsWS("""<GetRepositories>
<repository>
    <id>repository1</id>
    <repositoryGroupId>Group1</repositoryGroupId>
</repository><repository>
    <id>repository2</id>
        <repositoryGroupId>Group1</repositoryGroupId>
</repository><repository>
    <id>repository2_1</id>
    <repositoryGroupId>Group2</repositoryGroupId>
</repository><repository>
    <id>repository2_2</id>
    <repositoryGroupId>Group2</repositoryGroupId>
</repository>
        </GetRepositories>""", result)

    def testGetRepositoriesWithError(self):
        result = ''.join(compose(self.hd.getRepositories(domainId='adomain', repositoryGroupId='doesnotexist')))
        self.assertEqualsWS("""<error code="idDoesNotExist">The value of an argument (id or key) is unknown or illegal.</error>""", result)
        result = ''.join(compose(self.hd.getRepositories(domainId='baddomain')))
        self.assertEqualsWS("""<error code="idDoesNotExist">The value of an argument (id or key) is unknown or illegal.</error>""", result)

    def testGetRepository(self):
        result = ''.join(compose(self.hd.getRepository(domainId='adomain', repositoryId='repository1')))
        self.assertEqualsWS("""<GetRepository>
<repository>
    <id>repository1</id>
    <repositoryGroupId>Group1</repositoryGroupId>
</repository>
</GetRepository>""", result)

    def testGetRepositoryWithErrors(self):
        result = ''.join(compose(self.hd.getRepository(domainId='adomain', repositoryId='repository12')))
        self.assertEqualsWS("""<error code="idDoesNotExist">The value of an argument (id or key) is unknown or illegal.</error>""", result)
