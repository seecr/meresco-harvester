## begin license ##
#
# "Meresco Harvester" consists of two subsystems, namely an OAI-harvester and
# a web-control panel.
# "Meresco Harvester" is originally called "Sahara" and was developed for
# SURFnet by:
# Seek You Too B.V. (CQ2) http://www.cq2.nl
#
# Copyright (C) 2006-2007 SURFnet B.V. http://www.surfnet.nl
# Copyright (C) 2007-2008 SURF Foundation. http://www.surf.nl
# Copyright (C) 2007-2011 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2007-2009 Stichting Kennisnet Ict op school. http://www.kennisnetictopschool.nl
# Copyright (C) 2009 Tilburg University http://www.uvt.nl
# Copyright (C) 2011, 2015 Stichting Kennisnet http://www.kennisnet.nl
# Copyright (C) 2013, 2015 Seecr (Seek You Too B.V.) http://seecr.nl
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

from meresco.components.json import JsonDict
from meresco.harvester.saharaget import SaharaGet, SaharaGetException
from StringIO import StringIO
from meresco.harvester.namespaces import namespaces
from seecr.test import SeecrTestCase, CallTrace
from urlparse import parse_qs, urlparse

class SaharaGetTest(SeecrTestCase):
    def setUp(self):
        SeecrTestCase.setUp(self)
        self.get = SaharaGet('http://localhost:1234')
        self.urlopen = CallTrace()
        self.get._urlopen = self.urlopen._urlopen

    def testGetRepositoryIds(self):
        self.setResponse({'GetRepositoryIds':["id1", "id2"]})
        ids = self.get.getRepositoryIds('cq2Test1')
        self.assertEquals(['id1','id2'], ids)
        url, query = self.getRequest()
        self.assertEqual('http://localhost:1234/get', url)
        self.assertEqual({'verb': ['GetRepositoryIds'], 'domainId': ['cq2Test1']}, query)

    def testGetRepository(self):
        self.setResponse({'GetRepository': dict(
                identifier='cq2Repository2_1',
                set='set',
                metadataPrefix='oai_dc',
                collection='collection',
                baseurl="http://baseurl.example.org",
                targetId="aTargetId",
                mappingId="aMappingId",
                use=True,
                repositoryGroupId='cq2Group2',
                complete=False,
                action=None,
                maximumIgnore=100
            ),
            'GetTarget': dict(identifier='aTargetId'),
            'GetMapping': dict(identifier='aMappingId'),
        })
        repository = self.get.getRepository('cq2Test1', 'cq2Repository2_1')
        self.assertEquals('cq2Test1', repository.domainId)
        self.assertEquals('cq2Repository2_1', repository.id)
        self.assertEquals('set', repository.set)
        self.assertEquals('collection', repository.collection)
        self.assertEquals('oai_dc', repository.metadataPrefix)
        self.assertEquals('http://baseurl.example.org', repository.baseurl)
        self.assertEquals('aTargetId', repository.targetId)
        self.assertEquals('aMappingId', repository.mappingId)
        self.assertEquals(True, repository.use)
        self.assertEquals('cq2Group2', repository.repositoryGroupId)
        # Test read call
        url, query = self.getRequest()
        self.assertEqual('http://localhost:1234/get', url)
        self.assertEqual({'verb': ['GetRepository'], 'domainId': ['cq2Test1'], 'identifier': ['cq2Repository2_1']}, query)

        target = repository.target()
        self.assertEquals(repository.targetId, target.id)
        url, query = self.getRequest()
        self.assertEqual('http://localhost:1234/get', url)
        self.assertEqual({'verb': ['GetTarget'], 'identifier': [repository.targetId]}, query)

        mapping = repository.mapping()
        self.assertEquals(repository.mappingId, mapping.id)
        url, query = self.getRequest()
        self.assertEqual('http://localhost:1234/get', url)
        self.assertEqual({'verb': ['GetMapping'], 'identifier': [repository.mappingId]}, query)

    def testSaharaGetError(self):
        self.setError(dict(message="The verb 'Blah' is not recognized", code='badVerb'))
        try:
            self.get.getRepository('error', 'repositoryId')
            self.fail()
        except SaharaGetException, sge:
            self.assertEquals("The verb 'Blah' is not recognized", str(sge))

    def testGetTarget(self):
        self.setResponse({'GetTarget': dict(
                identifier='aTargetId',
                name='A Target',
                username='aUsername',
                password='aPassword',
                baseurl='http://baseurl.example.org',
                port=3128,
                path='/aPath',
                delegate=['id1', 'id2'],
            )})
        target = self.get.getTarget('cq2Test1', 'aTargetId')
        self.assertEquals('cq2Test1', target.domainId)
        self.assertEquals('aTargetId', target.id)
        self.assertEquals('A Target', target.name)
        self.assertEquals('aUsername', target.username)
        self.assertEquals('aPassword', target.password)
        self.assertEquals('http://baseurl.example.org', target.baseurl)
        self.assertEquals(3128, target.port)
        self.assertEquals('/aPath', target.path)
        self.assertEquals(['id1', 'id2'], target.delegate)

    def setError(self, errorDict):
        self.urlopen.methods['_urlopen'] = lambda *args, **kwargs: StringIO(JsonDict(
                request={"request":"ignored"},
                error=errorDict
            ).dumps())

    def setResponse(self, responseDict):
        self.urlopen.methods['_urlopen'] = lambda *args, **kwargs: StringIO(JsonDict(
                request={"request":"ignored"},
                response=responseDict
            ).dumps())

    def getRequest(self):
        fullurl = self.urlopen.calledMethods[-1].args[0]
        splitted = urlparse(fullurl)
        return '{0.scheme}://{0.netloc}{0.path}'.format(splitted), parse_qs(splitted.query)


GETREPOSITORY = """<?xml version="1.0" encoding="UTF-8"?>
<saharaget xmlns="%(sahara)s">
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
""" % namespaces

GETREPOSITORIES = """<?xml version="1.0" encoding="UTF-8"?>
<saharaget xmlns="%(sahara)s">
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
""" % namespaces

GETTARGET = """<?xml version="1.0" encoding="UTF-8"?>
<saharaget xmlns="%(sahara)s">
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
""" % namespaces

GETMAPPING = """<?xml version="1.0" encoding="UTF-8"?>
<saharaget xmlns="%(sahara)s">
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
""" % namespaces

GETERROR = """<?xml version="1.0" encoding="UTF-8"?>
<saharaget xmlns="%(sahara)s">
<responseDate>2006-02-13T16:15:12Z</responseDate>
<request>https://sahara.cq2.org/saharaget?verb=Blah&amp;domainId=mydomain</request>
<error code="badVerb">The verb 'Blah' is not recognized</error>
</saharaget>
""" % namespaces

