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
# Teddy Uploader Test
#

from StringIO import StringIO
import unittest, os, sys
import teddyuploader, mapping
from virtualuploader import VirtualUploader, UploaderException
from cq2utils.networking.growlclient import GrowlClient
from cq2utils.calltrace import CallTrace

def createUpload(aDictionary):
	upload = mapping.Upload()
	upload.setProperty('sortfields', ['generic4'])
	upload.fields = aDictionary
	return upload

class MyTarget:
	def __init__(self):
		self.__dict__ = {'hostname': 'aap.noot.mies', 'port': '22', 'username': 'mies', 'privateKey': 'HGDJWYDINSIKND'}

target = MyTarget()

class MockGrowlClient(GrowlClient):
	
	def __init__(self):
		self._sent = []
		self._parts = []
		self._stream = self
		self._currentDocumentId = None
		self._readResult = lambda id: "OK"
		self.flush = lambda: None
	
	def send(self, anId, documentBody):
		self.sent.append((anId, documentBody))
		
	def write(self, aString):
		pass
		
	def startPart(self, partName, partType):
		partStream = StringIO()
		self._parts.append([partName, partType, partStream])
		return partStream
	
	def getByteStream(self):
		return None
	
	def stopPart(self):
		partStreamIndex = 2
		self._parts[-1][partStreamIndex] = self._parts[-1][partStreamIndex].getvalue() #makes the stream readable
		
class TeddyUploaderTest(unittest.TestCase):

	def createUploader(self):
 		result = teddyuploader.TeddyUploader(target, self, 'myCollection')
		result._growlClient = MockGrowlClient()
		return result

	def testInheritFromVirtualUploader(self):
		self.assert_(isinstance(self.createUploader(), VirtualUploader))
	
	def testSend(self):
		uploader = self.createUploader()
		uploader.send(createUpload({'dcsubject':'boom', 'generic4':'vuur'}))
		parts = uploader._growlClient._parts
		self.assertEquals([['fields', 'text/xml', '<fields><field name="generic4" tokenize="false">vuur</field><field name="dcsubject">boom</field><field name="collection">myCollection</field></fields>']], parts)
	
	def testSendWithOriginalFromNowOnANormalField(self):
		uploader = self.createUploader()
		uploader.send(createUpload({'dcsubject':'boom', 'generic4':'vuur', 'original:dc':'<fiets>vis</fiets>'}))
		parts = uploader._growlClient._parts
		self.assertEquals(1, len(parts))
		self.assertEquals(['fields', 'text/xml', '<fields><field name="generic4" tokenize="false">vuur</field><field name="dcsubject">boom</field><field name="original:dc">&lt;fiets&gt;vis&lt;/fiets&gt;</field><field name="collection">myCollection</field></fields>'], parts[0])
		
	def testSendWithParts(self):
		uploader = self.createUploader()
		upload = createUpload({'dcsubject':'boom'})
		upload.parts['partone'] = 'Part One'
		upload.parts['parttwo'] = '<xml>Part Two</xml>'
		uploader.send(upload)
		parts = uploader._growlClient._parts
		self.assertEquals(3, len(parts))
		self.assertEquals(['partone', 'text/plain', 'Part One'], parts[1])
		self.assertEquals(['parttwo', 'text/plain', '&lt;xml&gt;Part Two&lt;/xml&gt;'], parts[2])
		
	def testSendMultipleValuesInList(self):
		uploader = self.createUploader()
		uploader.send(createUpload({'creator': ['ben', 'berend', 'beun']}))
		parts = uploader._growlClient._parts
		self.assertEquals([['fields', 'text/xml', '<fields><field name="creator">ben</field><field name="creator">berend</field><field name="creator">beun</field><field name="collection">myCollection</field></fields>']], parts)

	def testDelete(self):
 		uploader = teddyuploader.TeddyUploader(target, self, 'myCollection')
		client = CallTrace('GrowlClient')
		uploader._growlClient = client
		upload = mapping.Upload()
		upload.id = '1234'
		uploader.delete(upload)
		
		self.assertEquals(1, len(client.calledMethods))
		self.assertEquals("delete('1234')", str(client.calledMethods[0]))
		

	def _removeWhiteSpace(self, aString):
		return ''.join(aString.split())

	def assertEqualsWS(self, s1, s2):
		self.assertEquals(self._removeWhiteSpace(s1), self._removeWhiteSpace(s2))	

	def logLine(self, *args, **kwargs):
		"""Self Shunt"""
		pass
		
if __name__ == '__main__':
	unittest.main()
