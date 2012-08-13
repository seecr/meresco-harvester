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
# Copyright (C) 2011 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2011 Stichting Kennisnet http://www.kennisnet.nl
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

import unittest
from slowfoot import binderytools
from urllib import urlencode
from meresco.harvester.oairequest import OaiRequest, OAIError
from mockoairequest import MockOaiRequest


class OaiRequestTest(unittest.TestCase):
    def setUp(self):
        self.request = MockOaiRequest('mocktud')
        
    def testMockOaiRequest(self):
        binding = self.request.request({'verb': 'ListRecords', 'metadataPrefix': 'oai_dc'})
        self.assertEquals('2004-12-29T13:19:27Z', str(binding.OAI_PMH.responseDate))
        
    def testOtherOaiRequest(self):
        binding = self.request.request({'verb': 'GetRecord', 'metadataPrefix': 'oai_dc', 'identifier': 'oai:rep:12345'})
        self.assertEquals('2005-04-28T12:16:27Z', str(binding.OAI_PMH.responseDate))
        
    def testListRecordsError(self):
        try:
            self.request.listRecords(resumptionToken='BadResumptionToken')
            self.fail()
        except OAIError, e:
            self.assertEquals('The value of the resumptionToken argument is invalid or expired.',e.errorMessage())
            self.assertEquals(u'badResumptionToken', e.errorCode())
            
    def testListRecords(self):
        records, resumptionToken, responseDate = self.request.listRecords(metadataPrefix='oai_dc')
        self.assertEquals("TestToken", resumptionToken)
        self.assertEquals("2004-12-29T13:19:27Z", responseDate)
        self.assertEquals(3, len(records))
        self.assertEquals('oai:tudelft.nl:007087', str(records[0].header.identifier))
        if records[0].header.deleted:
            self.fail()
        
    def testIdentify(self):
        identify = self.request.identify()
        self.assertEquals('TU Delft digital repository', str(identify.repositoryName))

    def mockRequest(self, args):
        self.mockRequest_args = args
        return binderytools.bind_file('mocktud/00001.xml')
    
    def testListRecordArgs(self):
        self.request.request = self.mockRequest
        self.request.listRecords(metadataPrefix='kaas')
        self.assertEquals('kaas', self.mockRequest_args['metadataPrefix'])
        self.assert_(not self.mockRequest_args.has_key('resumptionToken'))
        self.request.listRecords(from_='from', until='until',set='set', metadataPrefix='prefix')
        self.assertEquals('from', self.mockRequest_args['from'])
        self.assertEquals('until', self.mockRequest_args['until'])
        self.assertEquals('set', self.mockRequest_args['set'])
        self.assertEquals('prefix', self.mockRequest_args['metadataPrefix'])
        
    def testGetRecord(self):
        record = self.request.getRecord(identifier='oai:rep:12345', metadataPrefix='oai_dc')
        self.assertEquals('oai:rep:12345',record.header.identifier)
        
    def testListRecordsWithAnEmptyList(self):
        records, resumptionToken, responseDate = self.request.listRecords(resumptionToken='EmptyListToken')
        self.assertEquals(0, len(records))
        self.assertEquals("", resumptionToken)
        self.assertEquals("2005-01-12T14:34:49Z", responseDate)

    def testBuildRequestUrl(self):
        oaiRequest = OaiRequest("http://x.y.z/oai")
        self.assertEquals("http://x.y.z/oai?verb=ListRecords&metadataPrefix=oai_dc", oaiRequest._buildRequestUrl([('verb', 'ListRecords'), ('metadataPrefix', 'oai_dc')]))

        oaiRequest = OaiRequest("http://x.y.z/oai?apikey=xyz123")
        self.assertEquals("http://x.y.z/oai?apikey=xyz123&verb=ListRecords&metadataPrefix=oai_dc", oaiRequest._buildRequestUrl([('verb', 'ListRecords'), ('metadataPrefix', 'oai_dc')]))

        
    def xtest_LIVE_Retrieve(self):
        request = OaiRequest('http://library.wur.nl/oai')
        amarabinding = request.request({'verb': 'ListRecords', 'metadataPrefix': 'oai_dc'})
        amarabinding.OAI_PMH
 
