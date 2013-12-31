## begin license ##
#
# "Meresco Harvester" consists of two subsystems, namely an OAI-harvester and
# a web-control panel.
# "Meresco Harvester" is originally called "Sahara" and was developed for
# SURFnet by:
# Seek You Too B.V. (CQ2) http://www.cq2.nl
#
# Copyright (C) 2013 Seecr (Seek You Too B.V.) http://seecr.nl
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

from seecr.test import SeecrTestCase
from meresco.harvester.deleteids import readIds, writeIds
from os.path import join

class DeleteIdsTest(SeecrTestCase):

    def testReadIds(self):
        filename = join(self.tempdir, "test.ids")
        open(filename, 'w').write("uploadId1\n%0A  uploadId2\n   uploadId3")

        self.assertEquals(['uploadId1', '\n  uploadId2', '   uploadId3'], readIds(filename))

    def testWriteIds(self):
        filename = join(self.tempdir, "test.ids")
        writeIds(filename, ['uploadId1', '\n  uploadId2', '   uploadId3'])
        self.assertEquals('uploadId1\n%0A  uploadId2\n   uploadId3\n', open(filename).read())

