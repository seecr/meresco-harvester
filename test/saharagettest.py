## begin license ##
#
#    "Meresco Harvester" consists of two subsystems, namely an OAI-harvester and
#    a web-control panel.
#    "Meresco Harvester" is originally called "Sahara" and was developed for
#    SURFnet by:
#        Seek You Too B.V. (CQ2) http://www.cq2.nl
#    Copyright (C) 2006-2007 SURFnet B.V. http://www.surfnet.nl
#    Copyright (C) 2007-2008 SURF Foundation. http://www.surf.nl
#    Copyright (C) 2007-2010 Seek You Too (CQ2) http://www.cq2.nl
#    Copyright (C) 2007-2009 Stichting Kennisnet Ict op school.
#       http://www.kennisnetictopschool.nl
#    Copyright (C) 2009 Tilburg University http://www.uvt.nl
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

import unittest
from merescoharvester.harvester.saharaget import SaharaGet, SaharaGetException
from slowfoot.wrappers import wrapp
from slowfoot import binderytools

class SaharaGetTest(unittest.TestCase):
    def setUp(self):
        self.get = SaharaGet('mocksahara.example.org')
        self.get._read = self.mock_read
        self.mock_read_args = []
        
    def testGetRepositoryIds(self):
        ids = self.get.getRepositoryIds('cq2Test1')
        self.assertEquals(['id1','id2'], ids)
        self.assertEquals(1,len(self.mock_read_args))
        self.assertEquals({'verb':'GetRepositories', 'domainId':'cq2Test1'},
                            self.mock_read_args[0])
        
    def testGetRepository(self):
        repository = self.get.getRepository('cq2Test1', 'cq2Repository2_1')
        self.assertEquals('cq2Test1', repository.domainId)
        self.assertEquals('cq2Repository2_1', repository.id)
        self.assertEquals('set', repository.set)
        self.assertEquals('collection', repository.collection)
        self.assertEquals('oai_dc', repository.metadataPrefix)
        self.assertEquals('http://baseurl.example.org', repository.baseurl)
        self.assertEquals('aTargetId', repository.targetId)
        self.assertEquals('aMappingId', repository.mappingId)
        self.assertEquals('true', repository.use)
        self.assertEquals('cq2Group2', repository.repositoryGroupId)
        # Test deprecated stuff
        self.assertEquals(repository.id, repository.key)
        self.assertEquals(repository.repositoryGroupId, repository.institutionkey)
        # Test read call
        self.assertEquals(1, len(self.mock_read_args))
        self.assertEquals('GetRepository', self.mock_read_args[0]['verb'])
        
        target = repository.target()
        self.assertEquals(repository.targetId, target.id)
        self.assertEquals(2, len(self.mock_read_args))
        self.assertEquals('GetTarget', self.mock_read_args[1]['verb'])
        
        mapping = repository.mapping()
        self.assertEquals(repository.mappingId, mapping.id)
        self.assertEquals(3, len(self.mock_read_args))
        self.assertEquals('GetMapping', self.mock_read_args[2]['verb'])
        
    def testSaharaUrl(self):
        s = SaharaGet('sahara.example.org')
        self.assertEquals('sahara.example.org', s.saharaurl)
        s = SaharaGet('sahara.other.example.org')
        self.assertEquals('sahara.other.example.org', s.saharaurl)
        
    def testSaharaGetError(self):
        try:
            self.get.getRepository('error', 'repositoryId')
            self.fail()
        except SaharaGetException, sge:
            self.assertEquals("The verb 'Blah' is not recognized", str(sge))
        
    def testGetTarget(self):
        target = self.get.getTarget('cq2Test1', 'aTargetId')
        self.assertEquals('cq2Test1', target.domainId)
        self.assertEquals('aTargetId', target.id)
        self.assertEquals('A Target', target.name)
        self.assertEquals('aUsername', target.username)
        self.assertEquals('aPassword', target.password)
        self.assertEquals('http://baseurl.example.org', target.baseurl)
        self.assertEquals('3128', target.port)
        self.assertEquals('/aPath', target.path)
        self.assertEquals(['id1', 'id2'], target.delegate)
    
    def mock_read(self, **kwargs):
        self.mock_read_args.append(kwargs)
        verb = kwargs['verb']
        if kwargs['domainId'] == 'error':
            return wrapp(binderytools.bind_string(GETERROR))
        elif verb == 'GetRepository':
            return wrapp(binderytools.bind_string(GETREPOSITORY))
        elif verb == 'GetRepositories':
            return wrapp(binderytools.bind_string(GETREPOSITORIES))
        elif verb == 'GetTarget':
            return wrapp(binderytools.bind_string(GETTARGET))
        elif verb == 'GetMapping':
            return wrapp(binderytools.bind_string(GETMAPPING))
        
GETREPOSITORY = """<?xml version="1.0" encoding="UTF-8"?>
<saharaget>
<responseDate>2006-01-24T13:16:41Z</responseDate>
<request>
<verb>GetRepository</verb>
    <domainId>cq2Test1</domainId>
    <repositoryId>cq2Repository2_1</repositoryId>
</request>
<GetRepository>
<repository>
    <use>true</use>
    <action>refresh</action>
    <id>cq2Repository2_1</id>
    <baseurl>http://baseurl.example.org</baseurl>
    <set>set</set>
    <collection>collection</collection>
    <metadataPrefix>oai_dc</metadataPrefix>
    <targetId>aTargetId</targetId>
    <mappingId>aMappingId</mappingId>
    <repositoryGroupId>cq2Group2</repositoryGroupId>
</repository>
</GetRepository>
</saharaget>
"""

GETREPOSITORIES = """<?xml version="1.0" encoding="UTF-8"?>
<saharaget>
<responseDate>2006-01-24T13:16:41Z</responseDate>
<request>
<verb>GetRepositories</verb>
    <domainId>cq2Test1</domainId>
</request>
<GetRepositories>
<repository>
    <use>true</use>
    <action>refresh</action>
    <id>id1</id>
    <baseurl>http://baseurl.example.org</baseurl>
    <set>set</set>
    <collection>collection</collection>
    <metadataPrefix>oai_dc</metadataPrefix>
    <targetId>aTargetId</targetId>
    <mappingId>aMappingId</mappingId>
    <repositoryGroupId>cq2Group2</repositoryGroupId>
</repository>
<repository>
    <use>true</use>
    <action>refresh</action>
    <id>id2</id>
    <baseurl>http://baseurl.example.org</baseurl>
    <set>set</set>
    <collection>collection</collection>
    <metadataPrefix>oai_dc</metadataPrefix>
    <targetId>aTargetId</targetId>
    <mappingId>aMappingId</mappingId>
    <repositoryGroupId>cq2Group2</repositoryGroupId>
</repository>
</GetRepositories>
</saharaget>
"""

GETTARGET = """<?xml version="1.0" encoding="UTF-8"?>
<saharaget>
<responseDate>2006-01-24T13:16:41Z</responseDate>
<request>
<verb>GetTarget</verb>
<domainId>cq2Test1</domainId>
<targetId>aTargetId</targetId>
</request>
<GetTarget>
<target>
    <id>aTargetId</id>
    <name>A Target</name>
    <username>aUsername</username>
    <password>aPassword</password>
    <baseurl>http://baseurl.example.org</baseurl>
    <port>3128</port>
    <path>/aPath</path>
    <delegate>id1</delegate>
    <delegate>id2</delegate>
</target>
</GetTarget>
</saharaget>
"""

GETMAPPING = """<?xml version="1.0" encoding="UTF-8"?>
<saharaget>
<responseDate>2006-01-24T13:16:41Z</responseDate>
<request>
<verb>GetMapping</verb>
<domainId>cq2Test1</domainId>
<mappingId>aMappingId</mappingId>
</request>
<GetMapping>
    <mapping>
    <id>aMappingId</id>
    <name>lorenet_lom2surf</name>
    <description>Vulling:
    generic1 = upload.id (&lt;repo.id&gt;:&lt;oai.identifier&gt;)
    generic2 = Content Package URL
    generic3 = institutionId
    generic5 = studierichting
    url = http://lorenet.cq2.org/luzi.showrecord?repository=&lt;repo.id&gt;&amp;identifier=&lt;input.header.identifier&gt;</description>
    
    <code># template
showmetadataurl = 'http://lorenet.cq2.org/showrecord?'+metadataquery
if input.repository.id == 'utlore' and locations:
packageurl = locations[0]
else:
packageurl = 'http://ims.lorenet.org/imscp?'+urlencode({'metadataUrl':getmetadataurl})

upload.fields['url'] = showmetadataurl
</code>
</mapping>
</GetMapping>
</saharaget>
"""

GETERROR = """<?xml version="1.0" encoding="UTF-8"?>
<saharaget>
<responseDate>2006-02-13T16:15:12Z</responseDate>
<request>https://sahara.cq2.org/saharaget?verb=Blah&amp;domainId=mydomain</request>
<error code="badVerb">The verb 'Blah' is not recognized</error>
</saharaget>
"""

