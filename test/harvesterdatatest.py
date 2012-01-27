## begin license ##
# 
# "Meresco Harvester" consists of two subsystems, namely an OAI-harvester and
# a web-control panel.
# "Meresco Harvester" is originally called "Sahara" and was developed for 
# SURFnet by:
# Seek You Too B.V. (CQ2) http://www.cq2.nl 
# 
# Copyright (C) 2011 Seecr (Seek You Too B.V.) http://seecr.nl
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

    def testGetRepositoryGroupIds(self):
        open(join(self.tempdir, 'adomain.domain'), 'w').write("""<?xml version="1.0" encoding="UTF-8"?>
<domain>
    <id>adomain</id>
    <mappingId>ignored MAPPING</mappingId>
    <repositoryGroupId>Group1</repositoryGroupId>
    <repositoryGroupId>Group2</repositoryGroupId>
</domain>""")
        hd = HarvesterData(self.tempdir)
        self.assertEquals(["Group1", "Group2"], hd.getRepositoryGroupIds(domainId="adomain"))
 
    def testGetRepositoryIds(self):
        open(join(self.tempdir, 'adomain.Group1.repositoryGroup'), 'w').write("""<?xml version="1.0" encoding="UTF-8"?>
<repositoryGroup>
  <id>Group1</id>
  <name xml:lang="nl">Groep1</name>
  <name xml:lang="en">Group1</name>
  <repositoryId>repository1</repositoryId>
  <repositoryId>repository2</repositoryId>
</repositoryGroup>""")
        hd = HarvesterData(self.tempdir)
        self.assertEquals(["repository1", "repository2"], hd.getRepositoryIds(domainId="adomain", repositoryGroupId="Group1"))

    def testGetRepositoryGroupId(self):
        open(join(self.tempdir, 'adomain.repository1.repository'), 'w').write("""<?xml version="1.0" encoding="UTF-8"?>
<repository>
  <id>repository1</id>
  <repositoryGroupId>Group1</repositoryGroupId>
</repository>""")
        hd = HarvesterData(self.tempdir)
        self.assertEquals("Group1", hd.getRepositoryGroupId(domainId="adomain", repositoryId="repository1"))
