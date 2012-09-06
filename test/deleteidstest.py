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

