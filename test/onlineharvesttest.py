## begin license ##
#
#    "Meresco Harvester" consists of two subsystems, namely an OAI-harvester and
#    a web-control panel.
#    "Meresco Harvester" is originally called "Sahara" and was developed for 
#    SURFnet by:
#        Seek You Too B.V. (CQ2) http://www.cq2.nl
#    Copyright (C) 2006-2007 SURFnet B.V. http://www.surfnet.nl
#    Copyright (C) 2007-2008 Seek You Too (CQ2) http://www.cq2.nl
#    Copyright (C) 2007-2008 SURF Foundation. http://www.surf.nl
#    Copyright (C) 2007-2008 Stichting Kennisnet Ict op school.
#       http://www.kennisnetictopschool.nl
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
from merescoharvester.harvester.onlineharvest import OnlineHarvest
from StringIO import StringIO
from merescoharvester.harvester.mapping import Mapping, Upload, DataMapAssertionException, DEFAULT_DC_CODE
from cq2utils.wrappers import wrapp
import os

class OnlineHarvestTest(unittest.TestCase):
    def setUp(self):
        self.mock_createUpload_exception = ''
        self._testpath = os.path.realpath(os.path.curdir)

    def testRealMapping(self):
        output = StringIO()
        mapping = Mapping('mappingId')
        mapping.code = DEFAULT_DC_CODE
        data = 'file://%s/mocktud/00002.xml' % self._testpath
        harvest = OnlineHarvest(output)
        harvest.performMapping(mapping, data)
        self.assertEquals(3,output.getvalue().count('upload.id='))

    def testMapping(self):
        output = StringIO()
        mapping = self
        data = 'file://%s/mocktud/00002.xml' % self._testpath
        harvest = OnlineHarvest(output)
        harvest.performMapping(mapping, data)
        self.assertEquals(True, self.createUpload_args['doAssertions'])

    def testMappingWithDeletedRecord(self):
        output = StringIO()
        mapping = Mapping('mappingId')
        mapping.code = DEFAULT_DC_CODE
        data = 'file://%s/mocktud/00003.xml' % self._testpath
        harvest = OnlineHarvest(output)
        harvest.performMapping(mapping, data)
        self.assertEquals("upload.id=repository.id:oai:tudelft.nl:107087\nDELETED", output.getvalue().strip())

    def testMappingRaisesDataMapAssertionException(self):
        output = StringIO()
        mapping = self
        self.mock_createUpload_exception=DataMapAssertionException('O no, it\'s a snake!!')
        data = 'file://%s/mocktud/00002.xml' % self._testpath
        harvest = OnlineHarvest(output)
        harvest.performMapping(mapping, data)
        self.assertEquals(2,output.getvalue().count('upload.id='))

    def testMappingRaisesException(self):
        output = StringIO()
        mapping = self
        self.mock_createUpload_exception=Exception('Mushroom, mushroom')
        data = 'file://%s/mocktud/00002.xml' % self._testpath
        harvest = OnlineHarvest(output)
        try:
            harvest.performMapping(mapping, data)
            self.fail()
        except Exception, ex:
            self.assertEquals('Mushroom, mushroom',str(ex))
        self.assertEquals('',output.getvalue())



    #mocking
    def createUpload(self, repository, header, metadata, about, logger=None, doAssertions=False):
        self.createUpload_args={'doAssertions':doAssertions}
        if self.mock_createUpload_exception:
            ex = self.mock_createUpload_exception
            self.mock_createUpload_exception = None
            raise ex
        upload = Upload()
        return upload

    def createEmptyUpload(self, repository, header, metadata, about):
        upload = Upload()
        upload.init(repository, header, metadata, about)
        return upload
