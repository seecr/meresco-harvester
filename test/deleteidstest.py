## begin license ##
#
# "Meresco Harvester" consists of two subsystems, namely an OAI-harvester and
# a web-control panel.
# "Meresco Harvester" is originally called "Sahara" and was developed for
# SURFnet by:
# Seek You Too B.V. (CQ2) http://www.cq2.nl
#
# Copyright (C) 2013, 2020 Seecr (Seek You Too B.V.) https://seecr.nl
# Copyright (C) 2020 Netherlands Institute for Sound and Vision https://beeldengeluid.nl/
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

from seecr.test import SeecrTestCase, CallTrace
from meresco.components import Bucket
from meresco.harvester.deleteids import readIds, writeIds, DeleteIds
from os.path import join

class DeleteIdsTest(SeecrTestCase):

    def testReadIds(self):
        filename = join(self.tempdir, "test.ids")
        with open(filename, "w") as fp:
            fp.write("uploadId1\n%0A  uploadId2\n   uploadId3")

        self.assertEqual(['uploadId1', '\n  uploadId2', '   uploadId3'], readIds(filename))

    def testWriteIds(self):
        filename = join(self.tempdir, "test.ids")
        writeIds(filename, ['uploadId1', '\n  uploadId2', '   uploadId3'])
        with open(filename) as fp:
            self.assertEqual('uploadId1\n%0A  uploadId2\n   uploadId3\n', fp.read())

    def testDeleteWithError(self):
        writeIds(join(self.tempdir, "test.ids"), ['id:{}'.format(i) for i in xrange(10)])
        deleteIds = DeleteIds(Bucket(id='test'), self.tempdir)
        def delete(anUpload):
            if anUpload.id == 'id:7':
                raise ValueError('fout')
        observer = CallTrace(methods=dict(delete=delete))
        deleteIds.addObserver(observer)
        self.assertRaises(ValueError, lambda: deleteIds.delete())
        self.assertEqual(['id:7', 'id:8','id:9'], readIds(join(self.tempdir, 'test.ids')))
        self.assertEqual(8, len([m for m in observer.calledMethodNames() if m == 'delete']))

    def testDeleteWithBatches(self):
        writeIds(join(self.tempdir, "test.ids"), ['id:{}'.format(i) for i in xrange(10)])
        deleteIds = DeleteIds(Bucket(id='test'), self.tempdir, batchSize=3)
        origWriteIds = deleteIds._writeIds
        idBatches = []
        def myWriteIds(ids):
            idBatches.append(ids)
            origWriteIds(ids)
        deleteIds._writeIds = myWriteIds
        observer = CallTrace()
        deleteIds.addObserver(observer)
        deleteIds.delete()
        self.assertEqual([], readIds(join(self.tempdir, 'test.ids')))
        self.assertEqual(10, len([m for m in observer.calledMethodNames() if m == 'delete']))
        self.assertEqual([7, 4, 1, 0], [len(b) for b in idBatches])

