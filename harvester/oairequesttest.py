#!/usr/bin/env python
## begin license ##
#
#    "Sahara" consists of two subsystems, namely an OAI-harvester and a web-control panel.
#    "Sahara" is developed for SURFnet by:
#        Seek You Too B.V. (CQ2) http://www.cq2.nl
#    Copyright (C) 2006,2007 SURFnet B.V. http://www.surfnet.nl
#
#    This file is part of "Sahara"
#
#    "Sahara" is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    "Sahara" is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with "Sahara"; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
## end license ##
#
# Copyright (C) 2005 Seek You Too B.V. http://www.cq2.nl
#
# $Id: oairequesttest.py 4825 2007-04-16 13:36:24Z TJ $

import unittest
from cq2utils import binderytools
from urllib import urlencode
from oairequest import OAIRequest, MockOAIRequest, OAIError

class OAIRequestTest(unittest.TestCase):
	def setUp(self):
		self.request = MockOAIRequest('mocktud')
		
		
	def testMockOAIRequest(self):
		binding = self.request.request({'verb':'ListRecords','metadataPrefix':'oai_dc'})
		self.assertEquals('2004-12-29T13:19:27Z',str(binding.OAI_PMH.responseDate))
		
	def testOtherOAIRequest(self):
		binding = self.request.request({'verb':'GetRecord','metadataPrefix':'oai_dc', 'identifier':'oai:rep:00000'})
		self.assertEquals('2005-04-28T12:48:13Z',str(binding.OAI_PMH.responseDate))
		
	def testListRecordsError(self):
		try:
			self.request.listRecords(resumptionToken='BadResumptionToken')
			self.fail()
		except OAIError, e:
			self.assertEquals('The value of the resumptionToken argument is invalid or expired.',str(e))
			self.assertEquals( u'badResumptionToken',e.code())
			
	def testListRecords(self):
		records = self.request.listRecords(metadataPrefix='oai_dc')
		i = 0
		for r in records:	
			i+=1
		self.assertEquals(3,i)
		self.assertEquals('oai:tudelft.nl:007087',str(records[0].header.identifier))
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
		self.assertEquals('kaas',self.mockRequest_args['metadataPrefix'])
		self.assert_(not self.mockRequest_args.has_key('resumptionToken'))
		self.request.listRecords(from_='from',until='until',set='set',metadataPrefix='prefix')
		self.assertEquals('from',self.mockRequest_args['from'])
		self.assertEquals('until',self.mockRequest_args['until'])
		self.assertEquals('set',self.mockRequest_args['set'])
		self.assertEquals('prefix',self.mockRequest_args['metadataPrefix'])
		
	def testGetRecord(self):
		record = self.request.getRecord(identifier='oai:rep:12345', metadataPrefix='oai_dc')
		self.assertEquals('oai:rep:12345',record.header.identifier)
		
	def testListRecordsWithAnEmptyList(self):
		records = self.request.listRecords(resumptionToken='EmptyListToken')
		i = 0
		for record in records: i+=1
		self.assertEquals(0,i)
		
		
	def xtest_LIVE_Retrieve(self):
		request = OAIRequest('http://library.wur.nl/oai')
		amarabinding = request.request({'verb':'ListRecords','metadataPrefix':'oai_dc'})
		amarabinding.OAI_PMH
					
if __name__ == '__main__': unittest.main()
