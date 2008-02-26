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
# 
import unittest
from repositorystatus import RepositoryStatus
import tempfile
from cStringIO import StringIO

class RepositoryStatusTest(unittest.TestCase):
	def setUp(self):
		self.repositoryStatus = RepositoryStatus()
	
	def testZero(self):
		self.assertEquals('', self.repositoryStatus.lastSuccesDate)
		self.assertEquals('', self.repositoryStatus.harvested)
		self.assertEquals('', self.repositoryStatus.uploaded)
		self.assertEquals('', self.repositoryStatus.deleted)
		self.assertEquals('', self.repositoryStatus.total)
		self.assertEquals(0, len(self.repositoryStatus.errors))
		
	def testAddSucces(self):
		self.repositoryStatus.addSucces('2006-03-13 12:13:14.456','Harvested/Uploaded/Deleted/Total: 200/199/1/1542')
		self.assertEquals('2006-03-13T12:13:14Z', self.repositoryStatus.lastSuccesDate)
		self.assertEquals('200', self.repositoryStatus.harvested)
		self.assertEquals('199', self.repositoryStatus.uploaded)
		self.assertEquals('1', self.repositoryStatus.deleted)
		self.assertEquals('1542', self.repositoryStatus.total)
		self.assertEquals(0, len(self.repositoryStatus.errors))
	
	def testAddSuccesDates(self):
		self.repositoryStatus.addSucces('2006-03-01 12:13:14.456','Harvested/Uploaded/Deleted/Total: 300/297/3/1100')
		self.repositoryStatus.addSucces('2006-03-03 12:13:14.456','Harvested/Uploaded/Deleted/Total: 200/199/1/1542')
		self.assertEquals('2006-03-03T12:13:14Z', self.repositoryStatus.lastSuccesDate)
		self.assertEquals('200', self.repositoryStatus.harvested)
		self.assertEquals('199', self.repositoryStatus.uploaded)
		self.assertEquals('1', self.repositoryStatus.deleted)
		self.assertEquals('1542', self.repositoryStatus.total)
		self.assertEquals(0, len(self.repositoryStatus.errors))
	
	def testAddOnlyErrors(self):
		self.repositoryStatus.addError('2006-03-01 12:13:14.456','Sorry, but the VM has crashed.')
		self.assertEquals('', self.repositoryStatus.lastSuccesDate)
		self.assertEquals('', self.repositoryStatus.harvested)
		self.assertEquals('', self.repositoryStatus.uploaded)
		self.assertEquals('', self.repositoryStatus.deleted)
		self.assertEquals('', self.repositoryStatus.total)
		self.assertEquals(1, len(self.repositoryStatus.errors))
		self.assertEquals(('2006-03-01T12:13:14Z','Sorry, but the VM has crashed.'), self.repositoryStatus.errors[0])
	
	def testAddTwoErrors(self):
		self.repositoryStatus.addError('2006-03-01 12:13:14.456','Sorry, but the VM has crashed.')
		self.repositoryStatus.addError('2006-03-02 12:13:14.456','java.lang.NullPointerException.')
		self.assertEquals('', self.repositoryStatus.lastSuccesDate)
		self.assertEquals('', self.repositoryStatus.harvested)
		self.assertEquals('', self.repositoryStatus.uploaded)
		self.assertEquals('', self.repositoryStatus.deleted)
		self.assertEquals('', self.repositoryStatus.total)
		self.assertEquals(2, len(self.repositoryStatus.errors))
		self.assertEquals(('2006-03-01T12:13:14Z','Sorry, but the VM has crashed.'), self.repositoryStatus.errors[0])
		self.assertEquals(('2006-03-02T12:13:14Z','java.lang.NullPointerException.'), self.repositoryStatus.errors[1])
	
	def testAddErrorsAfterSucces(self):
		self.repositoryStatus.addSucces('2006-03-03 12:13:14.456','Harvested/Uploaded/Deleted/Total: 200/199/1/1542')
		self.repositoryStatus.addError('2006-03-04 12:13:14.456','Sorry, but the VM has crashed.')
		self.assertEquals('2006-03-03T12:13:14Z', self.repositoryStatus.lastSuccesDate)
		self.assertEquals('200', self.repositoryStatus.harvested)
		self.assertEquals('199', self.repositoryStatus.uploaded)
		self.assertEquals('1', self.repositoryStatus.deleted)
		self.assertEquals('1542', self.repositoryStatus.total)
		self.assertEquals(1, len(self.repositoryStatus.errors))
		self.assertEquals(('2006-03-04T12:13:14Z','Sorry, but the VM has crashed.'), self.repositoryStatus.errors[0])
	
	def testAddErrorsBeforeSucces(self):
		self.repositoryStatus.addError('2006-03-02 12:13:14.456','Sorry, but the VM has crashed.')
		self.repositoryStatus.addSucces('2006-03-03 12:13:14.456','Harvested/Uploaded/Deleted/Total: 200/199/1/1542')
		self.assertEquals('2006-03-03T12:13:14Z', self.repositoryStatus.lastSuccesDate)
		self.assertEquals('200', self.repositoryStatus.harvested)
		self.assertEquals('199', self.repositoryStatus.uploaded)
		self.assertEquals('1', self.repositoryStatus.deleted)
		self.assertEquals('1542', self.repositoryStatus.total)
		self.assertEquals(0, len(self.repositoryStatus.errors))
	
	def testIntegration(self):
		streamIn = StringIO("""[2005-08-20 20:00:00.456]\tERROR\t[repositoryId]\tError 1
[2005-08-21 20:00:00.456]\tSUCCES\t[repositoryId]\tHarvested/Uploaded/Deleted/Total: 4/3/2/10
[2005-08-22 00:00:00.456]\tSUCCES\t[repositoryId]\tHarvested/Uploaded/Deleted/Total: 8/4/3/16
[2005-08-22 20:00:00.456]\tERROR\t[repositoryId]\tError 2
[2005-08-23 20:00:00.456]\tERROR\t[repositoryId]\tError 3
[2005-08-23 20:00:01.456]\tERROR\t[repositoryId]\tError 4
[2005-08-23 20:00:02.456]\tERROR\t[repositoryId]\tError 5
[2005-08-24 00:00:00.456]\tSUCCES\t[repositoryId]\tHarvested/Uploaded/Deleted/Total: 8/4/3/20
[2005-08-24 20:00:00.456]\tERROR\t[repositoryId]\tError With Scary Characters < & > " '
""")
		streamOut = StringIO()
		self.repositoryStatus.main(streamIn, streamOut)
		self.assertEquals("""<?xml version="1.0"?>
<status>
  <lastHarvestDate>2005-08-24T00:00:00Z</lastHarvestDate>
  <harvested>8</harvested>
  <uploaded>4</uploaded>
  <deleted>3</deleted>
  <total>20</total>
  <totalerrors>1</totalerrors>
  <recenterrors>
    <error date="2005-08-24T20:00:00Z">Error With Scary Characters &lt; &amp; &gt; " '</error>
  </recenterrors>
</status>""", streamOut.getvalue())
		
	def testZero(self):
		streamIn = StringIO()
		streamOut = StringIO()
		self.repositoryStatus.main(streamIn, streamOut)
		self.assertEquals("""<?xml version="1.0"?>
<status>
  <lastHarvestDate></lastHarvestDate>
  <harvested></harvested>
  <uploaded></uploaded>
  <deleted></deleted>
  <total></total>
  <totalerrors>0</totalerrors>
  <recenterrors></recenterrors>
</status>""", streamOut.getvalue())

if __name__ == '__main__':
	unittest.main()
