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
# Copyright (C) 2007-2009, 2011 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2007-2009 Stichting Kennisnet Ict op school. http://www.kennisnetictopschool.nl
# Copyright (C) 2009 Tilburg University http://www.uvt.nl
# Copyright (C) 2011, 2020-2021 Stichting Kennisnet https://www.kennisnet.nl
# Copyright (C) 2020-2021 Data Archiving and Network Services https://dans.knaw.nl
# Copyright (C) 2020-2021 SURF https://www.surf.nl
# Copyright (C) 2020-2021 Seecr (Seek You Too B.V.) https://seecr.nl
# Copyright (C) 2020-2021 The Netherlands Institute for Sound and Vision https://beeldengeluid.nl
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
from meresco.harvester.ids import Ids, readIds, writeIds
from os.path import join

from contextlib import contextmanager
@contextmanager
def _Ids(*args, **kwargs):
    _ids = Ids(*args, **kwargs)
    try:
        yield _ids
    finally:
        _ids.close()

class IdsTest(SeecrTestCase):
    def testAddOne(self):
        with _Ids(self.tempdir + '/doesnotexistyet/', 'idstest') as ids:
            ids.add('id:1')
            self.assertEqual(1, len(ids))

    def testAddTwice(self):
        with _Ids(self.tempdir, 'idstest') as ids:
            ids.add('id:1')
            ids.add('id:1')
            self.assertEqual(1, len(ids))
            with open(self.tempdir + '/idstest.ids') as f:
                self.assertEqual(1, len(f.readlines()))

    def testInit(self):
        self.writeTestIds('one', ['id:1'])
        with _Ids(self.tempdir, 'one') as ids:
            self.assertEqual(1, len(ids))

        self.writeTestIds('three', ['id:1', 'id:2', 'id:3'])
        with _Ids(self.tempdir, 'three') as ids:
            self.assertEqual(3, len(ids))

    def testRemoveExistingId(self):
        self.writeTestIds('three', ['id:1', 'id:2', 'id:3'])
        with _Ids(self.tempdir, 'three') as ids:
            ids.remove('id:1')
            self.assertEqual(2, len(ids))
        with open(self.tempdir + '/three.ids') as fp:
            self.assertEqual(2, len(fp.readlines()))

    def testRemoveNonExistingId(self):
        self.writeTestIds('three', ['id:1', 'id:2', 'id:3'])

        with _Ids(self.tempdir, 'three') as ids:
            ids.remove('id:4')
            self.assertEqual(3, len(ids))
        with open(self.tempdir + '/three.ids') as fp:
            self.assertEqual(3, len(fp.readlines()))

    def testAddStrangeIds(self):
        with _Ids(self.tempdir, 'idstest') as ids:
            ids.add('id:1')
            ids.add('\n   id:1')
            ids.add('   id:2')
            with open(self.tempdir + '/idstest.ids') as fp:
                self.assertEqual(3, len(fp.readlines()))
            self.assertEqual(['id:1', '\n   id:1', '   id:2'], list(ids))

        with _Ids(self.tempdir, 'idstest') as ids:
            self.assertEqual(['id:1', '\n   id:1', '   id:2'], list(ids))

    def testRemoveStrangeId(self):
        with _Ids(self.tempdir, 'idstest') as ids:
            ids.add('id:1')
            ids.add('\n   id:1')
            ids.add('   id:2')
            self.assertEqual(['id:1', '\n   id:1', '   id:2'], list(ids))
            ids.remove('id:1')
            ids.remove('\n   id:1')
            ids.remove('   id:2')
            self.assertEqual([], list(ids))
    
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

    def testEscaping(self):
        ids = Ids(self.tempdir, "pruebo")
        try:
            ids.add("needs_\n_escape")
            with open(join(self.tempdir, "pruebo.ids")) as fp:
                self.assertEqual('needs_%0A_escape\n', fp.read())
            self.assertEqual(['needs_\n_escape'], ids.getIds())
            ids.reopen()
            with open(join(self.tempdir, "pruebo.ids")) as fp:
                self.assertEqual('needs_%0A_escape\n', fp.read())
            self.assertEqual(['needs_\n_escape'], ids.getIds())
            ids.reopen()
            self.assertEqual(['needs_\n_escape'], ids.getIds())
        finally:
            ids.close()


    def writeTestIds(self, name, ids):
        with open("{}/{}.ids".format(self.tempdir, name), 'w') as w:
            for anId in ids:
                w.write(anId + '\n')
