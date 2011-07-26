from os.path import join
from cq2utils import CQ2TestCase

from meresco.harvester.harvesterdata import HarvesterData

class HarvesterDataTest(CQ2TestCase):

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
